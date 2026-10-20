"""Plant disease detection pipeline.

Leaf image -> validation & preprocessing -> CNN (MobileNetV3) -> disease class -> advisory.

The trained model file (ml/models/disease_cnn.pt) is produced by
ml/training/train_disease_cnn.py. If it is missing, or PyTorch is not installed, the API
reports that the model is unavailable — it never returns a made-up prediction.
"""

import hashlib
import io
import json
import logging
import threading
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.api.errors import AppError
from app.config import get_settings
from app.services.disease_model_arch import build_model, preprocess

logger = logging.getLogger("krishiveda")

ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_SIDE_PX = 64
Image.MAX_IMAGE_PIXELS = 40_000_000  # refuse "decompression bomb" images

INFO_FILE = Path(__file__).resolve().parent.parent / "data" / "disease_info.json"
DISEASE_INFO: dict = json.loads(INFO_FILE.read_text(encoding="utf-8"))["classes"]

DISCLAIMER = ("This is a preliminary AI screening result, not a confirmed diagnosis. It only covers the crops and "
              "diseases listed as supported. Please confirm with an agriculture officer or your Krishi Vigyan Kendra "
              "before spraying any chemical.")


# ------------------------------------------------------------------ validation
def validate_image(data: bytes, filename: str | None) -> Image.Image:
    max_bytes = int(get_settings().max_upload_mb * 1024 * 1024)
    if not data:
        raise AppError(400, "EMPTY_FILE", "The uploaded file is empty.")
    if len(data) > max_bytes:
        raise AppError(413, "FILE_TOO_LARGE", f"Image is larger than {get_settings().max_upload_mb:g} MB.")
    if filename and Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise AppError(415, "UNSUPPORTED_FILE_TYPE", "Please upload a JPG, PNG or WEBP image.")
    try:
        probe = Image.open(io.BytesIO(data))
        probe.verify()  # detects truncated/corrupt files
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        raise AppError(400, "INVALID_IMAGE", "The file could not be read as an image.")
    if image.format not in ALLOWED_FORMATS:
        raise AppError(415, "UNSUPPORTED_FILE_TYPE", "Please upload a JPG, PNG or WEBP image.")
    if min(image.size) < MIN_SIDE_PX:
        raise AppError(400, "IMAGE_TOO_SMALL", f"Image must be at least {MIN_SIDE_PX}×{MIN_SIDE_PX} pixels.")
    return image


# ------------------------------------------------------------------ model
class DiseaseModel:
    def __init__(self, path: Path):
        import torch  # imported here so the API can run without PyTorch installed

        ckpt = torch.load(path, map_location="cpu", weights_only=True)
        self.class_names: list[str] = ckpt["class_names"]
        self.version: str = ckpt["version"]
        self.arch: str = ckpt["arch"]
        self.preprocess_cfg: dict = ckpt["preprocess"]
        self.metrics: dict = ckpt.get("metrics", {})
        self.dataset: dict = ckpt.get("dataset", {})
        self.net = build_model(len(self.class_names))
        self.net.load_state_dict(ckpt["state_dict"])
        self.net.eval()
        self._torch = torch

    def predict_proba(self, image: Image.Image) -> np.ndarray:
        cfg = self.preprocess_cfg
        x = preprocess(image, cfg["resize"], cfg["image_size"], cfg["mean"], cfg["std"])
        with self._torch.inference_mode():
            logits = self.net(self._torch.from_numpy(x))
            return self._torch.softmax(logits, dim=1)[0].numpy()


_lock = threading.Lock()
_model: DiseaseModel | None = None
_model_mtime: float | None = None
_load_error: str | None = None


