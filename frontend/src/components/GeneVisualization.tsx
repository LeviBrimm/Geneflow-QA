import type { VariantResult } from "../types";

export function GeneVisualization({ result }: { result: VariantResult }) {
  const position = result.reference.position ?? 0;
  const marker = Math.max(6, Math.min(94, position % 100));

  return (
    <div className="gene-viz" aria-label="Gene visualization">
      <div className="gene-viz-header">
        <span>{result.parsed.gene}</span>
        <span>{result.reference.domain}</span>
      </div>
      <div className="gene-bar">
        <span className="domain domain-left">Domain A</span>
        <span className="domain domain-right">Domain B</span>
        <span className="variant-marker" style={{ left: `${marker}%` }} title={result.parsed.notation} />
      </div>
      <p>{result.reference.summary}</p>
    </div>
  );
}
