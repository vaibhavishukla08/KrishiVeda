from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.farmers import get_farmer_or_404
from app.database.session import get_db
from app.models.orm import CropRecommendation
from app.schemas.requests import CropRecommendIn
from app.services import crop_service

router = APIRouter(prefix="/api/crops", tags=["crop recommendation"])


@router.get("/model")
def crop_model():
    return crop_service.model_info()


@router.post("/recommend")
def recommend_crop(payload: CropRecommendIn, db: Session = Depends(get_db)):
    if payload.farmer_id is not None:
        get_farmer_or_404(db, payload.farmer_id)
    inputs = payload.model_dump(exclude={"farmer_id"})
    result = crop_service.recommend(inputs)
    record = CropRecommendation(
        farmer_id=payload.farmer_id,
        inputs=inputs,
        recommended_crop=result["recommended_crop"],
        confidence=result["confidence"],
        alternatives=[{"crop": c["crop"], "probability": c["probability"]} for c in result["candidates"][1:]],
        model_version=result["model_version"],
    )
    db.add(record)
    db.commit()
    return {**result, "recommendation_id": record.id}
