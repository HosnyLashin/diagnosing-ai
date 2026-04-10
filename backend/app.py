"""
app.py
======
Flask application factory and entry point.

Run locally:
    python app.py

Production (Railway/Render):
    gunicorn app:app
"""

import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

import ai_engine
from routes.auth import auth_bp
from routes.diagnosis import diag_bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    # ── config ────────────────────────────────────────────────────────────────
    app.config["JWT_SECRET_KEY"]        = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

    # ── extensions ────────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})   # tighten origins in production
    JWTManager(app)

    # ── blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(diag_bp, url_prefix="/api/diagnosis")

    # ── health check ──────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ── global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Internal server error."}), 500

    return app


# ── startup ───────────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    ai_engine.initialise()          # load models once before serving requests
    app.run(debug=False, port=5000)
