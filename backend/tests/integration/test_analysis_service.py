from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.models.user import User
from app.models.variant import AnalysisJob, ExternalReferenceSnapshot, Variant, VariantEvidenceSnapshot, VariantQuery
from app.services import analysis_service
from app.services import reference_data
from app.services.analysis_service import (
    InvalidVariantInputError,
    VariantReferenceNotFoundError,
    complete_analysis_job,
    fail_analysis_job,
    start_analysis_job,
    submit_variant_analysis,
)
from app.services.external_reference import ExternalReferenceResult
from app.services.external_reference import EnsemblVariantReference


def test_submit_variant_analysis_creates_query_job_and_enqueues(client):
    user = _registered_user(client, "service-success@example.com")
    enqueued_job_ids: list[str] = []

    db = SessionLocal()
    try:
        submission = submit_variant_analysis(
            db,
            user,
            "BRCA1 c.5266dupC",
            enqueued_job_ids.append,
        )
        query = db.get(VariantQuery, submission.query_id)
        job = db.get(AnalysisJob, submission.job_id)

        assert query is not None
        assert query.raw_input == "BRCA1 c.5266dupC"
        assert query.status == "queued"
        assert job is not None
        assert job.status == "queued"
        assert enqueued_job_ids == [submission.job_id]
    finally:
        db.close()


def test_invalid_variant_submission_does_not_create_rows(client):
    user = _registered_user(client, "service-invalid@example.com")

    db = SessionLocal()
    try:
        before = _query_count(db)

        with pytest.raises(InvalidVariantInputError):
            submit_variant_analysis(db, user, "bad", lambda _: None)

        assert _query_count(db) == before
    finally:
        db.close()


def test_unknown_variant_submission_does_not_create_rows(client):
    user = _registered_user(client, "service-unknown@example.com")

    db = SessionLocal()
    try:
        before = _query_count(db)

        with pytest.raises(VariantReferenceNotFoundError):
            submit_variant_analysis(db, user, "BRCA1 c.9999dupC", lambda _: None)

        assert _query_count(db) == before
    finally:
        db.close()


def test_live_reference_submission_creates_dynamic_variant(client, monkeypatch):
    user = _registered_user(client, "service-live-reference@example.com")
    enqueued_job_ids: list[str] = []
    settings = SimpleNamespace(
        external_reference_mode="live",
        external_reference_base_url="https://rest.ensembl.org",
        external_reference_timeout_seconds=3.0,
    )
    monkeypatch.setattr(reference_data, "get_settings", lambda: settings)
    monkeypatch.setattr(
        reference_data,
        "fetch_ensembl_variant_reference",
        lambda *_args, **_kwargs: EnsemblVariantReference(
            gene_symbol="BRAF",
            gene_full_name="B-Raf proto-oncogene, serine/threonine kinase",
            gene_description="BRAF live Ensembl record",
            hgvs="p.V600E",
            variant_type="missense",
            significance="pathogenic",
            condition="Not provided by Ensembl VEP",
            allele_frequency=0.0001,
            summary="Live Ensembl VEP annotation for BRAF p.V600E.",
            position=140753336,
            domain=None,
            transcript_id="ENST00000646891",
            transcript_hgvs="ENST00000646891.2:c.1799T>A",
            protein_hgvs="ENSP00000493543.1:p.Val600Glu",
            rsid="rs113488022",
            consequence_terms=["missense_variant"],
            impact="MODERATE",
            raw_payload={},
        ),
    )

    db = SessionLocal()
    try:
        submission = submit_variant_analysis(db, user, "BRAF p.V600E", enqueued_job_ids.append)
        query = db.get(VariantQuery, submission.query_id)
        variant = db.scalar(select(Variant).where(Variant.hgvs == "p.V600E"))

        assert query is not None
        assert query.parsed_gene == "BRAF"
        assert variant is not None
        assert query.variant_id == variant.id
        assert variant.gene.symbol == "BRAF"
        assert variant.reference_source == "ensembl_vep"
        assert variant.rsid == "rs113488022"
        assert enqueued_job_ids == [submission.job_id]
    finally:
        db.close()


