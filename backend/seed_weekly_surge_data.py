"""
seed_weekly_surge_data.py
─────────────────────────────────────────────────────────────────────────────
Adds systematic weekly-distributed medical records to the existing PostgreSQL
tables so that the bi-weekly Z-score anomaly detector has enough signal to fire.

Pattern for each seeded disease:
  - Weeks -52 to -7:  low stable baseline (1–3 cases/week)
  - Weeks -6  to -1:  moderate rise       (3–5 cases/week)
  - Week   0 (now):   clear spike         (8–14 cases/week)

This creates clear, detectable anomalies without replacing existing data.
Uses real patients already in the DB (round-robin assignment).

Run from backend/:
    ./venv/bin/python3.11 seed_weekly_surge_data.py
"""
import uuid
import random
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import SessionLocal, Patient, MedicalRecord

# ─── Config ──────────────────────────────────────────────────────────────────

# Diseases to seed with clear surge patterns
SURGE_DISEASES = [
    "Fever (Jwara)",
    "Rhinitis (Pratishyaya)",
    "Asthma (Tamaka Shwasa)",
    "Dengue (Dandashthaka Jwara)",
    "Cough (Kasa)",
    "Diarrhoea (Atisara)",
    "Acidity (Amlapitta)",
    "Joint Pain (Amavata)",
]

SYMPTOMS_MAP = {
    "Fever (Jwara)":              "Elevated Kapha, Pitta imbalance, body ache, loss of appetite",
    "Rhinitis (Pratishyaya)":     "Nasal congestion, watery discharge, sneezing, Kapha excess",
    "Asthma (Tamaka Shwasa)":     "Laboured breathing, chest tightness, Vata-Kapha imbalance",
    "Dengue (Dandashthaka Jwara)":"Sharp Pitta fever, severe joint pain, retro-orbital headache",
    "Cough (Kasa)":               "Dry/wet cough, throat irritation, Kapha accumulation",
    "Diarrhoea (Atisara)":        "Loose stools, abdominal cramps, Pitta aggravation",
    "Acidity (Amlapitta)":        "Sour belching, heartburn, Pitta excess, Ama accumulation",
    "Joint Pain (Amavata)":       "Joint stiffness, swelling, Vata-Ama imbalance",
}

SEVERITY_CHOICES = ["Mild", "Moderate", "Severe"]
# Numeric encoding, matching generate_historical_data.py's convention — medical_records.severity
# is a numeric 1-10 string everywhere else (real registration/voice-pipeline data included), so
# seeded rows must use the same scale rather than the raw text label.
SEVERITY_SCORES = {"Mild": "3", "Moderate": "6", "Severe": "9"}

# Weekly case pattern (relative weights, 52 weeks)
# Weeks 0–45: baseline (1–3 cases/wk), weeks 46–50: rising, week 51: spike
def weekly_case_count(week_index: int, spike_intensity: int = 10) -> int:
    if week_index <= 44:
        return random.choice([0, 0, 1, 1, 1, 2, 2, 3])
    elif week_index <= 47:
        return random.randint(3, 5)
    elif week_index <= 50:
        return random.randint(5, 8)
    else:
        return random.randint(spike_intensity - 2, spike_intensity + 2)


def main():
    with SessionLocal() as db:
        # Load all existing patient IDs
        patients = db.query(Patient.id, Patient.city).all()
        if not patients:
            print("ERROR: No patients found. Run generate_historical_data.py first.")
            sys.exit(1)

        patient_ids  = [p.id for p in patients]
        patient_cities = {p.id: p.city for p in patients}
        print(f"Loaded {len(patient_ids)} existing patients")

        now        = datetime.utcnow()
        # Start 52 weeks ago (Monday of that week)
        week_start = now - timedelta(weeks=52)

        total_added = 0

        for disease in SURGE_DISEASES:
            symptoms   = SYMPTOMS_MAP.get(disease, "General symptoms")
            spike_lvl  = random.randint(9, 14)

            for week_idx in range(52):
                n_cases = weekly_case_count(week_idx, spike_lvl)
                if n_cases == 0:
                    continue

                # Distribute cases across random days within this week
                week_date = week_start + timedelta(weeks=week_idx)

                for _ in range(n_cases):
                    patient_id = random.choice(patient_ids)
                    visit_day  = week_date + timedelta(days=random.randint(0, 6))

                    record = MedicalRecord(
                        id         = str(uuid.uuid4()),
                        patient_id = patient_id,
                        visit_date = visit_day,
                        diagnosis  = disease,
                        symptoms   = symptoms,
                        severity   = SEVERITY_SCORES[random.choice(SEVERITY_CHOICES)],
                        prakriti   = random.choice(["Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha"]),
                        vikriti    = random.choice(["Vata", "Pitta", "Kapha"]),
                        notes      = f"Seeded weekly surge data — week {week_idx + 1}/52",
                    )
                    db.add(record)
                    total_added += 1

            print(f"  ✓ {disease}: spike week = {spike_lvl} cases, seeded across 52 weeks")

        db.commit()
        print(f"\n✅ Done — added {total_added} weekly records across {len(SURGE_DISEASES)} diseases")
        print("The bi-weekly Z-score detector should now detect surges in the most recent weeks.")


if __name__ == "__main__":
    main()
