"""
app.py
======
Flask application — single file, no blueprints.
All routes defined here directly.

Run locally:
    python app.py

Production (Render):
    gunicorn app:app --workers 1 --timeout 120
"""

import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import resend
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import text

import ai_engine

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── app setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["JWT_SECRET_KEY"]           = os.getenv("JWT_SECRET_KEY", "change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

CORS(app, resources={r"/api/*": {"origins": "*"}})
JWTManager(app)

resend.api_key = os.getenv("RESEND_API_KEY", "")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:3000")
FROM_EMAIL     = os.getenv("FROM_EMAIL", "noreply@diagnosingai.com")


# ── DB helper ─────────────────────────────────────────────────────────────────
def conn():
    return ai_engine.get_engine().connect()


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL HELPER
# ══════════════════════════════════════════════════════════════════════════════

def send_verification_email(to_email: str, name: str, token: str):
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    resend.Emails.send({
        "from":    FROM_EMAIL,
        "to":      to_email,
        "subject": "Verify your Diagnosing AI account",
        "html": f"""
        <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px">
            <h2 style="color:#2dd4bf">Diagnosing AI</h2>
            <p>Hi {name},</p>
            <p>Please verify your email address by clicking the button below.
               This link expires in <strong>24 hours</strong>.</p>
            <a href="{verify_url}"
               style="display:inline-block;margin:24px 0;padding:12px 28px;
                      background:#2dd4bf;color:#0d1117;border-radius:8px;
                      text-decoration:none;font-weight:bold">
                Verify Email
            </a>
            <p style="color:#888;font-size:13px">
                If you didn't create an account, ignore this email.<br>
                Link: {verify_url}
            </p>
        </div>
        """
    })


# ══════════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
def register():
    data     = request.get_json()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    token  = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)

    try:
        with conn() as c:
            exists = c.execute(
                text("SELECT 1 FROM patients WHERE Email = :e"), {"e": email}
            ).fetchone()
            if exists:
                return jsonify({"error": "An account with this email already exists."}), 409

            result = c.execute(text("""
                INSERT INTO patients (Name, Email, PasswordHash,
                                      VerifyToken, VerifyTokenExpires, IsVerified)
                VALUES (:n, :e, :p, :t, :x, FALSE)
                RETURNING PatientID
            """), {"n": name, "e": email, "p": hashed, "t": token, "x": expires})
            patient_id = result.fetchone()[0]
            c.commit()

        send_verification_email(email, name, token)

        return jsonify({
            "message": "Account created. Please check your email to verify your account.",
        }), 201

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.get("/api/auth/verify-email")
def verify_email():
    token = request.args.get("token", "")
    if not token:
        return jsonify({"error": "Token is required."}), 400

    try:
        with conn() as c:
            row = c.execute(text("""
                SELECT PatientID, VerifyTokenExpires, IsVerified
                FROM patients WHERE VerifyToken = :t
            """), {"t": token}).fetchone()

            if not row:
                return jsonify({"error": "Invalid verification link."}), 400

            patient_id, expires, is_verified = row

            if is_verified:
                return jsonify({"message": "Email already verified. You can log in."}), 200

            if datetime.now(timezone.utc) > expires.replace(tzinfo=timezone.utc):
                return jsonify({"error": "Verification link has expired. Please request a new one."}), 410

            c.execute(text("""
                UPDATE patients
                SET IsVerified = TRUE, VerifyToken = NULL, VerifyTokenExpires = NULL
                WHERE PatientID = :id
            """), {"id": patient_id})
            c.commit()

        return jsonify({"message": "Email verified successfully. You can now log in."}), 200

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.post("/api/auth/resend-verification")
def resend_verification():
    data  = request.get_json()
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    try:
        with conn() as c:
            row = c.execute(text("""
                SELECT PatientID, Name, IsVerified FROM patients WHERE Email = :e
            """), {"e": email}).fetchone()

            if not row:
                # Return success anyway to avoid email enumeration
                return jsonify({"message": "If that email exists, a new link has been sent."}), 200

            patient_id, name, is_verified = row

            if is_verified:
                return jsonify({"error": "This email is already verified."}), 400

            token   = secrets.token_urlsafe(32)
            expires = datetime.now(timezone.utc) + timedelta(hours=24)

            c.execute(text("""
                UPDATE patients
                SET VerifyToken = :t, VerifyTokenExpires = :x
                WHERE PatientID = :id
            """), {"t": token, "x": expires, "id": patient_id})
            c.commit()

        send_verification_email(email, name, token)
        return jsonify({"message": "A new verification email has been sent."}), 200

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.post("/api/auth/login")
def login():
    data     = request.get_json()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        with conn() as c:
            row = c.execute(text("""
                SELECT PatientID, Name, Email, PasswordHash, IsVerified
                FROM patients WHERE Email = :e
            """), {"e": email}).fetchone()

        if not row:
            return jsonify({"error": "Invalid email or password."}), 401

        patient_id, name, email_db, hashed, is_verified = row

        if not bcrypt.checkpw(password.encode(), hashed.encode()):
            return jsonify({"error": "Invalid email or password."}), 401

        if not is_verified:
            return jsonify({
                "error": "Please verify your email before logging in.",
                "unverified": True,
            }), 403

        token = create_access_token(identity=str(patient_id))
        return jsonify({
            "token": token,
            "user":  {"id": patient_id, "name": name, "email": email_db},
        }), 200

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.post("/api/auth/logout")
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully."}), 200


