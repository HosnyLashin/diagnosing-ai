// src/pages/Note.js
import { useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import "../styles/diagnose.css";

export default function Note() {
  const [note,    setNote]    = useState("");
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const submit = async () => {
    if (!note.trim()) { setError("Please enter a clinical note."); return; }
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/diagnosis/note", { note });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="diagnose-page">
      <div className="page-header">
        <Link to="/dashboard" className="back-link">← Back</Link>
        <h1>📋 Clinical Note</h1>
        <p>Describe your symptoms in your own words and our AI will extract and analyse them.</p>
      </div>

      {!result ? (
        <>
          {error && <div className="page-error">{error}</div>}

          <textarea
            className="note-input"
            rows={8}
            placeholder="Example: I've had a fever of 38.9°C, a productive cough, and extreme fatigue for 5 days…"
            value={note}
            onChange={e => setNote(e.target.value)}
          />

          <div className="sym-footer">
            <button
              className="predict-btn"
              onClick={submit}
              disabled={loading || !note.trim()}
            >
              {loading ? "Analysing note…" : "Analyse Note"}
            </button>
          </div>
        </>
      ) : (
        <NoteResult result={result} onReset={() => { setResult(null); setNote(""); }} />
      )}
    </div>
  );
}

function NoteResult({ result, onReset }) {
  const top = Object.entries(result.probabilities)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <div className="result-card">
      <div className="result-prediction">
        <div className="result-label">Most Likely Diagnosis</div>
        <div className="result-disease">{result.prediction}</div>
      </div>

      {result.resolved_symptoms?.length > 0 && (
        <div className="result-section">
          <h3>🩺 Symptoms Detected</h3>
          <div className="tag-list">
            {result.resolved_symptoms.map(s => (
              <span key={s} className="tag tag-symptom">{s.replace(/_/g, " ")}</span>
            ))}
          </div>
        </div>
      )}

      {result.resolved_tests?.length > 0 && (
        <div className="result-section">
          <h3>🧪 Tests Identified</h3>
          <div className="tag-list">
            {result.resolved_tests.map(t => (
              <span key={t} className="tag tag-test">{t.replace(/_/g, " ")}</span>
            ))}
          </div>
        </div>
      )}

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

      <button className="reset-btn" onClick={onReset}>Try Another Note</button>
    </div>
  );
}