def test_ai_dependency_failure_can_be_persisted(client, monkeypatch):
    user = _registered_user(client, "service-ai-failure@example.com")

    db = SessionLocal()
    try:
        submission = submit_variant_analysis(db, user, "TP53 p.R175H", lambda _: None)
        job = start_analysis_job(db, submission.job_id)
        assert job is not None

        def fail_explanation(*_):
            raise TimeoutError("AI service timed out")

        monkeypatch.setattr(analysis_service, "generate_explanation", fail_explanation)
        with pytest.raises(TimeoutError) as exc_info:
            complete_analysis_job(db, job, ai_mode="mock")

        failed_job = fail_analysis_job(db, submission.job_id, exc_info.value)
        assert failed_job is not None
        query = db.get(VariantQuery, submission.query_id)

        assert failed_job.status == "failed"
        assert failed_job.error_message == "AI service timed out"
        assert query is not None
        assert query.status == "failed"
    finally:
        db.close()


def test_completed_analysis_persists_external_reference_snapshot(client, monkeypatch):
    user = _registered_user(client, "service-external-success@example.com")

    db = SessionLocal()
    try:
        submission = submit_variant_analysis(db, user, "BRCA1 c.5266dupC", lambda _: None)
        job = start_analysis_job(db, submission.job_id)
        assert job is not None

        monkeypatch.setattr(
            analysis_service,
            "fetch_external_reference",
            lambda *_args: ExternalReferenceResult(
                source="ensembl",
                lookup_status="success",
                external_id="ENSG00000012048",
                external_url="https://www.ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000012048",
                gene_biotype="protein_coding",
                location="17:43044295-43170245",
                summary="BRCA1 DNA repair associated",
            ),
        )

        complete_analysis_job(db, job, ai_mode="mock")

        snapshot = db.scalar(
            select(ExternalReferenceSnapshot).where(ExternalReferenceSnapshot.query_id == submission.query_id)
        )
        query = db.get(VariantQuery, submission.query_id)

        assert snapshot is not None
        assert snapshot.lookup_status == "success"
        assert snapshot.external_id == "ENSG00000012048"
        assert query is not None
        assert query.status == "completed"
    finally:
        db.close()


def test_completed_analysis_persists_variant_evidence_snapshot(client):
    user = _registered_user(client, "service-variant-evidence@example.com")

    db = SessionLocal()
    try:
        submission = submit_variant_analysis(db, user, "TP53 p.R175H", lambda _: None)
        job = start_analysis_job(db, submission.job_id)
        assert job is not None

        complete_analysis_job(db, job, ai_mode="mock")

        snapshot = db.scalar(
            select(VariantEvidenceSnapshot).where(VariantEvidenceSnapshot.query_id == submission.query_id)
        )

        assert snapshot is not None
        assert snapshot.source == "seeded-variant-evidence"
        assert snapshot.normalized_hgvs == "NM_000546.6:c.524G>A"
        assert snapshot.impact == "MODERATE"
        assert snapshot.clinical_significance == "Pathogenic"
    finally:
        db.close()


def test_external_reference_failure_is_saved_without_failing_analysis(client, monkeypatch):
    user = _registered_user(client, "service-external-failure@example.com")

    db = SessionLocal()
    try:
        submission = submit_variant_analysis(db, user, "CFTR ΔF508", lambda _: None)
        job = start_analysis_job(db, submission.job_id)
        assert job is not None

        monkeypatch.setattr(
            analysis_service,
            "fetch_external_reference",
            lambda *_args: ExternalReferenceResult(
                source="ensembl",
                lookup_status="failed",
                error_message="lookup timed out",
            ),
        )

        complete_analysis_job(db, job, ai_mode="mock")

        db.refresh(job)
        snapshot = db.scalar(
            select(ExternalReferenceSnapshot).where(ExternalReferenceSnapshot.query_id == submission.query_id)
        )

        assert job.status == "completed"
        assert snapshot is not None
        assert snapshot.lookup_status == "failed"
        assert snapshot.error_message == "lookup timed out"
    finally:
        db.close()


def _registered_user(client, email: str) -> User:
    response = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        db.expunge(user)
        return user
    finally:
        db.close()


def _query_count(db) -> int:
    return db.scalar(select(func.count()).select_from(VariantQuery))
