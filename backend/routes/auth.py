"""
routes/auth.py — PostgreSQL compatible
"""

import bcrypt
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_mail import Mail, Message
from sqlalchemy import text
import os

import ai_engine

auth_bp = Blueprint("auth", __name__)
mail = Mail()

TOKEN_EXPIRY_HOURS = 24


def _get_conn():
    return ai_engine.get_engine().connect()


def _send_verification_email(email: str, name: str, token: str):
    """Send a verification email with a unique token link."""
    base_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "yourapp.com")
    verify_url = f"https://{base_url}/api/auth/verify-email?token={token}"
    msg = Message(
        subject="Verify your email address",
        recipients=[email],
        html=f"""
            <p>Hi {name},</p>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verify_url}">{verify_url}</a></p>
            <p>This link will expire in {TOKEN_EXPIRY_HOURS} hours.</p>
            <p>If you did not create an account, you can ignore this email.</p>
        """,
    )
    mail.send(msg)


def _issue_verification_token(conn, patient_id: int) -> str:
    """Generate a fresh token + expiry and persist it, then return the token."""
    token   = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)
    conn.execute(text("""
        UPDATE patients
        SET verification_token = :t, verification_token_expires = :exp
        WHERE PatientID = :id
    """), {"t": token, "exp": expires, "id": patient_id})
    return token


@auth_bp.post("/register")
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

    try:
        with _get_conn() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM patients WHERE Email = :e"), {"e": email}
            ).fetchone()
            if exists:
                return jsonify({"error": "An account with this email already exists."}), 409

            result = conn.execute(text("""
                INSERT INTO patients (Name, Email, PasswordHash, is_verified)
                VALUES (:n, :e, :p, FALSE)
                RETURNING PatientID
            """), {"n": name, "e": email, "p": hashed})
            patient_id = result.fetchone()[0]

            token = _issue_verification_token(conn, patient_id)
            conn.commit()

        _send_verification_email(email, name, token)

        return jsonify({
            "message": "Account created successfully. Please check your email to verify your account.",
            "user":    {"id": patient_id, "name": name, "email": email},
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.get("/verify-email")
def verify_email():
    token = request.args.get("token", "").strip()

    if not token:
        return jsonify({"error": "Verification token is required."}), 400

    try:
        with _get_conn() as conn:
            row = conn.execute(
                text("""
                    SELECT PatientID, is_verified, verification_token_expires
                    FROM patients
                    WHERE verification_token = :t
                """),
                {"t": token}
            ).fetchone()

            if not row:
                return jsonify({"error": "Invalid verification token."}), 400

            patient_id, is_verified, expires = row

            if is_verified:
                return jsonify({"message": "Email is already verified. You can log in."}), 200

            if datetime.now(timezone.utc) > expires.replace(tzinfo=timezone.utc):
                return jsonify({
                    "error": "Verification token has expired. Please request a new one.",
                    "resend": True,
                }), 400

            conn.execute(text("""
                UPDATE patients
                SET is_verified = TRUE,
                    verification_token = NULL,
                    verification_token_expires = NULL
                WHERE PatientID = :id
            """), {"id": patient_id})
            conn.commit()

        return jsonify({"message": "Email verified successfully. You can now log in."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.post("/resend-verification")
def resend_verification():
    data  = request.get_json()
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required."}), 400

    try:
        with _get_conn() as conn:
            row = conn.execute(
                text("SELECT PatientID, Name, is_verified FROM patients WHERE Email = :e"),
                {"e": email}
            ).fetchone()

            if not row:
                return jsonify({"message": "If that email is registered, a new verification link has been sent."}), 200

            patient_id, name, is_verified = row

            if is_verified:
                return jsonify({"message": "This account is already verified. You can log in."}), 200

            token = _issue_verification_token(conn, patient_id)
            conn.commit()

        _send_verification_email(email, name, token)

        return jsonify({"message": "A new verification email has been sent. Please check your inbox."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.post("/login")
def login():
    data     = request.get_json()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        with _get_conn() as conn:
            row = conn.execute(
                text("SELECT PatientID, Name, Email, PasswordHash, is_verified FROM patients WHERE Email = :e"),
                {"e": email}
            ).fetchone()

        if not row:
            return jsonify({"error": "Invalid email or password."}), 401

        patient_id, name, email_db, hashed, is_verified = row

        if not bcrypt.checkpw(password.encode(), hashed.encode()):
            return jsonify({"error": "Invalid email or password."}), 401

        if not is_verified:
            return jsonify({
                "error":  "Please verify your email address before logging in.",
                "resend": True,
            }), 403

        token = create_access_token(identity=str(patient_id))
        return jsonify({
            "token": token,
            "user":  {"id": patient_id, "name": name, "email": email_db},
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.post("/logout")
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    patient_id = int(get_jwt_identity())
    try:
        with _get_conn() as conn:
            row = conn.execute(
                text("SELECT PatientID, Name, Email FROM patients WHERE PatientID = :id"),
                {"id": patient_id}
            ).fetchone()
        if not row:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"id": row[0], "name": row[1], "email": row[2]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
