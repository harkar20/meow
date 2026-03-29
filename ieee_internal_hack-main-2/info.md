# Meowmeow Hackathon Extension Report

## 1. Project Overview

### What the project does
Meowmeow is an AI-assisted clinical interview platform. A user answers adaptive symptom questions in the frontend UI, and the system returns a risk-oriented assessment with probable conditions and recommended action.

### Problem statement
Patients often struggle to explain symptoms clearly, and triage quality drops when context is missing. The project solves this by collecting structured answers plus behavioral signals, then running ML-assisted reasoning to produce clearer, faster preliminary risk insights.

### Key features
- User authentication (email/password and Google token flow)
- Adaptive interview sessions with dynamic follow-up questions
- Behavioral metadata capture from typing patterns
- AI/ML-backed risk inference with graceful fallback when ML service is down
- Session history and population-level anonymous reporting

## 2. Architecture

### Components
- Frontend: React + Vite (`frontend/`)
- Backend API: FastAPI (`backend/`)
- Database: PostgreSQL via SQLAlchemy (configurable by `DATABASE_URL`)
- AI/ML service: FastAPI microservice (`ml/ml_api.py`)

### Data flow (step-by-step)
1. User interacts with React pages (login, interview, history, population).
2. Frontend calls backend REST endpoints at `/api/...`.
3. FastAPI routes validate payloads, authenticate users, and write/read records using SQLAlchemy models.
4. Backend calls ML service endpoints (`/ml/next-question`, `/ml/analyze-intensity`, `/ml/infer`) for adaptive questioning and risk inference.
5. ML output is stored in session records and returned to frontend.
6. Frontend renders progress, risk output, history, and aggregated population signals.

## 3. What AI Did

### Files created
- `backend/services/__init__.py`
- `backend/services/ml_service.py`
- `backend/.env.example`
- `info.md`

### Files modified
- `backend/routes/session.py`
- `backend/database.py`
- `backend/main.py`
- `backend/auth.py`
- `backend/requirements.txt`
- `frontend/src/api/endpoints.js`
- `frontend/src/api/client.js`

### Why each change was necessary
- `backend/services/ml_service.py`: centralized ML proxy calls so route logic stays thin and stable.
- `backend/routes/session.py`: reused the new service helper and cleaned imports for safer runtime behavior.
- `backend/database.py`: improved DB URL compatibility (`postgres://` normalization) and safer pooled connections (`pool_pre_ping=True`).
- `backend/main.py`: added `/health/db` endpoint so DB connectivity is testable directly in browser/Postman.
- `backend/.env.example`: provided a ready PostgreSQL configuration template for fast setup.
- `frontend/src/api/endpoints.js`: switched history/population requests from mock to real backend for true end-to-end flow.
- `frontend/src/api/client.js`: fixed default API base URL to `http://localhost:8000/api` for backend alignment.
- `backend/auth.py`: changed JWT import to `python-jose` (already in requirements) to remove runtime import failure.
- `backend/requirements.txt`: pinned `bcrypt==4.0.1` to avoid passlib/bcrypt runtime incompatibility on current Python.

## 4. Code Explanation

### Important backend functions/APIs
- `backend/main.py`
  - `app`: FastAPI application setup, CORS config, router registration.
  - `/health`: basic liveness endpoint.
  - `/health/db`: confirms configured database is reachable.
- `backend/routes/auth.py`
  - `/api/auth/register`: creates user and returns JWT.
  - `/api/auth/login`: validates credentials and returns JWT.
  - `/api/auth/me`: returns current authenticated user.
- `backend/routes/session.py`
  - `/api/session/start`: creates a new interview session.
  - `/api/session/answer`: stores answer + metadata, requests next ML question.
  - `/api/session/result/{id}`: computes/fetches risk output and persists session result.
  - `/api/session/history`: returns user’s recent sessions.
  - `/api/session/population/report` and `/summary`: records and retrieves anonymous aggregate symptom data.
- `backend/services/ml_service.py`
  - `call_ml_service(...)`: backend-to-ML HTTP bridge with graceful fallback behavior.

### Database schema (SQLAlchemy models)
- `users` (`backend/models/user.py`)
  - auth + profile fields: `id`, `email`, `hashed_password`, demographic and health profile fields.
- `sessions` (`backend/models/session.py`)
  - interview lifecycle: `id`, `user_id`, `status`, `risk_tier`, `risk_score`, `top_conditions`, timestamps.
- `session_answers`
  - per-question captured content + behavioral metadata for each session.
- `population_aggregate`
  - anonymous city/region/category event records for trend dashboards.
- `symptom_vectors`
  - optional extracted symptom mappings per session.

## 5. How to Run (VERY IMPORTANT)

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- PostgreSQL 14+

### A) Setup PostgreSQL
```bash
psql -U postgres
CREATE DATABASE meowmeow;
```

