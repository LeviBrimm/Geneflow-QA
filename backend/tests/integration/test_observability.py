import logging

from app.observability.middleware import REQUEST_ID_HEADER


class ListLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def capture_logger(name: str) -> ListLogHandler:
    logging.disable(logging.NOTSET)
    handler = ListLogHandler()
    logger = logging.getLogger(name)
    logger.disabled = False
    logger.propagate = True
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return handler


def test_request_id_header_is_generated(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]


def test_request_id_header_preserves_caller_value(client):
    request_id = "test-request-123"
    response = client.get("/api/health", headers={REQUEST_ID_HEADER: request_id})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == request_id


def test_request_log_includes_trace_fields(client):
    handler = capture_logger("app.http")

    response = client.get("/api/health", headers={REQUEST_ID_HEADER: "trace-me"})

    assert response.status_code == 200
    record = next(record for record in handler.records if record.name == "app.http")
    assert record.getMessage() == "request_completed"
    assert record.request_id == "trace-me"
    assert record.method == "GET"
    assert record.path == "/api/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0


def test_analysis_job_logs_lifecycle(client, auth_headers):
    handler = capture_logger("app.jobs.analysis")

    response = client.post(
        "/api/variants/analyze",
        json={"raw_input": "BRCA1 c.5266dupC"},
        headers=auth_headers,
    )

    assert response.status_code == 202
    payload = response.json()
    job_records = [record for record in handler.records if record.name == "app.jobs.analysis"]
    job_messages = {record.getMessage() for record in job_records}

    assert {"analysis_job_started", "analysis_job_completed"}.issubset(job_messages)
    assert all(record.job_id == payload["job_id"] for record in job_records)
    assert all(record.query_id == payload["query_id"] for record in job_records)
