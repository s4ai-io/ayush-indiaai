"""
Data Migration Script — Populates PostgreSQL from all 6 data sources

Usage:
    cd backend
    source venv/bin/activate
    python migrate_data.py
"""
import sys
import os
import json
import csv
import uuid
from datetime import datetime, date

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, SessionLocal
from models_db import (
    Patient, MedicalRecord, HealthRecord, AyushTreatment,
    TreatmentFeedback, PublicHealthTrend, LocationNode
)


def get_data_path(filename):
    """Resolve data file path"""
    # Check backend/data first, then project root data/
    backend_path = os.path.join(os.path.dirname(__file__), "data", filename)
    root_path = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    if os.path.exists(backend_path):
        return backend_path
    elif os.path.exists(root_path):
        return root_path
    return None


def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d", "%Y-%m"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def safe_float(val):
    try:
        return float(val) if val else None
    except (ValueError, TypeError):
        return None


def safe_int(val):
    try:
        return int(float(val)) if val else None
    except (ValueError, TypeError):
        return None


def migrate_registrations(db):
    """registrations.json → Patient"""
    path = get_data_path("registrations.json")
    if not path:
        print("  ⚠ registrations.json not found, skipping")
        return {}

    with open(path, "r") as f:
        data = json.load(f)

    patient_map = {}  # original_id (if present) → db uuid
    count_patients = 0
    count_records = 0

    for entry in data:
        basic = entry.get("basicInfo", {})
        contact = entry.get("contactInfo", {})
        other = entry.get("otherInfo", {})

        # New schema uses 'age' directly, no DOB logic needed if not present
        # If 'id' is not in json, we just create a new one, but we return a map if needed.
        # Generated data doesn't have 'id' key in root usually, but let's check.
        
        patient_id = uuid.uuid4()
        patient = Patient(
            id=patient_id,
            first_name=basic.get("firstName"),
            last_name=basic.get("lastName"),
            gender=basic.get("gender"),
            age=basic.get("age"),
            marital_status=basic.get("maritalStatus"),
            
            mobile=contact.get("mobileNumber"),
            address=contact.get("address"),
            city=contact.get("city"),
            state=contact.get("state"),
            pincode=contact.get("pincode"),
            
            occupation=other.get("occupation"),
            blood_group=other.get("bloodGroup"),
            id_type=other.get("idType"),
            id_number=other.get("idNumber"),
            
            # Default/Derived
            nationality=basic.get("nationality", "Indian"),
        )
        db.add(patient)
        if "id" in entry:
            patient_map[entry["id"]] = patient_id
        count_patients += 1

        # Generated data currently doesn't have medicalRecords, but if it did:
        for record in entry.get("medicalRecords", []):
            mr = MedicalRecord(
                id=uuid.uuid4(),
                patient_id=patient_id,
                symptoms=record.get("symptoms"),
                diagnosis=record.get("diagnosis"),
                notes=record.get("notes"),
                prescription=record.get("prescription"),
                visit_date=parse_date(record.get("timestamp")),
            )
            db.add(mr)
            count_records += 1

    db.commit()
    print(f"  ✓ registrations.json → {count_patients} patients, {count_records} medical records")
    return patient_map


def migrate_patients_csv(db, existing_map):
    """patients.csv → Patient (new entries for ML patients not in registrations)"""
    path = get_data_path("patients.csv")
    if not path:
        print("  ⚠ patients.csv not found, skipping")
        return {}

    csv_patient_map = {}  # P00001 → uuid
    count = 0

    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["patient_id"]
            patient_id = uuid.uuid4()
            patient = Patient(
                id=patient_id,
                first_name=pid,  # CSV only has patient_id, no real name
                gender=row.get("gender"),
                age=safe_int(row.get("age")),
                prakriti=row.get("prakriti"),
                vikriti=row.get("vikriti"),
                bmi=safe_float(row.get("bmi")),
                city=row.get("city"),
                occupation=row.get("occupation"),
            )
            db.add(patient)
            csv_patient_map[pid] = patient_id
            count += 1

    db.commit()
    print(f"  ✓ patients.csv → {count} patients")
    return csv_patient_map


