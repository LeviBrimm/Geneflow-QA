import { ClipboardList, DatabaseZap, Download, ExternalLink, RefreshCcw, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { GeneVisualization } from "../components/GeneVisualization";
import { getVariant, reportUrl, tokenStore } from "../lib/api";
import type { VariantResult } from "../types";

export function ResultPage() {
  const { queryId } = useParams();
  const [result, setResult] = useState<VariantResult | null>(null);
  const [error, setError] = useState("");

  async function load() {
    if (!queryId) return;
    setError("");
    try {
      setResult(await getVariant(Number(queryId)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load result.");
    }
  }

  useEffect(() => {
    void load();
  }, [queryId]);

  if (error) {
    return (
      <section className="panel">
        <p className="error">{error}</p>
      </section>
    );
  }
  if (!result) {
    return (
      <section className="panel">
        <p className="muted">Loading result...</p>
      </section>
    );
  }

  return (
    <section className="result-dossier">
      <div className="dossier-header">
        <div>
          <p className="eyebrow">Analysis result</p>
          <h1>{result.raw_input}</h1>
          <div className="dossier-meta">
            <span className={`badge ${result.status}`}>{result.status}</span>
            <span>Job {result.job_id.slice(0, 8)}</span>
            <span>{new Date(result.created_at).toLocaleString()}</span>
          </div>
        </div>
        <div className="actions">
          <button className="secondary-button" onClick={load} title="Refresh result">
            <RefreshCcw size={17} />
            <span>Refresh</span>
          </button>
          <a
            className="primary-button"
            href={`${reportUrl(result.query_id)}?token=${tokenStore.get() ?? ""}`}
            title="Open HTML report"
            target="_blank"
            rel="noreferrer"
          >
            <Download size={17} />
            <span>Report</span>
          </a>
        </div>
      </div>

      <div className="dossier-grid">
        <article className="panel evidence-card span-8">
          <div className="section-header tight">
            <div>
              <p className="eyebrow">Parsed specimen</p>
              <h2>Reference match</h2>
            </div>
            <ClipboardList size={22} />
          </div>
          <div className="summary-grid">
            <Metric label="Gene" value={result.parsed.gene} />
            <Metric label="Notation" value={result.parsed.notation} />
            <Metric label="Type" value={result.parsed.variant_type} />
            <Metric label="Significance" value={result.reference.significance} />
          </div>
          <GeneVisualization result={result} />
        </article>

        <aside className="panel evidence-card span-4">
          <div>
            <p className="eyebrow">Evidence record</p>
            <h2>{result.reference.rsid}</h2>
          </div>
          <dl className="evidence-list">
            <div>
              <dt>Gene name</dt>
              <dd>{result.reference.gene_full_name}</dd>
            </div>
            <div>
              <dt>Condition</dt>
              <dd>{result.reference.condition}</dd>
            </div>
            <div>
              <dt>Allele frequency</dt>
              <dd>{result.reference.allele_frequency}</dd>
            </div>
            <div>
              <dt>Domain</dt>
              <dd>{result.reference.domain}</dd>
            </div>
          </dl>
          <p className="evidence-summary">{result.reference.summary}</p>
        </aside>

        <article className="panel evidence-card span-12 external-reference-card">
          <div className="section-header tight">
            <div>
              <p className="eyebrow">Public data enrichment</p>
              <h2>External Reference</h2>
            </div>
            <div className="external-source">
              <DatabaseZap size={18} />
              <span>{result.external_reference.source ?? "pending"}</span>
            </div>
          </div>
          <div className="summary-grid">
            <Metric label="Lookup" value={result.external_reference.lookup_status} />
            <Metric label="External ID" value={result.external_reference.external_id} />
            <Metric label="Biotype" value={result.external_reference.gene_biotype} />
            <Metric label="Location" value={result.external_reference.location} />
          </div>
          <p className="evidence-summary">
            {result.external_reference.error_message ??
              result.external_reference.summary ??
              "External reference enrichment is still pending."}
          </p>
          {result.external_reference.external_url && (
            <a
              className="secondary-button inline-link"
              href={result.external_reference.external_url}
              target="_blank"
              rel="noreferrer"
            >
              <ExternalLink size={16} />
              <span>Open Ensembl record</span>
            </a>
          )}
        </article>

        <article className="panel explanation-panel span-12">
          <div className="section-header tight">
            <div>
              <p className="eyebrow">Guarded explanation</p>
              <h2>Interpretation context</h2>
            </div>
            <span className="model-pill">{result.explanations.model_used ?? "processing"}</span>
          </div>
          <div className="explanation-grid">
            <article>
              <h3>General</h3>
              <p>{result.explanations.general ?? "Explanation is still processing."}</p>
            </article>
            <article>
              <h3>Technical</h3>
              <p>{result.explanations.technical ?? "Explanation is still processing."}</p>
            </article>
          </div>
          <div className="disclaimer-strip">
            <ShieldAlert size={16} />
            <span>Educational context only. This report does not provide medical advice.</span>
          </div>
        </article>

        <article className="panel span-12">
          <div className="section-header tight">
            <div>
              <p className="eyebrow">Comparison queue</p>
              <h2>Similar Variants</h2>
            </div>
          </div>
          <div className="comparison-table">
            {result.similar_variants.map((item) => (
              <div className="comparison-row" key={item.variant_id}>
                <strong>{item.gene} {item.hgvs}</strong>
                <span>{item.significance}</span>
                <span>{item.condition}</span>
                <span>{Math.round(item.similarity_score * 100)}%</span>
              </div>
            ))}
            {!result.similar_variants.length && <p className="muted">No similar variants available.</p>}
          </div>
        </article>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value ?? "Unavailable"}</strong>
    </div>
  );
}
