"""Image validation, model-unavailable handling, and (when the trained model exists) real inference."""

import io
from pathlib import Path

import pytest
from PIL import Image

from app.services import disease_service

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "ml" / "datasets" / "plantvillage_subset"


def image_bytes(fmt="JPEG", size=(256, 256), color=(60, 140, 60)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    return buf.getvalue()


def post(client, data: bytes, name="leaf.jpg", mime="image/jpeg", **form):
    return client.post("/api/disease/predict", files={"file": (name, data, mime)}, data=form)


@pytest.mark.parametrize("data,name,status,code", [
    (b"", "leaf.jpg", 400, "EMPTY_FILE"),
    (b"not an image at all", "leaf.jpg", 400, "INVALID_IMAGE"),
    (image_bytes(), "leaf.gif", 415, "UNSUPPORTED_FILE_TYPE"),
    (image_bytes(size=(40, 40)), "leaf.jpg", 400, "IMAGE_TOO_SMALL"),
    (image_bytes(fmt="BMP"), "leaf.jpg", 415, "UNSUPPORTED_FILE_TYPE"),
], ids=["empty", "not-image", "gif-extension", "too-small", "bmp-content"])
def test_upload_validation(client, data, name, status, code):
    r = post(client, data, name)
    assert r.status_code == status, r.text
    assert r.json()["error"]["code"] == code


def test_upload_too_large(client, settings):
    big = b"\xff\xd8" + b"0" * int(settings.max_upload_mb * 1024 * 1024 + 10)
    r = post(client, big)
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_truncated_jpeg_rejected(client):
    data = image_bytes()
    r = post(client, data[: len(data) // 2])
    assert r.status_code == 400


def test_unknown_farmer_rejected(client):
    r = post(client, image_bytes(), farmer_id="999999")
    assert r.status_code == 404


def test_model_unavailable_returns_503(client, settings, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "disease_model_path", tmp_path / "missing.pt")
    monkeypatch.setattr(disease_service, "_model", None)
    r = post(client, image_bytes())
    assert r.status_code == 503
    err = r.json()["error"]
    assert err["code"] == "MODEL_NOT_AVAILABLE"
    assert "not found" in err["details"]["reason"]
    info = client.get("/api/disease/model").json()
    assert info["available"] is False and len(info["supported_classes"]) == 38


def test_preprocess_shape_and_normalisation():
    from app.services.disease_model_arch import preprocess
    x = preprocess(Image.new("RGB", (640, 480), (124, 116, 104)))  # ~ImageNet mean colour
    assert x.shape == (1, 3, 224, 224)
    assert abs(float(x.mean())) < 0.05


def test_disease_info_covers_every_class():
    for key, info in disease_service.DISEASE_INFO.items():
        if info.get("healthy") or info.get("no_leaf"):
            continue
        for field in ("crop", "disease", "cause", "symptoms", "management", "prevention"):
            assert info.get(field), f"{key} is missing {field}"


# ---------------------------------------------------------------- real model (skipped if not trained)
model_ready = pytest.mark.skipif(not disease_service.get_settings().disease_model_path.exists(), reason="disease model not trained")


@model_ready
def test_model_classes_match_disease_info():
    model = disease_service.load_model(force=True)
    assert model is not None
    assert set(model.class_names) == set(disease_service.DISEASE_INFO)


@model_ready
def test_model_reloads_when_file_changes(settings, monkeypatch, tmp_path):
    import os
    import shutil

    copy = tmp_path / "model.pt"
    shutil.copy(settings.disease_model_path, copy)
    monkeypatch.setattr(settings, "disease_model_path", copy)
    first = disease_service.load_model(force=True)
    assert disease_service.load_model() is first  # unchanged file -> same object
    stat = copy.stat()
    os.utime(copy, (stat.st_atime, stat.st_mtime + 10))  # simulate re-training
    assert disease_service.load_model() is not first
    monkeypatch.undo()
    disease_service.load_model(force=True)


@model_ready
@pytest.mark.skipif(not DATASET.exists(), reason="dataset subset not downloaded")
def test_real_prediction_on_dataset_image(client, farmer):
    disease_service.load_model(force=True)
    sample = sorted((DATASET / "Tomato___Late_blight").glob("*.jpg"))[0]
    r = post(client, sample.read_bytes(), sample.name, farmer_id=str(farmer["id"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] in {"diseased", "healthy", "uncertain", "no_leaf"}
    assert len(body["top_predictions"]) == 3
    probs = [p["probability"] for p in body["top_predictions"]]
    assert probs == sorted(probs, reverse=True) and 0 < probs[0] <= 1
    assert body["analysis_id"] > 0
    history = client.get(f"/api/farmers/{farmer['id']}/history").json()
    assert history["disease_analyses"][0]["predicted_class"] == body["prediction"]["class"]
