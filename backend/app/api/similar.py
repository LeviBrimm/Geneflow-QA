from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import SimilarVariantResponse
from app.db.database import get_db
from app.models.user import User
from app.models.variant import Variant
from app.services.similarity import similar_variants

router = APIRouter(prefix="/api/similar", tags=["similar"])


@router.get(
    "/{variant_id}",
    response_model=list[SimilarVariantResponse],
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Variant not found."},
    },
)
def similar(variant_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[SimilarVariantResponse]:
    if not db.get(Variant, variant_id):
        raise HTTPException(status_code=404, detail="Variant not found.")
    return [SimilarVariantResponse(**item) for item in similar_variants(db, variant_id)]
