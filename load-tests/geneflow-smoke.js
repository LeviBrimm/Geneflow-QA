import http from "k6/http";
import { check, group, sleep } from "k6";
import { Counter, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8001";
const VARIANT_INPUT = __ENV.VARIANT_INPUT || "BRCA1 c.5266dupC";
const JOB_TIMEOUT_SECONDS = Number(__ENV.JOB_TIMEOUT_SECONDS || 15);

export const analysisFailures = new Counter("analysis_failures");
export const jobCompletionTime = new Trend("job_completion_time");

export const options = {
  scenarios: {
    smoke: {
      executor: "constant-vus",
      vus: Number(__ENV.VUS || 3),
      duration: __ENV.DURATION || "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<750"],
    analysis_failures: ["count<1"],
    job_completion_time: ["p(95)<5000"],
  },
};

export default function () {
  let token;
  let jobId;

  group("health", () => {
    const response = http.get(`${BASE_URL}/api/health`);
    check(response, {
      "health returns 200": (res) => res.status === 200,
      "health reports ok": (res) => res.json("status") === "ok",
    });
  });

  group("auth", () => {
    const email = `load-${__VU}-${__ITER}-${Date.now()}@example.com`;
    const password = "password123";
    const register = http.post(
      `${BASE_URL}/api/auth/register`,
      JSON.stringify({ email, password }),
      jsonHeaders(),
    );
    const authOk = check(register, {
      "register returns 201": (res) => res.status === 201,
      "register returns token": (res) => Boolean(res.json("access_token")),
    });
    if (!authOk) {
      analysisFailures.add(1);
      return;
    }

    token = register.json("access_token");

    const login = http.post(
      `${BASE_URL}/api/auth/login`,
      JSON.stringify({ email, password }),
      jsonHeaders(),
    );
    check(login, {
      "login returns 200": (res) => res.status === 200,
      "login returns token": (res) => Boolean(res.json("access_token")),
    });
  });

  group("analysis submission", () => {
    if (!token) return;
    const response = http.post(
      `${BASE_URL}/api/variants/analyze`,
      JSON.stringify({ raw_input: VARIANT_INPUT }),
      authHeaders(token),
    );
    const submissionOk = check(response, {
      "analysis returns 202": (res) => res.status === 202,
      "analysis starts queued": (res) => res.json("status") === "queued",
      "analysis returns job id": (res) => Boolean(res.json("job_id")),
    });
    if (!submissionOk) {
      analysisFailures.add(1);
      return;
    }
    jobId = response.json("job_id");
  });

  group("job polling", () => {
    if (!token || !jobId) return;

    const started = Date.now();
    let finalStatus = "queued";

    while (Date.now() - started < JOB_TIMEOUT_SECONDS * 1000) {
      const response = http.get(`${BASE_URL}/api/jobs/${jobId}`, authHeaders(token));
      const statusOk = check(response, {
        "job poll returns 200": (res) => res.status === 200,
        "job has valid status": (res) => ["queued", "processing", "completed", "failed"].includes(res.json("status")),
      });
      if (!statusOk) {
        analysisFailures.add(1);
        return;
      }

      finalStatus = response.json("status");
      if (finalStatus === "completed" || finalStatus === "failed") break;
      sleep(0.5);
    }

    const elapsed = Date.now() - started;
    jobCompletionTime.add(elapsed);
    check(finalStatus, {
      "job completes": (status) => status === "completed",
    });
    if (finalStatus !== "completed") {
      analysisFailures.add(1);
    }
  });

  sleep(1);
}

function jsonHeaders() {
  return {
    headers: {
      "Content-Type": "application/json",
    },
  };
}

function authHeaders(token) {
  return {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };
}
