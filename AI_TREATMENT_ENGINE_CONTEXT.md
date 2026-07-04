# AI Treatment Engine — Working Context

> Purpose: running record of how the "Generate AI Plan" pipeline actually works, what's real vs
> stale in the live models, and what diagnostic tooling exists — so a new chat can pick up without
> re-deriving this from scratch.
> Last verified against code + live DB: 2026-07-04.

## 1. What "Generate AI Plan" actually does — it's retrieval, not an LLM

Doctor fills the Clinical Assessment form on
[src/app/doctor/treatment/[visit_id]/page.tsx](src/app/doctor/treatment/%5Bvisit_id%5D/page.tsx#L264-L329)
→ `POST /api/ml/recommend` → proxies to FastAPI `POST /api/recommend`
([backend/main.py:222](backend/main.py#L222)) → a 3-stage hybrid engine
([backend/services/hybrid_service.py](backend/services/hybrid_service.py)):

1. **Base retrieval** — substring search of the disease name against
   `backend/data/Codified_Ayurvedic_disease.csv` (NAMASTE-mapped codes)
   ([ISHAAyush_service.py:204-237](backend/services/ISHAAyush_service.py#L204-L237)). Ties broken by
   shortest matching `Name English` string. No match → UI shows "no match found."
2. **Patient clustering** — scikit-learn K-Means (`n_clusters=10`) over
   age/gender/prakriti/vikriti/disease/severity
   ([patient_clustering_service.py](backend/services/patient_clustering_service.py)).
3. **RL bandit overlay** — epsilon-greedy (`epsilon=0.2`) contextual bandit, Q-table keyed by
   `"{cluster_id}_{disease}"` ([rl_service.py:47-74](backend/services/rl_service.py#L47-L74)); splices
   in a learned herb/yoga if the Q-value is positive.

**No LLM generates the plan text.** A separate LLM agent (`treatment_agent.py`) only helps fill the
form from voice input and is explicitly instructed not to generate the plan itself. This is a
deliberate design choice per `backend/docs/AyurGenixAI_Model_Report.md` — retrieval traces every
output to a verified CSV row; an LLM risks hallucinated herb combinations in a clinical setting.

### The "predicted improvement %" heuristic
[ISHAAyush_service.py:458-463](backend/services/ISHAAyush_service.py#L458-L463) — **not a trained
model**: `75 + (10 if prakriti == vikriti else 0)`, capped at 95 (cap never actually engages — only
two possible outputs, 75.0 or 85.0). Ignores age/severity/comorbidities/symptoms entirely; two
patients with the same prakriti/vikriti pair but wildly different severity get an identical number.
Note: the CSV row's own `Doshas`/`Constitution/Prakriti` columns silently override the doctor's
dropdown picks before this runs, if those columns are non-empty for the matched disease
([ISHAAyush_service.py:169-180](backend/services/ISHAAyush_service.py#L169-L180)).

## 2. How "accuracy" is captured — a doctor rating, not a validation gate

No automated correctness check runs before the plan is shown. The real signal: after
reviewing/editing, the doctor clicks **"Accurate"** or **"Needs Changes"**
([page.tsx:962-982](src/app/doctor/treatment/%5Bvisit_id%5D/page.tsx#L962-L982)), submitted with the
prescription (`POST /api/prescribe`) and stored as a `TreatmentFeedback` row
([models.py:68-79](backend/models.py#L68-L79)) with reward mapping `positive→+1.0`,
`negative→-1.0` ([rl_service.py:100-108](backend/services/rl_service.py#L100-L108)). A second,
objective pathway exists — `ClinicalOutcomeScore` (before/after vitals → calculated reward,
[models.py:81-93](backend/models.py#L81-L93)) — but has **0 rows** as of this writing; unused so far.

## 3. How future changes happen — a closed learning loop, not plan editing

`POST /api/prescribe` → `trigger_retraining()` background task
([main.py:246-266](backend/main.py#L246-L266)): `retrain_clusters()` (refits K-Means on all
historical `MedicalRecord`+`Patient` rows) → `retrain_from_feedback()` / `retrain_from_outcomes()`
(TD update `Q(s,a) += 0.1 * (reward - Q(s,a))`). The mechanism for "future changes" is **not**
editing a saved plan — it's that the *next* patient in the same cluster/disease gets a different
recommendation because the Q-table shifted. No plan-level versioning exists: `/api/prescribe`
always inserts new `AyushTreatment`/`TreatmentFeedback` rows rather than updating, and
`GET /api/visits/{visit_id}` reads back via `.first()` with no `ORDER BY` — re-submitting a plan for
the same visit has no deterministic "latest" guarantee.

## 4. Concrete gaps found (verified against live DB, 2026-07-04)

1. **RL is functionally dormant on historical data.** `retrain_from_feedback()` requires
   `cluster_id` inside `TreatmentFeedback.ml_context`
   ([rl_service.py:90-96](backend/services/rl_service.py#L90-L96)) — confirmed via direct SQL scan
   that **0 of 14,688** existing feedback rows have it (their `ml_context` only has
   `disease`/`dosha`/`prakriti`/`season`, e.g. `{"disease":"Constipation (Vibandha)","dosha":"Vata",...}`).
   Every one gets silently marked `is_retrained=True` and skipped, contributing nothing, despite
   11,120 positive / 3,568 negative real ratings on file. Almost certainly because this data was bulk
   **synthetic-seeded** directly into Postgres rather than produced through the real
   `/api/prescribe` flow (which does stamp `cluster_id` correctly).
2. **The live clustering model was stale.** Recognized only 35 disease categories; ~1/3 of real
   patients (5,750 / 16,126) had a diagnosis the model had never seen, so `OneHotEncoder
   (handle_unknown="ignore")` silently zeroed disease's contribution to their cluster assignment for
   those patients. **Update:** the real `patient_cluster_model.pkl` was actually retrained in commit
   `0519803` (2026-07-04 17:01, your own commit) — file grew 16.5KB→83KB. Re-run
   `model_report.py` to check current staleness before relying on this finding.
3. **K-Means cluster indices aren't stable across retrains.** "Cluster 8" before a refit and
   "Cluster 8" after are not guaranteed to be the same population — which also means Q-table
   `cluster_id` keys can go stale the moment `retrain_clusters()` runs again.
4. **`ClinicalOutcomeScore` is unused** — 0 rows, so the objective (non-subjective) reward pathway
   has never contributed anything yet.

## 5. Diagnostic tool: `backend/scripts/model_report.py`

Generates a self-contained HTML report (`backend/reports/model_report.html`, tracked in git as a
point-in-time snapshot — re-run and re-add to refresh it) showing:
- Current cluster sizes/characterization and Q-table contents, computed live.
- The `cluster_id` gap above, recomputed live (not hardcoded).
- A sandboxed clustering-retrain demo (real data + 150 synthetic patients of one profile) with a
  **fair** before/after inertia comparison (both measured on the same real rows — sklearn's raw
  `.inertia_` is not comparable across separate fits, which was a bug in the first draft of this
  script, since fixed).
- A read-only replay of `retrain_from_feedback()`'s decision logic against real feedback rows (no
  commit, proves the gap above), plus a synthetic step-by-step walkthrough of the
  `Q(s,a) += lr * (reward - Q(s,a))` update rule.

**Safety model:** copies the real `.pkl` files to a temp sandbox before any refit; the one
production method that also writes to the DB (`retrain_from_feedback`'s `db.commit()`) is
reimplemented read-only with no ORM writes. Asserts file mtime/size and `is_retrained` counts are
identical before/after the run — raises if that's ever violated.

Run: `cd backend && source venv/bin/activate && python3 scripts/model_report.py --open`

## 6. Open follow-ups (not yet done)

- Backfill `cluster_id` into historical `TreatmentFeedback.ml_context` rows (re-derive via the
  clustering pipeline from each row's stored disease/prakriti/vikriti) so `retrain_from_feedback()`
  can actually learn from the 14,688 ratings already on file.
- Confirm what triggered the 2026-07-04 17:01 real `retrain_clusters()` (commit `0519803`) and
  re-check current model staleness.
- Decide whether plan-level versioning/audit trail is worth adding (currently every `/api/prescribe`
  call creates new rows with no "latest" guarantee on read-back).
