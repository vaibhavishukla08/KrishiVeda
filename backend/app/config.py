"""Application settings, loaded from environment variables or backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "KrishiVeda API"
    app_version: str = "0.35.0"

    # SQLite works out of the box. For MySQL use e.g.
    # mysql+pymysql://krishiveda:password@localhost:3306/krishiveda?charset=utf8mb4
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'krishiveda.db').as_posix()}"

    # Comma-separated list of allowed frontend origins
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # External services (all optional)
    openweather_api_key: str = ""
    data_gov_in_api_key: str = ""
    # Access code for the Expert Panel (until real login exists). Empty = panel disabled.
    expert_access_code: str = ""

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    anthropic_api_key: str = ""
    advisory_model: str = "claude-opus-5-5"

    # ML artefacts
    disease_model_path: Path = PROJECT_ROOT / "ml" / "models" / "disease_cnn.pt"
    crop_model_path: Path = PROJECT_ROOT / "ml" / "models" / "crop_recommender.joblib"
    # Below this confidence the disease result is reported as "uncertain"
    disease_confidence_threshold: float = 0.70

    max_upload_mb: float = 5.0
    http_timeout_seconds: float = 12.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
