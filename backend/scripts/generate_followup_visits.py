"""
Seed a handful of pending follow-up visits for existing, already-diagnosed
patients — demonstrates the Pending Queue fix (see FOLLOWUP_QUEUE_FIX.md).

For each of N patients that already have a prescribed visit, clones their
most recent visit into a new MedicalRecord (same diagnosis/symptoms/prakriti/
vikriti/comorbidities, parent_visit_id set, vitals + prescription left blank)
so it shows up as a real follow-up waiting in the doctor's Pending Queue.

Usage:
    ./venv/bin/python scripts/generate_followup_visits.py            # 5 follow-ups
    FOLLOWUP_SEED_COUNT=10 ./venv/bin/python scripts/generate_followup_visits.py
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import desc
from models import SessionLocal, MedicalRecord

COUNT = int(os.getenv("FOLLOWUP_SEED_COUNT", "5"))


def run():
    with SessionLocal() as db:
        # Most recent PRESCRIBED, non-follow-up visit per patient — used as the
        # anchor so we don't chain a follow-up onto another follow-up.
        candidates = (
            db.query(MedicalRecord)
            .filter(MedicalRecord.prescription.isnot(None))
            .filter(MedicalRecord.prescription != "")
            .filter(MedicalRecord.prescription != "{}")
            .filter(MedicalRecord.parent_visit_id.is_(None))
            .order_by(desc(MedicalRecord.visit_date))
            .limit(500)
            .all()
        )

        seen_patients = set()
        created = 0
        for parent in candidates:
            if created >= COUNT:
                break
            if parent.patient_id in seen_patients:
                continue
            seen_patients.add(parent.patient_id)

            followup = MedicalRecord(
                id=str(uuid.uuid4()),
                patient_id=parent.patient_id,
                visit_date=datetime.utcnow(),
                diagnosis=parent.diagnosis,
                symptoms=parent.symptoms,
                prakriti=parent.prakriti,
                vikriti=parent.vikriti,
                severity=parent.severity,
                comorbidities=parent.comorbidities,
                notes="",
                prescription="{}",
                parent_visit_id=parent.id,
            )
            db.add(followup)
            created += 1
            print(f"✓ Follow-up queued: patient={parent.patient_id} condition={parent.diagnosis!r} parent_visit={parent.id}")

        db.commit()
        print(f"\nDone — created {created} pending follow-up visit(s). They will now appear in the doctor's Pending Queue.")


if __name__ == "__main__":
    run()
