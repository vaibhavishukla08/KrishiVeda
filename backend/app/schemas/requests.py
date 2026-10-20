from typing import Literal

from pydantic import BaseModel, Field


class CropRecommendIn(BaseModel):
    """Soil and climate inputs. Ranges are physical/agronomic limits; values outside the
    training data range are accepted but produce a reliability warning."""

    N: float = Field(ge=0, le=300, description="Soil nitrogen (kg/ha)")
    P: float = Field(ge=0, le=300, description="Soil phosphorus (kg/ha)")
    K: float = Field(ge=0, le=400, description="Soil potassium (kg/ha)")
    temperature: float = Field(ge=-10, le=55, description="Average temperature (°C)")
    humidity: float = Field(ge=0, le=100, description="Relative humidity (%)")
    ph: float = Field(ge=3, le=10, description="Soil pH")
    rainfall: float = Field(ge=0, le=5000, description="Rainfall (mm)")
    farmer_id: int | None = None


class AdvisoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class AdvisoryIn(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    language: Literal["en", "hi"] = "en"
    farmer_id: int | None = None
    history: list[AdvisoryTurn] = Field(default_factory=list, max_length=10)
