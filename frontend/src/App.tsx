import { Activity, Database, FileText, History, LogOut } from "lucide-react";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";

import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { ResultPage } from "./pages/ResultPage";
import { tokenStore } from "./lib/api";

export function App() {
  const navigate = useNavigate();
  const isAuthed = Boolean(tokenStore.get());

  function logout() {
    tokenStore.clear();
    navigate("/");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/" className="brand" aria-label="GeneFlow home">
          <Activity size={24} />
          <span>GeneFlow QA</span>
        </NavLink>
        <nav className="nav">
          <NavLink to="/" title="Analyze">
            <Database size={18} />
            <span>Analyze</span>
          </NavLink>
          <NavLink to="/history" title="History">
            <History size={18} />
            <span>History</span>
          </NavLink>
          {isAuthed && (
            <button className="icon-button" onClick={logout} title="Log out">
              <LogOut size={18} />
              <span>Log out</span>
            </button>
          )}
        </nav>
      </header>

      <main>
        <section className="notice">
          <FileText size={18} />
          <span>Educational only. Not medical advice. No patient data is used.</span>
        </section>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/results/:queryId" element={<ResultPage />} />
        </Routes>
      </main>
    </div>
  );
}
