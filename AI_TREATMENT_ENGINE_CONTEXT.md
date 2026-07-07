# AI Treatment Engine — Working Context

> Purpose: running record of how the "Generate AI Plan" pipeline actually works, what's real vs
> stale in the live models, and what diagnostic tooling exists — so a new chat can pick up without
> re-deriving this from scratch.
> Last verified against code + live DB: 2026-07-07 (supersedes the 2026-07-04 version — the
> follow-up-outcome commit `597f6db` changed the reward mechanism after that date; see §2/§3).
> Patient clustering (K-Means) still executes in the pipeline but does **not** drive any part of the
> recommendation or RL decision — treat it as inert/decorative wherever it appears below, per
> explicit product direction. Do not feature it in outward-facing material.

## 1. What "Generate AI Plan" actually does — it's retrieval, not an LLM

Doctor fills the Clinical Assessment form on
[src/app/doctor/treatment/[visit_id]/page.tsx](src/app/doctor/treatment/%5Bvisit_id%5D/page.tsx#L264-L329)
→ `POST /api/ml/recommend` → proxies to FastAPI `POST /api/recommend`
([backend/main.py:222](backend/main.py#L222)) → a hybrid engine
([backend/services/hybrid_service.py](backend/services/hybrid_service.py)):

1. **Base retrieval** — substring search of the disease name against
   `backend/data/Codified_Ayurvedic_disease.csv` (NAMASTE-mapped codes)
   ([ISHAAyush_service.py:204-237](backend/services/ISHAAyush_service.py#L204-L237)). Ties broken by
   shortest matching `Name English` string. No match → UI shows "no match found."
2. **RL bandit overlay** — epsilon-greedy (`epsilon=0.2`) contextual bandit, Q-table now keyed by
   **`"{namc_code}_{prakriti}_{vikriti}"`** ([rl_service.py:50-51](backend/services/rl_service.py#L50-L51)),
   not the old `"{cluster_id}_{disease}"` key — changed in commit `597f6db` (2026-07-07). Splices in
   every learned herb/yoga/diet/lifestyle action with a positive Q-value
   ([hybrid_service.py:90-165](backend/services/hybrid_service.py#L90-L165)).

`get_cluster(patient_data)` is still called in this flow and a `cluster_id` is still attached to the
response ([hybrid_service.py:71-78](backend/services/hybrid_service.py#L71-L78)) — but per the code's
own comment ("analytics only — not used for RL state key") it has **zero influence** on which herbs/
yoga get recommended. It's leftover surface area, not a real capability; don't cite it as one.

**No LLM generates the plan text.** A separate LLM agent (`treatment_agent.py`) only helps fill the
form from voice input and is explicitly instructed not to generate the plan itself — retrieval traces
every output to a verified CSV row; an LLM risks hallucinated herb combinations in a clinical setting.
(Since 2026-07-04: `hybrid_service.py` also has an *opt-in* LLM narration step gated by
`ENABLE_LLM_NARRATION`, calling the Modal Gemma endpoint for a 2-3 sentence explanation of the
already-decided plan — off by default, and even when on it explains, it doesn't decide.)

### The "predicted improvement %" heuristic
[ISHAAyush_service.py:458-463](backend/services/ISHAAyush_service.py#L458-L463) — **not a trained
model**: `75 + (10 if prakriti == vikriti else 0)`, capped at 95 (cap never actually engages — only
two possible outputs, 75.0 or 85.0). Ignores age/severity/comorbidities/symptoms entirely; two
patients with the same prakriti/vikriti pair but wildly different severity get an identical number.
Note: the CSV row's own `Doshas`/`Constitution/Prakriti` columns silently override the doctor's
dropdown picks before this runs, if those columns are non-empty for the matched disease
([ISHAAyush_service.py:169-180](backend/services/ISHAAyush_service.py#L169-L180)). Unchanged since
2026-07-04 — still a live gap.

## 2. How the reward signal actually works now — a follow-up outcome, not the prescribe-time rating

**This section fully supersedes the 2026-07-04 version.** The doctor's "Accurate"/"Needs Changes"
click at prescribe time ([page.tsx:962-982](src/app/doctor/treatment/%5Bvisit_id%5D/page.tsx#L962-L982))
is still captured into `TreatmentFeedback.doctor_rating`, but as of commit `597f6db` it **no longer
moves any Q-value** — `retrain_from_feedback()`, the method that used to consume that rating, is not
called from anywhere in current `main.py`. It still exists in `rl_service.py` but is dead code on the
production path.

The real, current reward pathway is a **confirmed follow-up outcome**:

1. At prescribe time, a PENDING `ClinicalOutcomeScore` row is created for the visit
   ([csv_service.py:280-293](backend/services/csv_service.py#L280-L293)) — `target_vital` picked per
   disease (`_get_target_vital`: e.g. HbA1c for diabetes-like conditions, Systolic BP for
   hypertension-like, else generic `Symptom Severity (1-10)`), `baseline_value = null`.
2. When the same patient returns for a follow-up visit (`parent_visit_id` chains it to the original)
   and the doctor records new vitals + explicitly judges the previous plan — **Improved / No Change /
   Worsened** — the frontend calls `POST /api/visits/{visit_id}/outcome`
   ([main.py:1873-1933](backend/main.py#L1873-L1933)).
3. Backend computes a direction-aware `%` change between baseline and follow-up vitals
   (`_VITAL_DIRECTION`/`_VITAL_NORMALISER`, [main.py:1796-1810](backend/main.py#L1796-L1810)), rescales
   to a `signed` value in [-1, 1], then blends it with the doctor's judgment in
   `rl_service.py::_compute_outcome_reward` ([rl_service.py:318-332](backend/services/rl_service.py#L318-L332)):
   the doctor's dropdown picks a **reward band** (`improved` → 0.2 to 1.0, `no_change` → -0.2 to 0.2,
   `worsened` → -1.0 to -0.2), and `signed` only picks the position *within* that band. Code's own
   comment: this "keeps one noisy vitals reading from flipping the doctor's overall clinical call."
4. `apply_followup_outcome()` ([rl_service.py:334-378](backend/services/rl_service.py#L334-L378))
   applies this single blended reward **uniformly** to every herb/yoga/diet/lifestyle action in the
   parent visit's final plan — judges the plan as a whole, not per-item — via
   `Q(s,a) += learning_rate * (reward - Q(s,a))`.

**Live and active, not theoretical:** DB check 2026-07-07 — 15 `ClinicalOutcomeScore` rows total, 10
already closed (`is_retrained=True`) via real confirmed follow-up outcomes, 5 still pending. Only 4 of
the 15 have `baseline_value` resolved (the rest likely hit `_resolve_vital_reading` returning `None` —
e.g. a missing severity/vitals field on the parent or follow-up visit); worth a data-quality pass
before relying on this for a live demo walkthrough.

## 3. How future changes happen — clustering retrain is now a no-op for recommendation quality

`POST /api/prescribe` → `trigger_retraining()` background task
([main.py:264-285](backend/main.py#L264-L285)) now **only** calls `clustering_service.retrain_clusters()`.
The function's own docstring is explicit: *"Does NOT call retrain_from_feedback(): production Q-values
are only ever moved by a confirmed follow-up outcome... Does NOT call retrain_from_outcomes(): that
batch/backfill path would race with the live apply_followup_outcome path."* Since clustering doesn't
feed the RL state or the recommendation logic at all (§1), this background retrain currently has no
effect on what any doctor sees recommended — it only refits a cluster_id field that gets attached to
responses for display/analytics and nothing else.

The only path that moves a Q-value is `POST /api/visits/{visit_id}/outcome` →
`rl_service.apply_followup_outcome()` (§2). The mechanism for "future changes" is still not editing a
saved plan — it's that the *next* patient with the same NAMC code + Prakriti + Vikriti gets a
different recommendation because the Q-table shifted. No plan-level versioning exists: `/api/prescribe`
always inserts new `AyushTreatment`/`TreatmentFeedback` rows rather than updating, and
`GET /api/visits/{visit_id}` reads back via `.first()` with no `ORDER BY` — re-submitting a plan for
the same visit has no deterministic "latest" guarantee. Unchanged since 2026-07-04.

## 4. Concrete gaps found (updated 2026-07-07 against live DB + current code)

1. ~~RL is functionally dormant on historical data~~ — **RESOLVED / MOOT.** The old gap (0 of 14,688
   feedback rows had `cluster_id` in `ml_context`) doesn't apply to the new state key: live DB check
   2026-07-07 shows **14,706 of 14,709** `TreatmentFeedback` rows now carry `namc_code` in
   `ml_context` (backfilled by commit `4a2eaea`, "add vital signs backfill and follow-up chaining
   service"). Moot either way, since prescribe-time feedback no longer drives any Q-update regardless
   of what's in `ml_context` — only follow-up outcomes do (§2/§3).
2. ~~Clustering model was stale / cluster indices unstable across retrains~~ — **no longer worth
   tracking.** Clustering isn't part of the RL or recommendation decision path; don't spend further
   diagnostic effort here, and don't feature clustering as a capability in outward-facing material.
3. **`ClinicalOutcomeScore` is now live, not unused.** 15 rows total (2026-07-07), 10 closed via real
   confirmed follow-up outcomes, 5 pending — a real behavior change from the 2026-07-04 finding of 0
   rows. Only 4/15 have `baseline_value` resolved; check `_resolve_vital_reading` fallbacks
   (`severity` field parsing) if this needs to look cleaner for a demo.
4. **NEW — reward-band blending is judgment-dominant by design.** "Improved" always yields a reward in
   [0.2, 1.0] and "Worsened" always yields [-1.0, -0.2] regardless of how small the vitals change was;
   `signed` only moves the value within that band. A doctor's dropdown click fully determines the
   direction of every Q-update for that plan — vitals can't override it. This is a deliberate clinical-
   safety design choice (per the code's own comment), but worth being ready to explain if asked during
   Q&A why a marginal vitals change can still produce a large reward swing.

## 5. Diagnostic tool: `backend/scripts/model_report.py`

Generates a self-contained HTML report (`backend/reports/model_report.html`, tracked in git as a
point-in-time snapshot — re-run and re-add to refresh it). **Predates the follow-up-outcome mechanism
(§2/§3)** — it was built around the old cluster_id+disease state key and `retrain_from_feedback()`
path, so its walkthroughs and gap analysis no longer describe the live reward mechanism. Treat its
output as historical/illustrative only until it's updated to reflect `apply_followup_outcome()` and the
NAMC+Prakriti+Vikriti state key; don't cite its numbers as current without re-checking against §2-§4
above first.

**Safety model (still accurate):** copies the real `.pkl` files to a temp sandbox before any refit; the
one production method that also writes to the DB (`retrain_from_feedback`'s `db.commit()` — now dead
code, see §2) was reimplemented read-only with no ORM writes. Asserts file mtime/size and
`is_retrained` counts are identical before/after the run.

Run: `cd backend && source venv/bin/activate && python3 scripts/model_report.py --open`

## 6. Open follow-ups (not yet done)

- Update or retire `model_report.py` — it documents a reward mechanism (`retrain_from_feedback` +
  cluster_id+disease keys) that's no longer live. Either rewrite it around `apply_followup_outcome()`
  and the NAMC+Prakriti+Vikriti key, or clearly mark it deprecated so nobody cites its numbers as
  current.
- Data-quality pass on the 11/15 `ClinicalOutcomeScore` rows missing `baseline_value` — confirm whether
  `_resolve_vital_reading` is silently failing on a specific vital type or a specific visit shape.
- Decide whether plan-level versioning/audit trail is worth adding (currently every `/api/prescribe`
  call creates new rows with no "latest" guarantee on read-back). Unchanged from 2026-07-04.
- ~~Backfill `cluster_id` into historical `TreatmentFeedback.ml_context` rows~~ — dropped: clustering
  isn't part of the RL decision anymore, so this would no longer accomplish anything.
