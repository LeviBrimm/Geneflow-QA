import logging

from app.config.settings import get_settings
from app.db.database import SessionLocal
from app.services.analysis_service import complete_analysis_job, fail_analysis_job, start_analysis_job

logger = logging.getLogger("app.jobs.analysis")


def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = start_analysis_job(db, job_id)
        if not job:
            logger.warning("analysis_job_missing", extra={"job_id": job_id})
            return
        logger.info(
            "analysis_job_started",
            extra={"job_id": job.id, "query_id": job.query_id, "status": "processing"},
        )

        complete_analysis_job(db, job, get_settings().ai_mode)
        logger.info(
            "analysis_job_completed",
            extra={"job_id": job.id, "query_id": job.query_id, "status": "completed"},
        )
    except Exception as exc:  # noqa: BLE001 - background job must persist failure reason.
        job = fail_analysis_job(db, job_id, exc)
        if job:
            logger.exception(
                "analysis_job_failed",
                extra={"job_id": job.id, "query_id": job.query_id, "status": "failed"},
            )
    finally:
        db.close()
