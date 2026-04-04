# Kouper — Care Coordinator Assistant

LLM-powered tool that helps nurses book appointments and manage patient coordination.

## Quick Start

Three services, each in its own terminal:

**1. MLChallenge API** (patient data, port 5000)
```bash
cd MLChallenge/api
python flask-app.py
```

**2. Backend** (FastAPI, port 8000)
```bash
cd backend
pip install -r requirements.txt      # first time only
uvicorn app.server:app --reload
```

**3. Frontend** (SvelteKit, port 5173)
```bash
cd frontend
npm install                           # first time only
npm run dev
```

Open http://localhost:5173.

## Environment

Copy `.env.example` to `.env` (if present) and set `ANTHROPIC_API_KEY`.

## Tests

```bash
cd backend && pytest
```

## Docs (`docs/`)

| File | What it is |
|------|-----------|
| `CONTEXT.md` | Single source of truth — challenge brief, data, rules. **Read this first.** |
| `ARCHITECTURE.md` | System design, data flow, component overview |
| `PLAN.md` | Original project plan |
| `features-plan-v2.md` | Feature plan v2 (audit logging, scheduling, insurance) |
| `advanced-tier-plan.md` | Advanced tier implementation plan |
| `CLAUDE.md` | Dev conventions (data invention rules, project structure) |
| `data-changes.md` | Log of all invented/assumed data values |

## Structure

```
backend/      FastAPI app — routes, models, LLM integration
frontend/     SvelteKit UI
MLChallenge/  Flask patient data API (challenge scaffold)
docs/         All documentation
.kouper.db    SQLite database (auto-created on first run)
```
