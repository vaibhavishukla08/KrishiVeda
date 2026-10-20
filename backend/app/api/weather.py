from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.orm import WeatherRecord
from app.services import irrigation_service, weather_service

router = APIRouter(prefix="/api", tags=["weather & irrigation"])


def _save(db: Session, w: dict) -> None:
    cur = w["current"]
    db.add(WeatherRecord(
        location_name=w["location"]["name"][:120],
        latitude=w["location"]["latitude"],
        longitude=w["location"]["longitude"],
        temperature_c=cur["temperature_c"],
        humidity_pct=cur["humidity_pct"],
        rain_mm=cur["precipitation_mm"],
        condition=cur["condition"],
        source=w["source"]["provider"],
    ))
    db.commit()


@router.get("/weather")
async def weather(
    city: str | None = Query(None, min_length=2, max_length=80),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
):
    data = await run_in_threadpool(weather_service.get_weather, city, lat, lon)
    _save(db, data)
    return {**data, "alerts": irrigation_service.weather_alerts(data)}


@router.get("/irrigation/advice")
async def irrigation(
    crop: str = Query(..., min_length=2, max_length=40),
    stage: Literal["initial", "mid", "late"] = "mid",
    area_acres: float | None = Query(None, gt=0, le=10000),
    city: str | None = Query(None, min_length=2, max_length=80),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
):
    data = await run_in_threadpool(weather_service.get_weather, city, lat, lon)
    return {
        "weather": data,
        "advice": irrigation_service.irrigation_advice(data, crop, stage, area_acres),
        "supported_crops": sorted(irrigation_service.KC_VALUES),
    }
