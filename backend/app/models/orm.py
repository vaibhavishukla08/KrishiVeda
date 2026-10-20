"""Database tables (SQLAlchemy 2.0 ORM). The MySQL DDL equivalent is in database/schema.sql."""

from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Farmer(TimestampMixin, Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(15))
    preferred_language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    state: Mapped[str | None] = mapped_column(String(60))
    district: Mapped[str | None] = mapped_column(String(60))
    village: Mapped[str | None] = mapped_column(String(100))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    farms: Mapped[list["Farm"]] = relationship(back_populates="farmer", cascade="all, delete-orphan")


class Farm(TimestampMixin, Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), default="My Farm")
    location_name: Mapped[str | None] = mapped_column(String(120))  # used for weather lookup
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    area_acres: Mapped[float | None] = mapped_column(Float)
    soil_type: Mapped[str | None] = mapped_column(String(40))
    irrigation_type: Mapped[str | None] = mapped_column(String(40))

    farmer: Mapped[Farmer] = relationship(back_populates="farms")
    crops: Mapped[list["FarmCrop"]] = relationship(back_populates="farm", cascade="all, delete-orphan")


class FarmCrop(TimestampMixin, Base):
    __tablename__ = "farm_crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    crop_name: Mapped[str] = mapped_column(String(40), nullable=False)
    season: Mapped[str | None] = mapped_column(String(20))  # kharif / rabi / zaid
    sowing_date: Mapped[date | None] = mapped_column(Date)

    farm: Mapped[Farm] = relationship(back_populates="crops")


class DiseaseAnalysis(TimestampMixin, Base):
    __tablename__ = "disease_analyses"
    __table_args__ = (Index("ix_disease_farmer_created", "farmer_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="SET NULL"))
    image_name: Mapped[str | None] = mapped_column(String(255))
    image_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20))  # healthy / diseased / uncertain / no_leaf
    predicted_class: Mapped[str] = mapped_column(String(80))
    crop: Mapped[str | None] = mapped_column(String(40))
    disease: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float] = mapped_column(Float)
    top_predictions: Mapped[list] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(40))


class CropRecommendation(TimestampMixin, Base):
    __tablename__ = "crop_recommendations"
    __table_args__ = (Index("ix_croprec_farmer_created", "farmer_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="SET NULL"))
    inputs: Mapped[dict] = mapped_column(JSON)
    recommended_crop: Mapped[str] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    alternatives: Mapped[list] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(40))


class WeatherRecord(Base):
    __tablename__ = "weather_records"
    __table_args__ = (Index("ix_weather_location_observed", "location_name", "observed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_name: Mapped[str] = mapped_column(String(120))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    rain_mm: Mapped[float | None] = mapped_column(Float)
    condition: Mapped[str | None] = mapped_column(String(80))
    source: Mapped[str] = mapped_column(String(40))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MarketPrice(Base):
    __tablename__ = "market_prices"
    __table_args__ = (Index("ix_market_commodity_date", "commodity", "price_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commodity: Mapped[str] = mapped_column(String(60))
    variety: Mapped[str | None] = mapped_column(String(60))
    market: Mapped[str] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(60))
    state: Mapped[str | None] = mapped_column(String(60))
    min_price: Mapped[float | None] = mapped_column(Float)
    max_price: Mapped[float | None] = mapped_column(Float)
    modal_price: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="Rs/quintal")
    price_date: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(120))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExpertQuestion(TimestampMixin, Base):
    """A question a farmer sends to a human agriculture expert (answered in the Expert Panel)."""

    __tablename__ = "expert_questions"
    __table_args__ = (
        Index("ix_expert_status_created", "status", "created_at"),
        Index("ix_expert_farmer_created", "farmer_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="SET NULL"))
    farmer_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(15))  # so the expert can call back if needed
    crop: Mapped[str | None] = mapped_column(String(40))
    category: Mapped[str] = mapped_column(String(20))  # disease / pest / irrigation / soil / weather / market / other
    question: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(5), default="en")
    status: Mapped[str] = mapped_column(String(10), default="open")  # open / answered
    answer: Mapped[str | None] = mapped_column(Text)
    expert_name: Mapped[str | None] = mapped_column(String(100))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdvisoryMessage(TimestampMixin, Base):
    __tablename__ = "advisory_messages"
    __table_args__ = (Index("ix_advisory_farmer_created", "farmer_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id", ondelete="SET NULL"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(40))  # "anthropic" or "knowledge_base"
    language: Mapped[str] = mapped_column(String(5), default="en")