def load_model(force: bool = False) -> DiseaseModel | None:
    """Return the loaded model, (re)loading it if the file is new or has been retrained."""
    global _model, _model_mtime, _load_error
    with _lock:
        path = get_settings().disease_model_path
        if not path.exists():
            _model, _model_mtime = None, None
            _load_error = "Model file not found. Train it with ml/training/train_disease_cnn.py (see docs/setup.md)."
            return None
        mtime = path.stat().st_mtime
        if _model is not None and not force and mtime == _model_mtime:
            return _model
        try:
            _model, _model_mtime = DiseaseModel(path), mtime
            _load_error = None
            logger.info("Loaded disease model %s", _model.version)
        except ImportError:
            _load_error = "PyTorch is not installed. Run: pip install -r backend/requirements-ml.txt"
        except Exception as exc:  # corrupt or incompatible checkpoint
            logger.exception("Could not load disease model")
            _load_error = f"Model file could not be loaded ({type(exc).__name__})."
        return _model


def supported_classes() -> list[dict]:
    rows = []
    for key, info in DISEASE_INFO.items():
        if info.get("no_leaf"):
            continue
        rows.append({
            "class": key,
            "crop": info["crop"],
            "crop_hi": info.get("crop_hi"),
            "disease": "Healthy" if info.get("healthy") else info["disease"],
            "disease_hi": "स्वस्थ" if info.get("healthy") else info.get("disease_hi"),
        })
    return rows


def model_info() -> dict:
    model = load_model()
    crops = sorted({r["crop"] for r in supported_classes()})
    if not model:
        return {"available": False, "reason": _load_error, "supported_crops": crops}
    return {
        "available": True,
        "version": model.version,
        "architecture": model.arch,
        "num_classes": len(model.class_names),
        "metrics": model.metrics,
        "dataset": model.dataset,
        "supported_crops": crops,
        "confidence_threshold": get_settings().disease_confidence_threshold,
    }


def _describe(class_name: str, probability: float) -> dict:
    info = DISEASE_INFO.get(class_name, {})
    return {
        "class": class_name,
        "probability": round(float(probability), 4),
        "crop": info.get("crop"),
        "crop_hi": info.get("crop_hi"),
        "disease": None if info.get("healthy") or info.get("no_leaf") else info.get("disease"),
        "disease_hi": None if info.get("healthy") or info.get("no_leaf") else info.get("disease_hi"),
        "healthy": bool(info.get("healthy")),
        "no_leaf": bool(info.get("no_leaf")),
    }


def predict(data: bytes, filename: str | None) -> dict:
    image = validate_image(data, filename)
    model = load_model()
    if not model:
        raise AppError(503, "MODEL_NOT_AVAILABLE", "Disease detection model is not available on the server.",
                       {"reason": _load_error})

    probs = model.predict_proba(image)
    order = np.argsort(probs)[::-1][:3]
    top = [_describe(model.class_names[i], probs[i]) for i in order]
    best = top[0]
    info = DISEASE_INFO.get(best["class"], {})
    threshold = get_settings().disease_confidence_threshold

    if best["no_leaf"]:
        status = "no_leaf"
        message = "No plant leaf was recognised in this photo. Take a close, clear photo of a single leaf."
    elif best["probability"] < threshold:
        status = "uncertain"
        message = ("The model is not confident about this image. Retake the photo in daylight with one leaf filling "
                   "the frame, or consult an expert. The possibilities below are shown for reference only.")
    elif best["healthy"]:
        status = "healthy"
        message = f"The {best['crop'].lower()} leaf looks healthy."
    else:
        status = "diseased"
        message = f"Signs of {best['disease']} were detected on the {best['crop'].lower()} leaf."

    advisory = None
    if status == "diseased":
        advisory = {k: info.get(k) for k in ("cause", "symptoms", "management", "prevention")}
    elif status == "healthy":
        advisory = {"cause": None, "symptoms": None,
                    "management": ["No treatment needed. Keep monitoring the crop every few days."],
                    "prevention": ["Maintain balanced nutrition and irrigation.", "Remove weeds and keep the field clean."]}

    return {
        "status": status,
        "message": message,
        "prediction": best,
        "top_predictions": top,
        "advisory": advisory,
        "confidence_threshold": threshold,
        "model_version": model.version,
        "image_sha256": hashlib.sha256(data).hexdigest(),
        "image_size": list(image.size),
        "disclaimer": DISCLAIMER,
    }
