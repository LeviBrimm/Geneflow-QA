from sqlalchemy import select

from app.db.database import SessionLocal
from app.jobs.analysis import run_analysis_job
from app.models.gene import Gene
from app.models.variant import AnalysisJob, VariantQuery
from app.services.reference_data import lookup_variant
from app.services.parser import parse_variant


def test_worker_job_persists_failure_when_reference_is_missing(client, auth_headers):
    register = client.post(
        "/api/auth/register",
        json={"email": "failure@example.com", "password": "password123"},
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        gene = db.scalar(select(Gene).where(Gene.symbol == "BRCA1"))
        query = VariantQuery(
            user_id=2,
            variant_id=None,
            raw_input="BRCA1 c.5266dupC",
            parsed_gene="BRCA1",
            parsed_variant="c.5266dupC",
            status="queued",
        )
        db.add(query)
        db.flush()
        job = AnalysisJob(id="forced-failure", query_id=query.id, status="queued")
        db.add(job)
        db.commit()
        assert gene is not None

        run_analysis_job(job.id)
        db.refresh(job)
        db.refresh(query)

        assert job.status == "failed"
        assert query.status == "failed"
        assert "Variant reference data was not found" in job.error_message
    finally:
        db.close()

    response = client.get("/api/jobs/forced-failure", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_reference_lookup_returns_seeded_variant(client):
    db = SessionLocal()
    try:
        variant = lookup_variant(db, parse_variant("TP53 p.R175H"))
        assert variant is not None
        assert variant.significance == "Pathogenic"
        assert variant.gene.symbol == "TP53"
    finally:
        db.close()
