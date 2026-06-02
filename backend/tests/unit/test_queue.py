from types import SimpleNamespace

import fakeredis

from app.jobs import queue as queue_module


def test_enqueue_analysis_job_adds_rq_job(monkeypatch):
    monkeypatch.setattr(
        queue_module,
        "get_settings",
        lambda: SimpleNamespace(
            analysis_queue_mode="rq",
            analysis_queue_name="analysis",
            redis_url="redis://unused:6379/0",
        ),
    )
    fake_redis = fakeredis.FakeRedis()
    rq_queue = queue_module.get_analysis_queue(connection=fake_redis)

    rq_job_id = queue_module.enqueue_analysis_job("analysis-job-1", queue=rq_queue)

    assert rq_queue.count == 1
    queued_job = rq_queue.fetch_job(rq_job_id)
    assert queued_job is not None
    assert queued_job.args == ("analysis-job-1",)
