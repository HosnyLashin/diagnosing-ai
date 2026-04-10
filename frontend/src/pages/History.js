// src/pages/History.js
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import "../styles/history.css";

export default function History() {
  const [history,  setHistory]  = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");

  useEffect(() => {
    api.get("/diagnosis/history")
      .then(res => setHistory(res.data.history))
      .catch(() => setError("Failed to load history."))
      .finally(() => setLoading(false));
  }, []);

  const confirm = async (id, confirmed) => {
    try {
      await api.patch(`/diagnosis/${id}/confirm`, { confirmed });
      setHistory(prev =>
        prev.map(d => d.id === id ? { ...d, confirmed } : d)
      );
    } catch {
      alert("Failed to update diagnosis.");
    }
  };

  if (loading) return <div className="page-loading">Loading history…</div>;

  return (
    <div className="history-page">
      <div className="page-header">
        <Link to="/dashboard" className="back-link">← Back</Link>
        <h1>📊 My Diagnosis History</h1>
        <p>{history.length} record{history.length !== 1 ? "s" : ""} found</p>
      </div>

      {error && <div className="page-error">{error}</div>}

      {history.length === 0 ? (
        <div className="history-empty">
          <p>No diagnoses yet. <Link to="/diagnose">Check your symptoms</Link> to get started.</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map(d => (
            <div key={d.id} className={`history-card ${d.confirmed ? "confirmed" : ""}`}>
              <div className="hcard-top">
                <div className="hcard-disease">{d.disease}</div>
                <div className="hcard-date">
                  {d.date ? new Date(d.date).toLocaleDateString("en-GB", {
                    day: "numeric", month: "short", year: "numeric"
                  }) : "—"}
                </div>
              </div>

              {d.symptoms && (
                <div className="hcard-detail">
                  <span className="hcard-label">Symptoms:</span> {d.symptoms}
                </div>
              )}
              {d.tests && (
                <div className="hcard-detail">
                  <span className="hcard-label">Tests:</span> {d.tests}
                </div>
              )}

              <div className="hcard-footer">
                <span className={`hcard-status ${d.confirmed ? "status-yes" : "status-no"}`}>
                  {d.confirmed ? "✓ Confirmed" : "Unconfirmed"}
                </span>
                <div className="hcard-actions">
                  {!d.confirmed && (
                    <button
                      className="confirm-btn yes"
                      onClick={() => confirm(d.id, true)}
                    >
                      Confirm Diagnosis
                    </button>
                  )}
                  {d.confirmed && (
                    <button
                      className="confirm-btn no"
                      onClick={() => confirm(d.id, false)}
                    >
                      Mark Unconfirmed
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
