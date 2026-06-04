# GeneFlow QA Test Strategy

## Goal

GeneFlow treats the application as a system under test. The SDET value is the layered automation around parser correctness, API contracts, async job behavior, auth boundaries, failure handling, and browser workflows.

## Test Layers

- Unit tests cover deterministic business logic: parser validation, AI prompt guardrails, and similarity math.
- Contract tests inspect FastAPI's generated OpenAPI schema for required endpoints, response codes, auth parameters, and typed request/response models.
- Service tests exercise analysis orchestration without HTTP: query/job creation, enqueue boundaries, rejected submissions, and dependency failures.
- Integration tests exercise FastAPI routes with an in-memory database: auth, protected routes, variant submission, job polling, history, reports, invalid input, missing records, and persisted job failures.
- Migration tests apply Alembic revisions against a clean database and verify the expected schema is created.
- E2E tests use Playwright with mocked API responses so UI workflows can run consistently in CI without external services.
- Load tests use k6 against the Docker stack to exercise health, auth, analysis submission, and job polling under light concurrent traffic.
- Docker smoke tests verify the live backend, Redis/RQ worker, database persistence, and result retrieval path.
- CI runs backend tests, frontend build, and Playwright E2E checks on every push and pull request.

## High-Risk Areas

- Variant parsing: malformed biological notation should fail clearly without creating database records.
- Auth boundaries: protected history, report, and job routes must reject missing or invalid tokens.
- Async jobs: queued, processing, completed, and failed states must be visible and persisted.
- AI explanations: generated text must include educational-only guardrails and avoid medical advice.
- Reports: report output must be tied to the requesting user and contain the same stored result data.

## Current Automated Coverage

- Parser accepts supported examples, normalizes whitespace and delta symbols, and rejects malformed or unsupported notation.
- Auth covers registration, duplicate registration, login failure, missing token, and invalid token.
- Analysis service tests verify valid submissions create query/job rows and enqueue once, invalid or unknown variants create no query rows, and AI dependency failures can be persisted.
- API contract tests cover required paths, HTTP methods, documented response codes, auth parameters, and typed schemas for analysis, history, result, job, similar-variant, and health responses.
- API flow covers analysis creation, job lookup, result retrieval, history, report generation, invalid variant, unknown variant, and missing resources.
- Migration coverage verifies `alembic upgrade head` creates the initial schema and records the expected revision.
- Queue tests verify analysis jobs are enqueued through RQ.
- Failure tests verify a worker job persists `failed` status and error message when reference data is missing.
- Playwright covers registration, analysis submission, processing feedback, result rendering, history navigation, and validation error display.
- k6 smoke load tests cover health, auth, analysis submission, and job polling against the live Docker stack.
- Docker worker smoke tests submit a real job and verify it reaches `completed` with persisted explanations.

## Test Data

Seeded public/sample-safe records:

- `BRCA1 c.5266dupC`
- `TP53 p.R175H`
- `CFTR ΔF508`

The seeded data is intentionally small so assertions stay stable and understandable during interviews.

## Manual Smoke Checklist

- `docker compose up --build`
- Open `http://localhost:5173`
- Register with a test email and password.
- Submit `BRCA1 c.5266dupC`.
- Confirm status transitions to completed and the result page loads.
- Open history and confirm the query appears.
- Open the HTML report and confirm the disclaimer is present.

## Next Automation Improvements

- Add deployment smoke tests after the app has a hosted environment.
