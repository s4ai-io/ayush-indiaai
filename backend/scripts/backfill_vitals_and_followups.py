"""
backfill_vitals_and_followups.py
─────────────────────────────────
One-off, idempotent backfill for the bulk historical dataset that predates
both the vitals columns and the parent_visit_id follow-up chain (it was
loaded by generate_historical_data_v2.py / migrate_synthetic_v2_postgres.py,
neither of which know about either). See FOLLOWUP_QUEUE_FIX.md and
AI_TREATMENT_ENGINE_CONTEXT.md-adjacent docs for the live-app features this
backfill retrofits onto old data.

What it does, for every ALREADY-COMPLETED visit (prescription not empty —
pending/queued visits are deliberately left untouched, since filling in
vitals for a visit nobody has seen yet would be wrong):

  1. Groups each patient's completed visits by diagnosis (case/space
     normalized) and orders each group by visit_date.
  2. The earliest visit in a group is the "root" — gets baseline vitals
     sampled from a disease+severity-biased range (services/vitals_pool.py).
  3. Every later visit in the same group is chained via parent_visit_id to
     the visit immediately before it, and gets vitals sampled as an
     improvement over the parent's vitals (biased by that visit's recorded
     AyushTreatment.outcome, so "Recovered" moves further toward normal than
     "Stable").
  4. A patient+diagnosis with only one completed visit just gets baseline
     vitals — no chain to build.

Only rows with bpm IS NULL are written, and parent_visit_id is only ever set
if it's currently NULL — safe to re-run; it will not touch anything it (or
a real doctor) already filled in.

Run from backend/:
    ./venv/bin/python3.11 scripts/backfill_vitals_and_followups.py
"""
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import and_

from models import SessionLocal, MedicalRecord, AyushTreatment
from services.vitals_pool import sample_baseline_vitals, sample_followup_vitals, VITAL_KEYS

SEED = int(os.getenv("BACKFILL_SEED", "42"))

_COMPLETED = and_(
    MedicalRecord.prescription.isnot(None),
    MedicalRecord.prescription != "",
    MedicalRecord.prescription != "{}",
)


def _severity_label(raw: str | None) -> str:
    try:
        score = int(str(raw).strip())
    except (TypeError, ValueError):
        return "Moderate"
    if score <= 3:
        return "Mild"
    if score <= 6:
        return "Moderate"
    return "Severe"


def run() -> None:
    rng = random.Random(SEED)

    with SessionLocal() as db:
        records = (
            db.query(MedicalRecord)
            .filter(_COMPLETED)
            .order_by(MedicalRecord.patient_id, MedicalRecord.visit_date)
            .all()
        )
        print(f"Found {len(records)} completed visits to consider.")

        outcomes = dict(
            db.query(AyushTreatment.medical_record_id, AyushTreatment.outcome).all()
        )

        groups: dict[tuple[str, str], list[MedicalRecord]] = defaultdict(list)
        for r in records:
            key = (r.patient_id, (r.diagnosis or "").strip().lower())
            groups[key].append(r)  # already ordered by visit_date from the query

        vitals_written = 0
        chains_linked = 0

        for (_patient_id, _diag), group in groups.items():
            if not group[0].diagnosis:
                continue  # skip blank/unknown diagnoses — nothing meaningful to bias on

            prev_record = None
            prev_vitals = None
            for record in group:
                already_has_vitals = record.bpm is not None
                if prev_record is None:
                    # Root of the chain (or a standalone single visit).
                    if not already_has_vitals:
                        vitals = sample_baseline_vitals(record.diagnosis, _severity_label(record.severity), rng)
                        for key in VITAL_KEYS:
                            setattr(record, key, vitals[key])
                        vitals_written += 1
                        prev_vitals = vitals
                    else:
                        prev_vitals = {key: getattr(record, key) for key in VITAL_KEYS}
                else:
                    if record.parent_visit_id is None:
                        record.parent_visit_id = prev_record.id
                        chains_linked += 1
                    if not already_has_vitals:
                        outcome = outcomes.get(record.id) or outcomes.get(prev_record.id) or "Improved"
                        vitals = sample_followup_vitals(record.diagnosis, prev_vitals or {}, outcome, rng)
                        for key in VITAL_KEYS:
                            setattr(record, key, vitals[key])
                        vitals_written += 1
                        prev_vitals = vitals
                    else:
                        prev_vitals = {key: getattr(record, key) for key in VITAL_KEYS}
                prev_record = record

        db.commit()
        print(f"Vitals written : {vitals_written}")
        print(f"Follow-up links created : {chains_linked}")
        print("Done.")


if __name__ == "__main__":
    run()
