"""
routes/diagnosis.py — PostgreSQL compatible
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import text

import ai_engine

diag_bp = Blueprint("diagnosis", __name__)


def _get_conn():
    return ai_engine.get_engine().connect()


@diag_bp.get("/symptoms")
@jwt_required()
def list_symptoms():
    with _get_conn() as conn:
        symptoms = [
            r[0] for r in conn.execute(text("SELECT SymptomName FROM symptoms ORDER BY SymptomName")).fetchall()
        ]
    return jsonify({"symptoms": symptoms}), 200


@diag_bp.post("/symptoms")
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@diag_bp.post("/note")
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@diag_bp.get("/history")
@jwt_required()
def history():
    patient_id = int(get_jwt_identity())
    try:
        with _get_conn() as conn:
            rows = conn.execute(text("""
                SELECT
                    d.DiagnosisID,
                    d.PredictedDisease,
                    d.Confirmed,
                    d.CreatedAt,
                    STRING_AGG(DISTINCT s.SymptomName::text, ', ') AS Symptoms,
                    STRING_AGG(DISTINCT t.TestName::text,    ', ') AS Tests
                FROM diagnoses d
                LEFT JOIN patient_symptoms ps ON d.PatientID = ps.PatientID
                LEFT JOIN symptoms s          ON ps.SymptomID = s.SymptomID
                LEFT JOIN patient_tests pt    ON d.PatientID = pt.PatientID
                LEFT JOIN tests t             ON pt.TestID = t.TestID
                WHERE d.PatientID = :pid
                GROUP BY d.DiagnosisID, d.PredictedDisease, d.Confirmed, d.CreatedAt
                ORDER BY d.CreatedAt DESC
            """), {"pid": patient_id}).fetchall()

        history = [
            {
                "id":        row[0],
                "disease":   row[1],
                "confirmed": bool(row[2]),
                "date":      row[3].isoformat() if row[3] else None,
                "symptoms":  row[4] or "",
                "tests":     row[5] or "",
            }
            for row in rows
        ]
        return jsonify({"history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@diag_bp.patch("/<int:diagnosis_id>/confirm")
@jwt_required()
def confirm_diagnosis(diagnosis_id: int):
    patient_id = int(get_jwt_identity())
    data       = request.get_json()
    confirmed  = data.get("confirmed", False)

    try:
        with _get_conn() as conn:
            row = conn.execute(
                text("SELECT PatientID FROM diagnoses WHERE DiagnosisID = :id"),
                {"id": diagnosis_id}
            ).fetchone()
            if not row or row[0] != patient_id:
                return jsonify({"error": "Diagnosis not found."}), 404

            conn.execute(
                text("UPDATE diagnoses SET Confirmed = :c WHERE DiagnosisID = :id"),
                {"c": confirmed, "id": diagnosis_id}
            )
            conn.commit()

        return jsonify({"message": "Diagnosis updated."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
