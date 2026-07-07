# GeneFlow Architecture Notes

## Request Flow

1. User registers or logs in.
2. User submits a public variant string.
3. Route delegates submission to the analysis service.
4. Analysis service parses and validates the input.
5. Analysis service matches the variant against seeded public/sample-safe reference data or resolves a live Ensembl VEP-backed reference when enabled.
6. Analysis service stores a `variant_queries` row and an `analysis_jobs` row.
7. Analysis service enqueues the analysis job in Redis through RQ.
8. Worker process picks up the queued job.
9. Worker delegates status transitions, external reference enrichment, variant evidence snapshots, guarded explanations, similarity work, and failure persistence back to the analysis service.
10. External enrichment stores an `external_reference_snapshots` row so live API evidence, mock evidence, and lookup failures are auditable.
11. Variant evidence stores normalized HGVS, transcript IDs, consequence terms, impact, clinical significance, and source links in `variant_evidence_snapshots`.
12. Frontend polls `/api/jobs/{job_id}` and then loads `/api/variants/{query_id}`.
13. User can view history and open an HTML report.

## Reliability Surfaces

- Alembic applies database schema migrations before the Docker API process starts.
- Every API response includes `X-Request-ID`; the API preserves caller-provided IDs for traceability.
- API access logs and worker job logs use structured fields for request IDs, job IDs, status, and duration.
- Invalid parser input returns `422`.
- Unknown reference variants return `404` when no seeded or live Ensembl reference can be resolved.
- External reference lookup failures are captured on the query result and do not fail an otherwise valid analysis.
- Variant evidence is persisted separately from AI explanations so source evidence remains auditable.
- Variant records carry an explicit source marker so seeded demo records and live Ensembl VEP records remain distinguishable.
- Worker failures are persisted in `analysis_jobs.error_message`.
- Routes stay thin while service-level tests cover persistence and dependency failure behavior.
- The frontend surfaces queued, processing, completed, and failed states.

## Testing Strategy

- Unit tests cover parser, prompt building, external reference mapping, variant evidence normalization, external API fallback, and similarity math.
- Integration tests cover auth, service orchestration, job creation, worker execution, result retrieval, history, report generation, invalid input, unknown variants, external reference snapshots, variant evidence snapshots, and dependency failures.
- Playwright test covers the browser registration and analysis submission workflow.
