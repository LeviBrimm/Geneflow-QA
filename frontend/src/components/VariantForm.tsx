import { Play } from "lucide-react";
import { FormEvent, useState } from "react";

const examples = ["BRCA1 c.5266dupC", "TP53 p.R175H", "CFTR ΔF508", "BRAF c.1799T>A"];

export function VariantForm({ onSubmit, disabled }: { onSubmit: (rawInput: string) => void; disabled: boolean }) {
  const [rawInput, setRawInput] = useState(examples[0]);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit(rawInput);
  }

  return (
    <form className="variant-form" onSubmit={submit}>
      <label>
        Variant input
        <input value={rawInput} onChange={(event) => setRawInput(event.target.value)} disabled={disabled} required />
      </label>
      <span className="example-label">Demo shortcuts</span>
      <div className="example-row">
        {examples.map((example) => (
          <button type="button" key={example} onClick={() => setRawInput(example)} disabled={disabled}>
            {example}
          </button>
        ))}
      </div>
      <button className="primary-button" disabled={disabled} type="submit">
        <Play size={18} />
        <span>Start Analysis</span>
      </button>
    </form>
  );
}
