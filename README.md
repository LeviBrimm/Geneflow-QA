# GeneFlow QA Platform

GeneFlow QA Platform is a full-stack web app for exploring public genomic variant reference data. A user enters a variant, the app parses it, checks it against seeded reference records, starts an analysis job, generates guarded explanations, shows similar variants, saves the query, and produces an HTML report.

This is an educational project. It uses public/sample-safe data only, does not use patient data, and does not provide medical advice.

## Features

- FastAPI API for auth, variant analysis, job status, history, similar variants, reports, and health checks.
- Service-layer orchestration for variant submission, analysis jobs, result assembly, and failure persistence.
- React + TypeScript frontend with registration, variant submission, polling, results, history, and report access.
- PostgreSQL data model for users, genes, variants, submitted queries, jobs, explanations, and embeddings.
- Alembic migrations for repeatable schema setup in Docker and local environments.
- Deterministic mock explanation service by default, so the app can run and test without an external AI key.
- Seeded reference examples for `BRCA1`, `TP53`, and `CFTR`.
- Request ID headers and structured logs for API and worker traceability.
- Automated backend tests and Playwright E2E tests.
- Docker Compose setup with PostgreSQL, Redis, backend, worker, and frontend.

## Architecture

```text
React/Vite UI
  -> FastAPI REST API
    -> analysis service layer
      -> PostgreSQL reference data and query history
      -> Redis/RQ analysis queue
      -> Worker process
        -> analysis service layer -> AI explanation -> similarity -> report
```

The API process creates query/job records and enqueues analysis work. A separate worker process listens on Redis, runs the analysis job, and updates the database with completed or failed status.

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

## QA Strategy

Testing is a core part of the project, not an afterthought. See [docs/test-strategy.md](docs/test-strategy.md) for the automation layers, risk areas, current coverage, and manual smoke checklist.

## Verification

Backend tests use SQLite in memory for speed while the application default remains PostgreSQL.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Frontend build:

```bash
cd frontend
npm install
npm run build
```

Playwright E2E tests:

```bash
cd frontend
npm run test:e2e
```

Docker worker smoke test:

```bash
bash scripts/docker-worker-smoke.sh
```

Database migrations:

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe schema change"
```

If an older local Docker database was created before migrations existed, reset the local dev volume once:

```bash
docker compose down -v
docker compose up --build
```

Lightweight k6 load smoke test:

```bash
docker run --rm \
  -e BASE_URL=http://host.docker.internal:8001 \
  -v "$PWD/load-tests:/scripts" \
  grafana/k6:0.55.0 run /scripts/geneflow-smoke.js
```

See [load-tests](load-tests) for k6 options.

## Deferred Enhancements

- Real LLM provider integration.
- pgvector-backed similarity queries.
- PDF export.
- OAuth.
- Cloud deployment and CloudWatch/OpenTelemetry metrics.
