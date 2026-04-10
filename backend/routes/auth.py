"""
routes/auth.py
==============
POST /api/auth/register  — create account
POST /api/auth/login     — returns JWT access token
POST /api/auth/logout    — client-side token discard (stateless JWT)
GET  /api/auth/me        — return current user info
"""

import bcrypt
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy import text

import ai_engine

auth_bp = Blueprint("auth", __name__)


def _get_conn():
    return ai_engine.get_engine().connect()


@auth_bp.post("/register")
def register():
    data = request.get_json()
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

            conn.execute(text("""
                INSERT INTO patients (Name, Email, PasswordHash)
                VALUES (:n, :e, :p)
            """), {"n": name, "e": email, "p": hashed})
            conn.commit()

            patient_id = conn.execute(
                text("SELECT TOP 1 PatientID FROM patients ORDER BY PatientID DESC")
            ).fetchone()[0]

        token = create_access_token(identity=str(patient_id))
        return jsonify({
            "message": "Account created successfully.",
            "token":   token,
            "user":    {"id": patient_id, "name": name, "email": email},
        }), 201

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
                text("SELECT PatientID, Name, Email, PasswordHash FROM patients WHERE Email = :e"),
                {"e": email}
            ).fetchone()

        if not row:
            return jsonify({"error": "Invalid email or password."}), 401

        patient_id, name, email_db, hashed = row

        if not bcrypt.checkpw(password.encode(), hashed.encode()):
            return jsonify({"error": "Invalid email or password."}), 401

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
    # JWT is stateless — client simply discards the token
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
