import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.models.variant import AnalysisJob, Explanation, VariantQuery
from app.services.ai_explainer import generate_explanation
from app.services.parser import VariantParseError, parse_variant
from app.services.reference_data import lookup_variant
from app.services.similarity import similar_variants


class EnqueueAnalysisJob(Protocol):
    def __call__(self, job_id: str) -> None: ...


class AnalysisServiceError(Exception):
    pass


class InvalidVariantInputError(AnalysisServiceError):
    pass


class VariantReferenceNotFoundError(AnalysisServiceError):
    pass


class QueryNotFoundError(AnalysisServiceError):
    pass


@dataclass(frozen=True)
class AnalysisSubmission:
    query_id: int
    job_id: str
    status: str


def submit_variant_analysis(
    db: Session,
    user: User,
    raw_input: str,
    enqueue_job: EnqueueAnalysisJob,
) -> AnalysisSubmission:
    try:
        parsed = parse_variant(raw_input)
    except VariantParseError as exc:
        raise InvalidVariantInputError(str(exc)) from exc

    variant = lookup_variant(db, parsed)
    if not variant:
        raise VariantReferenceNotFoundError("Variant not found in reference data.")

    query = VariantQuery(
        user_id=user.id,
        variant_id=variant.id,
        raw_input=raw_input,
        parsed_gene=parsed.gene,
        parsed_variant=parsed.notation,
        status="queued",
    )
    db.add(query)
    db.flush()
    job = AnalysisJob(id=uuid.uuid4().hex, query_id=query.id, status="queued")
    db.add(job)
    db.commit()

    enqueue_job(job.id)
    return AnalysisSubmission(query_id=query.id, job_id=job.id, status=job.status)


def list_query_history(db: Session, user: User) -> list[dict]:
    queries = db.scalars(
        select(VariantQuery).where(VariantQuery.user_id == user.id).order_by(VariantQuery.created_at.desc())
    ).all()
    return [_query_summary(query) for query in queries]


def get_query_result(db: Session, user: User, query_id: int) -> dict:
    query = db.scalar(
        select(VariantQuery)
        .options(
            selectinload(VariantQuery.variant),
            selectinload(VariantQuery.explanation),
            selectinload(VariantQuery.job),
        )
        .where(VariantQuery.id == query_id)
        .where(VariantQuery.user_id == user.id)
    )
    if not query:
        raise QueryNotFoundError("Query not found.")

    variant = query.variant
    gene = variant.gene if variant else None
    return {
        **_query_summary(query),
        "parsed": {
            "gene": query.parsed_gene,
            "notation": query.parsed_variant,
            "variant_type": variant.variant_type if variant else "unknown",
            "is_valid": True,
        },
        "reference": {
            "gene_full_name": gene.full_name if gene else None,
            "gene_description": gene.description if gene else None,
            "rsid": variant.rsid if variant else None,
            "significance": variant.significance if variant else None,
            "condition": variant.condition if variant else None,
            "allele_frequency": variant.allele_frequency if variant else None,
            "summary": variant.summary if variant else None,
            "position": variant.position if variant else None,
            "domain": variant.domain if variant else None,
        },
        "explanations": {
            "general": query.explanation.general_explanation if query.explanation else None,
            "technical": query.explanation.technical_explanation if query.explanation else None,
            "model_used": query.explanation.model_used if query.explanation else None,
        },
        "similar_variants": similar_variants(db, variant.id) if variant else [],
    }


def start_analysis_job(db: Session, job_id: str) -> AnalysisJob | None:
    job = db.get(AnalysisJob, job_id)
    if not job:
        return None

    job.status = "processing"
    job.started_at = datetime.utcnow()
    job.query.status = "processing"
    db.commit()
    return job


def complete_analysis_job(db: Session, job: AnalysisJob, ai_mode: str) -> None:
    query = db.get(VariantQuery, job.query_id)
    if not query or not query.variant:
        raise RuntimeError("Variant reference data was not found.")

    result = generate_explanation(query.variant.gene, query.variant, ai_mode)
    db.add(
        Explanation(
            query_id=query.id,
            general_explanation=result.general_explanation,
            technical_explanation=result.technical_explanation,
            model_used=result.model_used,
        )
    )
    similar_variants(db, query.variant.id)
    job.status = "completed"
    query.status = "completed"
    job.completed_at = datetime.utcnow()
    db.commit()


def fail_analysis_job(db: Session, job_id: str, error: Exception) -> AnalysisJob | None:
    db.rollback()
    job = db.get(AnalysisJob, job_id)
    if not job:
        return None

    job.status = "failed"
    job.error_message = str(error)
    job.completed_at = datetime.utcnow()
    job.query.status = "failed"
    db.commit()
    return job


def _query_summary(query: VariantQuery) -> dict:
    return {
        "query_id": query.id,
        "raw_input": query.raw_input,
        "status": query.status,
        "created_at": query.created_at.isoformat() if isinstance(query.created_at, datetime) else query.created_at,
        "job_id": query.job.id if query.job else None,
    }
