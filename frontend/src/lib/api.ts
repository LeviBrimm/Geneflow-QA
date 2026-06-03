import type { AnalyzeResponse, AuthResponse, HistoryItem, JobResponse, VariantResult } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
export const AUTH_CHANGED_EVENT = "geneflow-auth-changed";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const tokenStore = {
  get: () => window.localStorage.getItem("geneflow_token"),
  set: (token: string) => {
    window.localStorage.setItem("geneflow_token", token);
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  },
  clear: () => {
    window.localStorage.removeItem("geneflow_token");
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  },
};

export async function register(email: string, password: string): Promise<AuthResponse> {
  return request("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }, false);
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return request("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }, false);
}

export async function analyze(rawInput: string): Promise<AnalyzeResponse> {
  return request("/api/variants/analyze", { method: "POST", body: JSON.stringify({ raw_input: rawInput }) });
}

export async function getJob(jobId: string): Promise<JobResponse> {
  return request(`/api/jobs/${jobId}`);
}

export async function getVariant(queryId: number): Promise<VariantResult> {
  return request(`/api/variants/${queryId}`);
}

export async function getHistory(): Promise<HistoryItem[]> {
  return request("/api/variants/history");
}

export function reportUrl(queryId: number): string {
  return `${API_BASE}/api/reports/${queryId}`;
}

async function request<T>(path: string, init: RequestInit = {}, withAuth = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (withAuth) {
    const token = tokenStore.get();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let message = "Request failed.";
    try {
      const payload = await response.json();
      message = payload.detail ?? message;
    } catch {
      message = response.statusText;
    }
    if (withAuth && response.status === 401) {
      tokenStore.clear();
      if (message.toLowerCase().includes("expired")) {
        message = "Session expired. Please log in again.";
      }
    }
    throw new ApiError(response.status, message);
  }
  return response.json();
}
