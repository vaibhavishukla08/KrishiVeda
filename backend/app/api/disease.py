from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.errors import AppError
from app.api.farmers import get_farmer_or_404
from app.config import get_settings
from app.database.session import get_db
from app.models.orm import DiseaseAnalysis
from app.services import disease_service

router = APIRouter(prefix="/api/disease", tags=["disease detection"])


@router.get("/model")
def disease_model():
    return {**disease_service.model_info(), "supported_classes": disease_service.supported_classes()}


@router.post("/predict")
async def predict_disease(
    file: UploadFile = File(..., description="Leaf photo (JPG/PNG/WEBP, max 5 MB)"),
    farmer_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if farmer_id is not None:
        get_farmer_or_404(db, farmer_id)
    max_bytes = int(get_settings().max_upload_mb * 1024 * 1024)
    data = await file.read(max_bytes + 1)  # read at most one byte over the limit
    if len(data) > max_bytes:
        raise AppError(413, "FILE_TOO_LARGE", f"Image is larger than {get_settings().max_upload_mb:g} MB.")

    # CNN inference is CPU-bound: run it off the event loop
    result = await run_in_threadpool(disease_service.predict, data, file.filename)

    pred = result["prediction"]
    record = DiseaseAnalysis(
        farmer_id=farmer_id,
        image_name=(file.filename or "")[:255] or None,
        image_sha256=result["image_sha256"],
        status=result["status"],
        predicted_class=pred["class"],
        crop=pred["crop"],
        disease=pred["disease"],
        confidence=pred["probability"],
        top_predictions=result["top_predictions"],
        model_version=result["model_version"],
    )
    db.add(record)
    db.commit()
    return {**result, "analysis_id": record.id}
