// src/pages/VerifyEmail.js
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api from "../api/client";
import "../styles/auth.css";

export default function VerifyEmail() {
  const [searchParams]  = useSearchParams();
  const [status,  setStatus]  = useState("loading"); // loading | success | expired | invalid
  const [email,   setEmail]   = useState("");
  const [resent,  setResent]  = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) { setStatus("invalid"); return; }

    api.get(`/auth/verify-email?token=${token}`)
      .then(() => setStatus("success"))
      .catch(err => {
        const msg = err.response?.data?.error || "";
        setStatus(msg.includes("expired") ? "expired" : "invalid");
      });
  }, [searchParams]);

  const resendEmail = async () => {
    if (!email) return;
    setSending(true);
    try {
      await api.post("/auth/resend-verification", { email });
      setResent(true);
    } catch {
      alert("Failed to resend. Please try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🧬</div>
        <h1 className="auth-title">Diagnosing AI</h1>

        {status === "loading" && (
          <p className="auth-subtitle">Verifying your email…</p>
        )}

        {status === "success" && (
          <>
            <p className="auth-subtitle" style={{color:"#34d399"}}>
              ✅ Email verified successfully!
            </p>
            <p style={{color:"#7d8590",marginBottom:24,fontSize:"0.9rem"}}>
              Your account is ready. You can now sign in.
            </p>
            <Link to="/login" className="auth-btn" style={{display:"block",textAlign:"center",padding:"12px"}}>
              Go to Login
            </Link>
          </>
        )}

        {status === "expired" && (
          <>
            <p className="auth-subtitle" style={{color:"#f87171"}}>
              ⏰ Verification link expired
            </p>
            <p style={{color:"#7d8590",marginBottom:16,fontSize:"0.9rem"}}>
              Your link expired after 24 hours. Enter your email to get a new one.
            </p>
            {!resent ? (
              <div className="auth-form">
                <div className="field">
                  <label>Email</label>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </div>
                <button className="auth-btn" onClick={resendEmail} disabled={sending || !email}>
                  {sending ? "Sending…" : "Resend Verification Email"}
                </button>
              </div>
            ) : (
              <p style={{color:"#34d399",fontSize:"0.9rem"}}>
                ✅ New verification email sent! Check your inbox.
              </p>
            )}
          </>
        )}

        {status === "invalid" && (
          <>
            <p className="auth-subtitle" style={{color:"#f87171"}}>
              ❌ Invalid verification link
            </p>
            <p style={{color:"#7d8590",marginBottom:16,fontSize:"0.9rem"}}>
              This link is invalid or has already been used.
              Enter your email to get a new one.
            </p>
            {!resent ? (
              <div className="auth-form">
                <div className="field">
                  <label>Email</label>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                  />
                </div>
                <button className="auth-btn" onClick={resendEmail} disabled={sending || !email}>
                  {sending ? "Sending…" : "Resend Verification Email"}
                </button>
              </div>
            ) : (
              <p style={{color:"#34d399",fontSize:"0.9rem"}}>
                ✅ New verification email sent! Check your inbox.
              </p>
            )}
          </>
        )}

        <p className="auth-switch" style={{marginTop:24}}>
          <Link to="/login">← Back to Login</Link>
        </p>
      </div>
    </div>
  );
}
