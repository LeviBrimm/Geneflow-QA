from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import AnalyzeRequest, AnalyzeResponse, QuerySummaryResponse, VariantResultResponse
from app.db.database import get_db
from app.jobs.queue import enqueue_analysis_job
from app.models.user import User
from app.services.analysis_service import (
    InvalidVariantInputError,
    QueryNotFoundError,
    VariantReferenceNotFoundError,
    get_query_result,
    list_query_history,
    submit_variant_analysis,
)

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
        submission = submit_variant_analysis(db, current_user, payload.raw_input, enqueue_analysis_job)
    except InvalidVariantInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VariantReferenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnalyzeResponse(query_id=submission.query_id, job_id=submission.job_id, status=submission.status)


@router.get(
    "/history",
    response_model=list[QuerySummaryResponse],
    responses={401: {"description": "Missing or invalid bearer token."}},
)
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    return list_query_history(db, current_user)


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
    try:
        return get_query_result(db, current_user, query_id)
    except QueryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
