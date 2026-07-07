"""
migrate_synthetic_v2_postgres.py
──────────────────────────────────
Loads synthetic_data_v2/*.csv (generate_historical_data_v2.py +
seed_weekly_surge_data_v2.py) into Postgres. Mirrors migrate_csv_postgres.py's
delete-then-bulk-insert pattern exactly, just pointed at the new v2 output
directory instead of db_dump/.

IMPORTANT: like migrate_csv_postgres.py, this clears the patients /
medical_records / ayush_treatments / treatment_feedbacks tables before
loading. That's necessary here specifically to replace whatever the *old*
generator (generate_historical_data.py) already wrote - loading the v2 data
on top of the old rows would leave the fixed-pincode/duplicate-diagnosis
patterns this v2 pass exists to fix still mixed into the live tables. It does
NOT touch db_dump/*.csv or any other file on disk.

Run from backend/ (after generate_historical_data_v2.py and, optionally,
seed_weekly_surge_data_v2.py):
    ./venv/bin/python3.11 migrate_synthetic_v2_postgres.py
"""
import os

import pandas as pd
from sqlalchemy.orm import sessionmaker

from models import init_db, Patient, MedicalRecord, AyushTreatment, TreatmentFeedback, engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DATA_DIR = os.path.join(os.path.dirname(__file__), "synthetic_data_v2")
PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
MEDICAL_RECORDS_CSV = os.path.join(DATA_DIR, "medical_records.csv")
AYUSH_TREATMENTS_CSV = os.path.join(DATA_DIR, "ayush_treatments.csv")
TREATMENT_FEEDBACK_CSV = os.path.join(DATA_DIR, "treatment_feedback.csv")


