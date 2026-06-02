from rq import Queue
from redis import Redis

from app.config.settings import get_settings
from app.jobs.analysis import run_analysis_job


def get_redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def get_analysis_queue(connection: Redis | None = None, is_async: bool = True) -> Queue:
    settings = get_settings()
    return Queue(
        settings.analysis_queue_name,
        connection=connection or get_redis_connection(),
        is_async=is_async,
    )


def enqueue_analysis_job(job_id: str, queue: Queue | None = None) -> str:
    settings = get_settings()
    if settings.analysis_queue_mode == "inline":
        run_analysis_job(job_id)
        return f"inline-{job_id}"

    rq_queue = queue or get_analysis_queue()
    rq_job = rq_queue.enqueue(
        "app.jobs.analysis.run_analysis_job",
        job_id,
        job_timeout=300,
        result_ttl=600,
        failure_ttl=3600,
    )
    return rq_job.id
