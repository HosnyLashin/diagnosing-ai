// src/pages/Auth.js
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";
import api from "../api/client";
import "../styles/auth.css";

// ── Login ────────────────────────────────────────────────────────────────────
export function Login() {
  const { login }  = useAuth();
  const navigate   = useNavigate();
  const [form,     setForm]      = useState({ email: "", password: "" });
  const [error,    setError]     = useState("");
  const [loading,  setLoading]   = useState(false);
  const [unverified, setUnverified] = useState(false);
  const [resent,   setResent]    = useState(false);
  const [sending,  setSending]   = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setError(""); setUnverified(false); setResent(false);
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      if (err.response?.data?.unverified) {
        setUnverified(true);
      } else {
        setError(err.response?.data?.error || "Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async () => {
    setSending(true);
    try {
      await api.post("/auth/resend-verification", { email: form.email });
      setResent(true);
    } catch {
      setError("Failed to resend verification email.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🧬</div>
        <h1 className="auth-title">Diagnosing AI</h1>
        <p className="auth-subtitle">Sign in to your account</p>

        {error && <div className="auth-error">{error}</div>}

        {unverified && (
          <div className="auth-error" style={{borderColor:"#f59e0b",color:"#f59e0b",background:"rgba(245,158,11,0.1)"}}>
            Your email is not verified yet.
            {!resent ? (
              <button
                onClick={resendVerification}
                disabled={sending}
                style={{display:"block",marginTop:8,background:"none",border:"none",
                        color:"#f59e0b",cursor:"pointer",textDecoration:"underline",
                        padding:0,fontSize:"0.88rem"}}
              >
                {sending ? "Sending…" : "Resend verification email"}
              </button>
            ) : (
              <span style={{display:"block",marginTop:8,fontSize:"0.85rem",color:"#34d399"}}>
                ✅ Verification email sent! Check your inbox.
              </span>
            )}
          </div>
        )}

        <form onSubmit={handle} className="auth-form">
          <div className="field">
            <label>Email</label>
            <input type="email" required value={form.email}
              onChange={e => setForm({...form, email: e.target.value})}
              placeholder="you@example.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" required value={form.password}
              onChange={e => setForm({...form, password: e.target.value})}
              placeholder="••••••••" />
          </div>
          <button className="auth-btn" disabled={loading}>
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  );
}

// ── Register ──────────────────────────────────────────────────────────────────
export function Register() {
  const navigate  = useNavigate();
  const [form,    setForm]    = useState({ name: "", email: "", password: "" });
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const [done,    setDone]    = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/register", {
        name: form.name, email: form.email, password: form.password
      });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  if (done) return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">📧</div>
        <h1 className="auth-title">Check your email</h1>
        <p style={{color:"#7d8590",marginBottom:24,fontSize:"0.9rem",textAlign:"center"}}>
          We sent a verification link to <strong style={{color:"#e6edf3"}}>{form.email}</strong>.
          Click the link to activate your account. It expires in 24 hours.
        </p>
        <p className="auth-switch">
          Already verified? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🧬</div>
        <h1 className="auth-title">Diagnosing AI</h1>
        <p className="auth-subtitle">Create your account</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handle} className="auth-form">
          <div className="field">
            <label>Full Name</label>
            <input type="text" required value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
              placeholder="Hosny Lashin" />
          </div>
          <div className="field">
            <label>Email</label>
            <input type="email" required value={form.email}
              onChange={e => setForm({...form, email: e.target.value})}
              placeholder="you@example.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" required value={form.password}
              onChange={e => setForm({...form, password: e.target.value})}
              placeholder="Min. 8 characters" />
          </div>
          <button className="auth-btn" disabled={loading}>
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
