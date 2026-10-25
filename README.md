# AI Showrunner

> An AI showrunner for serialized fiction — story bible, continuity, and episode generation.

Maintains a living story bible, tracks continuity across episodes, and drafts episodes with the cast and world state kept consistent.

## Features

- Story bible with characters, world, and arcs
- Continuity tracker across episodes
- Episode editor with AI drafts
- Consistency checks against the bible

## Architecture

| Layer | Stack | Path |
|---|---|---|
| Frontend | Astro (file-based routing) | `frontend/` |
| Backend | FastAPI + SQLAlchemy + Pydantic | `backend/` |
| Tests | pytest | `backend/tests/` |

Frontend routes: `bible, continuity, episode-editor`.

## Quick start

Backend (from `backend/`):

```bash
pip install -r requirements.txt
cp .env.example .env        # optional — works with no keys
python3 -m uvicorn app.main:app --port 8001
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev
```

Tests: `python3 -m pytest backend/tests/ -v`

## Deployment

The frontend builds to a static bundle and deploys to GitHub Pages on every
push to `main` (`.github/workflows/deploy.yml`):

**https://adineo-cmd2.github.io/ai-showrunner/**

## Project structure

```
backend/
  app/          FastAPI application
  tests/        pytest suite
frontend/
  src/pages/    Astro routes
```
