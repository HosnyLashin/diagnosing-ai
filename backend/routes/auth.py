"""
routes/auth.py — Clean & complete (Flask Blueprint)
"""

import bcrypt
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_mail import Message
from sqlalchemy import text

import ai_engine

auth_bp = Blueprint("auth", __name__)

TOKEN_EXPIRY_HOURS = 24


# ================== HELPERS ==================

def _get_conn():
    return ai_engine.get_engine().connect()


def _send_verification_email(mail, email: str, name: str, token: str):
    verify_url = f"https://diagnosing-ai-production.up.railway.app/api/auth/verify-email?token={token}"

    msg = Message(
        subject="Verify your email",
        recipients=[email],
        html=f"""
        <p>Hi {name},</p>
        <p>Click below to verify your account:</p>
        <a href="{verify_url}">{verify_url}</a>
        <p>This expires in {TOKEN_EXPIRY_HOURS} hours.</p>
        """
    )
    mail.send(msg)


def _issue_verification_token(conn, patient_id: int):
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)

    conn.execute(text("""
        UPDATE patients
        SET verification_token = :t,
            verification_token_expires = :exp
        WHERE PatientID = :id
    """), {"t": token, "exp": expires, "id": patient_id})

    return token


# ================== ROUTES ==================

@auth_bp.post("/register")
def register():
    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password too short"}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        with _get_conn() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM patients WHERE Email=:e"),
                {"e": email}
            ).fetchone()

            if exists:
                return jsonify({"error": "Email already exists"}), 409

            result = conn.execute(text("""
                INSERT INTO patients (Name, Email, PasswordHash, is_verified)
                VALUES (:n, :e, :p, FALSE)
                RETURNING PatientID
            """), {"n": name, "e": email, "p": hashed})

            patient_id = result.fetchone()[0]

            token = _issue_verification_token(conn, patient_id)
            conn.commit()

        # IMPORTANT: pass mail from main.py
        from flask import current_app
        _send_verification_email(current_app.extensions["mail"], email, name, token)

        return jsonify({"message": "Registered. Check email."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.get("/verify-email")
def verify_email():
    token = request.args.get("token", "")

    if not token:
        return jsonify({"error": "Token required"}), 400

    try:
        with _get_conn() as conn:
            row = conn.execute(text("""
                SELECT PatientID, is_verified, verification_token_expires
                FROM patients
                WHERE verification_token=:t
            """), {"t": token}).fetchone()

            if not row:
                return jsonify({"error": "Invalid token"}), 400

            patient_id, is_verified, expires = row

            if is_verified:
                return jsonify({"message": "Already verified"}), 200

            if datetime.now(timezone.utc) > expires.replace(tzinfo=timezone.utc):
                return jsonify({"error": "Token expired"}), 400

            conn.execute(text("""
                UPDATE patients
                SET is_verified=TRUE,
                    verification_token=NULL,
                    verification_token_expires=NULL
                WHERE PatientID=:id
            """), {"id": patient_id})

            conn.commit()

        return jsonify({"message": "Email verified"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.post("/login")
def login():
    data = request.get_json()

    email = data.get("email", "").lower()
    password = data.get("password", "")

    try:
        with _get_conn() as conn:
            row = conn.execute(text("""
                SELECT PatientID, PasswordHash, is_verified
                FROM patients WHERE Email=:e
            """), {"e": email}).fetchone()

        if not row:
            return jsonify({"error": "Invalid credentials"}), 401

        patient_id, hashed, verified = row

        if not bcrypt.checkpw(password.encode(), hashed.encode()):
            return jsonify({"error": "Invalid credentials"}), 401

        if not verified:
            return jsonify({"error": "Verify email first"}), 403

        token = create_access_token(identity=str(patient_id))
        return jsonify({"token": token}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())

    try:
        with _get_conn() as conn:
            row = conn.execute(text("""
                SELECT Name, Email FROM patients WHERE PatientID=:id
            """), {"id": user_id}).fetchone()

        return jsonify({"name": row[0], "email": row[1]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
