"""
One-time migration: rebuild the RL Q-table from scratch by replaying every
TreatmentFeedback row into the new "{namc_code}_{prakriti}_{vikriti}" state
key format. Legacy-format keys ("{cluster_id}_{disease}") disappear because
the table is rebuilt fresh — the old file is kept as a backup.

Prerequisite: scripts/backfill_rl_state_keys.py has been run, so every row's
ml_context carries namc_code + vikriti.

Usage:
  python3 scripts/rebuild_q_table.py --dry-run   # replay + report, no writes
  python3 scripts/rebuild_q_table.py             # backup old table, write new
"""
import sys, os, json, shutil, pickle, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import joblib
from models import SessionLocal, TreatmentFeedback, AyushTreatment
from services.rl_service import RLRecommendationService

DRY_RUN = "--dry-run" in sys.argv

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'models')
Q_TABLE_PATH = os.path.join(MODELS_DIR, 'rl_q_table.pkl')
DEMO_Q_TABLE_PATH = os.path.join(MODELS_DIR, 'demo_q_table.pkl')

LEARNING_RATE = 0.1
# Single ("Vata") or compound ("Vata-Pitta") dosha values are both valid states
DOSHA_RE = re.compile(r"^(vata|pitta|kapha)(-(vata|pitta|kapha))?$", re.IGNORECASE)

# UI labels stored by older demo-submit versions, mapped to the canonical
# convention the reward table expects
RATING_MAP = {"accurate": "positive", "needs changes": "negative", "none": "", "null": ""}


def normalize_rating(raw: str) -> str:
    r = (raw or "").strip().lower()
    return RATING_MAP.get(r, r if r in ("positive", "negative") else "")


def table_stats(q_table: dict) -> dict:
    new_fmt = legacy = 0
    diseases = set()
    positive_actions = 0
    for state, actions in q_table.items():
        parts = state.rsplit("_", 2)
        if len(parts) == 3 and DOSHA_RE.match(parts[1]) and DOSHA_RE.match(parts[2]):
            new_fmt += 1
            diseases.add(parts[0])
        else:
            legacy += 1
        positive_actions += sum(1 for q in actions.values() if q > 0)
    return {
        "states": len(q_table),
        "new_format": new_fmt,
        "legacy": legacy,
        "diseases": len(diseases),
        "positive_actions": positive_actions,
    }


def run():
    print(f"{'DRY RUN — ' if DRY_RUN else ''}Rebuilding Q-table from TreatmentFeedback history\n")

    if os.path.exists(Q_TABLE_PATH):
        before = table_stats(joblib.load(Q_TABLE_PATH))
        print(f"BEFORE: {before}")
    else:
        print("BEFORE: no existing Q-table file")

    q_table: dict = {}
    replayed = skipped_no_key = no_actions = errors = 0

    with SessionLocal() as db:
        # Eagerly load treatments keyed by medical_record_id for plan reconstruction
        treatments = {}
        for t in db.query(AyushTreatment).all():
            treatments[t.medical_record_id] = t

        rows = db.query(TreatmentFeedback).order_by(
            TreatmentFeedback.created_at, TreatmentFeedback.id
        ).all()
        print(f"Feedback rows to replay: {len(rows)}  (treatments loaded: {len(treatments)})")

        for fb in rows:
            try:
                ctx = json.loads(fb.ml_context or "{}")
                namc_code = (ctx.get("namc_code") or "").strip()
                prakriti = (ctx.get("prakriti") or "").strip()
                vikriti = (ctx.get("vikriti") or ctx.get("dosha") or "").strip()

                if not namc_code or not DOSHA_RE.match(prakriti) or not DOSHA_RE.match(vikriti):
                    skipped_no_key += 1
                    continue

                state = f"{namc_code}_{prakriti}_{vikriti}"

                # Try structured plan from feedback columns first
                final_plan = json.loads(fb.final_plan or fb.ai_plan or "{}")

                # If plan is empty, reconstruct from AyushTreatment columns
                if not final_plan or not final_plan.get("herbs"):
                    tx = treatments.get(fb.medical_record_id)
                    if tx:
                        def _csv_to_list(val):
                            return [s.strip() for s in (val or "").split(",") if s.strip()]
                        herbs_list = _csv_to_list(tx.herbs_prescribed)
                        yoga_list = _csv_to_list(tx.yoga_prescribed)
                        diet_list = _csv_to_list(tx.diet_plan)
                        final_plan = {
                            "herbs": [{"name": h} for h in herbs_list],
                            "yoga": [{"practice": y} for y in yoga_list],
                            "diet": diet_list,
                            "lifestyle": [],
                        }

                added = json.loads(fb.added_herbs or "[]")
                removed = json.loads(fb.removed_herbs or "[]")
                rating = normalize_rating(fb.doctor_rating)

                action_keys = RLRecommendationService._plan_action_keys(final_plan, removed)
                if not action_keys:
                    no_actions += 1
                    continue

                state_q = q_table.setdefault(state, {})
                for key in action_keys:
                    reward = RLRecommendationService._compute_herb_reward(key, added, removed, rating)
                    old_q = state_q.get(key, 0.0)
                    state_q[key] = float(old_q + LEARNING_RATE * (reward - old_q))
                replayed += 1
            except Exception as e:
                errors += 1
                print(f"  ! error on feedback {fb.id}: {e}")

    after = table_stats(q_table)
    print(f"\nReplayed: {replayed} | skipped (no valid key): {skipped_no_key} | no actions: {no_actions} | errors: {errors}")
    print(f"AFTER:  {after}")

    if DRY_RUN:
        print("\nDRY RUN — nothing written.")
        return

    if os.path.exists(Q_TABLE_PATH):
        backup = os.path.join(MODELS_DIR, f"rl_q_table.backup-{datetime.now():%Y%m%d-%H%M%S}.pkl")
        shutil.copy2(Q_TABLE_PATH, backup)
        print(f"\nBacked up old table -> {backup}")

    joblib.dump(q_table, Q_TABLE_PATH)
    print(f"Wrote new Q-table -> {Q_TABLE_PATH}")

    # Fresh demo baseline = copy of the rebuilt production table
    # (demo loader uses pickle.load, so write with pickle)
    with open(DEMO_Q_TABLE_PATH, 'wb') as f:
        pickle.dump(q_table, f)
    print(f"Reset demo table  -> {DEMO_Q_TABLE_PATH}")
    print("\nDone. Restart (or touch a file of) the backend so it reloads the new table.")


if __name__ == "__main__":
    run()
