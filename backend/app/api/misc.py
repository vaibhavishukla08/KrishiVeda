"""Health, market prices, advisory assistant and static resources."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.farmers import get_farmer_or_404
from app.config import get_settings
from app.database.session import check_db, get_db
from app.models.orm import AdvisoryMessage
from app.schemas.requests import AdvisoryIn
from app.services import advisory_service, crop_service, disease_service, market_service, weather_service

router = APIRouter(prefix="/api")
RESOURCES = json.loads((Path(__file__).resolve().parent.parent / "data" / "resources.json").read_text(encoding="utf-8"))


@router.get("/health", tags=["system"])
def health():
    settings = get_settings()
    db_ok = check_db()
    disease = disease_service.model_info()
    crop = crop_service.model_info()
    return {
        "status": "ok" if db_ok else "degraded",
        "version": settings.app_version,
        "database": {"connected": db_ok, "engine": settings.database_url.split(":", 1)[0]},
        "disease_model": {"available": disease["available"], "version": disease.get("version"), "reason": disease.get("reason")},
        "crop_model": {"available": crop["available"], "version": crop.get("version")},
        "weather_provider": weather_service.active_provider(),
        "market_prices": "live" if settings.data_gov_in_api_key else "demo",
        "advisory_provider": advisory_service.active_provider(),
    }


# ---------------------------------------------------------------- market prices
@router.get("/market-prices", tags=["market prices"])
async def market_prices(
    commodity: str | None = Query(None, max_length=60),
    state: str | None = Query(None, max_length=60),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return await run_in_threadpool(market_service.get_prices, db, commodity, state, limit)


@router.get("/market-prices/commodities", tags=["market prices"])
def market_commodities():
    return {"commodities": market_service.demo_commodities()}


# ---------------------------------------------------------------- advisory
@router.get("/advisory/status", tags=["advisory"])
def advisory_status():
    return {"ai_configured": advisory_service.ai_configured(), "provider": advisory_service.active_provider(),
            "model": advisory_service.active_model()}


@router.post("/advisory/ask", tags=["advisory"])
async def advisory_ask(payload: AdvisoryIn, db: Session = Depends(get_db)):
    context = None
    if payload.farmer_id is not None:
        farmer = get_farmer_or_404(db, payload.farmer_id)
        farm = farmer.farms[0] if farmer.farms else None
        # A farmer may have no farm yet, so never read farm attributes without checking it exists
        location = (farm.location_name if farm else None) or farmer.district or farmer.state
        parts = [f"location {location}" if location else None,
                 f"crops: {', '.join(c.crop_name for c in farm.crops)}" if farm and farm.crops else None,
                 f"soil: {farm.soil_type}" if farm and farm.soil_type else None]
        context = "; ".join(p for p in parts if p) or None

    result = await run_in_threadpool(
        advisory_service.answer, payload.question, payload.language, context,
        [t.model_dump() for t in payload.history],
    )
    msg = AdvisoryMessage(farmer_id=payload.farmer_id, question=payload.question, answer=result["answer"],
                          provider=result["provider"], language=payload.language)
    db.add(msg)
    db.commit()
    return {**result, "message_id": msg.id}


# ---------------------------------------------------------------- resources
@router.get("/resources/schemes", tags=["resources"])
def schemes():
    return {"schemes": RESOURCES["schemes"], "helplines": RESOURCES["helplines"], "note": RESOURCES["_note"]}


@router.get("/resources/stubble", tags=["resources"])
def stubble():
    return RESOURCES["stubble"]
