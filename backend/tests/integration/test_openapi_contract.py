REQUIRED_OPERATIONS = {
    "/api/auth/register": {
        "post": {"responses": {"201", "409", "422"}, "protected": False},
    },
    "/api/auth/login": {
        "post": {"responses": {"200", "401", "422"}, "protected": False},
    },
    "/api/variants/analyze": {
        "post": {"responses": {"202", "401", "404", "422"}, "protected": True},
    },
    "/api/variants/history": {
        "get": {"responses": {"200", "401", "422"}, "protected": True},
    },
    "/api/variants/{query_id}": {
        "get": {"responses": {"200", "401", "404", "422"}, "protected": True},
    },
    "/api/jobs/{job_id}": {
        "get": {"responses": {"200", "401", "404", "422"}, "protected": True},
    },
    "/api/similar/{variant_id}": {
        "get": {"responses": {"200", "401", "404", "422"}, "protected": True},
    },
    "/api/reports/{query_id}": {
        "get": {"responses": {"200", "401", "404", "422"}, "protected": True},
    },
    "/api/health": {
        "get": {"responses": {"200"}, "protected": False},
    },
}


def test_openapi_schema_exposes_required_operations(client):
    schema = client.get("/openapi.json").json()

    for path, methods in REQUIRED_OPERATIONS.items():
        assert path in schema["paths"]
        for method, expectation in methods.items():
            assert method in schema["paths"][path]
            operation = schema["paths"][path][method]
            assert expectation["responses"].issubset(set(operation["responses"].keys()))


def test_protected_operations_document_auth_parameters(client):
    schema = client.get("/openapi.json").json()

    for path, methods in REQUIRED_OPERATIONS.items():
        for method, expectation in methods.items():
            if not expectation["protected"]:
                continue
            parameters = schema["paths"][path][method].get("parameters", [])
            documented_params = {(param["name"], param["in"]) for param in parameters}

            assert ("authorization", "header") in documented_params
            assert ("token", "query") in documented_params


def test_analyze_contract_documents_request_and_response_schema(client):
    schema = client.get("/openapi.json").json()
    analyze_operation = schema["paths"]["/api/variants/analyze"]["post"]

    request_schema = analyze_operation["requestBody"]["content"]["application/json"]["schema"]
    response_schema = analyze_operation["responses"]["202"]["content"]["application/json"]["schema"]

    assert request_schema["$ref"].endswith("/AnalyzeRequest")
    assert response_schema["$ref"].endswith("/AnalyzeResponse")

    analyze_request = schema["components"]["schemas"]["AnalyzeRequest"]
    analyze_response = schema["components"]["schemas"]["AnalyzeResponse"]

    assert analyze_request["required"] == ["raw_input"]
    assert {"query_id", "job_id", "status"}.issubset(set(analyze_response["required"]))