def run_migration() -> None:
    if not os.path.exists(PATIENTS_CSV):
        print(f"ERROR: {PATIENTS_CSV} not found. Run generate_historical_data_v2.py first.")
        return

    print("Initializing Database...")
    init_db()
    session = SessionLocal()

    print("Clearing existing patients / medical_records / ayush_treatments / treatment_feedbacks...")
    try:
        session.query(TreatmentFeedback).delete()
        session.query(AyushTreatment).delete()
        session.query(MedicalRecord).delete()
        session.query(Patient).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error clearing existing data: {e}")

    # 1. Patients
    print("Migrating Patients...")
    df_p = pd.read_csv(PATIENTS_CSV)
    for _, row in df_p.iterrows():
        age_val = row.get("age")
        try:
            age_val = int(age_val) if not pd.isna(age_val) and str(age_val).strip() else None
        except Exception:
            age_val = None

        p = Patient(
            id=str(row.get("id")),
            first_name=str(row.get("first_name", "")),
            last_name=str(row.get("last_name", "")),
            gender=str(row.get("gender", "")),
            age=age_val,
            marital_status=str(row.get("marital_status", "")),
            mobile=str(row.get("mobile", "")),
            address=str(row.get("address", "")),
            city=str(row.get("city", "")),
            state=str(row.get("state", "")),
            pincode=str(row.get("pincode", "")),
            blood_group=str(row.get("blood_group", "")) if not pd.isna(row.get("blood_group")) else "",
            occupation=str(row.get("occupation", "")) if not pd.isna(row.get("occupation")) else "",
            id_type=str(row.get("id_type", "")),
            id_number=str(row.get("id_number", "")),
            diagnosis_done=str(row.get("diagnosis_done", "False")) == "True",
        )
        if not pd.isna(row.get("created_at")):
            p.created_at = pd.to_datetime(row.get("created_at")).to_pydatetime()
        if not pd.isna(row.get("updated_at")):
            p.updated_at = pd.to_datetime(row.get("updated_at")).to_pydatetime()
        session.add(p)
    session.commit()

    # 2. Medical Records
    if os.path.exists(MEDICAL_RECORDS_CSV):
        print("Migrating Medical Records...")
        df_m = pd.read_csv(MEDICAL_RECORDS_CSV)

        def _int_or_none(v):
            try:
                return int(v) if not pd.isna(v) and str(v).strip() else None
            except Exception:
                return None

        def _float_or_none(v):
            try:
                return float(v) if not pd.isna(v) and str(v).strip() else None
            except Exception:
                return None

        for _, row in df_m.iterrows():
            parent_visit_id = row.get("parent_visit_id")
            m = MedicalRecord(
                id=str(row.get("id")),
                patient_id=str(row.get("patient_id")),
                diagnosis=str(row.get("diagnosis", "")),
                symptoms=str(row.get("symptoms", "")),
                prakriti=str(row.get("prakriti", "")),
                vikriti=str(row.get("vikriti", "")),
                severity=str(row.get("severity", "")),
                comorbidities=str(row.get("comorbidities", "")) if not pd.isna(row.get("comorbidities")) else "",
                notes=str(row.get("notes", "")),
                prescription=str(row.get("prescription", "")),
                parent_visit_id=str(parent_visit_id) if not pd.isna(parent_visit_id) and str(parent_visit_id).strip() else None,
                bpm=_int_or_none(row.get("bpm")),
                sugar_level=_float_or_none(row.get("sugar_level")),
                spo2=_int_or_none(row.get("spo2")),
                temperature=_float_or_none(row.get("temperature")),
                systolic_bp=_int_or_none(row.get("systolic_bp")),
                diastolic_bp=_int_or_none(row.get("diastolic_bp")),
            )
            if not pd.isna(row.get("visit_date")):
                try:
                    m.visit_date = pd.to_datetime(row.get("visit_date")).to_pydatetime()
                except Exception:
                    pass
            session.add(m)
        session.commit()

    # 3. Ayush Treatments
    if os.path.exists(AYUSH_TREATMENTS_CSV):
        print("Migrating Ayush Treatments...")
        df_a = pd.read_csv(AYUSH_TREATMENTS_CSV)
        for _, row in df_a.iterrows():
            a = AyushTreatment(
                id=str(row.get("id")),
                patient_id=str(row.get("patient_id")),
                medical_record_id=str(row.get("medical_record_id")),
                disease=str(row.get("disease", "")),
                herbs_prescribed=str(row.get("herbs_prescribed", "")),
                yoga_prescribed=str(row.get("yoga_prescribed", "")),
                diet_plan=str(row.get("diet_plan", "")),
                treatment_duration_weeks=str(row.get("treatment_duration_weeks", "")),
                improvement_percentage=str(row.get("improvement_percentage", "")),
                outcome=str(row.get("outcome", "")),
            )
            if not pd.isna(row.get("visit_date")):
                try:
                    a.visit_date = pd.to_datetime(row.get("visit_date")).to_pydatetime()
                except Exception:
                    pass
            session.add(a)
        session.commit()

    # 4. Treatment Feedbacks
    if os.path.exists(TREATMENT_FEEDBACK_CSV):
        print("Migrating Treatment Feedbacks...")
        df_f = pd.read_csv(TREATMENT_FEEDBACK_CSV)
        for _, row in df_f.iterrows():
            f = TreatmentFeedback(
                id=str(row.get("id")),
                patient_id=str(row.get("patient_id")),
                medical_record_id=str(row.get("medical_record_id", "")),
                ai_plan=str(row.get("ai_plan", "")),
                ml_context=str(row.get("ml_context", "")),
                doctor_rating=str(row.get("doctor_rating", "")),
                doctor_comments=str(row.get("doctor_comments", "")) if not pd.isna(row.get("doctor_comments")) else "",
                is_retrained=str(row.get("is_retrained", "False")) == "True",
            )
            if not pd.isna(row.get("created_at")):
                try:
                    f.created_at = pd.to_datetime(row.get("created_at")).to_pydatetime()
                except Exception:
                    pass
            session.add(f)
        session.commit()

    session.close()
    print("Migration Complete!")


if __name__ == "__main__":
    run_migration()
