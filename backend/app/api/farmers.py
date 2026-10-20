from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.errors import AppError
from app.database.session import get_db
from app.models.orm import AdvisoryMessage, CropRecommendation, DiseaseAnalysis, Farm, Farmer, FarmCrop
from app.schemas.farmer import FarmerIn, FarmerOut, FarmIn

router = APIRouter(prefix="/api/farmers", tags=["farmers"])


def get_farmer_or_404(db: Session, farmer_id: int) -> Farmer:
    farmer = db.execute(
        select(Farmer).where(Farmer.id == farmer_id).options(selectinload(Farmer.farms).selectinload(Farm.crops))
    ).scalar_one_or_none()
    if not farmer:
        raise AppError(404, "FARMER_NOT_FOUND", f"Farmer {farmer_id} was not found.")
    return farmer


def _apply_farm(farmer: Farmer, data: FarmIn) -> None:
    farm = farmer.farms[0] if farmer.farms else Farm(farmer=farmer)
    for field, value in data.model_dump(exclude={"crops"}).items():
        setattr(farm, field, value)
    farm.crops = [FarmCrop(**c.model_dump()) for c in data.crops]


@router.post("", response_model=FarmerOut, status_code=201)
def create_farmer(payload: FarmerIn, db: Session = Depends(get_db)):
    farmer = Farmer(**payload.model_dump(exclude={"farm"}))
    if payload.farm:
        _apply_farm(farmer, payload.farm)
    db.add(farmer)
    db.commit()
    return get_farmer_or_404(db, farmer.id)


@router.get("/{farmer_id}", response_model=FarmerOut)
def read_farmer(farmer_id: int, db: Session = Depends(get_db)):
    return get_farmer_or_404(db, farmer_id)


@router.put("/{farmer_id}", response_model=FarmerOut)
def update_farmer(farmer_id: int, payload: FarmerIn, db: Session = Depends(get_db)):
    farmer = get_farmer_or_404(db, farmer_id)
    for field, value in payload.model_dump(exclude={"farm"}).items():
        setattr(farmer, field, value)
    if payload.farm:
        _apply_farm(farmer, payload.farm)
    db.commit()
    db.expire_all()
    return get_farmer_or_404(db, farmer_id)


@router.get("/{farmer_id}/history")
def farmer_history(farmer_id: int, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    get_farmer_or_404(db, farmer_id)

    def latest(model):
        return db.execute(
            select(model).where(model.farmer_id == farmer_id).order_by(model.created_at.desc(), model.id.desc()).limit(limit)
        ).scalars().all()

    return {
        "disease_analyses": [
            {"id": a.id, "created_at": a.created_at, "status": a.status, "crop": a.crop, "disease": a.disease,
             "predicted_class": a.predicted_class, "confidence": a.confidence, "image_name": a.image_name}
            for a in latest(DiseaseAnalysis)
        ],
        "crop_recommendations": [
            {"id": r.id, "created_at": r.created_at, "recommended_crop": r.recommended_crop,
             "confidence": r.confidence, "inputs": r.inputs}
            for r in latest(CropRecommendation)
        ],
        "advisory": [
            {"id": m.id, "created_at": m.created_at, "question": m.question, "answer": m.answer,
             "provider": m.provider, "language": m.language}
            for m in latest(AdvisoryMessage)
        ],
    }


@router.get("/{farmer_id}/stats")
def farmer_stats(farmer_id: int, days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Aggregates for the Analytics page."""
    get_farmer_or_404(db, farmer_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    analyses = db.execute(
        select(DiseaseAnalysis).where(DiseaseAnalysis.farmer_id == farmer_id, DiseaseAnalysis.created_at >= since)
    ).scalars().all()
    recs = db.execute(
        select(CropRecommendation).where(CropRecommendation.farmer_id == farmer_id, CropRecommendation.created_at >= since)
    ).scalars().all()
    per_day = Counter(a.created_at.date().isoformat() for a in analyses)
    return {
        "period_days": days,
        "disease_checks": len(analyses),
        "by_status": dict(Counter(a.status for a in analyses)),
        "top_diseases": Counter(a.disease for a in analyses if a.disease).most_common(5),
        "checks_per_day": [{"date": d, "count": c} for d, c in sorted(per_day.items())],
        "recommendations": len(recs),
        "recommended_crops": dict(Counter(r.recommended_crop for r in recs)),
    }
