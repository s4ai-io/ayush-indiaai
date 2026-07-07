"""
vitals_pool.py
──────────────
Synthetic basic-health-parameter (vitals) sampling, shared by the historical
data generator (generate_historical_data_v2.py) and the one-off DB backfill
(scripts/backfill_vitals_and_followups.py) so both produce vitals the same
way.

Two entry points:
  - sample_baseline_vitals(disease, severity_label, rng)  — a visit with no
    prior visit for the same condition. Sampled from a disease-biased range,
    scaled by severity.
  - sample_followup_vitals(disease, parent_vitals, outcome, rng) — a follow-up
    visit for the same condition. Moves each vital from the parent's value
    toward the normal reference, by an amount driven by the recorded
    treatment outcome (bigger move for "Recovered", smaller for "Stable").

Units: bpm (beats/min), sugar_level (mg/dL), spo2 (%), temperature (°C),
systolic_bp / diastolic_bp (mmHg) — matching medical_records columns.
"""
from __future__ import annotations

import random

VITAL_KEYS = ("bpm", "sugar_level", "spo2", "temperature", "systolic_bp", "diastolic_bp")

# Normal adult reference range (low, high) and midpoint used as the
# "recovery target" a follow-up's vitals drift toward.
NORMAL_RANGES = {
    "bpm": (62, 88),
    "sugar_level": (75, 110),
    "spo2": (96, 99),
    "temperature": (36.3, 37.2),
    "systolic_bp": (108, 128),
    "diastolic_bp": (68, 82),
}

SEVERITY_SCALE = {"Mild": 0.3, "Moderate": 0.65, "Severe": 1.0}

# Recovery fraction (how far a follow-up moves from the parent's value toward
# normal) by treatment outcome — matches OUTCOME_OPTIONS in
# generate_historical_data_v2.py / AyushTreatment.outcome.
OUTCOME_RECOVERY = {
    "Recovered": (0.55, 0.85),
    "Significantly Improved": (0.45, 0.75),
    "Improved": (0.25, 0.5),
    "Stable": (0.05, 0.2),
    "Under Treatment": (0.0, 0.15),
}


def _disease_bias(disease: str) -> dict:
    """Elevated (low, high) range overrides for vitals a given condition plausibly affects."""
    d = (disease or "").lower()
    bias: dict[str, tuple[float, float]] = {}

    if any(k in d for k in ("diabet", "madhumeha")):
        bias["sugar_level"] = (140, 260)
    if any(k in d for k in ("hypertension", "raktachapa", "blood pressure")):
        bias["systolic_bp"] = (140, 172)
        bias["diastolic_bp"] = (90, 106)
    if any(k in d for k in ("asthma", "tamaka", "shwasa", "copd", "bronch", "pneumonia", "respiratory")):
        bias["spo2"] = (86, 94)
        bias["bpm"] = (92, 118)
    if any(k in d for k in ("fever", "jwara", "infection", "flu", "influenza", "viral", "malaria", "dengue", "typhoid")):
        bias["temperature"] = (38.0, 40.2)
        bias["bpm"] = (95, 122)
    if any(k in d for k in ("anemia", "pandu")):
        bias["bpm"] = (90, 112)
        bias["spo2"] = (93, 97)
    if any(k in d for k in ("cardiac", "heart", "hridroga", "hridaya")):
        bias["bpm"] = (85, 132)
        bias["systolic_bp"] = (130, 162)
    if any(k in d for k in ("obesity", "sthoulya")):
        bias["bpm"] = (80, 102)
        bias["systolic_bp"] = (124, 146)

    return bias


def _round(vital: str, value: float) -> float:
    if vital in ("sugar_level", "temperature"):
        return round(value, 1)
    return int(round(value))


def sample_baseline_vitals(disease: str, severity_label: str, rng: random.Random) -> dict:
    scale = SEVERITY_SCALE.get(severity_label, 0.65)
    bias = _disease_bias(disease)

    result = {}
    for vital in VITAL_KEYS:
        normal_lo, normal_hi = NORMAL_RANGES[vital]
        if vital in bias:
            elevated_lo, elevated_hi = bias[vital]
            # Interpolate between "normal" and "fully elevated" by severity.
            lo = normal_lo + (elevated_lo - normal_lo) * scale
            hi = normal_hi + (elevated_hi - normal_hi) * scale
        else:
            lo, hi = normal_lo, normal_hi
        result[vital] = _round(vital, rng.uniform(lo, hi))
    return result


def sample_followup_vitals(disease: str, parent_vitals: dict, outcome: str, rng: random.Random) -> dict:
    lo_frac, hi_frac = OUTCOME_RECOVERY.get(outcome, (0.2, 0.4))
    result = {}
    for vital in VITAL_KEYS:
        parent_value = parent_vitals.get(vital)
        normal_lo, normal_hi = NORMAL_RANGES[vital]
        target = (normal_lo + normal_hi) / 2
        if parent_value is None:
            result[vital] = _round(vital, rng.uniform(normal_lo, normal_hi))
            continue
        fraction = rng.uniform(lo_frac, hi_frac)
        moved = parent_value + (target - parent_value) * fraction
        # Small noise so it's not a perfectly clean interpolation, occasionally
        # a slight regression even on an "improved" visit — real vitals are noisy.
        noise_span = (normal_hi - normal_lo) * 0.08
        moved += rng.uniform(-noise_span, noise_span)
        result[vital] = _round(vital, moved)
    return result
