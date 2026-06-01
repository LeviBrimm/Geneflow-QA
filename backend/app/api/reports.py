from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.variant import VariantQuery
from app.services.report_generator import generate_html_report
from app.services.similarity import similar_variants

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{query_id}")
def report(query_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Response:
    query = db.scalar(
        select(VariantQuery)
        .options(selectinload(VariantQuery.variant), selectinload(VariantQuery.explanation))
        .where(VariantQuery.id == query_id)
        .where(VariantQuery.user_id == current_user.id)
    )
    if not query:
        raise HTTPException(status_code=404, detail="Query not found.")
    similar = similar_variants(db, query.variant.id) if query.variant else []
    return Response(content=generate_html_report(query, similar), media_type="text/html")
