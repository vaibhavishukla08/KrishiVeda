"""
Train the plant disease CNN (transfer learning, MobileNetV3-Large, PyTorch).

Pipeline: leaf image -> preprocessing/augmentation -> CNN (convolutional feature extraction
+ classification head) -> one of 39 classes (38 PlantVillage crop/disease classes + "no leaf").

Data   : ml/datasets/plantvillage_subset (created by ml/datasets/fetch_plantvillage_subset.py)
         PlantVillage via Mendeley Data doi:10.17632/tywbtsjrjv.1, CC0 1.0.
Split  : stratified per class, 70% train / 15% validation / 15% test (fixed seed).
Output : ml/models/disease_cnn.pt and ml/evaluation/disease_model_report.json

Usage (project root, backend venv active, torch installed):
    python ml/training/train_disease_cnn.py
    python ml/training/train_disease_cnn.py --head-epochs 2 --finetune-epochs 4
"""

import argparse
import json
import random
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))  # share architecture + preprocessing with the API
from app.services.disease_model_arch import ARCH, IMAGE_SIZE, MEAN, RESIZE, STD, build_model, preprocess  # noqa: E402

DATA_DIR = ROOT / "ml" / "datasets" / "plantvillage_subset"
MODEL_OUT = ROOT / "ml" / "models" / "disease_cnn.pt"
RESUME_OUT = ROOT / "ml" / "models" / "disease_cnn_resume.pt"  # full training state, written every epoch
REPORT_OUT = ROOT / "ml" / "evaluation" / "disease_model_report.json"

# Pre-trained ImageNet weights are downloaded by torchvision. Use the OS certificate store
# without Python 3.13+'s strict X.509 mode so this also works behind TLS-inspecting proxies.
_ctx = ssl.create_default_context()
_ctx.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
ssl._create_default_https_context = lambda: _ctx


class LeafDataset(Dataset):
    def __init__(self, items, transform):
        self.items, self.transform = items, transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, label = self.items[i]
        with Image.open(path) as img:
            return self.transform(img.convert("RGB")), label


