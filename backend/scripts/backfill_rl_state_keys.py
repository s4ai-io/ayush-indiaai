"""
One-time migration: patch ml_context in TreatmentFeedback rows
to add namc_code and dosha_state using the ISHAAyush lookup.

Usage:
  python3 scripts/backfill_rl_state_keys.py           # real run
  python3 scripts/backfill_rl_state_keys.py --dry-run  # count only
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from models import SessionLocal, TreatmentFeedback
from services.ISHAAyush_service import ISHAAyush_service

DRY_RUN = "--dry-run" in sys.argv
BATCH_SIZE = 500

def run():
    # Ensure dataset is loaded
    ISHAAyush_service.initialize()

    with SessionLocal() as db:
        total = db.query(TreatmentFeedback).count()
        print(f"Total feedback rows: {total}")

        patched = skipped = already_done = 0
        offset = 0

        while True:
            # Stable order — without it, committed updates shuffle Postgres row
            # order and offset pagination skips/revisits rows across batches
            batch = db.query(TreatmentFeedback).order_by(TreatmentFeedback.id).offset(offset).limit(BATCH_SIZE).all()
            if not batch:
                break

            for fb in batch:
                try:
                    ctx = json.loads(fb.ml_context or "{}")
                except Exception:
                    ctx = {}

                disease  = ctx.get("disease", "")
                prakriti = ctx.get("prakriti", "")
                # Historical (pre-revamp) rows store the imbalance under "dosha"
                vikriti  = ctx.get("vikriti") or ctx.get("dosha", "")

                if ctx.get("namc_code"):
                    if ctx.get("vikriti"):
                        already_done += 1
                        continue
                    # Previous run resolved namc_code but missed vikriti (old
                    # rows store it under "dosha") — repair the dosha state.
                    ctx["vikriti"] = vikriti
                    ctx["dosha_state"] = f"{prakriti}_{vikriti}"
                    if not DRY_RUN:
                        fb.ml_context = json.dumps(ctx)
                    patched += 1
                    continue

                if not disease:
                    skipped += 1
                    continue

                # Resolve namc_code from disease string using multi-stage matching:
                # 1. Full string (e.g. "Constipation (Vibandha)")
                # 2. English part only (e.g. "Constipation")
                # 3. Sanskrit part inside parens (e.g. "Vibandha")
                # 4. TF-IDF suggestion fallback
                try:
                    import re as _re
                    row = ISHAAyush_service._direct_search(disease)

                    if row is None:
                        # Try English part before parenthesis
                        eng = _re.sub(r'\s*\(.*\)', '', disease).strip()
                        if eng and eng != disease:
                            row = ISHAAyush_service._direct_search(eng)

                    if row is None:
                        # Try Sanskrit part inside parentheses
                        m = _re.search(r'\(([^)]+)\)', disease)
                        if m:
                            row = ISHAAyush_service._direct_search(m.group(1).strip())

                    if row is None:
                        # TF-IDF suggestion fallback
                        suggestions = ISHAAyush_service.get_suggestions(disease, 1)
                        if suggestions:
                            row = ISHAAyush_service._direct_search(suggestions[0])

                    if row is not None:
                        namc_code = row.get("NAMC_CODE") if hasattr(row, "get") else (
                            row["NAMC_CODE"] if "NAMC_CODE" in row.index else ""
                        )
                        namc_code = str(namc_code) if namc_code else ""
                    else:
                        namc_code = ""
                except Exception:
                    namc_code = ""

                if not namc_code:
                    skipped += 1
                    continue

                ctx["namc_code"]   = namc_code
                ctx["vikriti"]     = vikriti
                ctx["dosha_state"] = f"{prakriti}_{vikriti}"

                if not DRY_RUN:
                    fb.ml_context = json.dumps(ctx)

                patched += 1

            if not DRY_RUN:
                db.commit()

            offset += BATCH_SIZE
            print(f"  Processed {min(offset, total)}/{total} | patched={patched} skipped={skipped} already_done={already_done}")

        print(f"\n{'DRY RUN - ' if DRY_RUN else ''}Done.")
        print(f"  Patched:      {patched}")
        print(f"  Already done: {already_done}")
        print(f"  Skipped:      {skipped}")

if __name__ == "__main__":
    run()