def migrate_health_records(db, patient_map):
    """health_records.csv → HealthRecord"""
    path = get_data_path("health_records.csv")
    if not path:
        print("  ⚠ health_records.csv not found, skipping")
        return

    count = 0
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["patient_id"]
            patient_uuid = patient_map.get(pid)

            visit = parse_date(row.get("visit_date"))

            hr = HealthRecord(
                id=uuid.uuid4(),
                patient_id=patient_uuid,
                visit_date=visit.date() if visit else None,
                disease=row.get("disease"),
                disease_category=row.get("disease_category"),
                season=row.get("season"),
                severity=safe_int(row.get("severity")),
                duration_days=safe_int(row.get("duration_days")),
                sleep_hours=safe_float(row.get("sleep_hours")),
                exercise_days_week=safe_int(row.get("exercise_days_week")),
                stress_level=row.get("stress_level"),
                diet_type=row.get("diet_type"),
                water_intake_liters=safe_float(row.get("water_intake_liters")),
                meditation_minutes=safe_int(row.get("meditation_minutes")),
            )
            db.add(hr)
            count += 1

            if count % 500 == 0:
                db.commit()

    db.commit()
    print(f"  ✓ health_records.csv → {count} health records")


def migrate_treatments(db, patient_map):
    """treatments.csv → AyushTreatment"""
    path = get_data_path("treatments.csv")
    if not path:
        print("  ⚠ treatments.csv not found, skipping")
        return

    count = 0
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["patient_id"]
            patient_uuid = patient_map.get(pid)
            visit = parse_date(row.get("visit_date"))

            at = AyushTreatment(
                id=uuid.uuid4(),
                patient_id=patient_uuid,
                visit_date=visit.date() if visit else None,
                disease=row.get("disease"),
                herbs_prescribed=row.get("herbs_prescribed"),
                yoga_prescribed=row.get("yoga_prescribed"),
                diet_plan=row.get("diet_plan"),
                treatment_duration_weeks=safe_int(row.get("treatment_duration_weeks")),
                compliance_rate=safe_float(row.get("compliance_rate")),
                improvement_percentage=safe_float(row.get("improvement_percentage")),
                outcome=row.get("outcome"),
                follow_up_required=row.get("follow_up_required"),
            )
            db.add(at)
            count += 1

            if count % 500 == 0:
                db.commit()

    db.commit()
    print(f"  ✓ treatments.csv → {count} AYUSH treatments")


def migrate_public_health_trends(db):
    """public_health_trends.csv → PublicHealthTrend"""
    path = get_data_path("public_health_trends.csv")
    if not path:
        print("  ⚠ public_health_trends.csv not found, skipping")
        return

    count = 0
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month_dt = parse_date(row.get("month"))
            trend = PublicHealthTrend(
                id=uuid.uuid4(),
                month=month_dt.date() if month_dt else None,
                season=row.get("season"),
                disease_category=row.get("disease_category"),
                disease=row.get("disease"),
                cases_reported=safe_int(row.get("cases_reported")),
                avg_severity=safe_float(row.get("avg_severity")),
                avg_age=safe_float(row.get("avg_age")),
                recovery_rate=safe_float(row.get("recovery_rate")),
                treatment_success_rate=safe_float(row.get("treatment_success_rate")),
                top_herb=row.get("top_herb"),
                top_yoga=row.get("top_yoga"),
            )
            db.add(trend)
            count += 1

    db.commit()
    print(f"  ✓ public_health_trends.csv → {count} trend records")


def migrate_treatment_feedback(db):
    """treatment_feedback.csv → TreatmentFeedback"""
    path = get_data_path("treatment_feedback.csv")
    if not path:
        print("  ⚠ treatment_feedback.csv not found, skipping")
        return

    count = 0
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("patient_id"):
                continue

            ai_plan = {}
            ml_context = {}
            try:
                ai_plan = json.loads(row.get("treatment_plan_json", "{}"))
            except json.JSONDecodeError:
                pass
            try:
                ml_context = json.loads(row.get("context_json", "{}"))
            except json.JSONDecodeError:
                pass

            fb = TreatmentFeedback(
                id=uuid.uuid4(),
                ai_plan=ai_plan,
                ml_context=ml_context,
                doctor_rating=row.get("rating"),
                doctor_comments=row.get("feedback"),
                is_retrained=False,
            )
            db.add(fb)
            count += 1

    db.commit()
    print(f"  ✓ treatment_feedback.csv → {count} feedback records")


