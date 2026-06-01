import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthPanel } from "../components/AuthPanel";
import { VariantForm } from "../components/VariantForm";
import { analyze, getJob, tokenStore } from "../lib/api";
import type { JobStatus } from "../types";

export function HomePage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<JobStatus | "idle">("idle");
  const [message, setMessage] = useState("");
  const [isAuthed, setIsAuthed] = useState(Boolean(tokenStore.get()));

  useEffect(() => {
    setIsAuthed(Boolean(tokenStore.get()));
  }, []);

  async function handleAnalyze(rawInput: string) {
    setMessage("");
    setStatus("queued");
    try {
      const response = await analyze(rawInput);
      setStatus(response.status);
      const timer = window.setInterval(async () => {
        const job = await getJob(response.job_id);
        setStatus(job.status);
        if (job.status === "completed") {
          window.clearInterval(timer);
          navigate(`/results/${response.query_id}`);
        }
        if (job.status === "failed") {
          window.clearInterval(timer);
          setStatus("idle");
          setMessage(job.error_message ?? "Analysis job failed.");
        }
      }, 900);
    } catch (error) {
      setStatus("idle");
      setMessage(error instanceof Error ? error.message : "Unable to submit analysis.");
    }
  }

  function handleAuthed() {
    setIsAuthed(true);
  }

  return (
    <div className="workspace-grid">
      <section className="panel primary-panel">
        <div>
          <p className="eyebrow">Variant interpretation workflow</p>
          <h1>Analyze public genomic variant references with an auditable QA flow.</h1>
        </div>
        {isAuthed ? (
          <VariantForm onSubmit={handleAnalyze} disabled={status !== "idle"} />
        ) : (
          <AuthPanel onAuthed={handleAuthed} />
        )}
        {status !== "idle" && (
          <div className="status-strip" role="status">
            <span className="pulse" />
            <span>Analysis status: {status}</span>
          </div>
        )}
        {message && <p className="error">{message}</p>}
      </section>

      <aside className="panel compact-panel">
        <h2>Pipeline</h2>
        <ol className="pipeline">
          <li>Parse and validate HGVS-style input</li>
          <li>Match seeded public reference data</li>
          <li>Create async analysis job</li>
          <li>Generate guarded explanations</li>
          <li>Persist history and report output</li>
        </ol>
      </aside>
    </div>
  );
}
