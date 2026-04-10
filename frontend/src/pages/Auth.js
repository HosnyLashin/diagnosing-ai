// src/pages/Login.js
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../api/AuthContext";
import "../styles/auth.css";

export function Login() {
  const { login } = useAuth();
  const navigate  = useNavigate();
  const [form,    setForm]  = useState({ email: "", password: "" });
  const [error,   setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🧬</div>
        <h1 className="auth-title">Diagnosing AI</h1>
        <p className="auth-subtitle">Sign in to your account</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handle} className="auth-form">
          <div className="field">
            <label>Email</label>
            <input
              type="email" required
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
            />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password" required
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
            />
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

// ─────────────────────────────────────────────────────────────────────────────

export function Register() {
  const { register } = useAuth();
  const navigate     = useNavigate();
  const [form,    setForm]  = useState({ name: "", email: "", password: "" });
  const [error,   setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register(form.name, form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

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
            <input
              type="text" required
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="Hosny Lashin"
            />
          </div>
          <div className="field">
            <label>Email</label>
            <input
              type="email" required
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com"
            />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password" required
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="Min. 8 characters"
            />
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
