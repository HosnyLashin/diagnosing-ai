-- ══════════════════════════════════════════════════════════════════════════════
-- TEST PATIENTS SEED DATA — Diagnosing AI
-- 20 patients with confirmed diagnoses covering all 10 diseases
-- Run AFTER seed_data.sql
-- ══════════════════════════════════════════════════════════════════════════════

-- ── PATIENTS ─────────────────────────────────────────────────────────────────
INSERT INTO patients (Name, Email, PasswordHash) VALUES
('Ahmed Hassan',      'ahmed@test.com',   'hashed'),
('Sara Mohamed',      'sara@test.com',    'hashed'),
('Omar Ali',          'omar@test.com',    'hashed'),
('Nour Ibrahim',      'nour@test.com',    'hashed'),
('Karim Youssef',     'karim@test.com',   'hashed'),
('Layla Mahmoud',     'layla@test.com',   'hashed'),
('Tarek Samir',       'tarek@test.com',   'hashed'),
('Hana Adel',         'hana@test.com',    'hashed'),
('Youssef Nasser',    'youssef@test.com', 'hashed'),
('Mona Khalil',       'mona@test.com',    'hashed'),
('Amr Farouk',        'amr@test.com',     'hashed'),
('Dina Sayed',        'dina@test.com',    'hashed'),
('Khaled Gamal',      'khaled@test.com',  'hashed'),
('Rania Fawzy',       'rania@test.com',   'hashed'),
('Sherif Tawfik',     'sherif@test.com',  'hashed'),
('Nadia Helmy',       'nadia@test.com',   'hashed'),
('Mostafa Ezzat',     'mostafa@test.com', 'hashed'),
('Yasmine Lotfy',     'yasmine@test.com', 'hashed'),
('Bassem Ragab',      'bassem@test.com',  'hashed'),
('Iman Wagdy',        'iman@test.com',    'hashed');

-- ── DIAGNOSES (Confirmed = 1) ─────────────────────────────────────────────────
-- 2 patients per disease

-- Diabetes (patients 1, 2)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(1,  'Diabetes', 1),
(2,  'Diabetes', 1);

-- Influenza (patients 3, 4)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(3,  'Influenza', 1),
(4,  'Influenza', 1);

-- Hypertension (patients 5, 6)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(5,  'Hypertension', 1),
(6,  'Hypertension', 1);

-- Pneumonia (patients 7, 8)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(7,  'Pneumonia', 1),
(8,  'Pneumonia', 1);

-- Asthma (patients 9, 10)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(9,  'Asthma', 1),
(10, 'Asthma', 1);

-- Migraine (patients 11, 12)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(11, 'Migraine', 1),
(12, 'Migraine', 1);

-- Gastroenteritis (patients 13, 14)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(13, 'Gastroenteritis', 1),
(14, 'Gastroenteritis', 1);

-- Anemia (patients 15, 16)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(15, 'Anemia', 1),
(16, 'Anemia', 1);

-- UTI (patients 17, 18)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(17, 'Urinary Tract Infection', 1),
(18, 'Urinary Tract Infection', 1);

-- Acute MI (patients 19, 20)
INSERT INTO diagnoses (PatientID, PredictedDisease, Confirmed) VALUES
(19, 'Acute Myocardial Infarction', 1),
(20, 'Acute Myocardial Infarction', 1);

-- ── PATIENT_SYMPTOMS ──────────────────────────────────────────────────────────

-- Patient 1 — Diabetes
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 1, SymptomID FROM symptoms
WHERE SymptomName IN ('increased_thirst','frequent_urination','extreme_fatigue','blurry_vision','increased_hunger');

-- Patient 2 — Diabetes
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 2, SymptomID FROM symptoms
WHERE SymptomName IN ('unexplained_weight_loss','frequent_urination','slow_healing_sores','extreme_fatigue','blurry_vision');

-- Patient 3 — Influenza
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 3, SymptomID FROM symptoms
WHERE SymptomName IN ('fever','chills','muscle_aches','headache','dry_cough','extreme_fatigue');

-- Patient 4 — Influenza
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 4, SymptomID FROM symptoms
WHERE SymptomName IN ('fever','sore_throat','runny_nose','muscle_aches','chills','headache');

-- Patient 5 — Hypertension
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 5, SymptomID FROM symptoms
WHERE SymptomName IN ('severe_headache','chest_pain','dizziness','nosebleed','blurred_vision');

-- Patient 6 — Hypertension
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 6, SymptomID FROM symptoms
WHERE SymptomName IN ('shortness_of_breath','severe_headache','dizziness','blurred_vision','chest_pain');

-- Patient 7 — Pneumonia
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 7, SymptomID FROM symptoms
WHERE SymptomName IN ('productive_cough','high_fever','sharp_chest_pain','rapid_breathing','sweating');

-- Patient 8 — Pneumonia
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 8, SymptomID FROM symptoms
WHERE SymptomName IN ('high_fever','shortness_of_breath','productive_cough','loss_of_appetite','chest_pain');