### B) Run backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` if needed:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/meowmeow
ML_SERVICE_URL=http://localhost:8001
JWT_SECRET=change-me-in-production
```

Start backend:
```bash
cd ..
python -m uvicorn backend.main:app --reload --port 8000
```

### C) Run ML service
```bash
cd ml
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
python -m uvicorn ml.ml_api:app --reload --port 8001
```

### D) Run frontend
```bash
cd frontend
npm install
```

Create `.env` in `frontend/`:
```env
VITE_API_URL=http://localhost:8000/api
VITE_FIREBASE_API_KEY=your_key
VITE_FIREBASE_AUTH_DOMAIN=your_domain
VITE_FIREBASE_PROJECT_ID=your_project
```

Start frontend:
```bash
npm run dev
```

## 6. API Documentation

### Auth
- `POST /api/auth/register`
  - Request:
    ```json
    {"email":"user@example.com","password":"Pass1234!","full_name":"User"}
    ```
  - Response:
    ```json
    {"access_token":"...","token_type":"bearer","user":{"id":"...","email":"user@example.com"}}
    ```

- `POST /api/auth/login`
  - Request:
    ```json
    {"email":"user@example.com","password":"Pass1234!"}
    ```

- `GET /api/auth/me` (Bearer token required)

### Session
- `POST /api/session/start` (Bearer token required)
  - Response:
    ```json
    {"session_id":"...","first_question":"...","question_category":"general"}
    ```

- `POST /api/session/answer` (Bearer token required)
  - Request:
    ```json
    {
      "session_id":"...",
      "question_text":"...",
      "question_category":"general",
      "answer_text":"I feel tired since yesterday",
      "behavioral_metadata":{"deleted_segments":[],"typing_latency_ms":[110,95],"edit_count":1,"hedge_word_count":0}
    }
    ```

- `GET /api/session/result/{session_id}` (Bearer token required)
- `GET /api/session/history` (Bearer token required)

### Population
- `POST /api/session/population/report`
  - Request:
    ```json
    {"region":"CA","city":"San Francisco","symptom_category":"fatigue"}
    ```
- `GET /api/session/population/summary`

### Health
- `GET /health`
- `GET /health/db`

## 7. Demo Flow

1. Open frontend (`http://localhost:5173`).
2. Register/Login.
3. Start interview and submit multiple symptom answers.
4. View generated result page with risk tier and likely conditions.
5. Open history page and confirm completed assessment appears.
6. Open population page and confirm aggregate symptom data renders.
7. Verify backend health endpoints in browser/Postman:
   - `http://localhost:8000/health`
   - `http://localhost:8000/health/db`
   - `http://localhost:8000/docs`

## Updated File Structure (relevant)

```text
backend/
  .env.example
  main.py
  database.py
  auth.py
  requirements.txt
  routes/
    auth.py
    session.py
  models/
    user.py
    session.py
  services/
    __init__.py
    ml_service.py
frontend/
  src/
    api/
      client.js
      endpoints.js
ml/
  ml_api.py
info.md
```

## 8. Hackathon Boost

### 🔥 1. Feature Suggestions
- Add a “Red Flag Detector” banner: instantly show urgent keywords like chest pain, breathing difficulty, suicidal ideation, and recommend emergency action.
- Add PDF export for report: one-click downloadable summary with risk tier, top conditions, and next steps.
- Add multilingual interview mode: start with English + one local language using simple translation mapping.
- Add doctor handoff view: concise clinician-facing summary (symptoms timeline, behavioral flags, confidence).
- Add trend snapshot in dashboard: “your last 3 sessions” risk movement chart to show continuity.
- Add AI confidence explanation chips: small tags like “symptom match,” “intensity pattern,” “behavioral hesitation.”

### 🧠 2. Learning Focus
- FastAPI request lifecycle: routing, dependency injection, auth dependency, and response models.
- SQLAlchemy basics: model mapping, session lifecycle, transactions, and how table creation happens.
- JWT auth flow: token creation, validation, and protected endpoints.
- Service-layer pattern: why backend routes call `services/ml_service.py` instead of embedding HTTP logic.
- Graceful degradation: how fallback behavior works when ML service is unavailable.
- End-to-end API flow: React client → `/api/session/*` → DB + ML service.

### ⚠️ 3. Possible Questions by Judges
- Technical:
  - Why did you choose FastAPI over Flask/Django?
  - How do you ensure API reliability if the ML service is down?
  - How do you validate and secure user input?
- Architecture:
  - Why split backend and ML into separate services?
  - How does data move from interview response to final risk output?
  - Where is state stored, and what is persistent vs in-memory?
- AI/ML:
  - Which features influence risk tier most?
  - How do you avoid overclaiming medical certainty?
  - How do behavioral signals improve inference quality?
  - How would you evaluate model quality (accuracy, precision, recall, calibration)?

### 🛠️ 4. Challenges You May Face
- Local environment mismatch:
  - PostgreSQL URL/credentials wrong, missing tables, or port conflicts.
  - Node/npm or Python package version mismatch.
- Runtime service issues:
  - Backend starts but ML service is not reachable on `:8001`.
  - CORS or incorrect frontend API URL.
- Auth/demo edge cases:
  - Firebase key missing for Google auth.
  - JWT/bcrypt dependency compatibility issues.
- Deployment/scaling questions:
  - Cold-start latency on free tiers.
  - Need for background queueing if ML inference becomes slow.
  - Database connection limits under parallel demo traffic.

### 🎤 5. Pitch Tips (1–2 Minutes)
- 20 sec — Problem:
  - “Patients describe symptoms inconsistently, causing triage delays and missed context.”
- 30 sec — Solution:
  - “Meowmeow runs a structured AI interview, captures behavioral signals, and produces explainable risk guidance.”
- 30 sec — Architecture confidence:
  - “React frontend talks to FastAPI, FastAPI stores sessions in PostgreSQL and calls ML microservice for adaptive questioning and inference.”
- 20 sec — Demo highlights:
  - “Login, run interview, show result page, then show history and population analytics.”
- 20 sec — Safety + practicality:
  - “The system is assistive, not diagnostic; it degrades gracefully when ML is offline, so the workflow always stays usable.”
