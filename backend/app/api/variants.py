import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.api.schemas import AnalyzeRequest, AnalyzeResponse, QuerySummaryResponse, VariantResultResponse
from app.db.database import get_db
from app.jobs.queue import enqueue_analysis_job
from app.models.user import User
from app.models.variant import AnalysisJob, VariantQuery
from app.services.parser import VariantParseError, parse_variant
from app.services.reference_data import lookup_variant
from app.services.similarity import similar_variants

router = APIRouter(prefix="/api/variants", tags=["variants"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Variant not found in reference data."},
        422: {"description": "Invalid variant input."},
    },
)
def analyze_variant(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    try:
        parsed = parse_variant(payload.raw_input)
    except VariantParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    variant = lookup_variant(db, parsed)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found in reference data.")

    query = VariantQuery(
        user_id=current_user.id,
        variant_id=variant.id,
        raw_input=payload.raw_input,
        parsed_gene=parsed.gene,
        parsed_variant=parsed.notation,
        status="queued",
    )
    db.add(query)
    db.flush()
    job = AnalysisJob(id=uuid.uuid4().hex, query_id=query.id, status="queued")
    db.add(job)
    db.commit()
    enqueue_analysis_job(job.id)
    return AnalyzeResponse(query_id=query.id, job_id=job.id, status=job.status)


@router.get(
    "/history",
    response_model=list[QuerySummaryResponse],
    responses={401: {"description": "Missing or invalid bearer token."}},
)
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    queries = db.scalars(
        select(VariantQuery)
        .where(VariantQuery.user_id == current_user.id)
        .order_by(VariantQuery.created_at.desc())
    ).all()
    return [_query_summary(query) for query in queries]


@router.get(
    "/{query_id}",
    response_model=VariantResultResponse,
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Query not found."},
    },
)
def get_variant_result(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    query = db.scalar(
        select(VariantQuery)
        .options(
            selectinload(VariantQuery.variant),
            selectinload(VariantQuery.explanation),
            selectinload(VariantQuery.job),
        )
        .where(VariantQuery.id == query_id)
        .where(VariantQuery.user_id == current_user.id)
    )
    if not query:
        raise HTTPException(status_code=404, detail="Query not found.")
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


def _query_summary(query: VariantQuery) -> dict:
    return {
        "query_id": query.id,
        "raw_input": query.raw_input,
        "status": query.status,
        "created_at": query.created_at.isoformat() if isinstance(query.created_at, datetime) else query.created_at,
        "job_id": query.job.id if query.job else None,
    }
