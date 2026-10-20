"""
Fine-tune the disease CNN on real-field photos (PlantDoc) together with lab photos (PlantVillage).

Why: a model trained only on PlantVillage (single leaf, plain background) does poorly on farmers'
phone photos (cluttered backgrounds, several leaves, shadows). Mixing in field photos teaches the
CNN to ignore the background.

Starts from   : ml/models/disease_cnn.pt (the lab-trained model)
Data          : PlantVillage subset train split + PlantDoc train (85%), PlantDoc oversampled x3
Validation    : PlantVillage val split + PlantDoc train (15% held out) — best epoch = mean of both
Test          : PlantVillage test split (lab) and PlantDoc official test split (field)
Output        : ml/models/disease_cnn_field.pt (candidate) + ml/evaluation/disease_field_report.json
                The candidate is NOT deployed automatically; compare it first (see docs).

Usage (project root):
    python ml/datasets/fetch_plantdoc.py
    python ml/training/finetune_field.py --epochs 4
    python ml/training/finetune_field.py --epochs 4 --resume      # after an interruption
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "training"))
sys.path.insert(0, str(ROOT / "ml" / "evaluation"))
import train_disease_cnn as base  # noqa: E402  (reuses dataset, split, epoch loop, model builder)
from evaluate_disease import evaluate  # noqa: E402
from app.services.disease_service import DiseaseModel  # noqa: E402

PLANTDOC = ROOT / "ml" / "datasets" / "plantdoc"
INIT_MODEL = base.MODEL_OUT
CANDIDATE_OUT = ROOT / "ml" / "models" / "disease_cnn_field.pt"
RESUME_OUT = ROOT / "ml" / "models" / "disease_cnn_field_resume.pt"
REPORT_OUT = ROOT / "ml" / "evaluation" / "disease_field_report.json"


def plantdoc_items(split: str, classes: list[str]) -> list[tuple[Path, int]]:
    items = []
    for folder in sorted(p for p in (PLANTDOC / split).iterdir() if p.is_dir()):
        label = classes.index(folder.name)
        items += [(f, label) for f in sorted(folder.glob("*.jpg"))]
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--field-oversample", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    init = torch.load(INIT_MODEL, map_location="cpu", weights_only=True)
    classes = init["class_names"]
    lab_classes, lab_train, lab_val, lab_test = base.stratified_split(args.seed)
    assert lab_classes == classes, "PlantVillage classes do not match the initial model"

    field_all = plantdoc_items("train", classes)
    random.Random(args.seed).shuffle(field_all)
    n_val = round(0.15 * len(field_all))
    field_val, field_train = field_all[:n_val], field_all[n_val:]
    field_test = plantdoc_items("test", classes)
    train_items = lab_train + field_train * args.field_oversample
    print(f"lab train {len(lab_train)} | field train {len(field_train)} (x{args.field_oversample}) | "
          f"lab val {len(lab_val)} | field val {len(field_val)} | lab test {len(lab_test)} | field test {len(field_test)}")

    # Stronger augmentation than lab training: field photos vary in framing, light and blur
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(base.IMAGE_SIZE, scale=(0.35, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(25),
        transforms.ColorJitter(0.4, 0.4, 0.4, 0.05),
        transforms.RandomApply([transforms.GaussianBlur(5, sigma=(0.1, 2.0))], p=0.2),
        transforms.ToTensor(),
        transforms.Normalize(base.MEAN, base.STD),
    ])
    eval_tf = transforms.Compose([transforms.Resize(base.RESIZE), transforms.CenterCrop(base.IMAGE_SIZE),
                                  transforms.ToTensor(), transforms.Normalize(base.MEAN, base.STD)])
    loader = lambda items, tf, shuffle, bs: DataLoader(base.LeafDataset(items, tf), batch_size=bs, shuffle=shuffle,  # noqa: E731
                                                       num_workers=args.workers, persistent_workers=args.workers > 0)
    train_dl = loader(train_items, train_tf, True, args.batch_size)
    lab_val_dl = loader(lab_val, eval_tf, False, 64)
    field_val_dl = loader(field_val, eval_tf, False, 64)

    model = base.build_model(len(classes))
    model.load_state_dict(init["state_dict"])
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, args.epochs * len(train_dl)))
    version = "pv+pd-mnv3l-" + datetime.now(timezone.utc).strftime("%Y%m%d")
    history, best_score, start = [], -1.0, 0

    def save_candidate(state, metrics):
        torch.save({**{k: init[k] for k in ("arch", "class_names", "preprocess")},
                    "state_dict": state, "version": version, "metrics": metrics,
                    "dataset": {"name": "PlantVillage subset (CC0) + PlantDoc (CC BY 4.0, Singh et al. 2020)",
                                "license": "CC0 1.0 + CC BY 4.0"}}, CANDIDATE_OUT)

    if args.resume:
        ckpt = torch.load(RESUME_OUT, map_location="cpu", weights_only=False)  # our own file
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["optimizer"])
        sched.load_state_dict(ckpt["scheduler"])
        history, best_score, start = ckpt["history"], ckpt["best_score"], ckpt["next_epoch"]
        print(f"Resumed at epoch {start + 1}", flush=True)

    for epoch in range(start, args.epochs):
        t = time.time()
        tr = base.run_epoch(model, train_dl, criterion, opt, sched)
        lv = base.run_epoch(model, lab_val_dl, criterion)
        fv = base.run_epoch(model, field_val_dl, criterion)
        score = (lv[1] + fv[1]) / 2
        row = {"epoch": epoch + 1, "train_acc": round(tr[1], 4), "lab_val_acc": round(lv[1], 4),
               "field_val_acc": round(fv[1], 4), "score": round(score, 4), "seconds": round(time.time() - t)}
        history.append(row)
        print(row, flush=True)
        if score > best_score:
            best_score = score
            save_candidate(model.state_dict(), {"provisional": True, **row})
        torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(), "scheduler": sched.state_dict(),
                    "history": history, "best_score": best_score, "next_epoch": epoch + 1}, RESUME_OUT)

    # Final comparison on both test sets with the API's own inference code
    before, after = DiseaseModel(INIT_MODEL), DiseaseModel(CANDIDATE_OUT)
    report = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "candidate_version": version,
        "args": vars(args),
        "history": history,
        "lab_test": {"before": evaluate(before, lab_test), "after": evaluate(after, lab_test)},
        "field_test": {"before": evaluate(before, field_test), "after": evaluate(after, field_test)},
        "notes": [
            "Field test = PlantDoc official test split (small, so differences of a few % are within noise).",
            "Lab test = PlantVillage held-out split used for the original model.",
        ],
    }
    for name in ("lab_test", "field_test"):
        b, a = report[name]["before"], report[name]["after"]
        print(f"{name:10s} accuracy {b['accuracy']:.4f} -> {a['accuracy']:.4f} | macro-F1 {b['macro_f1']:.4f} -> {a['macro_f1']:.4f}")
    ckpt = torch.load(CANDIDATE_OUT, map_location="cpu", weights_only=True)
    ckpt["metrics"] = {"lab_test_accuracy": report["lab_test"]["after"]["accuracy"],
                       "field_test_accuracy": report["field_test"]["after"]["accuracy"],
                       "field_test_macro_f1": report["field_test"]["after"]["macro_f1"],
                       "test_accuracy": report["lab_test"]["after"]["accuracy"],
                       "test_images": report["lab_test"]["after"]["images"]}
    torch.save(ckpt, CANDIDATE_OUT)
    REPORT_OUT.write_text(json.dumps(report, indent=2))
    RESUME_OUT.unlink(missing_ok=True)
    print(f"Saved candidate {CANDIDATE_OUT} and report {REPORT_OUT}")


if __name__ == "__main__":
    main()
