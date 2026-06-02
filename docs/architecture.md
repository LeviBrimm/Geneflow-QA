# GeneFlow Architecture Notes

## Request Flow

1. User registers or logs in.
2. User submits a public variant string.
3. Backend parses and validates the input.
4. Backend matches the variant against seeded public/sample-safe reference data.
5. Backend stores a `variant_queries` row and an `analysis_jobs` row.
6. Backend enqueues the analysis job in Redis through RQ.
7. Worker process picks up the queued job.
8. Worker generates guarded explanations and marks the job completed or failed.
9. Frontend polls `/api/jobs/{job_id}` and then loads `/api/variants/{query_id}`.
10. User can view history and open an HTML report.

## Reliability Surfaces

- Invalid parser input returns `422`.
- Unknown reference variants return `404`.
- Worker failures are persisted in `analysis_jobs.error_message`.
- The frontend surfaces queued, processing, completed, and failed states.

## Testing Strategy

- Unit tests cover parser, prompt building, and similarity math.
- Integration tests cover auth, job creation, worker execution, result retrieval, history, report generation, invalid input, and unknown variants.
- Playwright test covers the browser registration and analysis submission workflow.
