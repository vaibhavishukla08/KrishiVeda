# KrishiVeda — Setup Guide

Tested on Windows 11 with Python 3.14, Node.js 24 and npm 11. The same steps work on macOS/Linux
(replace `.venv\Scripts\` with `.venv/bin/`).

## 1. Backend (FastAPI)

```powershell
cd D:\KrishiVeda
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -r backend\requirements.txt
.venv\Scripts\pip install -r backend\requirements-ml.txt   # PyTorch, needed for disease detection (~200 MB)
copy backend\.env.example backend\.env                      # then edit keys if you have them
```

Run the API (from the project root):

```powershell
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

- Interactive API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## 2. Frontend (React + Vite)

```powershell
cd D:\KrishiVeda\frontend
npm install
npm run dev
```

Open http://localhost:5173. In development, Vite forwards `/api/*` to the backend on port 8000, so
no API keys or backend URLs end up in the browser bundle.

Production build: `npm run build` (output in `frontend/dist`).

## 3. Machine-learning assets

Datasets and trained models are **not** committed to Git. Re-create them with:

```powershell
# Crop recommendation (2,200 rows, Apache 2.0) — about 150 KB, takes seconds
.venv\Scripts\python ml\datasets\fetch_crop_dataset.py
.venv\Scripts\python ml\training\train_crop_model.py

# Plant disease (PlantVillage, CC0) — downloads ~9,650 images (~150 MB) using HTTP range requests
.venv\Scripts\python ml\datasets\fetch_plantvillage_subset.py --per-class 250
.venv\Scripts\python ml\training\train_disease_cnn.py --head-epochs 1 --finetune-epochs 3
```

CPU training of the disease CNN took about 54 minutes on the development laptop. A checkpoint is
saved after every epoch; if training is interrupted, add `--resume` to the same command to continue.
The backend reloads `disease_cnn.pt` automatically when the file changes. Outputs:

| File | Purpose |
|------|---------|
| `ml/models/crop_recommender.joblib` | Random Forest + per-crop typical ranges |
| `ml/models/disease_cnn.pt` | MobileNetV3-Large weights, class names, preprocessing config, metrics |
| `ml/evaluation/*_report.json` | Hold-out metrics, per-class scores, confusion matrix |

The backend loads both models at startup. If a model file is missing, the related endpoint returns
`503 MODEL_NOT_AVAILABLE` with instructions — it never returns invented predictions.

## 4. Database

**SQLite (default)** — nothing to install. The file `backend/krishiveda.db` is created on first start.

**MySQL (recommended for deployment)**

1. Install MySQL 8 and create the database and user:
   ```sql
   CREATE DATABASE krishiveda CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'krishiveda'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON krishiveda.* TO 'krishiveda'@'localhost';
   ```
2. Set in `backend/.env`:
   ```
   DATABASE_URL=mysql+pymysql://krishiveda:choose-a-strong-password@localhost:3306/krishiveda?charset=utf8mb4
   ```
3. Start the backend — tables are created automatically. `database/schema.sql` contains the equivalent
   DDL if you prefer to create them manually.

## 5. Optional API keys (`backend/.env`)

| Variable | Without it | With it |
|----------|-----------|---------|
| `OPENWEATHER_API_KEY` | Free Open-Meteo API is used (real data, no key) | OpenWeather current weather + 5-day forecast |
| `DATA_GOV_IN_API_KEY` | Clearly labelled **demo** mandi prices | Live AGMARKNET prices from data.gov.in |
| `ANTHROPIC_API_KEY` | Offline knowledge-base answers (labelled) | Claude answers farmer questions |

Keys stay on the server; the frontend never sees them.

## 6. Tests

```powershell
cd D:\KrishiVeda\backend
..\.venv\Scripts\python -m pytest -q

cd D:\KrishiVeda\frontend
npm test
```

Backend tests use a temporary SQLite database and mocked HTTP responses, so they run offline.

## 7. Troubleshooting

- **`CERTIFICATE_VERIFY_FAILED: Missing Authority Key Identifier`** — your network (e.g. a campus
  firewall such as Sophos) inspects HTTPS traffic. The backend uses the OS certificate store via
  `truststore`, and the dataset scripts relax only Python 3.13+'s extra "strict" X.509 checks.
- **curl `CRYPT_E_NO_REVOCATION_CHECK`** on the same networks — add `--ssl-no-revoke`.
- **Frontend shows "Cannot reach the KrishiVeda server"** — start the backend on port 8000.
