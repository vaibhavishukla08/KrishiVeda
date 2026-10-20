# KrishiVeda — Progress Report (Milestone 1)

Date: 19 October 2026 · Version 0.35.0

## How completion is measured

Each requirement of the full project is given an **effort weight** (1 = small, 6 = very large) and a
score: **1** = implemented and tested, **0.5** = partly implemented, **0** = not started.
Completion = Σ(weight × score) / Σ(weight). Only features that run and were tested in this session
count as implemented.

| # | Requirement | Weight | Status | Score | Evidence |
|---|-------------|:-----:|--------|:----:|----------|
| 1 | React frontend, routing, responsive layout, mobile navigation | 3 | ✅ Done | 3 | `npm run build` OK; checked at 375 px and 1024 px, no horizontal scroll |
| 2 | FastAPI backend, validation, consistent JSON errors | 3 | ✅ Done | 3 | 67 backend tests |
| 3 | Initial automated tests + setup/API/architecture docs | 3 | ✅ Done | 3 | pytest + vitest; `docs/` |
| 4 | Authentication, authorisation, security hardening | 4 | ❌ Not started | 0 | endpoints are open (local demo only) |
| 5 | Deployment (hosting, HTTPS, CI/CD) | 4 | ❌ Not started | 0 | — |
| 6 | Database schema + persistence workflow | 3 | ✅ Done | 3 | profiles, history saved & read back (SQLite) |
| 7 | MySQL verified on a server + migrations (Alembic) | 2 | 🟡 Partial | 0.5 | MySQL DDL compiles; no server available to test |
| 8 | **A** Dashboard (overview cards, alerts, history, quick actions) | 3 | ✅ Done | 3 | verified in browser with live weather |
| 9 | **B** Disease detection: upload, validation, preview, API, preprocessing, inference, advisory | 4 | ✅ Done | 4 | validation tests; real inference test |
| 10 | **B** Trained CNN with documented evaluation (lab dataset) | 4 | ✅ Done | 4 | 98.23 % test accuracy, macro-F1 98.21 % (1,467 held-out images) |
| 11 | **B** Field-robust model incl. Indian staple crops (wheat, rice, cotton …) | 6 | 🟡 Partial | 3 | field accuracy 29.2 % → 63.6 % with PlantDoc; staple crops still missing |
| 12 | **C** Weather integration with tested fallback | 3 | ✅ Done | 3 | live Open-Meteo verified; OpenWeather path tested with mocks |
| 13 | **C** Rule-based irrigation guidance (FAO-56 estimates) | 3 | ✅ Done | 3 | 14 rule/endpoint tests |
| 14 | **C** Soil-moisture / sensor integration | 3 | ❌ Not started | 0 | — |
| 15 | Alerts & notifications (SMS / push) | 3 | 🟡 Partial | 0.5 | in-app alerts only |
| 16 | **D** Crop recommendation model + explanation | 4 | ✅ Done | 4 | RF 99.3 % hold-out; explanation table |
| 17 | **D** Location/season-aware recommendation (soil card, district data) | 3 | ❌ Not started | 0 | — |
| 18 | **E** Farmer profile, farm, crops, history | 3 | ✅ Done | 3 | UI + API + tests |
| 19 | **F** Market price dashboard + replaceable integration | 2 | ✅ Done | 2 | demo clearly labelled; live parser tested with mock |
| 20 | **F** Live prices verified with a real key, trends | 3 | ❌ Not started | 0 | no data.gov.in key available |
| 21 | **G** Advisory UI + offline knowledge-base fallback + "Ask an Expert" (human experts answer via Expert Panel; Kisan Call Centre & KVK links) | 2 | ✅ Done | 2 | EN/HI answers tested; ask → answer → reply flow tested in API and browser |
| 22 | **G** Real AI provider tested live, context-aware | 3 | 🟡 Partial | 1 | Claude integration coded; not tested (no key) |
| 23 | Parali/stubble management module | 2 | 🟡 Partial | 1 | static bilingual content |
| 24 | Government schemes module | 2 | 🟡 Partial | 1 | static list with official links |
| 25 | Analytics & reports (incl. export) | 3 | 🟡 Partial | 1 | basic charts; no export |
| 26 | English/Hindi coverage | 3 | 🟡 Partial | 2 | UI fully bilingual; some backend text English-only |
| 27 | Accessibility extras: voice input, offline/PWA, low-literacy UX | 4 | 🟡 Partial | 0.5 | keyboard focus, labels, contrast only |
| | **Total** | **85** | | **50.5** | **≈ 59 %** |

**Result: ≈ 59 % by this checklist — above the 35 % target.** This number depends on how the
full scope is defined. The biggest remaining items (field-robust disease model, authentication,
deployment, live data verification) are also the hardest, so the remaining ~44 % will take more
effort than the first 56 %.

## Model results (actual)

| Model | Result |
|-------|--------|
| Disease CNN v1 — lab only (PlantVillage subset, 39 classes) | lab test **98.23 %**, but real-field photos only **29.24 %** |
| Disease CNN v2 — lab + field (PlantVillage + PlantDoc), **deployed** | lab test **98.64 %**, field test **63.56 %** (crop identified 80.9 %, top-3 89.4 %); with the 70 % confidence threshold, confident field answers are 82.1 % correct |
| Crop recommender (Random Forest, 22 crops) | hold-out accuracy **99.32 %**, macro-F1 99.32 %, 5-fold CV 99.38 % ± 0.55 % |

Both scores are on lab/curated datasets; real-field performance is expected to be lower (see `ml/README.md`).

## Tests executed (actual results, 20 Oct 2026)

| Suite | Command | Result |
|-------|---------|--------|
| Backend (pytest) | `cd backend; ..\.venv\Scripts\python -m pytest -q` | **67 passed, 0 skipped** |
| Frontend (vitest) | `cd frontend; npm test` | **6 passed** |
| Frontend build | `npm run build` | OK (main bundle 270 kB, pages lazy-loaded) |
| Manual (browser) | dashboard, profile save, crop form, weather, Hindi toggle, advisory, leaf upload | all working; live Open-Meteo weather; held-out tomato late-blight leaf → "Disease detected, 83 %" (v1 model) |
| Field evaluation | `python ml/evaluation/evaluate_disease.py --data ml/datasets/plantdoc/test` | v1 29.24 % → v2 63.56 % on 236 field photos |
| Mobile layout | 375 px viewport | no horizontal scroll, bottom navigation works |

Not tested (no credentials / software available): MySQL server, live data.gov.in prices, live Claude answers.

## Next milestone (to reach ~65 %)

1. Authentication (phone + password/OTP, hashed passwords, per-farmer access control).
2. Live data: add data.gov.in and Anthropic keys and verify; add price trend charts.
3. MySQL on a real server + Alembic migrations.
4. Disease model: add Indian staple crops (wheat rust, rice blast, cotton leaf curl) and more field photos (collect local photos with expert labels) to push field accuracy beyond 64 %.
5. Region/season-aware crop recommendation using Soil Health Card values and district rainfall.
6. Deployment (Docker, HTTPS hosting) and CI running both test suites.
7. Translate remaining backend advisory text to Hindi; add voice input.
