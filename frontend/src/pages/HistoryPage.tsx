import { RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getHistory } from "../lib/api";
import type { HistoryItem } from "../types";

export function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState("");

  async function loadHistory() {
    setError("");
    try {
      setItems(await getHistory());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load history.");
    }
  }

  useEffect(() => {
    void loadHistory();
  }, []);

  return (
    <section className="panel">
      <div className="section-header">
        <div>
          <p className="eyebrow">Saved analysis</p>
          <h1>Query History</h1>
        </div>
        <button className="secondary-button" onClick={loadHistory} title="Refresh history">
          <RefreshCcw size={17} />
          <span>Refresh</span>
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="table">
        {items.map((item) => (
          <Link to={`/results/${item.query_id}`} className="table-row" key={item.query_id}>
            <span>{item.raw_input}</span>
            <span className={`badge ${item.status}`}>{item.status}</span>
            <span>{new Date(item.created_at).toLocaleString()}</span>
          </Link>
        ))}
        {!items.length && !error && <p className="muted">No saved queries yet.</p>}
      </div>
    </section>
  );
}
