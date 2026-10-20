# KrishiVeda API

Base URL (development): `http://localhost:8000`. Interactive docs with request/response schemas: `/docs`.

All errors use one JSON shape and a meaningful HTTP status:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Some inputs are invalid.",
             "details": { "fields": [{ "field": "ph", "message": "Input should be less than or equal to 10" }] } } }
```

Unexpected server errors return `500 INTERNAL_ERROR` without internal details (they are logged server-side).

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | DB connectivity, model availability, which providers are active (live/demo/offline) |

## Farmers & history

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/farmers` | Create farmer (+ optional farm and crops). `201` |
| GET | `/api/farmers/{id}` | Farmer with farms and crops. `404 FARMER_NOT_FOUND` |
| PUT | `/api/farmers/{id}` | Update farmer; replaces the first farm's details and crop list |
| GET | `/api/farmers/{id}/history?limit=20` | Recent disease analyses, crop recommendations and advisory Q&A |
| GET | `/api/farmers/{id}/stats?days=30` | Aggregates for the Reports page |

Example body:

```json
{ "name": "Ramesh Kumar", "phone": "9876543210", "preferred_language": "hi", "state": "Punjab",
  "farm": { "location_name": "Ludhiana", "area_acres": 2.5, "soil_type": "alluvial",
            "crops": [{ "crop_name": "wheat", "season": "rabi" }] } }
```

## Plant disease detection

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/disease/model` | Model availability, version, test metrics, supported crops/classes |
| POST | `/api/disease/predict` | `multipart/form-data`: `file` (JPG/PNG/WEBP ≤ 5 MB, ≥ 64×64 px), optional `farmer_id` |

Response (abridged):

```json
{ "status": "diseased",                       // healthy | diseased | uncertain | no_leaf
  "message": "Signs of Late blight were detected on the tomato leaf.",
  "prediction": { "class": "Tomato___Late_blight", "probability": 0.97, "crop": "Tomato", "disease": "Late blight" },
  "top_predictions": [ ... 3 items ... ],
  "advisory": { "cause": "...", "symptoms": "...", "management": ["..."], "prevention": ["..."] },
  "model_version": "pv-mnv3l-20261019", "analysis_id": 12, "disclaimer": "..." }
```

Errors: `400 EMPTY_FILE | INVALID_IMAGE | IMAGE_TOO_SMALL`, `413 FILE_TOO_LARGE`,
`415 UNSUPPORTED_FILE_TYPE`, `503 MODEL_NOT_AVAILABLE`.

## Crop recommendation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/crops/model` | Algorithm, dataset, licence, hold-out metrics |
| POST | `/api/crops/recommend` | Body: `N, P, K` (kg/ha), `temperature` (°C), `humidity` (%), `ph`, `rainfall` (mm), optional `farmer_id` |

Validation limits: N 0–300, P 0–300, K 0–400, temperature −10–55, humidity 0–100, pH 3–10, rainfall 0–5000.
Values outside the training data range are accepted but produce a `warnings` entry.

## Weather & irrigation

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/weather?city=Ludhiana` or `?lat=..&lon=..` | Current weather, 5-day forecast, rule-based alerts |
| GET | `/api/irrigation/advice?city=..&crop=wheat&stage=mid&area_acres=2` | Weather + irrigation advice (`irrigate`/`delay`/`monitor`) and FAO-56 water estimate |

Errors: `400 LOCATION_REQUIRED`, `404 LOCATION_NOT_FOUND`, `503 WEATHER_UNAVAILABLE | WEATHER_KEY_INVALID`.
Responses are cached for 10 minutes per location.

## Market prices

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/market-prices?commodity=Wheat&state=Punjab&limit=50` | `mode` is `live` (AGMARKNET) or `demo`; each record has `source` and `is_demo` |
| GET | `/api/market-prices/commodities` | Commodities available in the demo dataset |

## Advisory assistant

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/advisory/status` | Whether an AI provider is configured |
| POST | `/api/advisory/ask` | Body: `question` (3–1000 chars), `language` (`en`/`hi`), optional `farmer_id`, `history` |

`provider` in the response is `anthropic` or `knowledge_base`; `notice` explains any fallback.

## Ask an expert (human)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/expert/contacts` | Kisan Call Centre number/hours, KVK portal link, whether the Expert Panel is enabled |
| POST | `/api/expert/questions` | Farmer sends a question: `farmer_name`, `question` (10–2000 chars), optional `farmer_id`, `phone`, `crop`, `category`, `language`. `201` |
| GET | `/api/expert/questions?farmer_id=1` | The farmer's own questions with status and the expert's answer (phone not included) |
| GET | `/api/expert/verify` | 🔒 Check an expert access code |
| GET | `/api/expert/inbox?status=open\|answered\|all` | 🔒 Questions for experts (open ones oldest first; includes phone for call-back) |
| POST | `/api/expert/questions/{id}/answer` | 🔒 Body: `expert_name`, `answer` → marks the question answered |

🔒 = requires header `X-Expert-Code` matching `EXPERT_ACCESS_CODE` in `backend/.env`
(`401 INVALID_EXPERT_CODE`; `503 EXPERT_PANEL_DISABLED` if no code is configured). This shared code
is a stop-gap until expert accounts with login are built.

## Resources

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/resources/schemes` | Government schemes with official links, helplines |
| GET | `/api/resources/stubble` | Parali management alternatives (English + Hindi) |
