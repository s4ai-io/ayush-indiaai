# Learning Coverage — Working Notes

> Purpose: what the "Learning Coverage" tab is, how the pieces fit together, and one
> important pending step before it shows its full picture.
> Last verified against code: 2026-07-06 (commit `66aa656` + follow-up wiring fix).

## 1. What problem this solves

The RL bandit ([backend/services/rl_service.py](backend/services/rl_service.py)) only
"knows" a herb/yoga/diet/lifestyle item for a disease-dosha state once a doctor has
actually prescribed and rated it. With ~2,900 diseases in the NAMASTE catalog and only a
handful of doctor interactions to date, there was no way to see **which diseases have any
learning at all** versus which are still running on pure CSV retrieval. Learning Coverage
is that view.

## 2. Architecture — three pieces

```
  backfill_rl_state_keys.py          rebuild_q_table.py              /api/model/learning-coverage
  (DB migration, one-time)     →     (Q-table migration, one-time) → (live read endpoint)
  stamps namc_code + vikriti          replays ALL TreatmentFeedback     groups rl_service.q_table
  into historical                     rows into a fresh                by NAMC code, computes
  TreatmentFeedback.ml_context        {namc_code}_{prakriti}_{vikriti}  per-category learned
                                       Q-table (old cluster/disease     counts + status
                                       keyed states are dropped)
```

- **[backend/scripts/backfill_rl_state_keys.py](backend/scripts/backfill_rl_state_keys.py)**
  — patches `ml_context` on every `TreatmentFeedback` row so it carries `namc_code` (resolved
  from the stored disease string) and `vikriti` (older rows store this under `dosha` instead —
  the script now checks both). **Already run** — confirmed 0 of 14,696 feedback rows are
  missing `namc_code`/`vikriti` in Postgres.
- **[backend/scripts/rebuild_q_table.py](backend/scripts/rebuild_q_table.py)** — a from-scratch
  replay of every `TreatmentFeedback` row's reward into a brand-new Q-table keyed by the
  stable `{namc_code}_{prakriti}_{vikriti}` format (as opposed to the old, cluster-ID-based
  key that goes stale on every K-Means refit). Falls back to reconstructing the prescribed
  plan from `AyushTreatment.herbs_prescribed`/`yoga_prescribed`/`diet_plan` when a row's
  `final_plan`/`ai_plan` JSON is empty. Backs up the existing `rl_q_table.pkl` before
  overwriting, and resets `demo_q_table.pkl` to match. **⚠️ Not yet run for real** — see
  §4 below.
- **`GET /api/model/learning-coverage`** ([backend/main.py:1414](backend/main.py#L1414)) —
  reads the live in-memory `rl_service.q_table`, groups states by NAMC code (ignoring
  legacy-format keys, counted separately as `legacy_states`), and returns per-disease
  `n_states`, `n_actions`, `n_learned`, category breakdowns (`herbs_learned`/`yoga_learned`/
  `diet_learned`/`lifestyle_learned`), `max_q`, `top_learned` (top 5 by Q-value), and a
  `status` of `"learned"` (≥1 positive-Q action) or `"learning"` (states exist, nothing
  positive yet). A companion branch was added to the existing
  `GET /api/model/q-table-state?namc_code=...` endpoint (no dosha params) to return every
  dosha-state for one disease, used by the inspection modal.

## 3. Frontend

`Learning Coverage` tab in
[src/app/admin/model-dashboard/page.tsx](src/app/admin/model-dashboard/page.tsx)
(`LearningCoverageTab`):
- 4 stat tiles: Total Diseases (catalog) · With Learning Data · Learned · Learning.
- Filter pills (All / Learned / Learning) + search by name or NAMC code.
- Table of diseases with data: status badge, dosha-state count, learned-action count with
  emoji category breakdown (🌿 herb, 🧘 yoga, 🥗 diet, 🌿 lifestyle), max Q, top learned
  items. Diseases with **zero** Q-table data are not listed (by design — with ~2,900
  catalog diseases, listing all of them would mostly show "no data").
- Clicking a row opens an inspection modal (`InspectDiseaseModalContent`) showing every
  dosha-state for that disease with full Q-value tables, plus a **"Try in Live Demo →"**
  button that jumps to the Live Demo tab with that disease pre-filled.
- The pre-existing Live Demo tab is unmodified in behavior — only lifted `selectedDisease`
  state up to the page level so the two tabs can hand off a disease name.

## 4. Known pending step — the Q-table rebuild hasn't run yet

`rebuild_q_table.py` exists and its `--dry-run` has been verified to work: replaying all
history produces **~76 new-format states across ~72 diseases with ~28 learned actions**,
versus the live table's current **~9 new-format states across ~8 diseases** (240+ legacy
states). Until the real run happens, the Learning Coverage tab is accurate but shows only
the small slice of learning gathered from live/demo interactions since the state-key format
changed — not the full history.

**To apply it:**
```bash
cd backend
./venv/bin/python scripts/rebuild_q_table.py --dry-run   # confirm before/after counts
./venv/bin/python scripts/rebuild_q_table.py             # backs up old table, writes new one
touch main.py   # dev server runs with reload=True; this reloads the in-memory Q-table
```
After running, `GET /api/model/learning-coverage` should report `legacy_states: 0` and
`diseases_with_data` in the dozens instead of single digits, and `POST /api/recommend` for
diseases with historical ratings (e.g. Diabetes/Vata/Pitta) should surface more
`ai_learned: true` items.

This is a one-time migration — re-run it any time historical `TreatmentFeedback` data
changes materially (e.g. after a large backfill or bulk data import), since it fully
replaces the Q-table rather than incrementally updating it.
