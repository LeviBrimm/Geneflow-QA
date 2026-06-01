# GeneFlow QA Platform

GeneFlow QA Platform is a full-stack genomic variant interpretation demo built to showcase backend engineering, SDET automation, async processing, API design, and production-style reliability.

The app uses public/sample-safe reference records only. It is educational software and does not provide medical advice.

## Features

- FastAPI backend with typed routes for auth, analysis jobs, history, similar variants, reports, and health checks.
- React + TypeScript frontend with login/register, variant submission, status polling, result detail, gene visualization, history, and HTML reports.
- PostgreSQL-first data model with users, genes, variants, variant queries, analysis jobs, explanations, and vector-like embeddings.
- Deterministic mock AI explanation service by default, with an explicit seam for real LLM integration.
- Unit, integration, failure-path, and Playwright E2E test scaffolding.
- Docker Compose stack with PostgreSQL, Redis, backend, and frontend.
- GitHub Actions workflow for backend tests and frontend build.

## Architecture

```text
React/Vite UI
  -> FastAPI REST API
    -> PostgreSQL reference data and query history
    -> Background analysis task
      -> parser -> reference lookup -> AI explanation -> similarity -> report
```

Redis is included in Docker Compose to match the production queue direction. The MVP uses FastAPI background tasks so the project stays simple to run locally; the job service is isolated so Celery/RQ can replace it later.

## API Surface

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/variants/analyze`
- `GET /api/variants/{query_id}`
- `GET /api/variants/history`
- `GET /api/jobs/{job_id}`
- `GET /api/similar/{variant_id}`
- `GET /api/reports/{query_id}`
- `GET /api/health`

## Local Setup

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/api/health`

Example variants:

- `BRCA1 c.5266dupC`
- `TP53 p.R175H`
- `CFTR ΔF508`

## Backend Tests

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Tests use SQLite in memory for speed while the application default remains PostgreSQL.

## QA Strategy

The project is intentionally framed as an SDET showcase. See [docs/test-strategy.md](docs/test-strategy.md) for the automation layers, risk areas, current coverage, and manual smoke checklist.

## Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
```

Run E2E tests after the backend is running:

```bash
cd frontend
npm run test:e2e
```

## Portfolio Positioning

Resume wording:

> Built GeneFlow, a full-stack genomic variant analysis platform using FastAPI, React, PostgreSQL, async job processing, AI-generated explanations, Playwright E2E testing, integration tests, Docker, and CI/CD.

## Deferred Enhancements

- Real LLM provider integration.
- pgvector-backed similarity queries.
- Celery/RQ worker using Redis.
- PDF export.
- OAuth.
- Cloud deployment and CloudWatch/OpenTelemetry metrics.
