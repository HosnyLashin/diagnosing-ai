// src/pages/Dashboard.js
import { useAuth } from "../api/AuthContext";
import { Link } from "react-router-dom";
import "../styles/dashboard.css";

export default function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard">
      <header className="dash-header">
        <div className="dash-brand">🧬 Diagnosing AI</div>
        <div className="dash-user">
          <span>{user?.name}</span>
          <button className="logout-btn" onClick={logout}>Sign Out</button>
        </div>
      </header>

      <main className="dash-main">
        <div className="dash-welcome">
          <h1>Welcome back, {user?.name?.split(" ")[0]} 👋</h1>
          <p>What would you like to do today?</p>
        </div>

        <div className="dash-cards">
          <Link to="/diagnose" className="dash-card">
            <div className="card-icon">🩺</div>
            <h2>Check Symptoms</h2>
            <p>Select your symptoms from a list and get an AI-powered diagnosis prediction.</p>
          </Link>

          <Link to="/note" className="dash-card">
            <div className="card-icon">📋</div>
            <h2>Enter Clinical Note</h2>
            <p>Paste a clinical note or describe your condition in your own words.</p>
          </Link>

          <Link to="/history" className="dash-card">
            <div className="card-icon">📊</div>
            <h2>My History</h2>
            <p>View all your previous diagnoses and their outcomes.</p>
          </Link>
        </div>

        <div className="dash-disclaimer">
          ⚠️ This tool is for educational purposes only and is not a substitute
          for professional medical advice, diagnosis, or treatment.
        </div>
      </main>
    </div>
  );
}
