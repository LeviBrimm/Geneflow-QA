from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.variant import AnalysisJob

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    job = db.get(AnalysisJob, job_id)
    if not job or job.query.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job.id,
        "query_id": job.query_id,
        "status": job.status,
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
