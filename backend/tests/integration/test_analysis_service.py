import pytest
from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.models.user import User
from app.models.variant import AnalysisJob, ExternalReferenceSnapshot, VariantQuery
from app.services import analysis_service
from app.services.analysis_service import (
    InvalidVariantInputError,
    VariantReferenceNotFoundError,
    complete_analysis_job,
    fail_analysis_job,
    start_analysis_job,
    submit_variant_analysis,
)
from app.services.external_reference import ExternalReferenceResult


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
