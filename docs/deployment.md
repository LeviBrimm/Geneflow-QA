# GeneFlow Deployment Guide

## Target Platform

The first recommended deployment target is Render because GeneFlow maps cleanly to Render services:

- Backend API: Docker web service
- Worker: Docker background worker
- Database: managed PostgreSQL
- Queue: Render Key Value, Redis-compatible
- Frontend: static site built from the Vite app

The repository includes `render.yaml` as a starting blueprint. Some public URL values still need to be filled in after Render assigns service domains.

## Required Environment Variables

Backend API and worker:

| Key | Example | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Render Postgres connection string | The app normalizes `postgresql://` to `postgresql+psycopg://`. |
| `REDIS_URL` | Render Key Value connection string | Shared by API and worker. |
| `AUTH_SECRET` | Generated secret | Must be the same for API and worker. |
| `AI_MODE` | `mock` | Keep `mock` for the first deployment. |
| `OPENAI_API_KEY` | blank for mock mode | Required only when real AI mode is enabled. |
| `EXTERNAL_REFERENCE_MODE` | `mock` | Use `mock` for deterministic deploys, or `live` to call Ensembl REST. |
| `EXTERNAL_REFERENCE_BASE_URL` | `https://rest.ensembl.org` | Base URL for live external reference lookup. |
| `EXTERNAL_REFERENCE_TIMEOUT_SECONDS` | `3` | Timeout for external reference requests. |
| `CORS_ORIGINS` | `https://geneflow-frontend.onrender.com` | Set this after the frontend URL exists. |
| `ANALYSIS_QUEUE_NAME` | `analysis` | Must match API and worker. |
| `ANALYSIS_QUEUE_MODE` | `rq` | Use Redis/RQ in deployed environments. |

Frontend:

| Key | Example | Notes |
| --- | --- | --- |
| `VITE_API_BASE` | `https://geneflow-api.onrender.com` | Must be the public backend URL because browser requests cannot use Render private hostnames. |

## Render Deployment Steps

1. Merge CI-gated changes into `main`.
2. In Render, create a Blueprint from this repository.
3. Confirm the blueprint creates:
   - `geneflow-api`
   - `geneflow-worker`
   - `geneflow-frontend`
   - `geneflow-db`
   - `geneflow-redis`
4. Let the first backend deploy run migrations. The backend Docker command runs `alembic upgrade head` before starting Uvicorn.
5. Set `VITE_API_BASE` on the static frontend to the public backend URL.
6. Set `CORS_ORIGINS` on the backend to the public frontend URL.
7. Redeploy the frontend and backend after setting those URL values.
8. Run the deployed smoke test:

```bash
BASE_URL=https://geneflow-api.onrender.com bash scripts/deployed-smoke.sh
```

## Post-Deploy Checks

- Open the backend health endpoint: `/api/health`.
- Open the frontend URL and register a test account.
- Submit `BRCA1 c.5266dupC`.
- Confirm the job reaches `completed`.
- Confirm the result includes an external reference section. In mock mode it should show `ensembl-mock`.
- Open history and the HTML report.
- Check backend and worker logs for structured request/job fields.

## Rollback Notes

- Use Render's service rollback if a deployment breaks after passing CI.
- Keep database migrations backward-compatible whenever possible.
- If a migration is not backward-compatible, deploy it separately from application code and document the rollback tradeoff.

## Later Improvements

- Add a GitHub Actions job that runs `scripts/deployed-smoke.sh` against the hosted backend after deployment.
- Add a custom domain.
- Move `AI_MODE` from `mock` to a real provider after rate limits, timeouts, and cost controls are documented.
- Move `EXTERNAL_REFERENCE_MODE` from `mock` to `live` after deploy logs and timeout behavior are verified.