-- Patient 9 — Asthma
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 9, SymptomID FROM symptoms
WHERE SymptomName IN ('wheezing','chest_tightness','difficulty_breathing','coughing_at_night','shortness_of_breath');

-- Patient 10 — Asthma
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 10, SymptomID FROM symptoms
WHERE SymptomName IN ('wheezing','shortness_of_breath','chest_tightness','coughing_at_night');

-- Patient 11 — Migraine
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 11, SymptomID FROM symptoms
WHERE SymptomName IN ('throbbing_headache','nausea','sensitivity_to_light','sensitivity_to_sound','visual_aura');

-- Patient 12 — Migraine
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 12, SymptomID FROM symptoms
WHERE SymptomName IN ('throbbing_headache','vomiting','sensitivity_to_light','dizziness','nausea');

-- Patient 13 — Gastroenteritis
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 13, SymptomID FROM symptoms
WHERE SymptomName IN ('diarrhea','nausea','vomiting','stomach_cramps','low_grade_fever');

-- Patient 14 — Gastroenteritis
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 14, SymptomID FROM symptoms
WHERE SymptomName IN ('watery_stool','stomach_cramps','nausea','loss_of_appetite','low_grade_fever');

-- Patient 15 — Anemia
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 15, SymptomID FROM symptoms
WHERE SymptomName IN ('extreme_fatigue','pale_skin','weakness','dizziness','shortness_of_breath');

-- Patient 16 — Anemia
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 16, SymptomID FROM symptoms
WHERE SymptomName IN ('weakness','cold_hands_and_feet','irregular_heartbeat','brittle_nails','pale_skin');

-- Patient 17 — UTI
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 17, SymptomID FROM symptoms
WHERE SymptomName IN ('burning_urination','frequent_urge_to_urinate','cloudy_urine','pelvic_pain','low_grade_fever');

-- Patient 18 — UTI
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 18, SymptomID FROM symptoms
WHERE SymptomName IN ('strong_urine_odor','burning_urination','cloudy_urine','frequent_urge_to_urinate','pelvic_pain');

-- Patient 19 — Acute MI
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 19, SymptomID FROM symptoms
WHERE SymptomName IN ('crushing_chest_pain','pain_radiating_to_arm','cold_sweat','sudden_dizziness','shortness_of_breath');

-- Patient 20 — Acute MI
INSERT INTO patient_symptoms (PatientID, SymptomID)
SELECT 20, SymptomID FROM symptoms
WHERE SymptomName IN ('crushing_chest_pain','pain_radiating_to_jaw','sudden_nausea','cold_sweat','shortness_of_breath');

-- ── PATIENT_TESTS ─────────────────────────────────────────────────────────────

INSERT INTO patient_tests (PatientID, TestID)
SELECT 1, TestID FROM tests WHERE TestName IN ('fasting_blood_glucose','hba1c');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 2, TestID FROM tests WHERE TestName IN ('fasting_blood_glucose','hba1c','complete_blood_count');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 3, TestID FROM tests WHERE TestName IN ('rapid_influenza_test','complete_blood_count');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 4, TestID FROM tests WHERE TestName IN ('rapid_influenza_test');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 5, TestID FROM tests WHERE TestName IN ('blood_pressure_measurement','ecg');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 6, TestID FROM tests WHERE TestName IN ('blood_pressure_measurement','echocardiogram');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 7, TestID FROM tests WHERE TestName IN ('chest_xray','sputum_culture','complete_blood_count');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 8, TestID FROM tests WHERE TestName IN ('chest_xray','blood_culture','arterial_blood_gas');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 9, TestID FROM tests WHERE TestName IN ('spirometry','peak_flow_test');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 10, TestID FROM tests WHERE TestName IN ('spirometry','chest_xray');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 11, TestID FROM tests WHERE TestName IN ('mri_brain');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 12, TestID FROM tests WHERE TestName IN ('ct_scan','mri_brain');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 13, TestID FROM tests WHERE TestName IN ('stool_test','complete_blood_count');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 14, TestID FROM tests WHERE TestName IN ('stool_test');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 15, TestID FROM tests WHERE TestName IN ('complete_blood_count','serum_ferritin');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 16, TestID FROM tests WHERE TestName IN ('complete_blood_count','serum_ferritin');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 17, TestID FROM tests WHERE TestName IN ('urinalysis','urine_culture');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 18, TestID FROM tests WHERE TestName IN ('urinalysis','urine_culture');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 19, TestID FROM tests WHERE TestName IN ('ecg','troponin','echocardiogram');

INSERT INTO patient_tests (PatientID, TestID)
SELECT 20, TestID FROM tests WHERE TestName IN ('ecg','troponin','chest_xray');

-- ── VERIFY ────────────────────────────────────────────────────────────────────
SELECT 'Patients'         AS [Table], COUNT(*) AS [Count] FROM patients
UNION ALL
SELECT 'Diagnoses',        COUNT(*) FROM diagnoses
UNION ALL
SELECT 'Patient-Symptoms', COUNT(*) FROM patient_symptoms
UNION ALL
SELECT 'Patient-Tests',    COUNT(*) FROM patient_tests;
