import os
import pandas as pd
from sqlalchemy import create_engine
from models import init_db, Patient, MedicalRecord, AyushTreatment, TreatmentFeedback
from sqlalchemy.orm import sessionmaker
import uuid

import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ayush_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
MEDICAL_RECORDS_CSV = os.path.join(DATA_DIR, "medical_records.csv")
AYUSH_TREATMENTS_CSV = os.path.join(DATA_DIR, "ayush_treatments.csv")
TREATMENT_FEEDBACK_CSV = os.path.join(DATA_DIR, "treatment_feedback.csv")

def run_migration():
    print("Initializing Database...")
    init_db()
    session = SessionLocal()

    # Clear existing data in correct order to avoid ForeignKeyViolation
    try:
        session.query(TreatmentFeedback).delete()
        session.query(AyushTreatment).delete()
        session.query(MedicalRecord).delete()
        session.query(Patient).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error clearing existing data: {e}")
        # If deletion fails, we might still want to proceed or exiting
        # For now, let's try to continue if it was just empty or handle better

    # 1. Patients
    if os.path.exists(PATIENTS_CSV):
        print("Migrating Patients...")
        df_p = pd.read_csv(PATIENTS_CSV)
        for _, row in df_p.iterrows():
            age_val = row.get("age")
            try:
                age_val = int(age_val) if not pd.isna(age_val) and str(age_val).strip() else None
            except:
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
                blood_group=str(row.get("blood_group", "")),
                occupation=str(row.get("occupation", "")),
                id_type=str(row.get("id_type", "")),
                id_number=str(row.get("id_number", "")),
                diagnosis_done=str(row.get("diagnosis_done", "False")) == "True",
            )
            # handle dates
            if not pd.isna(row.get("created_at")):
                p.created_at = pd.to_datetime(row.get("created_at")).to_pydatetime()
            if not pd.isna(row.get("updated_at")):
                try: p.updated_at = pd.to_datetime(row.get("updated_at")).to_pydatetime()
                except: pass
            
            session.add(p)
        session.commit()

    # 2. Medical Records
    if os.path.exists(MEDICAL_RECORDS_CSV):
        print("Migrating Medical Records...")
        df_m = pd.read_csv(MEDICAL_RECORDS_CSV)
        for _, row in df_m.iterrows():
            m = MedicalRecord(
                id=str(row.get("id")),
                patient_id=str(row.get("patient_id")),
                diagnosis=str(row.get("diagnosis", "")),
                symptoms=str(row.get("symptoms", "")),
                prakriti=str(row.get("prakriti", "")),
                vikriti=str(row.get("doshas", row.get("vikriti", ""))),
                severity=str(row.get("severity", "")),
                comorbidities=str(row.get("comorbidities", "")),
                notes=str(row.get("notes", "")),
                prescription=str(row.get("prescription", "")),
            )
            if not pd.isna(row.get("visit_date")):
                try: m.visit_date = pd.to_datetime(row.get("visit_date")).to_pydatetime()
                except: pass
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
                outcome=str(row.get("outcome", ""))
            )
            if not pd.isna(row.get("visit_date")):
                try: a.visit_date = pd.to_datetime(row.get("visit_date")).to_pydatetime()
                except: pass
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
                doctor_comments=str(row.get("doctor_comments", "")),
                is_retrained=str(row.get("is_retrained", "False")) == "True"
            )
            if not pd.isna(row.get("created_at")):
                try: f.created_at = pd.to_datetime(row.get("created_at")).to_pydatetime()
                except: pass
            session.add(f)
        session.commit()

    session.close()
    print("Migration Complete!")

if __name__ == "__main__":
    run_migration()
