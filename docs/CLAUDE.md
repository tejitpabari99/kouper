# CLAUDE.md — Kouper Backend

Project-level guidance for the Kouper care coordinator backend.

## Data Conventions

When inventing data to fill gaps (patient records, phone numbers, emails, provider info, etc.), add entries to `data-changes.md` in the project root.

## Project Structure

- `backend/` — FastAPI application (routes, models, logic, LLM integration)
- `frontend/` — SvelteKit frontend
- `MLChallenge/` — Flask-based patient data API (challenge scaffold)
- `data-changes.md` — log of all invented/assumed data values
