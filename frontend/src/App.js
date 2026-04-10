// src/App.js
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./api/AuthContext";
import { Login, Register } from "./pages/Auth";
import Dashboard   from "./pages/Dashboard";
import Diagnose    from "./pages/Diagnose";
import History     from "./pages/History";
import Note        from "./pages/Note";
import VerifyEmail from "./pages/VerifyEmail";
import "./styles/global.css";

function Private({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

function Public({ children }) {
  const { user } = useAuth();
  return !user ? children : <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login"         element={<Public><Login /></Public>} />
          <Route path="/register"      element={<Public><Register /></Public>} />
          <Route path="/verify-email"  element={<VerifyEmail />} />

          {/* Protected */}
          <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
          <Route path="/diagnose"  element={<Private><Diagnose /></Private>} />
          <Route path="/note"      element={<Private><Note /></Private>} />
          <Route path="/history"   element={<Private><History /></Private>} />

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
