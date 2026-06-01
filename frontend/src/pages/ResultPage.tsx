import { Download, RefreshCcw } from "lucide-react";
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

  if (error) return <section className="panel"><p className="error">{error}</p></section>;
  if (!result) return <section className="panel"><p className="muted">Loading result...</p></section>;

  return (
    <section className="result-layout">
      <div className="panel">
        <div className="section-header">
          <div>
            <p className="eyebrow">Analysis result</p>
            <h1>{result.raw_input}</h1>
          </div>
          <div className="actions">
            <button className="secondary-button" onClick={load} title="Refresh result">
              <RefreshCcw size={17} />
              <span>Refresh</span>
            </button>
            <a
              className="secondary-button"
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
        <div className="summary-grid">
          <Metric label="Gene" value={result.parsed.gene} />
          <Metric label="Type" value={result.parsed.variant_type} />
          <Metric label="Significance" value={result.reference.significance} />
          <Metric label="Condition" value={result.reference.condition} />
        </div>
        <GeneVisualization result={result} />
      </div>

      <div className="panel">
        <h2>Explanations</h2>
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
      </div>

      <div className="panel">
        <h2>Similar Variants</h2>
        <div className="table">
          {result.similar_variants.map((item) => (
            <div className="table-row" key={item.variant_id}>
              <span>{item.gene} {item.hgvs}</span>
              <span>{item.condition}</span>
              <span>{item.similarity_score}</span>
            </div>
          ))}
          {!result.similar_variants.length && <p className="muted">No similar variants available.</p>}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
