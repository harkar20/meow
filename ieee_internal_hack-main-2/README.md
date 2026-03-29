# Meowmeow

**Intelligent Symptom Analysis & Risk Assessment Platform**

Meowmeow is a structured healthcare reasoning system that interviews users the way a clinician would — conversationally — and extracts clinical signals using NLP, Bayesian inference, and behavioral analysis.

## Architecture

```
Frontend (React + Vite)          Backend (FastAPI)              ML Pipeline
├── Firebase Auth (Google)       ├── JWT authentication         ├── NLP (spaCy/scispaCy)
├── Behavioral metadata capture  ├── PostgreSQL (SQLAlchemy)    ├── Intensity Analyzer
├── Speech-to-Text (Web API)     ├── Session management         ├── Bayesian Engine (pgmpy)
├── Text-to-Speech output        ├── REST API endpoints         ├── Interview Graph (networkx)
└── Framer Motion animations     └── ML service proxy           └── Temporal Trajectory
```

## Quick Start

### 1. Frontend

```bash
cd frontend
cp .env.example .env      # Add your Firebase config
npm install
npm run dev                # → http://localhost:5173
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env       # Configure DATABASE_URL, JWT_SECRET, etc.
uvicorn backend.main:app --reload --port 8000
```

### 3. ML Service (Sharan)

```bash
cd ml
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn ml_api:app --port 8001
```

## Environment Variables

### Frontend (.env)
| Variable | Description |
|---|---|
| `VITE_FIREBASE_API_KEY` | Firebase API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase auth domain |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID |
| `VITE_API_URL` | Backend URL (default: `http://localhost:8000/api`) |

### Backend (.env)
| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Secret for JWT token signing |
| `ML_SERVICE_URL` | ML microservice URL (default: `http://localhost:8001`) |
| `FIREBASE_PROJECT_ID` | Firebase project ID for token verification |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register with email/password |
| `POST` | `/api/auth/login` | Login with email/password |
| `POST` | `/api/auth/google` | Google Firebase auth |
| `GET` | `/api/auth/me` | Current user profile |
| `POST` | `/api/session/start` | Start clinical interview |
| `POST` | `/api/session/answer` | Submit answer + behavioral metadata |
| `GET` | `/api/session/result/:id` | Get risk assessment result |
| `GET` | `/api/session/history` | Past sessions |
| `POST` | `/api/session/population/report` | Submit anonymized population data |

## ML Integration

The backend calls the ML service at `ML_SERVICE_URL` for:
- `POST /ml/next-question` — adaptive question selection
- `POST /ml/infer` — Bayesian risk inference
- `POST /ml/extract-symptoms` — NLP symptom extraction
- `POST /ml/analyze-intensity` — text/audio intensity analysis
- `POST /ml/trajectory` — temporal trajectory analysis

If the ML service is unavailable, the backend degrades gracefully with default questions and placeholder results.

## Tech Stack

- **Frontend**: React, Vite, Framer Motion, Zustand, React Query, Firebase Auth, Recharts
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, JWT, Firebase Admin
- **ML**: spaCy, scispaCy, pgmpy, networkx, scikit-learn, librosa

## Team

- **Sharan** — AI/ML Pipeline
- **Teammate** — Frontend + Backend

## Medical Disclaimer

Meowmeow is **not** a medical diagnostic tool and does not replace professional medical advice. All outputs are informational only and based on probabilistic inference from symptom datasets. Always consult a qualified healthcare provider for medical decisions.
