# AI Multi-Agent Platform

AI Multi-Agent Platform is a knowledge and automation system for ingesting documents, building a searchable RAG knowledge base, coordinating specialist agents, and running workflow-driven analysis and reporting tasks.

The repository contains a FastAPI backend, a Vue 3 frontend, local infrastructure definitions, and detailed design documents for architecture, security, APIs, data, agents, workflows, eventing, and roadmap planning.

## Project Status

Current implementation highlights:

- Clean / hexagonal backend architecture with module boundaries.
- FastAPI application with `/api/v1` routers and OpenAPI docs.
- PostgreSQL-backed persistence with Alembic migrations.
- Authentication with username/password registration, login, JWT tokens, and user listing.
- Document upload to MinIO, parsing, OCR fallback, metadata extraction, and presigned download URLs.
- Knowledge indexing with structure-aware chunking, offline hashing embeddings, Qdrant vector storage, and semantic search.
- Agent planning and routing scaffold.
- Workflow execution scaffold with workflow instances and approval endpoint.
- Vue 3 marketing UI with Home, Features, About pages, dark mode, Tailwind CSS, Element Plus, and Vue Router.

Several modules are currently scaffolded with CRUD-style boundaries but still need business logic: analysis, reports, memory, notifications, audit, execution, advanced Q&A, production workflow orchestration, and full frontend-to-backend app screens.

## Repository Layout

```text
.
├── backend/                         # FastAPI backend
│   ├── app/
│   │   ├── api/                     # Aggregated API router
│   │   ├── core/                    # Config, database, security, logging, clients
│   │   ├── modules/                 # Feature modules
│   │   └── shared/                  # Shared domain/application/LLM interfaces
│   ├── migrations/                  # Alembic migrations
│   ├── tests/                       # Pytest tests
│   ├── docker-compose.yml           # Local backing services
│   ├── docker-compose.server.yml    # Server port variant
│   └── requirements.txt             # Python dependencies
├── frontend/                        # Vue 3 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── data/
│   │   ├── directives/
│   │   ├── router/
│   │   └── views/
│   └── package.json
├── *_SPECIFICATION.md               # System, API, agent, workflow, and event specs
├── *_ARCHITECTURE.md                # High-level and security architecture
├── TECH_STACK_DECISION.md
├── DATABASE_DESIGN.md
├── LLM_AND_RAG_STRATEGY.md
├── PROJECT_ROADMAP.md
└── PROJECT_CHECKLIST.md
```

## Backend Architecture

Backend features live in `backend/app/modules/<module>/` and follow four layers:

```text
domain/          # Entities and repository/provider ports
application/     # Use-case services and command DTOs
infrastructure/  # SQLAlchemy models, repositories, adapters, external clients
presentation/    # FastAPI routers, schemas, and dependency wiring
```

Shared infrastructure lives in `backend/app/core/`:

- `config.py` - environment-driven settings.
- `database.py` - async SQLAlchemy session setup.
- `security.py` - bcrypt and JWT helpers.
- `event_bus.py` - Kafka event bus abstraction.
- `clients.py` - lazy clients for Redis, Qdrant, and MinIO.
- `registry.py` - imports ORM models so Alembic and metadata see all tables.
- `logging.py` - structured logging setup.

## Backend Modules

The backend currently includes these modules:

- `auth` - register, login, users.
- `documents` - document records, upload, parsing, OCR, metadata, download URLs.
- `knowledge` - chunking, embeddings, Qdrant indexing, vector search.
- `qa` - Q&A conversation scaffold.
- `analysis` - analysis job scaffold.
- `reports` - report scaffold.
- `agents` - agent registry, task planning, routing, agent scaffold.
- `workflows` - workflow definitions, workflow runs, instances, approval.
- `memory` - memory item scaffold.
- `notifications` - notification scaffold.
- `audit` - audit log scaffold.
- `execution` - execution run scaffold.
- `events` - system event scaffold.

All module routers are mounted under `/api/v1`.

## API Overview

System endpoints:

- `GET /`
- `GET /health`
- `GET /docs`
- `GET /openapi.json`

Main API prefixes:

- `/api/v1/auth`
- `/api/v1/documents`
- `/api/v1/knowledge`
- `/api/v1/qa`
- `/api/v1/analysis`
- `/api/v1/reports`
- `/api/v1/agents`
- `/api/v1/workflows`
- `/api/v1/memory`
- `/api/v1/notifications`
- `/api/v1/audit`
- `/api/v1/execution`
- `/api/v1/events`

Implemented document and knowledge workflows include:

- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/{id}/parse`
- `GET /api/v1/documents/{id}/download-url`
- `POST /api/v1/knowledge/documents/{id}/index`
- `POST /api/v1/knowledge/search`

## Technology Stack

Backend:

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy async
- Alembic
- PostgreSQL 16
- Redis 7
- Qdrant
- MinIO / S3-compatible storage
- Kafka
- Uvicorn
- Pytest

Document and knowledge processing:

- `pypdf`
- `python-docx`
- `openpyxl`
- `pytesseract`
- `pdf2image`
- `Pillow`
- `langdetect`
- Offline hashing embeddings by default

Frontend:

- Vue 3
- TypeScript
- Vite
- Vue Router
- Tailwind CSS v4
- Element Plus
- Element Plus icons

## Prerequisites

Install these before running the full project locally:

- Python 3.11 or newer recommended.
- Node.js and npm.
- Docker and Docker Compose.
- Tesseract OCR and Poppler utilities if OCR features are needed.

For OCR on Ubuntu/Debian:

```bash
sudo apt-get install tesseract-ocr poppler-utils
```

Install language packs for the configured OCR languages as needed. The default backend setting is `tuk+eng+rus`.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Review `.env` and adjust service URLs or secrets if needed. The default local values match `backend/docker-compose.yml`.

Start local infrastructure:

```bash
cd backend
docker compose up -d
```

Apply database migrations:

```bash
alembic upgrade head
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Default URLs:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Default Vite URL:

- `http://localhost:5173/`

Build the frontend:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Local Infrastructure

`backend/docker-compose.yml` starts the backend dependencies:

| Service | Port | Purpose |
| --- | --- | --- |
| PostgreSQL | `5432` | Relational database, `agent_platform` |
| Redis | `6379` | Cache and session support |
| Qdrant REST | `6333` | Vector database API/dashboard |
| Qdrant gRPC | `6334` | Vector database gRPC |
| Kafka | `9092` | Event bus |
| MinIO API | `9000` | S3-compatible object storage |
| MinIO Console | `9001` | Storage web UI |

Useful commands:

```bash
cd backend
docker compose ps
docker compose down
docker compose down -v
```

`docker compose down -v` removes service volumes and deletes local data.

## Server Compose Variant

`backend/docker-compose.server.yml` is a server-oriented variant for host `172.16.6.76`.

Important differences:

- PostgreSQL host port is `5433`.
- Qdrant host ports are `6335` and `6336`.
- Kafka advertises `172.16.6.76:9092`.

Run it with:

```bash
cd backend
docker compose -f docker-compose.server.yml up -d
```

## Configuration

Backend settings are defined in `backend/app/core/config.py` and can be overridden through `backend/.env`.

Common settings:

- `ENVIRONMENT`
- `DEBUG`
- `JWT_SECRET`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `POSTGRES_DSN`
- `REDIS_URL`
- `QDRANT_URL`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `KAFKA_BOOTSTRAP_SERVERS`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `CORS_ORIGINS`

The default LLM provider is configured for Ollama with `gemma4:31b-cloud`. The default embedding provider is offline and does not require an external API.

## Database Migrations

Apply migrations:

```bash
cd backend
alembic upgrade head
```

Create a new migration after changing ORM models:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Tests

Run backend tests:

```bash
cd backend
pytest
```

The smoke tests exercise register/login and module CRUD against an in-memory SQLite database, so they do not require the Docker services.

Run frontend type-check and build:

```bash
cd frontend
npm run build
```

## Documentation

Project planning and design documents:

- `SYSTEM_REQUIREMENTS.md` - functional and non-functional requirements.
- `HIGH_LEVEL_ARCHITECTURE.md` - system architecture.
- `TECH_STACK_DECISION.md` - selected stack and rationale.
- `API_SPECIFICATION.md` - API design.
- `DATABASE_DESIGN.md` - schema and data model design.
- `SECURITY_ARCHITECTURE.md` - security model.
- `EVENT_BUS_SPECIFICATION.md` - Kafka/eventing design.
- `AGENT_SPECIFICATIONS.md` - specialist agent roles.
- `WORKFLOW_ENGINE_SPECIFICATION.md` - workflow engine design.
- `LLM_AND_RAG_STRATEGY.md` - model, retrieval, chunking, and RAG strategy.
- `PROJECT_ROADMAP.md` - phased delivery roadmap.
- `PROJECT_CHECKLIST.md` - current progress checklist.

## Development Notes

- Keep backend module dependencies pointing inward: presentation -> application -> domain, with infrastructure implementing domain ports.
- Register new routers in `backend/app/api/router.py`.
- Register new ORM models through `backend/app/core/registry.py` so migrations and metadata include them.
- Keep environment-specific service URLs in `.env`, not in application code.
- Use Alembic migrations for database schema changes.
- Prefer module-local services, repositories, schemas, and dependency providers over cross-module shortcuts.

