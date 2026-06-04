import logging
from datetime import datetime

from app.config.settings import get_settings
from app.db.database import SessionLocal
from app.models.variant import AnalysisJob, Explanation, VariantQuery
from app.services.ai_explainer import generate_explanation
from app.services.similarity import similar_variants

logger = logging.getLogger("app.jobs.analysis")


def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if not job:
            logger.warning("analysis_job_missing", extra={"job_id": job_id})
            return
        logger.info(
            "analysis_job_started",
            extra={"job_id": job.id, "query_id": job.query_id, "status": "processing"},
        )
        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.query.status = "processing"
        db.commit()

        query = db.get(VariantQuery, job.query_id)
        if not query or not query.variant:
            raise RuntimeError("Variant reference data was not found.")

        result = generate_explanation(query.variant.gene, query.variant, get_settings().ai_mode)
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
        logger.info(
            "analysis_job_completed",
            extra={"job_id": job.id, "query_id": query.id, "status": "completed"},
        )
    except Exception as exc:  # noqa: BLE001 - background job must persist failure reason.
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            job.query.status = "failed"
            db.commit()
            logger.exception(
                "analysis_job_failed",
                extra={"job_id": job.id, "query_id": job.query_id, "status": "failed"},
            )
    finally:
        db.close()
