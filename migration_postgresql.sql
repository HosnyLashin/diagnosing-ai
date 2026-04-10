-- ══════════════════════════════════════════════════════════════════════════════
-- PostgreSQL Migration — Diagnosing AI
-- Run once after creating the Railway/Render PostgreSQL database
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS diseases (
    DiseaseID   SERIAL PRIMARY KEY,
    DiseaseName VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS symptoms (
    SymptomID   SERIAL PRIMARY KEY,
    SymptomName VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tests (
    TestID   SERIAL PRIMARY KEY,
    TestName VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS patients (
    PatientID           SERIAL PRIMARY KEY,
    Name                VARCHAR(255) NOT NULL,
    Email               VARCHAR(255) UNIQUE,
    PasswordHash        VARCHAR(255),
    IsVerified          BOOLEAN   DEFAULT FALSE,
    VerifyToken         VARCHAR(255),
    VerifyTokenExpires  TIMESTAMP,
    CreatedAt           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS disease_symptoms (
    DiseaseID INT REFERENCES diseases(DiseaseID),
    SymptomID INT REFERENCES symptoms(SymptomID),
    PRIMARY KEY (DiseaseID, SymptomID)
);

CREATE TABLE IF NOT EXISTS disease_tests (
    DiseaseID INT REFERENCES diseases(DiseaseID),
    TestID    INT REFERENCES tests(TestID),
    PRIMARY KEY (DiseaseID, TestID)
);

CREATE TABLE IF NOT EXISTS patient_symptoms (
    PatientID INT REFERENCES patients(PatientID),
    SymptomID INT REFERENCES symptoms(SymptomID),
    PRIMARY KEY (PatientID, SymptomID)
);

CREATE TABLE IF NOT EXISTS patient_tests (
    PatientID INT REFERENCES patients(PatientID),
    TestID    INT REFERENCES tests(TestID),
    PRIMARY KEY (PatientID, TestID)
);

CREATE TABLE IF NOT EXISTS diagnoses (
    DiagnosisID      SERIAL PRIMARY KEY,
    PatientID        INT REFERENCES patients(PatientID),
    PredictedDisease VARCHAR(255) NOT NULL,
    Confirmed        BOOLEAN   DEFAULT FALSE,
    CreatedAt        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
