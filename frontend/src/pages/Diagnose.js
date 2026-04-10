// src/pages/Diagnose.js
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import "../styles/diagnose.css";

export default function Diagnose() {
  const [symptoms,  setSymptoms]  = useState([]);
  const [selected,  setSelected]  = useState(new Set());
  const [result,    setResult]    = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [fetching,  setFetching]  = useState(true);
  const [error,     setError]     = useState("");
  const [search,    setSearch]    = useState("");

  useEffect(() => {
    api.get("/diagnosis/symptoms")
      .then(res => setSymptoms(res.data.symptoms))
      .catch(() => setError("Failed to load symptoms."))
      .finally(() => setFetching(false));
  }, []);

  const toggle = (sym) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(sym) ? next.delete(sym) : next.add(sym);
      return next;
    });
  };

  const submit = async () => {
    if (selected.size === 0) { setError("Please select at least one symptom."); return; }
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/diagnosis/symptoms", {
        symptoms: [...selected],
        confirmed: false,
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Prediction failed.");
    } finally {
      setLoading(false);
    }
  };

  const filtered = symptoms.filter(s =>
    s.replace(/_/g, " ").includes(search.toLowerCase())
  );

  if (fetching) return <div className="page-loading">Loading symptoms…</div>;

  return (
    <div className="diagnose-page">
      <div className="page-header">
        <Link to="/dashboard" className="back-link">← Back</Link>
        <h1>🩺 Check Symptoms</h1>
        <p>Select all symptoms you are currently experiencing.</p>
      </div>

      {!result ? (
        <>
          <div className="sym-search">
            <input
              placeholder="Search symptoms…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <span>{selected.size} selected</span>
          </div>

          {error && <div className="page-error">{error}</div>}

          <div className="sym-grid">
            {filtered.map(sym => (
              <button
                key={sym}
                className={`sym-chip ${selected.has(sym) ? "selected" : ""}`}
                onClick={() => toggle(sym)}
              >
                {sym.replace(/_/g, " ")}
              </button>
            ))}
          </div>

          <div className="sym-footer">
            <button
              className="predict-btn"
              onClick={submit}
              disabled={loading || selected.size === 0}
            >
              {loading ? "Analysing…" : "Get Diagnosis"}
            </button>
          </div>
        </>
      ) : (
        <ResultCard result={result} onReset={() => { setResult(null); setSelected(new Set()); }} />
      )}
    </div>
  );
}

function ResultCard({ result, onReset }) {
  const top = Object.entries(result.probabilities)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="result-card">
      <div className="result-prediction">
        <div className="result-label">Most Likely Diagnosis</div>
        <div className="result-disease">{result.prediction}</div>
      </div>

      <div className="result-probs">
        <h3>Probability Breakdown</h3>
        {top.map(([disease, prob]) => (
          <div key={disease} className="prob-row">
            <span className="prob-name">{disease}</span>
            <div className="prob-bar-wrap">
              <div className="prob-bar" style={{ width: `${prob}%` }} />
            </div>
            <span className="prob-pct">{prob.toFixed(1)}%</span>
          </div>
        ))}
      </div>

      <div className="result-disclaimer">
        ⚠️ This is not a medical diagnosis. Please consult a doctor.
      </div>

      <button className="reset-btn" onClick={onReset}>Check Again</button>
    </div>
  );
}
