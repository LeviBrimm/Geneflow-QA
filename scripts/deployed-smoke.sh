#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${BASE_URL:-}" ]]; then
  echo "BASE_URL is required, for example: BASE_URL=https://geneflow-api.onrender.com bash scripts/deployed-smoke.sh"
  exit 1
fi

BASE_URL="${BASE_URL%/}"
VARIANT_INPUT="${VARIANT_INPUT:-BRCA1 c.5266dupC}"
JOB_TIMEOUT_SECONDS="${JOB_TIMEOUT_SECONDS:-60}"
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-2}"

curl_json() {
  local method="$1"
  local url="$2"
  local body="${3:-}"
  local token="${4:-}"

  local args=(-sS -X "$method" "$url" -H "Content-Type: application/json")
  if [[ -n "$token" ]]; then
    args+=(-H "Authorization: Bearer ${token}")
  fi
  if [[ -n "$body" ]]; then
    args+=(-d "$body")
  fi

  curl "${args[@]}"
}

json_value() {
  local payload="$1"
  local path="$2"
  JSON_PAYLOAD="$payload" JSON_PATH="$path" python3 - <<'PY'
import json
import os

value = json.loads(os.environ["JSON_PAYLOAD"])
for part in os.environ["JSON_PATH"].split("."):
    value = value[part]
print(value)
PY
}

assert_json_value() {
  local payload="$1"
  local path="$2"
  local expected="$3"
  local actual
  actual="$(json_value "$payload" "$path")"
  if [[ "$actual" != "$expected" ]]; then
    echo "Expected ${path}='${expected}', got '${actual}'."
    echo "$payload"
    exit 1
  fi
}

email="deploy-smoke-$(date +%s)-$RANDOM@example.com"
password="password123"

echo "Checking deployed backend health at ${BASE_URL}..."
health_payload="$(curl_json GET "${BASE_URL}/api/health")"
assert_json_value "$health_payload" "status" "ok"

echo "Registering deployed smoke-test user..."
register_payload="$(curl_json POST "${BASE_URL}/api/auth/register" "{\"email\":\"${email}\",\"password\":\"${password}\"}")"
token="$(json_value "$register_payload" "access_token")"
if [[ -z "$token" || "$token" == "None" ]]; then
  echo "Registration did not return an access token."
  echo "$register_payload"
  exit 1
fi

echo "Submitting deployed analysis job for ${VARIANT_INPUT}..."
analysis_payload="$(curl_json POST "${BASE_URL}/api/variants/analyze" "{\"raw_input\":\"${VARIANT_INPUT}\"}" "$token")"
query_id="$(json_value "$analysis_payload" "query_id")"
job_id="$(json_value "$analysis_payload" "job_id")"
assert_json_value "$analysis_payload" "status" "queued"

echo "Polling deployed worker job ${job_id}..."
deadline=$((SECONDS + JOB_TIMEOUT_SECONDS))
job_status="queued"
while (( SECONDS < deadline )); do
  job_payload="$(curl_json GET "${BASE_URL}/api/jobs/${job_id}" "" "$token")"
  job_status="$(json_value "$job_payload" "status")"
  echo "Job status: ${job_status}"
  if [[ "$job_status" == "completed" || "$job_status" == "failed" ]]; then
    break
  fi
  sleep "$POLL_INTERVAL_SECONDS"
done

if [[ "$job_status" != "completed" ]]; then
  echo "Expected deployed job to complete, got '${job_status}'."
  echo "${job_payload:-}"
  exit 1
fi

echo "Fetching deployed persisted result..."
result_payload="$(curl_json GET "${BASE_URL}/api/variants/${query_id}" "" "$token")"
assert_json_value "$result_payload" "status" "completed"
assert_json_value "$result_payload" "parsed.gene" "${VARIANT_INPUT%% *}"

echo "Fetching deployed HTML report..."
report_payload="$(curl -sS -H "Authorization: Bearer ${token}" "${BASE_URL}/api/reports/${query_id}")"
if [[ "$report_payload" != *"GeneFlow Variant Report"* || "$report_payload" != *"Educational use only"* ]]; then
  echo "Expected deployed report to include title and educational disclaimer."
  echo "$report_payload"
  exit 1
fi

echo "Deployed smoke test passed."
