# 🌱 KrishiVeda — AI-Powered Smart Agriculture MIS

**"Predicting Tomorrow's Risks, Protecting Today's Crops."**

KrishiVeda helps small farmers make better decisions with plant-disease detection from leaf photos,
weather-based irrigation guidance, data-driven crop recommendation, mandi prices and a farm advisory
assistant — in English and Hindi, on mobile or desktop.

| Module | Status | Data source |
|--------|--------|-------------|
| Dashboard (weather, crop health, irrigation, prices, alerts, history, quick actions) | ✅ Working | Backend APIs |
| Plant disease detection (upload → CNN → advisory) | ✅ Working — 98.6 % on lab photos, 63.6 % on real-field photos | MobileNetV3 trained on PlantVillage (CC0) + PlantDoc (CC BY 4.0) |
| Weather & smart irrigation | ✅ Working | Open-Meteo (no key) or OpenWeather (key); FAO-56 estimates |
| Crop recommendation | ✅ Working | Random Forest on Kaggle crop dataset (Apache 2.0) |
| Farmer profile & history | ✅ Working | SQLite by default, MySQL supported |
| Market prices | 🟡 Demo data until a data.gov.in key is added | AGMARKNET via data.gov.in |
| AI Farm Assistant | 🟡 Offline knowledge base until a Gemini key is added | Google Gemini (free tier) or Claude |
| Ask an Expert (human) | ✅ Working — farmers send questions, experts answer in the Expert Panel; one-tap Kisan Call Centre and KVK links | Expert Panel protected by `EXPERT_ACCESS_CODE` |
| Govt. schemes, Parali management | 🟡 Static reference content | Official portals |
| Reports / analytics | 🟡 Basic charts | Farmer history |
| English / Hindi | ✅ UI fully bilingual; some backend messages English-only | — |

## Quick start (Windows PowerShell)

```powershell
# Backend
python -m venv .venv
.venv\Scripts\pip install -r backend\requirements.txt -r backend\requirements-ml.txt
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload --port 8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Train or download the ML models first — see [docs/setup.md](docs/setup.md) and [ml/README.md](ml/README.md).

## Project structure

```
backend/   FastAPI app (api/, services/, models/, schemas/, database/, data/) + tests/
frontend/  React 19 + Vite + Tailwind 4 (pages/, components/, services/, hooks/, i18n/, utils/)
ml/        dataset download, training and evaluation scripts; trained models (git-ignored)
database/  MySQL schema (schema.sql)
docs/      setup, architecture, API, database schema, progress report
```

## Documentation

- [Setup guide](docs/setup.md) — install, run, database, API keys, troubleshooting
- [Architecture](docs/architecture.md) — components, pipelines, honesty & security rules
- [API reference](docs/api.md)
- [Database schema](docs/database-schema.md)
- [ML models & datasets](ml/README.md)
- [Progress report & completion checklist](docs/progress.md)

## Important

Disease and crop results are **preliminary decision support**, not a replacement for an agriculture
expert. Confirm with your Krishi Vigyan Kendra (KVK) or the Kisan Call Centre (1800-180-1551) before
spraying chemicals or making major decisions.
