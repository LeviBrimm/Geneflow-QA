import { CheckCircle2, Clock3, FileSearch, Microscope, ShieldCheck } from "lucide-react";
import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthPanel } from "../components/AuthPanel";
import { VariantForm } from "../components/VariantForm";
import { AUTH_CHANGED_EVENT, analyze, getJob, tokenStore } from "../lib/api";
import type { JobStatus } from "../types";

const visibleAnalysisSequence: JobStatus[] = ["queued", "processing", "completed"];
const visibleStepDelayMs = 550;
const pollIntervalMs = 900;

export function HomePage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<JobStatus | "idle">("idle");
  const [message, setMessage] = useState("");
  const [isAuthed, setIsAuthed] = useState(Boolean(tokenStore.get()));

  useEffect(() => {
    function syncAuthState() {
      setIsAuthed(Boolean(tokenStore.get()));
    }

    syncAuthState();
    window.addEventListener(AUTH_CHANGED_EVENT, syncAuthState);
    window.addEventListener("storage", syncAuthState);
    return () => {
      window.removeEventListener(AUTH_CHANGED_EVENT, syncAuthState);
      window.removeEventListener("storage", syncAuthState);
    };
  }, []);

  async function handleAnalyze(rawInput: string) {
    setMessage("");
    setStatus("queued");
    try {
      const response = await analyze(rawInput);
      setStatus("queued");
      const timer = window.setInterval(async () => {
        const job = await getJob(response.job_id);
        if (job.status === "completed") {
          window.clearInterval(timer);
          await playVisibleAnalysisSequence(setStatus);
          navigate(`/results/${response.query_id}`);
        }
        if (job.status === "failed") {
          window.clearInterval(timer);
          setStatus("idle");
          setMessage(job.error_message ?? "Analysis job failed.");
        }
        if (job.status === "processing") {
          setStatus("processing");
        }
      }, pollIntervalMs);
    } catch (error) {
      setStatus("idle");
      setMessage(error instanceof Error ? error.message : "Unable to submit analysis.");
    }
  }

  function handleAuthed() {
    setIsAuthed(true);
  }

  return (
    <div className="workbench-grid">
      <aside className="bench-rail">
        <div className="rail-block">
          <p className="eyebrow">Workbench</p>
          <h2>Variant intake</h2>
          <p className="rail-copy">
            Submit one public HGVS-style variant at a time. GeneFlow checks seeded demo records first and can fall back
            to live Ensembl evidence when live mode is enabled.
          </p>
        </div>
        <div className="rail-specimen">
          <span className="specimen-label">Try live lookup</span>
          <strong>BRAF c.1799T&gt;A</strong>
          <span>Ensembl VEP-backed record</span>
        </div>
        <div className="rail-checks" aria-label="QA checks">
          <span><ShieldCheck size={15} /> Auth boundary</span>
          <span><FileSearch size={15} /> Contracted API</span>
          <span><Clock3 size={15} /> Async job state</span>
        </div>
      </aside>

      <section className="analysis-console">
        <div className="console-header">
          <div>
            <p className="eyebrow">Genomic QA workbench</p>
            <h1>Run a traceable variant analysis from intake to report.</h1>
          </div>
          <div className="console-mark" aria-hidden="true">
            <Microscope size={30} />
          </div>
        </div>

        <p className="lede">
          GeneFlow validates the submitted notation, resolves public reference data through seeded records or configured
          Ensembl lookup, queues analysis work, stores history, and produces an educational report with guarded
          explanations.
        </p>

        {isAuthed ? (
          <VariantForm onSubmit={handleAnalyze} disabled={status !== "idle"} />
        ) : (
          <AuthPanel onAuthed={handleAuthed} />
        )}

        <PipelineProgress status={status} />

        {status !== "idle" && (
          <div className="status-strip" role="status">
            <span className="pulse" />
            <span>Analysis status: {status}</span>
          </div>
        )}
        {message && <p className="error">{message}</p>}
      </section>

      <aside className="evidence-rail">
        <div>
          <p className="eyebrow">System path</p>
          <h2>Queue-backed analysis</h2>
        </div>
        <ol className="pipeline">
          <li>Parse and validate HGVS-style input</li>
          <li>Resolve seeded or Ensembl reference data</li>
          <li>Create async analysis job</li>
          <li>Generate guarded explanations</li>
          <li>Persist history and report output</li>
        </ol>
        <div className="signal-grid" aria-label="Platform signals">
          <span>FastAPI</span>
          <span>Postgres</span>
          <span>Redis/RQ</span>
          <span>Playwright</span>
        </div>
      </aside>
    </div>
  );
}

async function playVisibleAnalysisSequence(setStatus: Dispatch<SetStateAction<JobStatus | "idle">>) {
  for (const nextStatus of visibleAnalysisSequence.slice(1)) {
    setStatus(nextStatus);
    await wait(visibleStepDelayMs);
  }
}

function wait(milliseconds: number) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function PipelineProgress({ status }: { status: JobStatus | "idle" }) {
  const steps = [
    { key: "queued", label: "Queued", detail: "Job record created" },
    { key: "processing", label: "Processing", detail: "Worker evaluates evidence" },
    { key: "completed", label: "Completed", detail: "Result ready" },
  ] as const;
  const activeIndex = status === "idle" ? -1 : steps.findIndex((step) => step.key === status);

  return (
    <div className="progress-track" aria-label="Analysis pipeline">
      {steps.map((step, index) => {
        const isActive = index <= activeIndex || status === "completed";
        return (
          <div className={`progress-step ${isActive ? "active" : ""}`} key={step.key}>
            <span>{isActive ? <CheckCircle2 size={16} /> : index + 1}</span>
            <div>
              <strong>{step.label}</strong>
              <small>{step.detail}</small>
            </div>
          </div>
        );
      })}
    </div>
  );
}
