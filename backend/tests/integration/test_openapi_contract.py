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


def test_openapi_documents_json_response_models(client):
    schema = client.get("/openapi.json").json()

    expected_refs = {
        ("/api/jobs/{job_id}", "get", "200"): "/JobStatusResponse",
        ("/api/variants/{query_id}", "get", "200"): "/VariantResultResponse",
        ("/api/health", "get", "200"): "/HealthResponse",
    }

    for (path, method, status_code), schema_ref in expected_refs.items():
        response_schema = schema["paths"][path][method]["responses"][status_code]["content"]["application/json"][
            "schema"
        ]
        assert response_schema["$ref"].endswith(schema_ref)


def test_result_contract_includes_external_reference_schema(client):
    schema = client.get("/openapi.json").json()
    result_schema = schema["components"]["schemas"]["VariantResultResponse"]

    assert result_schema["properties"]["external_reference"]["$ref"].endswith("/ExternalReferenceResponse")
    assert result_schema["properties"]["variant_evidence"]["items"]["$ref"].endswith("/VariantEvidenceResponse")

    reference_schema = schema["components"]["schemas"]["ReferenceDataResponse"]
    assert "reference_source" in reference_schema["properties"]

    external_schema = schema["components"]["schemas"]["ExternalReferenceResponse"]
    assert {
        "source",
        "lookup_status",
        "external_id",
        "external_url",
        "gene_biotype",
        "location",
        "summary",
        "error_message",
    }.issubset(set(external_schema["properties"]))

    variant_evidence_schema = schema["components"]["schemas"]["VariantEvidenceResponse"]
    assert {
        "source",
        "lookup_status",
        "evidence_level",
        "submitted_notation",
        "normalized_hgvs",
        "rsid",
        "transcript_id",
        "consequence_terms",
        "impact",
        "clinical_significance",
        "condition",
        "review_status",
        "external_url",
        "error_message",
    }.issubset(set(variant_evidence_schema["properties"]))


def test_openapi_documents_list_response_models(client):
    schema = client.get("/openapi.json").json()

    expected_item_refs = {
        ("/api/variants/history", "get", "200"): "/QuerySummaryResponse",
        ("/api/similar/{variant_id}", "get", "200"): "/SimilarVariantResponse",
    }

    for (path, method, status_code), schema_ref in expected_item_refs.items():
        response_schema = schema["paths"][path][method]["responses"][status_code]["content"]["application/json"][
            "schema"
        ]
        assert response_schema["type"] == "array"
        assert response_schema["items"]["$ref"].endswith(schema_ref)
