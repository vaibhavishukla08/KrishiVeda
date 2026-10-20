from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["disease", "pest", "irrigation", "soil", "weather", "market", "other"]


class ExpertQuestionIn(BaseModel):
    farmer_id: int | None = None
    farmer_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^[6-9]\d{9}$", description="10-digit Indian mobile number")
    crop: str | None = Field(default=None, max_length=40)
    category: Category = "other"
    question: str = Field(min_length=10, max_length=2000)
    language: Literal["en", "hi"] = "en"

    @field_validator("farmer_name", "question")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class ExpertAnswerIn(BaseModel):
    expert_name: str = Field(min_length=2, max_length=100)
    answer: str = Field(min_length=5, max_length=4000)


class ExpertQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    farmer_id: int | None
    farmer_name: str
    crop: str | None
    category: str
    question: str
    language: str
    status: str
    answer: str | None
    expert_name: str | None
    answered_at: datetime | None
    created_at: datetime


class ExpertInboxItem(ExpertQuestionOut):
    phone: str | None  # only shown to experts, never in the farmer list
