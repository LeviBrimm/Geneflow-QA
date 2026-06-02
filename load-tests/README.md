# Load Tests

This folder contains lightweight k6 checks for the local Docker stack. The goal is not to benchmark maximum throughput yet; it is to catch obvious performance or reliability problems in the API, Redis/RQ worker flow, and job polling path.

## Prerequisites

- k6 installed locally.
- GeneFlow running with Docker:

```bash
docker compose up --build
```

The default target is `http://localhost:8001`.

## Run

```bash
k6 run load-tests/geneflow-smoke.js
```

If k6 is not installed locally, run it through Docker:

```bash
docker run --rm \
  -e BASE_URL=http://host.docker.internal:8001 \
  -v "$PWD/load-tests:/scripts" \
  grafana/k6:0.55.0 run /scripts/geneflow-smoke.js
```

Useful overrides:

```bash
BASE_URL=http://localhost:8001 VUS=5 DURATION=1m k6 run load-tests/geneflow-smoke.js
```

```bash
VARIANT_INPUT="TP53 p.R175H" JOB_TIMEOUT_SECONDS=20 k6 run load-tests/geneflow-smoke.js
```

## What It Covers

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/variants/analyze`
- `GET /api/jobs/{job_id}`

The script verifies that jobs are accepted, processed by the worker, and eventually reach `completed`.
