"""
generate_historical_data_v2.py
────────────────────────────────
v2 of the synthetic Ayurvedic clinical data generator. Writes CSVs to
synthetic_data_v2/ (does NOT touch db_dump/ or the live database — load the
output into Postgres separately with migrate_synthetic_v2_postgres.py).

What changed vs. generate_historical_data.py, and why (see
PUBLIC_HEALTH_DASHBOARD.md and the data-realism plan for the full rationale):

  - Cities: ~140 across every state/UT, population-weighted (services/geo_reference.py),
    not 19 hand-picked metros.
  - Pincodes: sampled from each patient's own state's real India-Post postal
    range, not a fully random 6-digit string unrelated to their city.
  - Diagnoses: 109 total (28 seasonal/acute + 81 chronic/long-tail from the NAMC
    dataset, services/disease_pool.py) instead of ~20, with a Zipfian long tail
    instead of near-uniform frequency.
  - Names: 200+ per list, regionally weighted to the patient's state
    (services/name_pool.py) instead of one flat 27-name pool.
  - Age: sampled from an approximate India population-pyramid shape (more
    young adults, real presence of children and the elderly) instead of a
    bell curve hand-centered on 35.
  - Case counts: Poisson-sampled around a seasonal mean instead of a fixed
    integer per calendar month, so re-running with a different --seed
    produces different (but still seasonally sensible) totals.
  - Missingness, weekday-skewed visit dates, and occasional duplicate/
    follow-up visits are injected, matching how real intake data looks.

Run from backend/:
    ./venv/bin/python3.11 generate_historical_data_v2.py --seed 42
    ./venv/bin/python3.11 generate_historical_data_v2.py --seed 42 --years 2024 2025 2026 --patients 3500
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.geo_reference import CITIES, sample_pincode
from services.name_pool import sample_first_name, sample_last_name
from services.disease_pool import (
    SEASONAL_DISEASES,
    SEASONAL_SYMPTOMS,
    sample_chronic_disease,
    sample_severity,
    vary_symptoms,
)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_data_v2")

SEVERITY_SCORES = {"Mild": "3", "Moderate": "6", "Severe": "9"}
OUTCOME_OPTIONS = ["Improved", "Significantly Improved", "Stable", "Under Treatment", "Recovered"]
OUTCOME_WEIGHTS = [35, 30, 15, 15, 5]

MARITAL_STATUS_OPTIONS = ["Married", "Single", "Widowed", "Divorced"]
OCCUPATIONS = [
    "Farmer", "Teacher", "Engineer", "Doctor", "Business", "Student", "Housewife",
    "Labourer", "Government Employee", "Shopkeeper", "Driver", "Clerk", "Retired",
    "Nurse", "Tailor", "Electrician", "Plumber", "Accountant", "Software Engineer",
    "Homemaker", "Priest", "Carpenter", "Weaver", "Fisherman", "Potter",
]
# Real-world Indian blood-group distribution (approx.), not a uniform pick.
BLOOD_GROUP_WEIGHTS = [
    ("O+", 35), ("B+", 32), ("A+", 20), ("AB+", 7),
    ("O-", 2), ("B-", 1.5), ("A-", 1.5), ("AB-", 1),
]
LOCALITY_NAMES = [
    "MG Road", "Nehru Nagar", "Gandhi Chowk", "Ambedkar Marg", "Shivaji Nagar",
    "Station Road", "Model Town", "Civil Lines", "Sector 12", "Ring Road",
    "Old Bazaar", "Church Street", "Temple Road", "College Road", "Market Yard",
    "Green Park", "Lake View", "Hill Colony", "River Side", "New Colony",
]

DIET_MAP = {
    "Vata":       "Warm, oily foods. Avoid cold and dry. Sweet, sour, salty taste.",
    "Pitta":      "Cool, light foods. Avoid spicy and fermented. Sweet, bitter, astringent.",
    "Kapha":      "Light, dry, warm foods. Avoid heavy and oily. Pungent, bitter, astringent.",
    "Vata-Pitta": "Warm, moderately oily foods. Sweet, slightly sour.",
    "Pitta-Kapha":"Cool, light, non-oily foods. Bitter, astringent, sweet.",
    "Vata-Kapha": "Warm, light, slightly oily foods. Sour, pungent, bitter.",
}

# ─── Approximate India population-pyramid age weights (5-90) ─────────────────
# Coarse buckets, not exact census figures - young-skewed with a real elderly
# tail, replacing the old hand-centered "bell curve around 35".
AGE_BUCKETS = [
    (5, 14, 17), (15, 24, 18), (25, 34, 17), (35, 44, 14), (45, 54, 12),
    (55, 64, 9), (65, 74, 7), (75, 90, 6),
]


def _sample_age(rng: random.Random) -> int:
    lo, hi, _w = rng.choices(AGE_BUCKETS, weights=[b[2] for b in AGE_BUCKETS], k=1)[0]
    return rng.randint(lo, hi)


def _sample_blood_group(rng: random.Random) -> str:
    groups, weights = zip(*BLOOD_GROUP_WEIGHTS)
    return rng.choices(groups, weights=weights, k=1)[0]


def _weighted_choice(rng: random.Random, options, weights):
    return rng.choices(options, weights=weights, k=1)[0]


def _sample_visit_date(rng: random.Random, year: int, month: int) -> datetime:
    """Weekday-skewed day within the month (fewer Sunday visits, like a real clinic)."""
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    days = list(range(1, days_in_month + 1))
    weights = []
    for d in days:
        weekday = datetime(year, month, d).weekday()  # Mon=0 .. Sun=6
        weights.append(0.4 if weekday == 6 else 1.0)
    day = _weighted_choice(rng, days, weights)
    hour = rng.randint(8, 18)
    minute = rng.choice([0, 15, 30, 45])
    return datetime(year, month, day, hour, minute)


def _maybe_blank(rng: random.Random, value: str, blank_prob: float) -> str:
    return "" if rng.random() < blank_prob else value


def generate(seed: int, years: list[int], n_patients: int, out_dir: str) -> None:
    py_rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    os.makedirs(out_dir, exist_ok=True)

    city_names = [c[0] for c in CITIES]
    city_states = {c[0]: c[1] for c in CITIES}
    city_weights = [c[2] for c in CITIES]

    print("=" * 60)
    print("  Ayurveda Historical Data Generator v2")
    print(f"  Target years: {years}   seed: {seed}   patients: {n_patients}")
    print("=" * 60)

    # ── Patients ──────────────────────────────────────────────────────────────
    patients: list[dict] = []
    patient_ids: list[str] = []
    now_iso = datetime.utcnow().isoformat()

    print("\n[1/3] Generating patients...")
    for _ in range(n_patients):
        gender = py_rng.choice(["Male", "Female"])
        city = _weighted_choice(py_rng, city_names, city_weights)
        state = city_states[city]
        age = _sample_age(py_rng)
        first = sample_first_name(gender, state, py_rng)
        last = sample_last_name(state, py_rng)
        pid = str(uuid.uuid4())

        marital = "Single" if age < 21 else py_rng.choice(MARITAL_STATUS_OPTIONS)
        mobile = f"{py_rng.choice(['6','7','8','9'])}{py_rng.randint(100000000, 999999999)}"

        patients.append({
            "id": pid,
            "first_name": first,
            "last_name": last,
            "gender": gender,
            "age": age,
            "marital_status": marital,
            "mobile": mobile,
            "address": f"{py_rng.randint(1, 999)}, {py_rng.choice(LOCALITY_NAMES)}",
            "city": city,
            "state": state,
            "pincode": sample_pincode(state, py_rng),
            "blood_group": _maybe_blank(py_rng, _sample_blood_group(py_rng), 0.04),
            "occupation": _maybe_blank(py_rng, py_rng.choice(OCCUPATIONS), 0.06),
            "id_type": "Aadhaar",
            "id_number": str(py_rng.randint(100000000000, 999999999999)),
            "diagnosis_done": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        })
        patient_ids.append(pid)

    print(f"  {len(patients)} patients created across {len(set(p['city'] for p in patients))} cities")

    # ── Medical records / treatments / feedback, month by month ──────────────
    print("\n[2/3] Generating medical records + treatments...")
    records: list[dict] = []
    treatments: list[dict] = []
    feedbacks: list[dict] = []

    ritu_map = {1: "Shishira", 2: "Shishira", 3: "Vasanta", 4: "Vasanta",
                5: "Grishma", 6: "Grishma", 7: "Varsha", 8: "Varsha",
                9: "Sharad", 10: "Sharad", 11: "Hemanta", 12: "Hemanta"}
    # Base monthly case-volume means, calibrated against a 900-patient population.
    # Scaled by the actual --patients count so per-capita monthly incidence stays
    # constant instead of spreading a fixed case volume across a bigger/smaller
    # patient pool (which would just dilute or concentrate hotspot/alert density
    # for no epidemiological reason).
    BASELINE_POPULATION = 900
    pop_scale = n_patients / BASELINE_POPULATION
    seasonal_means_base = {7: 90, 8: 140, 9: 110, 1: 80, 2: 75, 5: 70, 6: 65,
                           3: 55, 4: 55, 10: 50, 11: 60, 12: 65}
    seasonal_means = {m: v * pop_scale for m, v in seasonal_means_base.items()}
    chronic_mean = 45 * pop_scale  # roughly flat all year - real chronic-disease OPD load

    def _make_record(disease, dosha, severity_label, prakriti, herbs, yoga, symptoms, year, month):
        pid = py_rng.choice(patient_ids)
        severity_score = SEVERITY_SCORES[severity_label]
        visit_dt = _sample_visit_date(py_rng, year, month)
        diet = DIET_MAP.get(prakriti, DIET_MAP["Vata"])
        outcome = _weighted_choice(py_rng, OUTCOME_OPTIONS, OUTCOME_WEIGHTS)
        dur_weeks = {"Mild": py_rng.randint(1, 3), "Moderate": py_rng.randint(3, 8),
                     "Severe": py_rng.randint(6, 16)}[severity_label]
        season = ritu_map[month]
        patient_symptoms = vary_symptoms(symptoms, py_rng)

        record_id = str(uuid.uuid4())
        records.append({
            "id": record_id,
            "patient_id": pid,
            "visit_date": visit_dt.isoformat(),
            "diagnosis": disease,
            "symptoms": patient_symptoms,
            "prakriti": prakriti,
            "vikriti": dosha,
            "severity": severity_score,
            "comorbidities": _maybe_blank(py_rng, py_rng.choice(
                ["None", "Hypertension", "Diabetes", "Obesity", "Stress", ""]), 0.10),
            "notes": f"Patient presents with {severity_label.lower()} {disease}. Season: {season}. Dosha predominant: {dosha}.",
            "prescription": json.dumps({"herbs": herbs, "yoga": yoga}),
        })
        treatments.append({
            "id": str(uuid.uuid4()),
            "patient_id": pid,
            "medical_record_id": record_id,
            "visit_date": visit_dt.isoformat(),
            "disease": disease,
            "herbs_prescribed": herbs,
            "yoga_prescribed": yoga,
            "diet_plan": diet,
            "treatment_duration_weeks": str(dur_weeks),
            "improvement_percentage": str(py_rng.randint(40, 95)),
            "outcome": outcome,
        })
        feedbacks.append({
            "id": str(uuid.uuid4()),
            "patient_id": pid,
            "medical_record_id": record_id,
            "ai_plan": "{}",
            "ml_context": f'{{"disease":"{disease}","dosha":"{dosha}","prakriti":"{prakriti}","season":"{season}"}}',
            "doctor_rating": py_rng.choice(["positive", "positive", "positive", "negative"]),
            "doctor_comments": py_rng.choice([
                "Patient responded well to treatment.",
                "Good improvement noted after 2 weeks.",
                "Requires follow-up after 1 month.",
                "Minimal response, dosage adjusted.",
                "Excellent recovery.",
                "",
            ]),
            "is_retrained": False,
            "created_at": now_iso,
        })

        # ~4% chance of a realistic short-interval follow-up visit for the same complaint
        if py_rng.random() < 0.04:
            follow_dt = visit_dt + timedelta(days=py_rng.randint(2, 6))
            if follow_dt.month == month:
                follow_id = str(uuid.uuid4())
                records.append({
                    "id": follow_id,
                    "patient_id": pid,
                    "visit_date": follow_dt.isoformat(),
                    "diagnosis": disease,
                    "symptoms": patient_symptoms,
                    "prakriti": prakriti,
                    "vikriti": dosha,
                    "severity": severity_score,
                    "comorbidities": "",
                    "notes": f"Follow-up visit for {disease}. Season: {season}.",
                    "prescription": json.dumps({"herbs": herbs, "yoga": yoga}),
                })

    for year in years:
        print(f"\n  -- Year {year} --")
        for month in range(1, 13):
            n_seasonal = int(np_rng.poisson(lam=seasonal_means.get(month, 50)))
            n_chronic = int(np_rng.poisson(lam=chronic_mean))

            for _ in range(n_seasonal):
                options = SEASONAL_DISEASES.get(month, SEASONAL_DISEASES[1])
                disease, dosha, severity_label, prakriti, herbs, yoga = py_rng.choice(options)
                symptoms = SEASONAL_SYMPTOMS.get(disease, f"Symptoms related to {disease}")
                _make_record(disease, dosha, severity_label, prakriti, herbs, yoga, symptoms, year, month)

            for _ in range(n_chronic):
                name, dosha, prakriti, sev_profile, herbs, yoga, symptoms, _tier = sample_chronic_disease(py_rng)
                severity_label = sample_severity(sev_profile, py_rng)
                _make_record(name, dosha, severity_label, prakriti, herbs, yoga, symptoms, year, month)

            print(f"  Month {year}-{month:02d} ({ritu_map[month]:10s}): {n_seasonal} seasonal + {n_chronic} chronic records")

    # ── Write CSVs ────────────────────────────────────────────────────────────
    print("\n[3/3] Writing CSVs...")
    _write_csv(os.path.join(out_dir, "patients.csv"), patients,
               ["id", "first_name", "last_name", "gender", "age", "marital_status", "mobile",
                "address", "city", "state", "pincode", "blood_group", "occupation", "id_type",
                "id_number", "diagnosis_done", "created_at", "updated_at"])
    _write_csv(os.path.join(out_dir, "medical_records.csv"), records,
               ["id", "patient_id", "visit_date", "diagnosis", "symptoms", "prakriti", "vikriti",
                "severity", "comorbidities", "notes", "prescription"])
    _write_csv(os.path.join(out_dir, "ayush_treatments.csv"), treatments,
               ["id", "patient_id", "medical_record_id", "visit_date", "disease", "herbs_prescribed",
                "yoga_prescribed", "diet_plan", "treatment_duration_weeks", "improvement_percentage", "outcome"])
    _write_csv(os.path.join(out_dir, "treatment_feedback.csv"), feedbacks,
               ["id", "patient_id", "medical_record_id", "ai_plan", "ml_context", "doctor_rating",
                "doctor_comments", "is_retrained", "created_at"])

    print(f"\n  Patients            : {len(patients)}")
    print(f"  Medical records     : {len(records)}")
    print(f"  AYUSH treatments    : {len(treatments)}")
    print(f"  Treatment feedbacks : {len(feedbacks)}")
    print(f"  Output directory    : {out_dir}")
    print("\nDone. Load into Postgres with migrate_synthetic_v2_postgres.py")
    print("=" * 60)


def _write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate v2 synthetic Ayurvedic clinical data")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default 42, reproducible)")
    parser.add_argument("--years", type=int, nargs="+", default=[2025],
                         help="One or more target years for visit dates, e.g. --years 2024 2025 2026. "
                              "The same generated patient pool gets a full year of visits for each year "
                              "listed, so patients realistically recur across years.")
    parser.add_argument("--patients", type=int, default=900, help="Number of patients to generate")
    parser.add_argument("--out-dir", type=str, default=OUT_DIR, help="Output directory for CSVs")
    args = parser.parse_args()

    generate(seed=args.seed, years=args.years, n_patients=args.patients, out_dir=args.out_dir)
