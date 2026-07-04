"""
seed_weekly_surge_data_v2.py
─────────────────────────────
v2 of the weekly-granularity seeder for the bi-weekly Z-score "early warning"
detector (analytics_service.detect_weekly_anomalies()). Appends to
synthetic_data_v2/medical_records.csv (run generate_historical_data_v2.py
first — this reads its patients.csv, it does not create new patients or
touch the live database).

Default behavior is now organic, not engineered: weekly case counts are
Poisson-sampled around a flat seasonal mean for each of the last 52 weeks
(some weeks up, some down), with no guaranteed spike. This is the point of
the v2 pass — the original script manufactured a guaranteed "week 0 spike"
every run specifically so the detector had something to fire on, which meant
the "early warning" feature was never actually tested against data it wasn't
tuned to pass.

Pass --demo-spike to restore the old guaranteed-spike behavior for demoing
the detector UI (flat baseline -> moderate rise -> clear spike in the most
recent weeks) - clearly opt-in and labeled as a demo, not the default.

Run from backend/ (after generate_historical_data_v2.py):
    ./venv/bin/python3.11 seed_weekly_surge_data_v2.py --seed 42
    ./venv/bin/python3.11 seed_weekly_surge_data_v2.py --demo-spike
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.disease_pool import vary_symptoms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_data_v2")
PATIENTS_CSV = os.path.join(OUT_DIR, "patients.csv")
MEDICAL_RECORDS_CSV = os.path.join(OUT_DIR, "medical_records.csv")

MEDICAL_RECORDS_FIELDS = [
    "id", "patient_id", "visit_date", "diagnosis", "symptoms", "prakriti",
    "vikriti", "severity", "comorbidities", "notes", "prescription",
]

# Acute/infectious diseases realistically prone to week-to-week case swings -
# canonical spellings matching generate_historical_data_v2.py / disease_pool.py
# exactly (the original script's "Diarrhoea" vs the generator's "Diarrhea" was
# one of the duplicate-diagnosis bugs this v2 pass fixes).
SURGE_DISEASES = [
    "Fever (Jwara)",
    "Rhinitis (Pratishyaya)",
    "Asthma (Tamaka Shwasa)",
    "Dengue (Dandashthaka Jwara)",
    "Cough (Kasa)",
    "Diarrhea (Atisara)",
    "Acidity (Amlapitta)",
    "Joint Pain (Amavata)",
]

SYMPTOMS_MAP = {
    "Fever (Jwara)":               "High temperature, chills, body ache, fatigue, sweating",
    "Rhinitis (Pratishyaya)":      "Runny nose, blocked nose, sneezing, post-nasal drip",
    "Asthma (Tamaka Shwasa)":      "Wheezing, breathlessness, chest tightness, cough at night",
    "Dengue (Dandashthaka Jwara)": "High fever, severe headache, rash, retro-orbital pain, myalgia",
    "Cough (Kasa)":                "Persistent cough, throat irritation, breathlessness",
    "Diarrhea (Atisara)":          "Loose watery stools, abdominal cramps, dehydration",
    "Acidity (Amlapitta)":         "Heartburn, sour belching, nausea, upper abdominal discomfort",
    "Joint Pain (Amavata)":        "Morning stiffness, swelling in joints, pain on movement",
}

# Herb/yoga pairs matching disease_pool.py's SEASONAL_DISEASES entries for these
# exact diagnoses, so a seeded record's (still-empty-of-a-real-treatment-row)
# prescription field reflects the same source data the main generator uses.
HERBS_YOGA_MAP = {
    "Fever (Jwara)":               ("Sudarshan Churna, Tulsi",  "Shavasana"),
    "Rhinitis (Pratishyaya)":      ("Shadabindu Taila",         "Jal Neti"),
    "Asthma (Tamaka Shwasa)":      ("Vasaka, Kantakari",        "Anulom Vilom"),
    "Dengue (Dandashthaka Jwara)": ("Papaya leaf, Guduchi",     "Bed rest, Shavasana"),
    "Cough (Kasa)":                ("Sitopaladi Churna, Tulsi", "Pranayama, Bhujangasana"),
    "Diarrhea (Atisara)":          ("Bilva, Kutaj",             "Pawanmuktasana"),
    "Acidity (Amlapitta)":         ("Shatavari, Licorice",      "Vajrasana, Setu Bandha"),
    "Joint Pain (Amavata)":        ("Ashwagandha, Guggulu",     "Pawanmuktasana, Trikonasana"),
}

SEVERITY_CHOICES = ["Mild", "Moderate", "Severe"]
# Numeric encoding, matching generate_historical_data_v2.py's convention — medical_records.severity
# is a numeric 1-10 string everywhere else (real registration/voice-pipeline data included), so
# seeded rows must use the same scale rather than the raw text label.
SEVERITY_SCORES = {"Mild": "3", "Moderate": "6", "Severe": "9"}
PRAKRITI_CHOICES = ["Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha"]
VIKRITI_CHOICES = ["Vata", "Pitta", "Kapha"]


def _load_patients() -> list[dict]:
    if not os.path.exists(PATIENTS_CSV):
        print(f"ERROR: {PATIENTS_CSV} not found. Run generate_historical_data_v2.py first.")
        sys.exit(1)
    with open(PATIENTS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _organic_weekly_count(np_rng: np.random.Generator, mean: float) -> int:
    return int(np_rng.poisson(lam=mean))


def _demo_weekly_count(rng: random.Random, week_index: int, spike_intensity: int) -> int:
    if week_index <= 44:
        return rng.choice([0, 0, 1, 1, 1, 2, 2, 3])
    elif week_index <= 47:
        return rng.randint(3, 5)
    elif week_index <= 50:
        return rng.randint(5, 8)
    else:
        return rng.randint(spike_intensity - 2, spike_intensity + 2)


def main(seed: int, demo_spike: bool) -> None:
    py_rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    patients = _load_patients()
    patient_ids = [p["id"] for p in patients]
    print(f"Loaded {len(patient_ids)} existing patients from {PATIENTS_CSV}")

    now = datetime.utcnow()
    week_start = now - timedelta(weeks=52)

    new_records: list[dict] = []

    for disease in SURGE_DISEASES:
        symptoms = SYMPTOMS_MAP[disease]
        spike_lvl = py_rng.randint(9, 14)
        organic_mean = py_rng.uniform(1.5, 3.0)

        for week_idx in range(52):
            if demo_spike:
                n_cases = _demo_weekly_count(py_rng, week_idx, spike_lvl)
            else:
                n_cases = _organic_weekly_count(np_rng, organic_mean)
            if n_cases == 0:
                continue

            week_date = week_start + timedelta(weeks=week_idx)
            herbs, yoga = HERBS_YOGA_MAP[disease]
            for _ in range(n_cases):
                patient_id = py_rng.choice(patient_ids)
                severity_label = py_rng.choice(SEVERITY_CHOICES)
                day_offset = py_rng.randint(0, 6)
                visit_day = (week_date + timedelta(days=day_offset)).replace(
                    hour=py_rng.randint(8, 18),
                    minute=py_rng.choice([0, 15, 30, 45]),
                    second=0, microsecond=0,
                )
                new_records.append({
                    "id": str(uuid.uuid4()),
                    "patient_id": patient_id,
                    "visit_date": visit_day.isoformat(),
                    "diagnosis": disease,
                    "symptoms": vary_symptoms(symptoms, py_rng),
                    "prakriti": py_rng.choice(PRAKRITI_CHOICES),
                    "vikriti": py_rng.choice(VIKRITI_CHOICES),
                    "severity": SEVERITY_SCORES[severity_label],
                    "comorbidities": "",
                    "notes": f"Patient presents with {severity_label.lower()} {disease}.",
                    "prescription": json.dumps({"herbs": herbs, "yoga": yoga}),
                })

        mode = f"spike week ~{spike_lvl} cases" if demo_spike else f"organic mean ~{organic_mean:.1f}/week"
        print(f"  {disease}: {mode}, seeded across 52 weeks")

    file_exists = os.path.exists(MEDICAL_RECORDS_CSV)
    mode = "a" if file_exists else "w"
    with open(MEDICAL_RECORDS_CSV, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MEDICAL_RECORDS_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_records)

    print(f"\nAdded {len(new_records)} weekly records across {len(SURGE_DISEASES)} diseases")
    print(f"Appended to {MEDICAL_RECORDS_CSV}")
    if demo_spike:
        print("Demo mode: guaranteed spike in the most recent weeks (for detector-UI demos).")
    else:
        print("Organic mode: no guaranteed spike - validates the detector against un-tuned data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed weekly-granularity records for the early-warning detector (v2)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default 42)")
    parser.add_argument("--demo-spike", action="store_true",
                         help="Force a guaranteed spike in the most recent weeks (old behavior, for demos)")
    args = parser.parse_args()

    main(seed=args.seed, demo_spike=args.demo_spike)
