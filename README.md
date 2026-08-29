# UniFlow AI

Minimal scaffold for the UniFlow AI project (MVP).

See `CLAUDE.md` for full architecture and requirements.

Quick start (development):

1. Copy `.env.example` to `.env` and fill values.
2. Start a Postgres instance (e.g., via Docker Compose):

```bash
docker compose up -d
```

3. Install dependencies and run the backend:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Next steps:
- Implement database models, API routes, and agents.
- Add frontend scaffold and CI.