@app.get("/api/auth/me")
@jwt_required()
def me():
    patient_id = int(get_jwt_identity())
    try:
        with conn() as c:
            row = c.execute(text("""
                SELECT PatientID, Name, Email FROM patients WHERE PatientID = :id
            """), {"id": patient_id}).fetchone()
        if not row:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"id": row[0], "name": row[1], "email": row[2]}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# DIAGNOSIS ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/diagnosis/symptoms")
@jwt_required()
def list_symptoms():
    with conn() as c:
        symptoms = [
            r[0] for r in c.execute(
                text("SELECT SymptomName FROM symptoms ORDER BY SymptomName")
            ).fetchall()
        ]
    return jsonify({"symptoms": symptoms}), 200


@app.post("/api/diagnosis/symptoms")
@jwt_required()
def predict_symptoms():
    patient_id = int(get_jwt_identity())
    data       = request.get_json()
    symptoms   = data.get("symptoms", [])

    if not symptoms:
        return jsonify({"error": "Please select at least one symptom."}), 400

    try:
        result = ai_engine.predict_from_symptoms(symptoms)
        ai_engine.save_diagnosis(
            patient_id=patient_id,
            symptoms=symptoms,
            tests=[],
            prediction=result["prediction"],
            confirmed=data.get("confirmed", False),
        )
        return jsonify(result), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.post("/api/diagnosis/note")
@jwt_required()
def predict_note():
    patient_id = int(get_jwt_identity())
    data       = request.get_json()
    note       = data.get("note", "").strip()

    if not note:
        return jsonify({"error": "Clinical note cannot be empty."}), 400

    try:
        result = ai_engine.predict_from_note(note)
        if not result["resolved_symptoms"]:
            return jsonify({"error": "No recognisable symptoms found in the note."}), 422

        ai_engine.save_diagnosis(
            patient_id=patient_id,
            symptoms=result["resolved_symptoms"],
            tests=result["resolved_tests"],
            prediction=result["prediction"],
            confirmed=False,
        )
        return jsonify({
            "prediction":        result["prediction"],
            "probabilities":     result["probabilities"],
            "resolved_symptoms": result["resolved_symptoms"],
            "resolved_tests":    result["resolved_tests"],
        }), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.get("/api/diagnosis/history")
@jwt_required()
def history():
    patient_id = int(get_jwt_identity())
    try:
        with conn() as c:
            rows = c.execute(text("""
                SELECT
                    d.DiagnosisID,
                    d.PredictedDisease,
                    d.Confirmed,
                    d.CreatedAt,
                    STRING_AGG(DISTINCT s.SymptomName, ', ') AS Symptoms,
                    STRING_AGG(DISTINCT t.TestName,    ', ') AS Tests
                FROM diagnoses d
                LEFT JOIN patient_symptoms ps ON d.PatientID = ps.PatientID
                LEFT JOIN symptoms s          ON ps.SymptomID = s.SymptomID
                LEFT JOIN patient_tests pt    ON d.PatientID = pt.PatientID
                LEFT JOIN tests t             ON pt.TestID = t.TestID
                WHERE d.PatientID = :pid
                GROUP BY d.DiagnosisID, d.PredictedDisease, d.Confirmed, d.CreatedAt
                ORDER BY d.CreatedAt DESC
            """), {"pid": patient_id}).fetchall()

        return jsonify({"history": [
            {
                "id":        r[0],
                "disease":   r[1],
                "confirmed": bool(r[2]),
                "date":      r[3].isoformat() if r[3] else None,
                "symptoms":  r[4] or "",
                "tests":     r[5] or "",
            }
            for r in rows
        ]}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


@app.patch("/api/diagnosis/<int:diagnosis_id>/confirm")
@jwt_required()
def confirm_diagnosis(diagnosis_id):
    patient_id = int(get_jwt_identity())
    confirmed  = request.get_json().get("confirmed", False)

    try:
        with conn() as c:
            row = c.execute(
                text("SELECT PatientID FROM diagnoses WHERE DiagnosisID = :id"),
                {"id": diagnosis_id}
            ).fetchone()
            if not row or row[0] != patient_id:
                return jsonify({"error": "Diagnosis not found."}), 404

            c.execute(
                text("UPDATE diagnoses SET Confirmed = :c WHERE DiagnosisID = :id"),
                {"c": confirmed, "id": diagnosis_id}
            )
            c.commit()
        return jsonify({"message": "Diagnosis updated."}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK & ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint not found."}), 404

@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "Method not allowed."}), 405

@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error."}), 500


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP — lazy init so gunicorn doesn't time out on worker boot
# ══════════════════════════════════════════════════════════════════════════════

_initialised = False

@app.before_request
def initialise_once():
    global _initialised
    if not _initialised:
        _initialised = True
        ai_engine.initialise()

if __name__ == "__main__":
    app.run(debug=False, port=5000)
