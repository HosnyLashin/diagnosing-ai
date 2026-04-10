"""
ai_engine.py
============
All AI logic — NER, embedding resolver, dataset builder, RF model.
Imported by Flask routes. Stateful objects (model, resolver) are held as
module-level singletons so they are loaded once at startup.
Uses PostgreSQL-compatible SQL syntax.
"""

import os
import re
from collections import defaultdict

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text
from transformers import (
    AutoModel,
    AutoModelForTokenClassification,
    AutoTokenizer,
    pipeline,
)

# ── singletons ────────────────────────────────────────────────────────────────
_engine      = None
_ner         = None
_resolver    = None
_model       = None
_all_columns = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(os.getenv("DATABASE_URL"))
    return _engine


# ══════════════════════════════════════════════════════════════════════════════
# NER
# ══════════════════════════════════════════════════════════════════════════════

def load_ner_pipeline(model_name: str = "samrawal/bert-base-uncased_clinical-ner"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    return pipeline(
        task="ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=0 if torch.cuda.is_available() else -1,
    )


def extract_entities(note: str, ner_pipeline) -> dict:
    raw = ner_pipeline(note)
    symptoms, treatments, tests = [], [], []
    for ent in raw:
        label = ent["entity_group"].upper()
        entry = {
            "text":       ent["word"].strip(),
            "confidence": round(ent["score"], 3),
        }
        if "PROBLEM" in label:
            symptoms.append(entry)
        elif "TREATMENT" in label:
            treatments.append(entry)
        elif "TEST" in label:
            tests.append(entry)
    return {"symptoms": symptoms, "treatments": treatments, "tests": tests}


# ══════════════════════════════════════════════════════════════════════════════
# RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

class SymptomResolver:
    def __init__(
        self,
        encoder_name: str = "emilyalsentzer/Bio_ClinicalBERT",
        similarity_threshold: float = 0.82,
    ):
        self.threshold = similarity_threshold
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(encoder_name)
        self.encoder   = AutoModel.from_pretrained(encoder_name).to(self.device)
        self.encoder.eval()
        self._sym_names:       list[str]         = []
        self._sym_embeddings:  np.ndarray | None = None
        self._test_names:      list[str]         = []
        self._test_embeddings: np.ndarray | None = None

    def _embed(self, texts: list[str]) -> np.ndarray:
        encoded = self.tokenizer(
            texts, padding=True, truncation=True, max_length=64, return_tensors="pt"
        ).to(self.device)
        with torch.no_grad():
            output = self.encoder(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1).float()
        emb  = (output.last_hidden_state * mask).sum(1) / mask.sum(1)
        emb  = emb.cpu().numpy()
        return emb / np.clip(np.linalg.norm(emb, axis=1, keepdims=True), 1e-9, None)

    def _resolve(self, spans, names, embeddings, label):
        if embeddings is None or not spans:
            return []
        sim     = self._embed(spans) @ embeddings.T
        matched = []
        for i, span in enumerate(spans):
            best_idx   = int(np.argmax(sim[i]))
            best_score = float(sim[i, best_idx])
            if best_score >= self.threshold:
                matched.append(names[best_idx])
        return list(dict.fromkeys(matched))

    def build_symptom_index(self, db_symptoms):
        self._sym_names      = db_symptoms
        self._sym_embeddings = self._embed([s.replace("_", " ") for s in db_symptoms])

    def build_test_index(self, db_tests):
        self._test_names      = db_tests
        self._test_embeddings = self._embed([t.replace("_", " ") for t in db_tests]) if db_tests else None

    def resolve_symptoms(self, spans):
        return self._resolve(spans, self._sym_names, self._sym_embeddings, "symptom")

    def resolve_tests(self, spans):
        return self._resolve(spans, self._test_names, self._test_embeddings, "test")


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — PostgreSQL compatible
# ══════════════════════════════════════════════════════════════════════════════

def _normalise(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[,/]", " ", s)
    s = re.sub(r"-", " ", s)
    s = re.sub(r"\s+", "_", s)
    return s


def _get_or_insert_disease_id(conn, disease: str) -> int:
    conn.execute(text("""
        INSERT INTO diseases (DiseaseName)
        VALUES (:d)
        ON CONFLICT (DiseaseName) DO NOTHING
    """), {"d": disease})
    return conn.execute(
        text("SELECT DiseaseID FROM diseases WHERE DiseaseName = :d"), {"d": disease}
    ).fetchone()[0]


def _get_or_insert_symptom(conn, symptom: str) -> int:
    conn.execute(text("""
        INSERT INTO symptoms (SymptomName)
        VALUES (:s)
        ON CONFLICT (SymptomName) DO NOTHING
    """), {"s": symptom})
    return conn.execute(
        text("SELECT SymptomID FROM symptoms WHERE SymptomName = :s"), {"s": symptom}
    ).fetchone()[0]


def _get_or_insert_test(conn, test: str) -> int:
    conn.execute(text("""
        INSERT INTO tests (TestName)
        VALUES (:t)
        ON CONFLICT (TestName) DO NOTHING
    """), {"t": test})
    return conn.execute(
        text("SELECT TestID FROM tests WHERE TestName = :t"), {"t": test}
    ).fetchone()[0]


# ══════════════════════════════════════════════════════════════════════════════
# DATASET & TRAINING
# ══════════════════════════════════════════════════════════════════════════════

def build_and_train():
    """Build dataset and train model. Returns (model, columns)."""
    engine = get_engine()
    with engine.connect() as conn:
        all_symptoms = [r[0] for r in conn.execute(text("SELECT SymptomName FROM symptoms")).fetchall()]
        patient_rows = conn.execute(text("""
            SELECT d.PredictedDisease, s.SymptomName
            FROM diagnoses d
            JOIN patient_symptoms ps ON d.PatientID = ps.PatientID
            JOIN symptoms s ON ps.SymptomID = s.SymptomID
            WHERE d.Confirmed = 1
        """)).fetchall()
        scraped_rows = conn.execute(text("""
            SELECT d.DiseaseName, s.SymptomName
            FROM disease_symptoms ds
            JOIN diseases d ON ds.DiseaseID = d.DiseaseID
            JOIN symptoms s ON ds.SymptomID = s.SymptomID
        """)).fetchall()

    disease_dict = defaultdict(list)
    for disease, symptom in patient_rows:
        disease_dict[disease].append(symptom)
    for disease, symptom in scraped_rows:
        if disease not in disease_dict:
            disease_dict[disease].append(symptom)

    rows = [
        {sym: int(sym in set(syms)) for sym in all_symptoms} | {"Disease": disease}
        for disease, syms in disease_dict.items()
    ]
    df = pd.DataFrame(rows, columns=all_symptoms + ["Disease"])

    X = df.drop("Disease", axis=1).astype(int)
    y = df["Disease"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if y.nunique() > 1 and y.value_counts().min() >= 2 else None
    )
    model = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    print(f"✅ Model trained — accuracy: {accuracy:.3f}")
    return model, list(X.columns)


def get_all_tests() -> list[str]:
    with get_engine().connect() as conn:
        return [r[0] for r in conn.execute(text("SELECT TestName FROM tests")).fetchall()]


# ══════════════════════════════════════════════════════════════════════════════
# PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

def predict_from_symptoms(symptom_list: list[str]) -> dict:
    global _model, _all_columns
    s = set(symptom_list)
    vec = pd.DataFrame([[int(col in s) for col in _all_columns]], columns=_all_columns)
    prediction = _model.predict(vec)[0]
    probs = _model.predict_proba(vec)[0]
    probabilities = {
        disease: round(float(prob) * 100, 2)
        for disease, prob in zip(_model.classes_, probs)
        if prob > 0.01
    }
    return {"prediction": prediction, "probabilities": probabilities}


def predict_from_note(note: str) -> dict:
    global _ner, _resolver
    entities = extract_entities(note, _ner)
    symptoms = _resolver.resolve_symptoms([e["text"] for e in entities["symptoms"]])
    tests    = _resolver.resolve_tests([e["text"] for e in entities["tests"]])
    result   = predict_from_symptoms(symptoms)
    result["resolved_symptoms"] = symptoms
    result["resolved_tests"]    = tests
    result["raw_entities"]      = entities
    return result


# ══════════════════════════════════════════════════════════════════════════════
# PATIENT RECORD SAVING
# ══════════════════════════════════════════════════════════════════════════════

def save_diagnosis(patient_id: int, symptoms: list[str], tests: list[str],
                   prediction: str, confirmed: bool):
    engine = get_engine()
    with engine.connect() as conn:
        for symptom in symptoms:
            sid = _get_or_insert_symptom(conn, symptom)
            conn.execute(text("""
                INSERT INTO patient_symptoms (PatientID, SymptomID)
                VALUES (:p, :s)
                ON CONFLICT (PatientID, SymptomID) DO NOTHING
            """), {"p": patient_id, "s": sid})

        for test in tests:
            tid = _get_or_insert_test(conn, test)
            conn.execute(text("""
                INSERT INTO patient_tests (PatientID, TestID)
                VALUES (:p, :t)
                ON CONFLICT (PatientID, TestID) DO NOTHING
            """), {"p": patient_id, "t": tid})

        conn.execute(
            text("INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES (:p, :d, :c)"),
            {"p": patient_id, "d": prediction, "c": confirmed}
        )
        conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP
# ══════════════════════════════════════════════════════════════════════════════

def initialise():
    global _ner, _resolver, _model, _all_columns

    print("🔄 Loading NER model...")
    _ner = load_ner_pipeline()

    print("🔄 Training RF model...")
    _model, _all_columns = build_and_train()

    print("🔄 Loading embedding resolver...")
    _resolver = SymptomResolver()
    _resolver.build_symptom_index(_all_columns)
    _resolver.build_test_index(get_all_tests())

    print("✅ AI engine ready.")
