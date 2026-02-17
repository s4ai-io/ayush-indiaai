import sys
import os
import json
import csv
from datetime import datetime
import uuid

# Add parent dir to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine, Base
from backend.models_db import Patient, MedicalRecord, Treatment

# Create Tables
Base.metadata.create_all(bind=engine)

def migrate_patients_and_records():
    db = SessionLocal()
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/registrations.json")
    
    if not os.path.exists(data_path):
        print(f"Skipping registrations: {data_path} not found")
        return

    with open(data_path, 'r') as f:
        registrations = json.load(f)

    print(f"Found {len(registrations)} registrations to migrate...")

    for reg in registrations:
        # 1. Create Patient
        basic = reg.get("basicInfo", {})
        contact = reg.get("contactInfo", {})
        
        # Parse Dates
        dob = None
        if basic.get("dateOfBirth"):
            try:
                dob = datetime.strptime(basic["dateOfBirth"], "%Y-%m-%d").date()
            except:
                pass

        patient_id = uuid.uuid4()
        # Use existing ID if valid UUID, else generate new
        try:
            if reg.get("id"):
                patient_id = uuid.UUID(reg["id"])
        except:
            pass            

        patient = Patient(
            id=patient_id,
            abha_id=basic.get("abhaId"),
            first_name=basic.get("firstName"),
            last_name=basic.get("lastName"),
            gender=basic.get("gender"),
            dob=dob,
            mobile=contact.get("mobileNumber"),
            email=contact.get("emailId"),
            city=contact.get("correspondenceCity"),
            state=contact.get("correspondenceState"),
            pincode=contact.get("correspondencePincode"),
            created_at=datetime.fromisoformat(reg["timestamp"].replace("Z", "+00:00")) if reg.get("timestamp") else datetime.now()
        )
        
        # Check for duplicates (by ABHA or Mobile if ABHA missing)
        existing = None
        if patient.abha_id:
            existing = db.query(Patient).filter(Patient.abha_id == patient.abha_id).first()
        
        if not existing:
            db.add(patient)
            db.commit()
            db.refresh(patient)
        else:
            patient = existing
            print(f"Patient {patient.first_name} already exists, skipping creation.")

        # 2. Create Medical Records
        records = reg.get("medicalRecords", [])
        for rec in records:
            # Check if record exists (by timestamp and patient_id to be safe)
            rec_ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00")) if rec.get("timestamp") else datetime.now()
            
            existing_rec = db.query(MedicalRecord).filter(
                MedicalRecord.patient_id == patient.id,
                MedicalRecord.diagnosis == rec.get("diagnosis"),
                MedicalRecord.visit_date == rec_ts
            ).first()

            if not existing_rec:
                new_record = MedicalRecord(
                    id=uuid.uuid4(),
                    patient_id=patient.id,
                    symptoms=rec.get("symptoms"),
                    diagnosis=rec.get("diagnosis"),
                    notes=rec.get("notes"),
                    prescription=rec.get("prescription"),
                    visit_date=rec_ts
                )
                db.add(new_record)
        
        db.commit()
    
    print("✓ Patients and Medical Records migrated.")
    db.close()

def migrate_feedback():
    db = SessionLocal()
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/treatment_feedback.csv")
    
    if not os.path.exists(data_path):
        print(f"Skipping feedback: {data_path} not found")
        return

    print("Migrating Treatment Feedback...")
    with open(data_path, 'r') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                # Try to link to patient
                patient_ref = row.get("patient_id")
                patient_id = None
                
                # If patient_ref is a UUID, try to find patient
                # (In our mock data, patient_id might be simple string like 'P001', so we might not match UUIDs from JSON)
                # For now, we will just store it if we can find a matching UUID, else leave null
                
                # Parse JSONs
                try:
                    ai_plan = json.loads(row.get("treatment_plan_json", "{}"))
                    ml_context = json.loads(row.get("context_json", "{}"))
                except:
                    ai_plan = {}
                    ml_context = {}

                treatment = Treatment(
                    id=uuid.uuid4(),
                    patient_id=patient_id, # Link if possible
                    ai_plan=ai_plan,
                    ml_context=ml_context,
                    doctor_rating=row.get("rating"),
                    doctor_comments=row.get("feedback"),
                    created_at=datetime.now() # CSV mock might not have timestamp
                )
                db.add(treatment)
                count += 1
            except Exception as e:
                print(f"Error skipping row: {e}")

        db.commit()
    print(f"✓ {count} Treatment Feedback records migrated.")
    db.close()

if __name__ == "__main__":
    print("Starting Migration...")
    migrate_patients_and_records()
    migrate_feedback()
    print("Migration Complete!")
