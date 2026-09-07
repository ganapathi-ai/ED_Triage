# ED Triage AI Assistant

AI-powered decision support tool for emergency department triage, based on the **Emergency Severity Index (ESI) v5** algorithm (Emergency Nurses Association, 2023).

## What it does

- Collects patient demographics, vital signs, and symptoms
- Runs rule-based triage engine (ESI Decision Points A–D)
- Assigns an ESI level (1–5) and risk level (HIGH/MEDIUM/LOW)
- Generates clinician-friendly explanations and recommendations
- Records clinician override and patient outcome for accuracy tracking
- Dashboard showing AI vs clinician agreement, under-triage, over-triage

## Architecture

```
React (Vite) UI  →  FastAPI backend  →  PostgreSQL / SQLite
                        ↓
                 ESI Rule Engine
```

## Project structure

```
Triage_assist/
├── app/
│   ├── main.py          # FastAPI app + endpoints
│   ├── triage.py        # ESI rule engine (heart of the AI)
│   ├── database.py      # SQLAlchemy models
│   └── models.py        # Pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── components/
│   │       ├── TriageForm.jsx
│   │       ├── TriageResult.jsx
│   │       ├── AssessmentHistory.jsx
│   │       └── Dashboard.jsx
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
├── render.yaml
└── .env.example
```

## Run locally

### Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Run with SQLite (no external DB needed)

The app defaults to SQLite if no `DATABASE_URL` is set:
```bash
# No .env file needed — just run the backend
uvicorn app.main:app --reload
```

## Run with PostgreSQL

Set `DATABASE_URL` to a PostgreSQL connection string:
```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/triage_db
```

## Deploy to Render

1. Push the repo to GitHub
2. Create a new Web Service on Render
3. Connect your repo
4. Use the `render.yaml` (or set manually):
   - Build: `pip install -r requirements.txt && cd frontend && npm install && npm run build`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add `DATABASE_URL` from Supabase (or another provider) as an environment variable

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/triage` | Run triage on patient data |
| GET | `/assessments` | List past assessments |
| GET | `/assessments/{id}` | Get one assessment |
| POST | `/assessments/{id}/override` | Clinician override |
| POST | `/assessments/{id}/outcome` | Record outcome |
| GET | `/dashboard` | Aggregate metrics |

## Disclaimer

This is a **decision-support prototype** for educational and demo purposes.
It is not a substitute for clinical judgment or a real triage system.
