# onboarding-workforce

Multi-agent system that reads a GitHub repo and produces a verified onboarding guide + ramp plan.

Status: step 1 — scaffold and data model only. No agent logic, no orchestration, no LLM calls yet.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the intended design.

## Stack

- Python 3.12, FastAPI
- Async SQLAlchemy 2.x + Alembic, Postgres
- pytest, uv, Docker Compose

## Run it

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
uv run pytest
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

## Endpoints

- `POST /runs` — create a `Run` for a repo URL, returns its id.
- `GET /runs/{id}` — run status and its blackboard entries.
