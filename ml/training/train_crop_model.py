"""
Train the crop recommendation model.

Dataset : Crop Recommendation Dataset by Atharva Ingle (Kaggle, Apache 2.0 licence)
          https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset
          2,200 rows, 22 crops, features N, P, K, temperature, humidity, ph, rainfall.
Model   : Random Forest classifier (scikit-learn), evaluated on a stratified 20% hold-out split
          and with 5-fold cross-validation.

Usage (from the project root, with the backend venv active):
    python ml/datasets/fetch_crop_dataset.py
    python ml/training/train_crop_model.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "ml" / "datasets" / "crop_recommendation" / "Crop_recommendation.csv"
MODEL_OUT = ROOT / "ml" / "models" / "crop_recommender.joblib"
REPORT_OUT = ROOT / "ml" / "evaluation" / "crop_model_report.json"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
SEED = 42


def main():
    if not DATA.exists():
        raise SystemExit(f"Dataset not found at {DATA}. Run: python ml/datasets/fetch_crop_dataset.py")
    df = pd.read_csv(DATA)
    X, y = df[FEATURES], df["label"]
    print(f"Loaded {len(df)} rows, {y.nunique()} crops")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    model = RandomForestClassifier(n_estimators=300, min_samples_leaf=1, random_state=SEED, n_jobs=-1)

    cv = cross_val_score(model, X_train, y_train, cv=StratifiedKFold(5, shuffle=True, random_state=SEED))
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = {
        "test_accuracy": round(accuracy_score(y_test, pred), 4),
        "test_macro_f1": round(f1_score(y_test, pred, average="macro"), 4),
        "cv5_accuracy_mean": round(cv.mean(), 4),
        "cv5_accuracy_std": round(cv.std(), 4),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }
    print(json.dumps(metrics, indent=2))

    # Refit on all data for deployment (metrics above come from the hold-out split)
    model.fit(X, y)

    # Per-crop typical ranges (10th, 50th, 90th percentile) used to explain recommendations
    crop_profiles = {
        crop: {f: [round(float(np.percentile(g[f], q)), 1) for q in (10, 50, 90)] for f in FEATURES}
        for crop, g in df.groupby("label")
    }
    dataset_ranges = {f: [round(float(df[f].min()), 1), round(float(df[f].max()), 1)] for f in FEATURES}
    importances = dict(zip(FEATURES, (round(float(v), 4) for v in model.feature_importances_)))

    version = "crop-rf-" + datetime.now(timezone.utc).strftime("%Y%m%d")
    bundle = {
        "model": model,
        "version": version,
        "algorithm": "RandomForestClassifier(n_estimators=300)",
        "features": FEATURES,
        "classes": sorted(y.unique().tolist()),
        "metrics": metrics,
        "crop_profiles": crop_profiles,
        "dataset_ranges": dataset_ranges,
        "feature_importances": importances,
        "dataset": {
            "name": "Crop Recommendation Dataset (Atharva Ingle, Kaggle)",
            "license": "Apache 2.0",
            "url": "https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset",
            "rows": len(df),
        },
    }
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_OUT, compress=3)

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "feature_importances": importances,
        "per_class": classification_report(y_test, pred, output_dict=True),
        "note": "Hold-out metrics on a stratified 20% split of the same dataset. The dataset was built by "
                "augmenting Indian rainfall, climate and fertiliser data, so very high scores reflect how separable "
                "this dataset is, not proven accuracy on real farms.",
    }
    REPORT_OUT.write_text(json.dumps(report, indent=2))
    print(f"Saved model to {MODEL_OUT}\nSaved report to {REPORT_OUT}")


if __name__ == "__main__":
    main()
