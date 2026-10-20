"""
Evaluate a disease model checkpoint on a folder of labelled images, using the API's own
preprocessing and inference code.

    # Real-field photos (PlantDoc official test split)
    python ml/evaluation/evaluate_disease.py --data ml/datasets/plantdoc/test

    # Save the report next to the other evaluation files
    python ml/evaluation/evaluate_disease.py --data ml/datasets/plantdoc/test --out ml/evaluation/field_eval.json

Folder layout: <data>/<KrishiVeda class name>/*.jpg
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.disease_service import DISEASE_INFO, DiseaseModel  # noqa: E402

THRESHOLDS = (0.5, 0.6, 0.7)


def labelled_images(data_dir: Path, class_names: list[str]) -> list[tuple[Path, int]]:
    items = []
    for folder in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        if folder.name not in class_names:
            print(f"  skipping unknown class folder {folder.name}")
            continue
        label = class_names.index(folder.name)
        items += [(f, label) for f in sorted(folder.iterdir()) if f.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    return items


def evaluate(model: DiseaseModel, items: list[tuple[Path, int]]) -> dict:
    names = model.class_names
    probs = []
    for path, _ in items:
        with Image.open(path) as img:
            probs.append(model.predict_proba(img))
    probs = np.array(probs)
    y_true = np.array([label for _, label in items])
    y_pred = probs.argmax(1)
    conf = probs.max(1)
    correct = y_true == y_pred

    crop_of = lambda i: DISEASE_INFO.get(names[i], {}).get("crop")  # noqa: E731
    crop_ok = np.array([crop_of(t) == crop_of(p) for t, p in zip(y_true, y_pred)])
    top3 = np.array([t in np.argsort(p)[::-1][:3] for t, p in zip(y_true, probs)])

    per_class = {}
    for c in sorted(set(y_true)):
        mask = y_true == c
        per_class[names[c]] = {"images": int(mask.sum()), "accuracy": round(float(correct[mask].mean()), 4)}

    present = sorted(set(y_true))
    return {
        "images": int(len(items)),
        "classes": len(present),
        "accuracy": round(float(correct.mean()), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=present, average="macro", zero_division=0)), 4),
        "top3_accuracy": round(float(top3.mean()), 4),
        "crop_identified_accuracy": round(float(crop_ok.mean()), 4),
        "by_threshold": {
            str(t): {"coverage": round(float((conf >= t).mean()), 4),
                     "accuracy_when_confident": round(float(correct[conf >= t].mean()), 4) if (conf >= t).any() else None}
            for t in THRESHOLDS
        },
        "per_class": per_class,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "ml" / "models" / "disease_cnn.pt")
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    model = DiseaseModel(args.model)
    items = labelled_images(args.data, model.class_names)
    report = {"model": str(args.model.name), "model_version": model.version, "data": str(args.data), **evaluate(model, items)}
    summary = {k: v for k, v in report.items() if k != "per_class"}
    print(json.dumps(summary, indent=2))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2))
        print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
