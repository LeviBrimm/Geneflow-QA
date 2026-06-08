import { FileClock, RefreshCcw, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getHistory } from "../lib/api";
import type { HistoryItem } from "../types";

export function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [error, setError] = useState("");
  const completedCount = items.filter((item) => item.status === "completed").length;
  const activeCount = items.filter((item) => item.status === "queued" || item.status === "processing").length;

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
    <section className="history-workspace">
      <div className="history-header">
        <div>
          <p className="eyebrow">Saved analysis</p>
          <h1>Query History</h1>
          <p className="lede">Review submitted variants, status transitions, timestamps, and report access paths.</p>
        </div>
        <button className="secondary-button" onClick={loadHistory} title="Refresh history">
          <RefreshCcw size={17} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="history-summary" aria-label="History summary">
        <div>
          <span>Total records</span>
          <strong>{items.length}</strong>
        </div>
        <div>
          <span>Completed</span>
          <strong>{completedCount}</strong>
        </div>
        <div>
          <span>Active jobs</span>
          <strong>{activeCount}</strong>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      <div className="logbook">
        <div className="logbook-head">
          <span><Search size={15} /> Variant</span>
          <span>Status</span>
          <span>Created</span>
          <span>Action</span>
        </div>
        {items.map((item) => (
          <Link to={`/results/${item.query_id}`} className="logbook-row" key={item.query_id}>
            <strong><FileClock size={16} /> {item.raw_input}</strong>
            <span className={`badge ${item.status}`}>{item.status}</span>
            <span>{new Date(item.created_at).toLocaleString()}</span>
            <span className="row-action">Open result</span>
          </Link>
        ))}
        {!items.length && !error && <p className="muted">No saved queries yet.</p>}
      </div>
    </section>
  );
}
