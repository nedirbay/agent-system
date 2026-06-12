# AI Multi-Agent Platform — Backend

FastAPI backend for the AI Multi-Agent Knowledge & Automation Platform, built
with a **clean / hexagonal architecture**. Aligns with the repository specs
(`SYSTEM_REQUIREMENTS.md`, `HIGH_LEVEL_ARCHITECTURE.md`, `DATABASE_DESIGN.md`,
`EVENT_BUS_SPECIFICATION.md`, `TECH_STACK_DECISION.md`).

## Architecture

Every feature lives in `app/modules/<module>/` and is split into four layers,
with dependencies pointing **inward** (presentation → application → domain;
infrastructure implements domain ports):

```
app/modules/<module>/
├── domain/              # entities + repository ports (no framework deps)
│   ├── entities.py
│   └── repositories.py
├── application/         # use-case services + commands (DTOs)
│   ├── commands.py
│   └── services.py
├── infrastructure/      # SQLAlchemy ORM models + repository adapters
│   ├── models.py
│   └── repositories.py
└── presentation/        # FastAPI router, pydantic schemas, DI wiring
    ├── router.py
    ├── schemas.py
    └── dependencies.py
```

**Cross-cutting infrastructure** lives in `app/core/`: configuration,
async database/session, security (bcrypt + JWT), structured logging, the
Event Bus publisher port (Kafka), and lazy clients for Redis / Qdrant / MinIO.

### Modules (13)

`auth` · `documents` · `knowledge` · `qa` · `analysis` · `reports` · `agents` ·
`workflows` · `memory` · `notifications` · `audit` · `execution` · `events`

All routers are mounted by `app/api/router.py` under the `/api/v1` prefix, and
all ORM models are registered on `Base.metadata` via `app/core/registry.py`.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # adjust as needed
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs:    http://localhost:8000/docs
- Health:      http://localhost:8000/health
- OpenAPI:     http://localhost:8000/openapi.json

## Database migrations (Alembic)

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## Tests

```bash
pytest
```

`tests/test_smoke.py` runs the full chain (register / login / module CRUD)
against an in-memory SQLite database, with no external services required.
