"""
scraper.py
==========
Standalone scraper — run manually when you want to add new diseases.
NOT imported or called by app.py.

Usage:
    "D:\Diagnosing Ai\.venv\Scripts\python.exe" "D:\Diagnosing Ai\backend\scraper.py"

You can add or remove URLs from the URLS list at the bottom.
"""

import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── DB connection ─────────────────────────────────────────────────────────────
def get_engine():
    conn_str = os.getenv("DB_CONNECTION")
    if conn_str:
        return create_engine(conn_str)
    return create_engine(
        "mssql+pyodbc://@localhost/Diagnosing%20AI"
        "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    )


# ── normalise ─────────────────────────────────────────────────────────────────
def _normalise(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[,/]", " ", s)
    s = re.sub(r"-", " ", s)
    s = re.sub(r"\s+", "_", s)
    return s


# ── scraping ──────────────────────────────────────────────────────────────────
def _scrape_section(html: str, keywords: tuple) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for header in soup.find_all(["h2", "h3"]):
        if any(kw in header.text.lower() for kw in keywords):
            ul = header.find_next("ul")
            if ul:
                items.extend(li.text.strip() for li in ul.find_all("li"))
            else:
                p = header.find_next("p")
                if p:
                    items.append(p.text.strip())
            break
    return items


def _clean_symptoms(raw: list[str]) -> list[str]:
    skip = (
        "doctor", "call", "seek", "symptom", "early", "late", "common",
        "other", "more", "sign", "overview", "influenza", "type", "cause",
        "risk", "factor", "complication",
    )
    out = []
    for s in raw:
        s = s.lower().strip()
        if len(s) < 4 or len(s) > 60:
            continue
        if any(w in s for w in skip):
            continue
        out.append(_normalise(s))
    return list(dict.fromkeys(out))


def _clean_tests(raw: list[str]) -> list[str]:
    """
    Extract only short test names — strip full sentences.
    Strategy: split on punctuation, take only fragments that look like
    a test name (short, no verb-like words).
    """
    sentence_words = (
        "the ", "your ", "after ", "over ", "provides", "measures",
        "is used", "can be", "will ", "this ", "that ", "which ",
        "to ", "by ", "for ", "and ", "with ", "you ", "it ",
        "blood sugar", "snapshot", "fasted", "previous",
    )
    out = []
    for t in raw:
        t = t.lower().strip()

        # If it looks like a sentence, try to extract the test name from it
        # e.g. "The HbA1c test measures your blood sugar..." → "hba1c test"
        if any(w in t for w in sentence_words) or len(t) > 50:
            # Try to pull a short capitalised phrase before first verb
            # by taking only the first 1-4 words
            words = t.split()
            short = " ".join(words[:3]).strip(".()")
            if 3 <= len(short) <= 40 and not any(w in short for w in sentence_words):
                t = short
            else:
                continue   # skip — can't extract a clean name

        if len(t) < 3 or len(t) > 50:
            continue

        out.append(_normalise(t))
    return list(dict.fromkeys(out))


# ── DB helpers ────────────────────────────────────────────────────────────────
def _get_or_insert_disease_id(conn, disease: str) -> int:
    conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM diseases WHERE DiseaseName = :d)
        INSERT INTO diseases (DiseaseName) VALUES (:d)
    """), {"d": disease})
    return conn.execute(
        text("SELECT DiseaseID FROM diseases WHERE DiseaseName = :d"), {"d": disease}
    ).fetchone()[0]


def _get_or_insert_symptom_id(conn, symptom: str) -> int:
    conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM symptoms WHERE SymptomName = :s)
        INSERT INTO symptoms (SymptomName) VALUES (:s)
    """), {"s": symptom})
    return conn.execute(
        text("SELECT SymptomID FROM symptoms WHERE SymptomName = :s"), {"s": symptom}
    ).fetchone()[0]


def _get_or_insert_test_id(conn, test: str) -> int:
    conn.execute(text("""
        IF NOT EXISTS (SELECT 1 FROM tests WHERE TestName = :t)
        INSERT INTO tests (TestName) VALUES (:t)
    """), {"t": test})
    return conn.execute(
        text("SELECT TestID FROM tests WHERE TestName = :t"), {"t": test}
    ).fetchone()[0]


# ── main scrape function ──────────────────────────────────────────────────────
def scrape_disease(engine, url: str):
    print(f"\n🌐 Scraping: {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ❌ Failed to fetch: {e}")
        return

    disease  = url.rstrip("/").split("/")[-1].replace("-", " ").title()
    symptoms = _clean_symptoms(_scrape_section(resp.text, ("symptom",)))
    tests    = _clean_tests(_scrape_section(resp.text, ("diagnos", "test", "investigation", "exam")))

    print(f"  Disease  : {disease}")
    print(f"  Symptoms : {symptoms}")
    print(f"  Tests    : {tests}")

    if not symptoms and not tests:
        print("  ⚠️  Nothing found — skipping.")
        return

    with engine.connect() as conn:
        disease_id = _get_or_insert_disease_id(conn, disease)

        # Insert symptoms and link to disease
        for s in symptoms:
            sid = _get_or_insert_symptom_id(conn, s)
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT 1 FROM disease_symptoms
                    WHERE DiseaseID = :d AND SymptomID = :s
                )
                INSERT INTO disease_symptoms (DiseaseID, SymptomID) VALUES (:d, :s)
            """), {"d": disease_id, "s": sid})

        # Insert tests and link to disease
        for t in tests:
            tid = _get_or_insert_test_id(conn, t)
            conn.execute(text("""
                IF NOT EXISTS (
                    SELECT 1 FROM disease_tests
                    WHERE DiseaseID = :d AND TestID = :t
                )
                INSERT INTO disease_tests (DiseaseID, TestID) VALUES (:d, :t)
            """), {"d": disease_id, "t": tid})

        conn.commit()

    print(f"  ✅ Stored — {len(symptoms)} symptoms, {len(tests)} tests linked to '{disease}'")


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = get_engine()

    # Add or remove URLs here as needed
    URLS = [
        "https://www.healthline.com/health/diabetes",
        "https://www.healthline.com/health/flu-causes",
        "https://www.healthline.com/health/asthma",
        "https://www.healthline.com/health/hypertension",
        "https://www.healthline.com/health/migraine",
        "https://www.healthline.com/health/pneumonia",
        "https://www.healthline.com/health/gastroenteritis",
        "https://www.healthline.com/health/anemia",
        "https://www.healthline.com/health/urinary-tract-infection-adults",
        "https://www.healthline.com/health/heart-attack",
    ]

    print("=" * 60)
    print("DIAGNOSING AI — DISEASE SCRAPER")
    print("=" * 60)

    for url in URLS:
        scrape_disease(engine, url)

    print("\n✅ Scraping complete.")
