# KrishiVeda — Architecture

```
┌──────────────────────────── Browser (mobile / desktop) ────────────────────────────┐
│ React 19 + Vite + Tailwind 4 · React Router · Recharts · EN/HI strings              │
│ pages/  Dashboard · Disease · Weather · Crops · Market · Advisory · Profile · ...    │
│ services/api.js  →  /api/*  (Vite dev proxy; no keys in the bundle)                 │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ JSON / multipart
┌───────────────────────────────────────▼─────────────────────────────────────────────┐
│ FastAPI (backend/app)                                                                │
│  api/        routers + consistent JSON error handlers                                │
│  schemas/    Pydantic validation (ranges, phone format, language)                    │
│  services/   disease_service ── disease_model_arch (shared with training)             │
│              crop_service · weather_service · irrigation_service                     │
│              market_service · advisory_service · http_client (OS trust store)        │
│  models/orm  SQLAlchemy 2.0 tables  ──►  SQLite (default) / MySQL 8                  │
│  data/       disease advisory, demo prices, knowledge base, schemes (EN/HI)          │
└──────┬───────────────┬────────────────────┬─────────────────────┬────────────────────┘
       │               │                    │                     │
  ml/models/*      Open-Meteo /         data.gov.in           Anthropic API
  (PyTorch CNN,    OpenWeather          (AGMARKNET)           (Claude, optional)
   scikit-learn)
```

## Disease detection pipeline

```
Leaf photo ─► validation (type, size ≤ 5 MB, ≥ 64 px, decodable, EXIF rotation)
          ─► preprocessing (resize short side 256 → centre crop 224 → ImageNet normalisation)
          ─► CNN: MobileNetV3-Large (convolutional feature extraction + new linear head, 39 outputs)
          ─► softmax → top-3 classes
          ─► status: no_leaf | uncertain (< 60 %) | healthy | diseased
          ─► advisory text from data/disease_info.json + disclaimer
          ─► stored in disease_analyses (image hash only, not the image)
```

`backend/app/services/disease_model_arch.py` defines the architecture and preprocessing once; the
training script imports it so training-time and prediction-time preprocessing cannot drift apart.
The final test-set evaluation calls the exact same `preprocess()` function the API uses.

## Irrigation guidance

* Measured: provider weather (temperature, humidity, rain, wind, FAO-56 reference ET0 from Open-Meteo).
* Estimated: crop water use `ETc = Kc × ET0` (FAO-56 Table 12 coefficients by growth stage),
  minus simplified effective rain (rain < 5 mm ignored, 80 % of the rest), over 3 days.
* Rules: delay if ≥ 10 mm rain in 2 days (or ≥ 70 % chance with ≥ 5 mm); irrigate if net need ≥ 15 mm;
  alerts use IMD heavy-rain thresholds (64.5 / 115.6 mm), heat ≥ 40 °C, frost ≤ 4 °C, wind > 15 km/h for spraying.
* No soil-moisture data is available, so the UI labels all quantities as estimates.

## Honesty rules built into the code

| Situation | Behaviour |
|-----------|-----------|
| Disease model missing / PyTorch not installed | `503 MODEL_NOT_AVAILABLE`, UI explains how to train |
| Low CNN confidence | status `uncertain`, asks for a better photo / expert |
| Crop model weak match (< 50 %) | explicit low-confidence warning |
| No data.gov.in key / API failure | demo prices with `is_demo: true` and a visible "Demo data" badge |
| No weather provider reachable | `503 WEATHER_UNAVAILABLE`, no made-up numbers |
| No Anthropic key / API failure | offline knowledge base, labelled "Offline guide" |

## Security notes

* All secrets come from environment variables (`backend/.env`, git-ignored); `.env.example` has none.
* CORS restricted to configured origins; only GET/POST/PUT allowed.
* Pydantic validates every input; uploads are size-limited before decoding and protected against
  decompression bombs.
* Internal errors are logged, never returned to clients.
* **Not yet implemented:** authentication. Farmer endpoints are open, which is acceptable only for a
  local single-user demo. See the 50 % milestone plan.
