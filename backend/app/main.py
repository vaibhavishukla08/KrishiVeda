"""KrishiVeda API — run with:  uvicorn app.main:app --reload  (from the backend folder)."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response

from app.api import crops, disease, expert, farmers, misc, weather
from app.api.errors import register_error_handlers
from app.config import get_settings
from app.database.session import init_db
from app.services import crop_service, disease_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    # Load ML models once at startup so the first request is fast
    disease_service.load_model()
    crop_service.load_model()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered smart agriculture API — Predicting Tomorrow's Risks, Protecting Today's Crops.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "X-Expert-Code"],
)
register_error_handlers(app)

for module in (misc, farmers, disease, crops, weather, expert):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def root():
    """Opening the backend URL in a browser shows the interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
