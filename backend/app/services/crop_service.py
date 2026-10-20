"""Crop recommendation using a Random Forest trained on the Kaggle "Crop Recommendation
Dataset" (Atharva Ingle, Apache 2.0). Train it with: python ml/training/train_crop_model.py
"""

import threading

import joblib
import numpy as np
import pandas as pd

from app.api.errors import AppError
from app.config import get_settings

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
FEATURE_LABELS = {
    "N": "Nitrogen (N)",
    "P": "Phosphorus (P)",
    "K": "Potassium (K)",
    "temperature": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "ph": "Soil pH",
    "rainfall": "Rainfall (mm)",
}
CROP_NAMES_HI = {
    "rice": "धान", "maize": "मक्का", "chickpea": "चना", "kidneybeans": "राजमा", "pigeonpeas": "अरहर",
    "mothbeans": "मोठ", "mungbean": "मूंग", "blackgram": "उड़द", "lentil": "मसूर", "pomegranate": "अनार",
    "banana": "केला", "mango": "आम", "grapes": "अंगूर", "watermelon": "तरबूज", "muskmelon": "खरबूजा",
    "apple": "सेब", "orange": "संतरा", "papaya": "पपीता", "coconut": "नारियल", "cotton": "कपास",
    "jute": "जूट", "coffee": "कॉफ़ी",
}

_lock = threading.Lock()
_bundle: dict | None = None


def load_model(force: bool = False) -> dict | None:
    """Load the trained model bundle once. Returns None if it has not been trained yet."""
    global _bundle
    with _lock:
        if _bundle is None or force:
            path = get_settings().crop_model_path
            # joblib uses pickle: only load model files you created yourself.
            _bundle = joblib.load(path) if path.exists() else None
        return _bundle


def model_info() -> dict:
    bundle = load_model()
    if not bundle:
        return {"available": False}
    return {
        "available": True,
        "version": bundle["version"],
        "algorithm": bundle["algorithm"],
        "classes": bundle["classes"],
        "metrics": bundle["metrics"],
        "dataset": bundle["dataset"],
    }


def recommend(inputs: dict, top_k: int = 3) -> dict:
    bundle = load_model()
    if not bundle:
        raise AppError(
            503,
            "MODEL_NOT_AVAILABLE",
            "Crop recommendation model is not trained yet. Run: python ml/training/train_crop_model.py",
        )
    x = pd.DataFrame([[float(inputs[f]) for f in FEATURES]], columns=FEATURES)
    probs = bundle["model"].predict_proba(x)[0]
    classes = list(bundle["model"].classes_)
    order = np.argsort(probs)[::-1][:top_k]

    warnings = []
    for f in FEATURES:
        lo, hi = bundle["dataset_ranges"][f]
        if not lo <= inputs[f] <= hi:
            warnings.append(
                f"{FEATURE_LABELS[f]} = {inputs[f]} is outside the training data range ({lo}–{hi}); "
                "the recommendation is less reliable."
            )

    def explain(crop: str) -> list[dict]:
        rows = []
        for f in FEATURES:
            p10, p50, p90 = bundle["crop_profiles"][crop][f]
            value = inputs[f]
            rows.append({
                "feature": f,
                "label": FEATURE_LABELS[f],
                "value": value,
                "typical_low": p10,
                "typical_median": p50,
                "typical_high": p90,
                "within_typical": p10 <= value <= p90,
            })
        return rows

    candidates = [
        {
            "crop": classes[i],
            "crop_hi": CROP_NAMES_HI.get(classes[i]),
            "probability": round(float(probs[i]), 4),
            "comparison": explain(classes[i]),
        }
        for i in order
    ]
    best = candidates[0]
    if best["probability"] < 0.5:
        warnings.append(
            "Low confidence: no crop in the dataset is a strong match for these conditions. "
            "Treat the suggestions as options to discuss with your local agriculture officer."
        )
    matched = [r["label"] for r in best["comparison"] if r["within_typical"]]
    summary = (
        f"{best['crop'].title()} is suggested because {len(matched)} of {len(FEATURES)} of your values "
        f"fall within the typical range seen for this crop in the training data"
        + (f" ({', '.join(matched)})." if matched else ".")
    )
    return {
        "recommended_crop": best["crop"],
        "recommended_crop_hi": best["crop_hi"],
        "confidence": best["probability"],
        "candidates": candidates,
        "explanation": summary,
        "warnings": warnings,
        "model_version": bundle["version"],
        "disclaimer": "Statistical suggestion from a public dataset of Indian conditions. Confirm with a soil test "
                      "report, local seed availability, market demand and your Krishi Vigyan Kendra (KVK).",
    }
