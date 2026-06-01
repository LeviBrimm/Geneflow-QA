def test_auth_analyze_job_result_report_flow(client, auth_headers):
    response = client.post(
        "/api/variants/analyze",
        json={"raw_input": "BRCA1 c.5266dupC"},
        headers=auth_headers,
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"

    job = client.get(f"/api/jobs/{payload['job_id']}", headers=auth_headers)
    assert job.status_code == 200
    assert job.json()["status"] in {"completed", "processing", "queued"}

    result = client.get(f"/api/variants/{payload['query_id']}", headers=auth_headers)
    assert result.status_code == 200
    result_payload = result.json()
    assert result_payload["parsed"]["gene"] == "BRCA1"
    assert result_payload["reference"]["significance"] == "Pathogenic"

    history = client.get("/api/variants/history", headers=auth_headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    report = client.get(f"/api/reports/{payload['query_id']}", headers=auth_headers)
    assert report.status_code == 200
    assert "GeneFlow Variant Report" in report.text


def test_protected_routes_require_authentication(client):
    assert client.get("/api/variants/history").status_code == 401
    assert client.get("/api/jobs/not-real").status_code == 401
    assert client.get("/api/reports/1").status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get("/api/variants/history", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_duplicate_registration_returns_409(client):
    payload = {"email": "duplicate@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


def test_login_rejects_bad_password(client):
    payload = {"email": "login@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/login", json={**payload, "password": "wrongpass"})
    assert response.status_code == 401


def test_invalid_variant_returns_422(client, auth_headers):
    response = client.post("/api/variants/analyze", json={"raw_input": "bad"}, headers=auth_headers)
    assert response.status_code == 422


def test_unknown_variant_returns_404(client, auth_headers):
    response = client.post("/api/variants/analyze", json={"raw_input": "BRCA1 c.9999dupC"}, headers=auth_headers)
    assert response.status_code == 404


def test_missing_job_and_query_return_404(client, auth_headers):
    assert client.get("/api/jobs/not-real", headers=auth_headers).status_code == 404
    assert client.get("/api/variants/999", headers=auth_headers).status_code == 404
    assert client.get("/api/reports/999", headers=auth_headers).status_code == 404
