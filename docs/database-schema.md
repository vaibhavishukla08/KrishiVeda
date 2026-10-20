# Database Schema

Defined in `backend/app/models/orm.py` (SQLAlchemy) and mirrored as MySQL DDL in `database/schema.sql`.

## Where is the data stored?

| Data | Location |
|------|----------|
| All app records (farmers, farms, crops, disease checks, recommendations, advice, weather log) | SQLite file `backend/krishiveda.db` by default, or the MySQL database set in `DATABASE_URL` |
| Uploaded leaf photos | **Not stored** — only the SHA-256 hash and file name are saved |
| Which farmer this browser is | `localStorage` key `kv_farmer_id` (and `kv_lang` for language) |
| Trained models | `ml/models/` |
| Test runs | a temporary SQLite file, never the real database |

Open the SQLite file with [DB Browser for SQLite](https://sqlitebrowser.org/) or from Python:
`python -c "import sqlite3; print(sqlite3.connect('backend/krishiveda.db').execute('select * from farmers').fetchall())"`.
To start fresh, stop the backend and delete `backend/krishiveda.db` — it is recreated empty on next start.

```
farmers 1 ──< farms 1 ──< farm_crops
   │
   ├──< disease_analyses       (farmer_id nullable: anonymous checks allowed)
   ├──< crop_recommendations
   └──< advisory_messages

weather_records   (log of fetched weather, per location)
market_prices     (cache of live AGMARKNET records; is_demo flag)
```

| Table | Key columns | Notes |
|-------|-------------|-------|
| farmers | id, name, phone, preferred_language, state, district, village, created_at, updated_at | phone validated as Indian mobile |
| farms | id, farmer_id → farmers (CASCADE), location_name, latitude, longitude, area_acres, soil_type, irrigation_type | location used for weather |
| farm_crops | id, farm_id → farms (CASCADE), crop_name, season, sowing_date | |
| disease_analyses | id, farmer_id → farmers (SET NULL), image_sha256, status, predicted_class, crop, disease, confidence, top_predictions (JSON), model_version, created_at | image not stored, only its SHA-256 |
| crop_recommendations | id, farmer_id, inputs (JSON), recommended_crop, confidence, alternatives (JSON), model_version, created_at | |
| weather_records | id, location_name, latitude, longitude, temperature_c, humidity_pct, rain_mm, condition, source, observed_at | |
| market_prices | id, commodity, variety, market, district, state, min/max/modal_price, unit, price_date, source, is_demo, fetched_at | index (commodity, price_date) |
| advisory_messages | id, farmer_id, question, answer, provider, language, created_at | provider = gemini / anthropic / knowledge_base |
| expert_questions | id, farmer_id → farmers (SET NULL), farmer_name, phone, crop, category, question, language, status, answer, expert_name, answered_at, created_at | questions for human experts; phone shown only in the Expert Panel |

Indexes: `(farmer_id, created_at)` on the three history tables for fast "recent history" queries.

Tables are created automatically on backend start (`init_db()`); there is no migration tool yet
(Alembic is planned for the next milestone).