def stratified_split(seed: int, max_per_class: int | None = None):
    classes = sorted(d.name for d in DATA_DIR.iterdir() if d.is_dir())
    rng = random.Random(seed)
    train, val, test = [], [], []
    for idx, c in enumerate(classes):
        files = sorted(p for p in (DATA_DIR / c).iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        rng.shuffle(files)
        files = files[:max_per_class] if max_per_class else files
        n_val = n_test = max(1, round(0.15 * len(files)))
        test += [(f, idx) for f in files[:n_test]]
        val += [(f, idx) for f in files[n_test : n_test + n_val]]
        train += [(f, idx) for f in files[n_test + n_val :]]
    return classes, train, val, test


def run_epoch(model, loader, criterion, optimizer=None, scheduler=None):
    training = optimizer is not None
    model.train(training)
    total, correct, loss_sum = 0, 0, 0.0
    with torch.set_grad_enabled(training):
        for x, y in loader:
            out = model(x)
            loss = criterion(out, y)
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                if scheduler:
                    scheduler.step()
            loss_sum += loss.item() * len(y)
            correct += (out.argmax(1) == y).sum().item()
            total += len(y)
    return loss_sum / total, correct / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head-epochs", type=int, default=2, help="epochs training only the new classifier head")
    ap.add_argument("--finetune-epochs", type=int, default=4, help="epochs fine-tuning the whole CNN")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true", help="continue from ml/models/disease_cnn_resume.pt")
    ap.add_argument("--max-per-class", type=int, default=None, help="use fewer images (quick smoke tests only)")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    classes, train_items, val_items, test_items = stratified_split(args.seed, args.max_per_class)
    print(f"{len(classes)} classes | train {len(train_items)} | val {len(val_items)} | test {len(test_items)}")

    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.6, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(0.3, 0.3, 0.3, 0.03),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(RESIZE), transforms.CenterCrop(IMAGE_SIZE), transforms.ToTensor(), transforms.Normalize(MEAN, STD),
    ])
    train_dl = DataLoader(LeafDataset(train_items, train_tf), batch_size=args.batch_size, shuffle=True,
                          num_workers=args.workers, persistent_workers=args.workers > 0)
    val_dl = DataLoader(LeafDataset(val_items, eval_tf), batch_size=64, num_workers=args.workers,
                        persistent_workers=args.workers > 0)

    model = build_model(len(classes), pretrained=not args.resume)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    version = "pv-mnv3l-" + datetime.now(timezone.utc).strftime("%Y%m%d")
    dataset = {"name": "PlantVillage (Mendeley Data doi:10.17632/tywbtsjrjv.1)", "license": "CC0 1.0",
               "subset": "up to 250 random images per class"}

    def save_model(state_dict, metrics):
        """Save a deployable checkpoint that the API can load."""
        MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "arch": ARCH,
            "state_dict": state_dict,
            "class_names": classes,
            "preprocess": {"resize": RESIZE, "image_size": IMAGE_SIZE, "mean": list(MEAN), "std": list(STD)},
            "version": version,
            "metrics": metrics,
            "dataset": dataset,
        }, MODEL_OUT)

    def set_phase(phase):
        """head: train only the classifier (backbone frozen); finetune: train the whole CNN."""
        for p in model.features.parameters():
            p.requires_grad = phase == "finetune"
        if phase == "head":
            return torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3, weight_decay=1e-4), None
        opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-4, total_steps=max(1, args.finetune_epochs * len(train_dl)))
        return opt, sched

    schedule = [("head", e) for e in range(1, args.head_epochs + 1)] + \
               [("finetune", e) for e in range(1, args.finetune_epochs + 1)]
    history, best_acc, best_state, start = [], 0.0, None, 0
    opt, sched, current_phase = None, None, None

    # Resume after an interruption: restores weights, optimiser, LR schedule and history
    if args.resume and RESUME_OUT.exists():
        ckpt = torch.load(RESUME_OUT, map_location="cpu", weights_only=False)  # our own file
        model.load_state_dict(ckpt["model"])
        history, best_acc, best_state, start = ckpt["history"], ckpt["best_acc"], ckpt["best_state"], ckpt["next_step"]
        if start < len(schedule):
            current_phase = schedule[start][0]
            opt, sched = set_phase(current_phase)
            opt.load_state_dict(ckpt["optimizer"])
            if sched and ckpt["scheduler"]:
                sched.load_state_dict(ckpt["scheduler"])
        print(f"Resumed after step {start} of {len(schedule)} (best val acc {best_acc:.4f})", flush=True)
    elif args.resume:
        raise SystemExit(f"No resume checkpoint at {RESUME_OUT}")

    for step in range(start, len(schedule)):
        phase, epoch = schedule[step]
        if phase != current_phase:
            opt, sched = set_phase(phase)
            current_phase = phase
        t = time.time()
        tr = run_epoch(model, train_dl, criterion, opt, sched)
        va = run_epoch(model, val_dl, criterion)
        row = {"phase": phase, "epoch": epoch, "train_loss": round(tr[0], 4), "train_acc": round(tr[1], 4),
               "val_loss": round(va[0], 4), "val_acc": round(va[1], 4), "seconds": round(time.time() - t)}
        history.append(row)
        print(row, flush=True)
        if va[1] >= best_acc:
            best_acc, best_state = va[1], {k: v.detach().clone() for k, v in model.state_dict().items()}
            # Usable best-so-far model even if training is interrupted later
            save_model(best_state, {"best_val_accuracy": round(best_acc, 4), "provisional": True})
        torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(),
                    "scheduler": sched.state_dict() if sched else None, "history": history,
                    "best_acc": best_acc, "best_state": best_state, "next_step": step + 1}, RESUME_OUT)

    model.load_state_dict(best_state)
    model.eval()

    # Final test evaluation uses the *same preprocessing function as the API*
    y_true, y_pred, confs = [], [], []
    with torch.inference_mode():
        for path, label in test_items:
            with Image.open(path) as img:
                x = torch.from_numpy(preprocess(img))
            probs = torch.softmax(model(x), 1)[0]
            y_true.append(label)
            y_pred.append(int(probs.argmax()))
            confs.append(float(probs.max()))
    y_true, y_pred, confs = np.array(y_true), np.array(y_pred), np.array(confs)
    metrics = {
        "test_accuracy": round(float((y_true == y_pred).mean()), 4),
        "test_macro_f1": round(float(f1_score(y_true, y_pred, average="macro")), 4),
        "best_val_accuracy": round(best_acc, 4),
        "test_images": int(len(y_true)),
        "train_images": len(train_items),
        "val_images": len(val_items),
        "mean_confidence_correct": round(float(confs[y_true == y_pred].mean()), 4),
        "mean_confidence_wrong": round(float(confs[y_true != y_pred].mean()), 4) if (y_true != y_pred).any() else None,
    }
    print(json.dumps(metrics, indent=2))

    save_model(model.state_dict(), metrics)
    RESUME_OUT.unlink(missing_ok=True)  # training finished; resume state no longer needed

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(json.dumps({
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "args": vars(args),
        "metrics": metrics,
        "history": history,
        "per_class": classification_report(y_true, y_pred, labels=list(range(len(classes))), target_names=classes,
                                           output_dict=True, zero_division=0),
        "confusion_matrix": {"labels": classes, "matrix": confusion_matrix(y_true, y_pred, labels=list(range(len(classes)))).tolist()},
        "limitations": [
            "PlantVillage photos are single leaves on plain backgrounds taken in controlled conditions; accuracy on "
            "real field photos (mixed backgrounds, multiple leaves, different lighting) is expected to be lower.",
            "PlantVillage contains several photos of the same leaf; a random split can place near-duplicates in both "
            "train and test sets, which can inflate the test score.",
            "Only the 14 crops / 38 classes in the dataset are supported. Other crops or diseases will be forced into "
            "one of these classes, which is why low-confidence results are reported as 'uncertain'.",
        ],
    }, indent=2))
    print(f"Saved {MODEL_OUT} and {REPORT_OUT}")


if __name__ == "__main__":
    main()
