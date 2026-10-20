from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Language = Literal["en", "hi"]


class FarmCropIn(BaseModel):
    crop_name: str = Field(min_length=2, max_length=40)
    season: Literal["kharif", "rabi", "zaid"] | None = None
    sowing_date: date | None = None

    @field_validator("crop_name")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().lower()


class FarmIn(BaseModel):
    name: str = Field(default="My Farm", min_length=1, max_length=100)
    location_name: str | None = Field(default=None, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    area_acres: float | None = Field(default=None, gt=0, le=10000)
    soil_type: str | None = Field(default=None, max_length=40)
    irrigation_type: str | None = Field(default=None, max_length=40)
    crops: list[FarmCropIn] = Field(default_factory=list, max_length=20)


class FarmerIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number")
    preferred_language: Language = "en"
    state: str | None = Field(default=None, max_length=60)
    district: str | None = Field(default=None, max_length=60)
    village: str | None = Field(default=None, max_length=100)
    farm: FarmIn | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must have at least 2 characters")
        return v


class FarmCropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    crop_name: str
    season: str | None
    sowing_date: date | None


class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    location_name: str | None
    latitude: float | None
    longitude: float | None
    area_acres: float | None
    soil_type: str | None
    irrigation_type: str | None
    crops: list[FarmCropOut]


class FarmerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: str | None
    preferred_language: str
    state: str | None
    district: str | None
    village: str | None
    created_at: datetime
    farms: list[FarmOut]