def seed_location_nodes(db):
    """Seed location graph nodes for GNN (from gnn_service.py hardcoded data)"""
    nodes = [
        {"pincode": "110001", "area_name": "Connaught Place", "city": "New Delhi",
         "adjacency": {"110002": 0.8, "110003": 0.7, "110004": 0.6, "110005": 0.9}},
        {"pincode": "110002", "area_name": "Daryaganj", "city": "New Delhi",
         "adjacency": {"110001": 0.8, "110006": 0.8}},
        {"pincode": "110003", "area_name": "Aliganj", "city": "New Delhi",
         "adjacency": {"110001": 0.7, "110005": 0.5}},
        {"pincode": "110004", "area_name": "Rashtrapati Bhawan", "city": "New Delhi",
         "adjacency": {"110001": 0.6}},
        {"pincode": "110005", "area_name": "Karol Bagh", "city": "New Delhi",
         "adjacency": {"110001": 0.9, "110003": 0.5}},
        {"pincode": "110006", "area_name": "Chandni Chowk", "city": "New Delhi",
         "adjacency": {"110002": 0.8}},
    ]
    for n in nodes:
        db.add(LocationNode(
            id=uuid.uuid4(),
            pincode=n["pincode"],
            area_name=n["area_name"],
            city=n["city"],
            adjacency=n["adjacency"],
        ))
    db.commit()
    print(f"  ✓ Seeded {len(nodes)} location nodes")


def main():
    print("=" * 60)
    print("AYUSH India AI — Data Migration")
    print("=" * 60)

    # Drop and recreate all tables (CASCADE for legacy FK constraints)
    print("\n1. Recreating database tables...")
    with engine.connect() as conn:
        conn.execute(__import__('sqlalchemy').text("DROP SCHEMA public CASCADE"))
        conn.execute(__import__('sqlalchemy').text("CREATE SCHEMA public"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("  ✓ All 8 tables created")

    db = SessionLocal()

    try:
        # 2. Migrate registrations.json → Patient + MedicalRecord
        print("\n2. Migrating registrations.json...")
        reg_map = migrate_registrations(db)

        # 3. Migrate patients.csv → Patient
        print("\n3. Migrating patients.csv...")
        csv_map = migrate_patients_csv(db, reg_map)

        # 4. Migrate health_records.csv → HealthRecord
        print("\n4. Migrating health_records.csv...")
        migrate_health_records(db, csv_map)

        # 5. Migrate treatments.csv → AyushTreatment
        print("\n5. Migrating treatments.csv...")
        migrate_treatments(db, csv_map)

        # 6. Migrate public_health_trends.csv → PublicHealthTrend
        print("\n6. Migrating public_health_trends.csv...")
        migrate_public_health_trends(db)

        # 7. Migrate treatment_feedback.csv → TreatmentFeedback
        print("\n7. Migrating treatment_feedback.csv...")
        migrate_treatment_feedback(db)

        # 8. Seed location nodes
        print("\n8. Seeding location nodes...")
        seed_location_nodes(db)

        # Summary
        print("\n" + "=" * 60)
        print("Migration Complete! Table row counts:")
        print("-" * 40)
        for table_name in ["patients", "medical_records", "health_records",
                           "ayush_treatments", "treatment_feedback",
                           "public_health_trends", "location_nodes",
                           "disease_spread_predictions"]:
            try:
                result = db.execute(
                    __import__('sqlalchemy').text(f"SELECT count(*) FROM {table_name}")
                )
                count = result.scalar()
                print(f"  {table_name:30s} → {count:>6} rows")
            except Exception as e:
                print(f"  {table_name:30s} → ERROR: {e}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
