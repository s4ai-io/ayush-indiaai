# AI Treatment Engine — Revamped Architecture

> **Status:** North-star specification for the full pipeline revamp.
> Every design decision here is a deliberate choice, not a default.
> The existing `AI_TREATMENT_ENGINE_CONTEXT.md` remains as the historical record of the current state.
> Last updated: 2026-07-04

---

## 1. Executive Summary

The AYUSH AI Treatment Engine generates personalised Ayurvedic treatment plans by combining codified clinical knowledge, patient-similarity clustering, reinforcement learning from doctor feedback, and LLM-generated explanation. It is explicitly **not** an LLM that generates herb recommendations — every herb, yoga practice, and dietary guideline traces directly to a verified row in the ISHAAyush/NAMASTE dataset. The LLM only narrates *why* those choices were made, after the plan is already locked. This stack — retrieval → clustering → RL → trained confidence model → LLM narration — is designed to be clinically safe, continuously improving, and fully auditable.

---

## 2. Design Principles

| Principle | What it means in practice |
|---|---|
| **Traceability over generation** | Every herb in the output maps to a specific NAMC-coded CSV row. No LLM can add or remove herbs. |
| **Stable learning** | RL state keys are `namc_code + dosha_state` — they never shift. Cluster IDs refit freely without invalidating learned Q-values. |
| **Honest confidence** | The improvement % is a trained regression model with a confidence interval. We do not show a number we cannot defend. |
| **Layered explainability** | Every output element has a structured reason string, independent of whether the LLM is available. |
| **LLM as narrator, not prescriber** | The LLM sees the finalised plan and explains it. It cannot modify the herb list. |
| **Objective signals over subjective** | ClinicalOutcomeScore (follow-up vitals) outweighs doctor ratings as a reward signal. |

---

## 3. Full System Architecture

> Clustering has been moved out of the recommendation pipeline entirely.
> It runs asynchronously after prescribe and feeds only into the
> analytics dashboard. It does not block or affect the recommendation.

```
  ┌────────────────────────────────────────────────────────┐
  │                     PATIENT INPUT                      │
  │  disease · prakriti · vikriti · age · gender           │
  │  severity · symptoms · comorbidities                   │
  └───────────────────────┬────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │  LAYER 1 — SEMANTIC DISEASE MATCHING                   │
  │                                                        │
  │  Sentence embeddings → cosine similarity               │
  │  Returns: top-3 candidate diseases + confidence scores │
  │  Assigns: NAMC code (stable identifier for all layers) │
  │                                                        │
  │  confidence ≥ 0.85 → auto-select top match             │
  │  confidence < 0.85 → surface alternatives to doctor    │
  └───────────────────────┬────────────────────────────────┘
                          │  namc_code
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │  LAYER 2 — KNOWLEDGE BASE RETRIEVAL                    │
  │                                                        │
  │  ISHAAyush CSV lookup by NAMC code                     │
  │  Extracts: herbs · yoga · diet · lifestyle             │
  │            formulation · prognosis · complications     │
  │                                                        │
  │  SAFETY ANCHOR: no generation, pure retrieval          │
  └───────────────────────┬────────────────────────────────┘
                          │  base treatment plan
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │  LAYER 3 — REINFORCEMENT LEARNING OPTIMIZATION         │
  │                                                        │
  │  Algorithm: Epsilon-greedy contextual bandit           │
  │  State key: "{namc_code}_{prakriti}_{vikriti}"         │
  │                                                        │
  │  If Q(state, action) > 0 AND action not in base plan:  │
  │    → insert learned herb at rank 1, flag as AI-learned │
  │                                                        │
  │  Rewards from: doctor ratings · edits · outcome vitals │
  └───────────────────────┬────────────────────────────────┘
                          │  possibly modified herb list
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │  LAYER 4 — IMPROVEMENT CONFIDENCE MODEL                │
  │                                                        │
  │  Algorithm: Gradient Boost Regressor                   │
  │  Features: age, severity, comorbidity_count,           │
  │            symptom_count, dosha_match, season,         │
  │            namc_code                                   │
  │  Target: ClinicalOutcomeScore.percentage_change        │
  │                                                        │
  │  Output: predicted_improvement + confidence_interval   │
  │          e.g. "72% (CI: 64–80%)"                       │
  └───────────────────────┬────────────────────────────────┘
                          │  finalised plan + confidence score
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │  LAYER 5 — LLM NARRATION                               │
  │                                                        │
  │  Model: Gemma-4-12B / Claude API                       │
  │  Input: locked herb list, NAMC code, patient profile   │
  │  Task: explain WHY each herb was chosen                │
  │                                                        │
  │  HARD CONSTRAINT: LLM cannot modify the herb list.     │
  │  Fallback: structured explainability strings if LLM    │
  │            is unavailable.                             │
  └───────────────────────┬────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │               TREATMENT RECOMMENDATION                 │
  │                                                        │
  │  · herbs (with dosage + AI-learned flag if applicable) │
  │  · yoga · diet · lifestyle                             │
  │  · predicted_improvement + confidence_interval         │
  │  · duration_weeks                                      │
  │  · namc_code + namc_term (Devanagari + English)        │
  │  · explanation_text (LLM narration)                    │
  │  · explainability[] (structured reason strings)        │
  └───────────────────────┬────────────────────────────────┘
                          │
                          ▼
  ┌────────────────────────────────────────────────────────┐
  │               DOCTOR REVIEW & FEEDBACK                 │
  │                                                        │
  │  Three possible actions (all trigger learning):        │
  │                                                        │
  │  A) Accept unchanged + Accurate → strong positive      │
  │  B) Edit (add/remove herbs) ± rate → diff-based signal │
  │  C) Accept unchanged, no rating → implicit weak +      │
  │                                                        │
  │  POST /api/prescribe stores:                           │
  │    · original_ai_plan  (what AI generated)             │
  │    · final_plan        (what doctor submitted)         │
  │    · added_herbs / removed_herbs (computed diff)       │
  │    · doctor_rating (may be empty)                      │
  │    · namc_code, dosha_state in ml_context              │
  └──────┬────────────────────────────┬───────────────────┘
         │                            │
         ▼ (immediate background)     ▼ (4 weeks later)
  ┌──────────────────────┐    ┌───────────────────────────┐
  │  RL RETRAIN          │    │  OUTCOME SCORE ENTRY       │
  │                      │    │                            │
  │  Diff-aware rewards  │    │  Doctor enters follow-up   │
  │  applied per herb:   │    │  vital (HbA1c, PEFR, etc.) │
  │  · added + rating    │    │  → ClinicalOutcomeScore    │
  │  · kept + rating     │    │    row updated             │
  │  · removed + rating  │    │  → triggers RL + GBM       │
  │  · implicit accept   │    │    retrain with objective  │
  └──────┬───────────────┘    │    reward signal           │
         │                    └───────────────────────────┘
         ▼ (async, does not block recommendation)
  ┌──────────────────────────────────────────────────────┐
  │  CLUSTERING (post-facto analytics only)              │
  │                                                      │
  │  K-Means refit on all MedicalRecord rows             │
  │  Output feeds Model Intelligence Dashboard only      │
  │  No effect on RL, improvement model, or responses    │
  └──────────────────────────────────────────────────────┘
```

---

## 4. Layer-by-Layer Deep Dive

### Layer 1 — Semantic Disease Matching

**Purpose:** Reliably resolve a free-text disease name to a verified NAMC code. This code is the single identifier that flows through every downstream layer.

**Current state:** Substring search (case-insensitive) → TF-IDF cosine fallback. Returns one result with no confidence score. Wrong match passes silently through the entire pipeline.

**Target state:**

```
  Doctor types "Madhumeh"
         │
         ▼
  Embed query with sentence-transformer
  (pre-computed embeddings for all ~600 disease names in CSV)
         │
         ▼
  Cosine similarity → ranked candidates:
  ┌─────────────────────────────────┬────────┬──────────────┐
  │ Disease                         │ NAMC   │ Confidence   │
  ├─────────────────────────────────┼────────┼──────────────┤
  │ Madhumeha (Diabetes Mellitus)   │ AM-042 │ 0.94  ← auto │
  │ Prameha (Urinary disorders)     │ AM-039 │ 0.61         │
  │ Sthoulya (Obesity)              │ AM-051 │ 0.48         │
  └─────────────────────────────────┴────────┴──────────────┘
         │
  confidence ≥ 0.85: auto-select, proceed
  confidence < 0.85: show table to doctor, request confirmation
```

**Key files to change:**
- `backend/services/ISHAAyush_service.py` — add `_semantic_search()` method
- `backend/data/` — add pre-computed `disease_embeddings.pkl`
- `backend/main.py` — surface alternatives in `/api/recommend` response when confidence is low

**Bug to fix:** `ISHAAyush_service.py:169-180` silently overwrites doctor's prakriti/vikriti with CSV column values. Change to log a warning instead of substituting.

---

### Layer 2 — Knowledge Base Retrieval

**Purpose:** Extract the codified Ayurvedic treatment for the matched disease. This is the system's safety anchor.

**Current state:** Works correctly. No changes to the retrieval logic.

**Target state:** Same algorithm, lookup by NAMC code instead of disease string (more precise, avoids any residual ambiguity).

**What does NOT change:**
- ISHAAyush CSV as the authoritative source
- Herb/yoga/diet extraction logic
- No LLM involvement at this layer

---

### Layer 3 — Reinforcement Learning Optimization

**Purpose:** Learn which herbs and yoga practices produce the best outcomes for a given disease-dosha combination, and surface those learnings in future recommendations.

**Current state:** State key is `"{cluster_id}_{disease}"`. Problem: cluster IDs shift on every K-Means refit, making all Q-table entries stale. Additionally, 0 of 14,688 historical feedback rows contain `cluster_id` in `ml_context`, so the RL bandit has never actually updated from real data.

**Target state:**

```
  State key: "{namc_code}_{prakriti}_{vikriti}"
  Examples:
    "AM-042_Vata_Pitta"    (Madhumeha, Vata prakriti, Pitta vikriti)
    "AM-012_Kapha_Kapha"   (Jwara, Kapha prakriti, Kapha vikriti)

  Total possible states:
    ~600 NAMC codes × 9 dosha combinations = ~5,400 states
    (sparse in practice — most disease-dosha combos have no data)
```

**Q-update formula (unchanged):**
```
  Q(s, a) = Q(s, a) + α × (reward − Q(s, a))
  α = 0.1, ε = 0.2 (20% explore, 80% exploit)
```

**What happens when the doctor manually edits the prescription:**

This is the most important — and currently broken — feedback path.

```
  CURRENT (BROKEN) BEHAVIOUR
  ──────────────────────────
  AI recommends: [Gymnema, Bitter Melon, Turmeric]
  Doctor adds:   Guchi Powder
  Doctor removes: Turmeric
  Doctor submits: [Gymnema, Bitter Melon, Guchi Powder]

  csv_service.py:220:
    ai_plan = json.dumps(treatment_plan)   ← treatment_plan is the
                                              EDITED list the doctor
                                              submitted, NOT the
                                              original AI output.

  rl_service.py:122:
    herbs = ai_plan.get("herbs", [])       ← reads [Gymnema, Bitter Melon,
                                              Guchi Powder] as if the AI
                                              suggested all three.

  Result:
    · Guchi Powder gets the same reward as Gymnema — but the AI
      never suggested it; the doctor added it.
    · Turmeric gets NO negative signal — the AI suggested it,
      the doctor rejected it, but the system never notices.
    · The diff is completely lost.
```

```
  TARGET (FIXED) BEHAVIOUR
  ─────────────────────────
  At /api/recommend time, the backend generates the original plan
  and stores it in the session / response payload as original_ai_plan.

  At /api/prescribe time, the frontend sends BOTH:
    · original_ai_plan  (what the AI generated, unmodified)
    · final_plan        (what the doctor submitted after editing)

  csv_service.py computes the diff:
    added_by_doctor   = final_herbs − original_herbs
    removed_by_doctor = original_herbs − final_herbs
    kept_by_doctor    = original_herbs ∩ final_herbs

  TreatmentFeedback now stores:
    · original_ai_plan  (new field)
    · final_plan        (renamed from ai_plan, stores the actual final)
    · added_herbs       (new field, list of doctor additions)
    · removed_herbs     (new field, list of doctor removals)
```

**Doctor-edit reward logic — Guchi Powder example:**

```
  Doctor adds Guchi Powder, rates "Accurate"
  ──────────────────────────────────────────
  State: AM-042_Vata_Pitta  (Madhumeha, Vata, Pitta)

  Signal mapping:
  ┌──────────────────────┬────────────────────────────┬──────────┐
  │ Herb                 │ Category                   │ Reward   │
  ├──────────────────────┼────────────────────────────┼──────────┤
  │ Gymnema              │ kept by doctor + Accurate  │ +1.0     │
  │ Bitter Melon         │ kept by doctor + Accurate  │ +1.0     │
  │ Guchi Powder         │ ADDED by doctor + Accurate │ +1.5     │
  │                      │  (higher signal: intentional│         │
  │                      │   expert addition)         │          │
  │ Turmeric             │ REMOVED by doctor          │ −0.8     │
  │                      │  (doctor rejected it)      │          │
  └──────────────────────┴────────────────────────────┴──────────┘

  After enough such signals for AM-042_Vata_Pitta:
    Q(state, "Guchi Powder") rises above 0
    → next similar patient gets Guchi Powder surfaced by RL
    Q(state, "Turmeric") drops
    → Turmeric stops being surfaced for this state

  Does Guchi Powder get added to the ISHAAyush CSV? NO.
  The CSV is the curated, verified knowledge base.
  RL-learned herbs are always flagged as "AI-learned" in the output.
  They enter the CSV only through a separate clinical curation process
  (out of scope for this engine).
```

**Doctor removes a herb + rates "Needs Changes":**

```
  Doctor removes Gymnema, adds nothing, rates "Needs Changes"
  ─────────────────────────────────────────────────────────────
  Gymnema (removed + Needs Changes) → reward = −1.0
  This is the strongest negative signal.
  The system has two reasons to reduce Q(state, Gymnema):
    1. Doctor explicitly removed it.
    2. Doctor rated the outcome negatively.
```

**Complete reward signal table:**

```
  ┌──────────────────────────────────────────────────┬──────────┐
  │ Signal                                           │ Reward   │
  ├──────────────────────────────────────────────────┼──────────┤
  │ ClinicalOutcomeScore.percentage_change           │ 0.0–1.0  │
  │   (objective, normalised from real vitals —      │          │
  │    overrides rating-based reward for kept herbs) │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor ADDED herb + Accurate rating              │ +1.5     │
  │  (intentional expert addition, confirmed good)   │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor ADDED herb + NO rating (implicit accept)  │ +0.7     │
  │  (doctor felt AI missed this herb, submitted     │          │
  │   without explicitly rating — still a clear      │          │
  │   intent signal)                                 │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor ADDED herb + Needs Changes rating         │ +0.3     │
  │  (doctor added it but overall plan still not     │          │
  │   good enough — weak positive for that herb)     │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor KEPT herb + Accurate rating               │ +1.0     │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor KEPT herb + NO rating (implicit accept)   │ +0.3     │
  │  (no edits, no rating, just prescribed —         │          │
  │   weakest positive, but still counts)            │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor KEPT herb + Needs Changes rating          │ +0.2     │
  │  (kept but plan inadequate — nearly neutral)     │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor REMOVED herb + NO rating                  │ −0.5     │
  │  (doctor removed it without commenting — clear   │          │
  │   rejection signal even without explicit rating) │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor REMOVED herb + Accurate rating            │ −0.8     │
  │  (AI suggested it; doctor didn't want it,        │          │
  │   but overall plan was acceptable)               │          │
  ├──────────────────────────────────────────────────┼──────────┤
  │ Doctor REMOVED herb + Needs Changes rating       │ −1.0     │
  │  (strongest negative — AI suggested it,          │          │
  │   doctor removed it AND rated plan as bad)       │          │
  └──────────────────────────────────────────────────┴──────────┘

  YOGA actions follow the same table.
  Objective outcome (ClinicalOutcomeScore) overrides the
  kept-herb rating signal but PRESERVES the addition/removal
  signals — those capture expert intent regardless of outcome.
```

**Detecting "no rating, no edits" (implicit acceptance):**

```python
  # At /api/prescribe processing time:
  edits_made = (added_herbs != [] or removed_herbs != [])
  rating_given = doctor_rating in ("positive", "negative")

  if not edits_made and not rating_given:
      implicit_accept = True   # all kept herbs → +0.3
  elif edits_made and not rating_given:
      implicit_accept = False  # use diff table, no quality boost
  elif not edits_made and rating_given:
      implicit_accept = False  # standard kept + rating logic
  else:
      implicit_accept = False  # edits + rating: full diff table
```

**Historical data backfill (one-time migration):**
```
  For each TreatmentFeedback row where ml_context lacks namc_code:
    1. Take stored disease string from ml_context
    2. Run through NAMC lookup table → resolve namc_code
    3. Combine with stored prakriti + vikriti → new state key
    4. Patch ml_context JSON in-place
  Note: historical rows have no diff data (added/removed_herbs)
  because original_ai_plan was never stored separately.
  These rows use the simpler: all herbs in ai_plan get the
  doctor_rating reward (existing behaviour, no regression).
  Only new rows (post-migration) get the full diff-based rewards.
  Estimated: ~14,688 rows → all become usable by retrain_from_feedback()
```

**Key files to change:**
- `backend/services/csv_service.py` — store `original_ai_plan` separately; compute and store herb diff
- `backend/services/rl_service.py` — update state key; add diff-aware reward logic
- `backend/utils/validators.py` — add `original_ai_plan` field to `PrescriptionRequest`
- `backend/scripts/` — add `backfill_rl_state_keys.py` migration script
- `backend/main.py` — update `ml_context` to include `namc_code` and `dosha_state`
- Frontend: pass `original_ai_plan` (stored at recommendation time) back with prescription submit

---

### Layer 4 — Improvement Confidence Model

**Purpose:** Provide an honest, patient-specific improvement estimate with a confidence interval that doctors can trust (or question) based on real clinical features.

**Current state:** `predicted_improvement = 75 + (10 if prakriti == vikriti else 0)`. Always returns 75.0 or 85.0. Does not consider age, severity, comorbidities, symptoms, or season.

**Target state — Gradient Boost Regressor:**

```
  Input features:
  ┌─────────────────────────────┬───────────────────────────┐
  │ Feature                     │ Encoding                  │
  ├─────────────────────────────┼───────────────────────────┤
  │ age                         │ continuous                 │
  │ severity                    │ ordinal 1–10               │
  │ comorbidity_count           │ integer                    │
  │ symptom_count               │ integer                    │
  │ dosha_match                 │ binary (prakriti==vikriti) │
  │ season (Ritu)               │ one-hot (6 seasons)        │
  │ namc_code                   │ target-encoded category    │
  └─────────────────────────────┴───────────────────────────┘

  Target variable:
    ClinicalOutcomeScore.percentage_change   (primary, once available)
    Doctor rating proxy (Accurate→80, Needs Changes→40) (interim)

  Output:
    predicted_improvement: float (e.g. 72.4)
    confidence_interval:   [low, high] (e.g. [64.1, 80.7])
    n_training_samples:    int (shown in explainability)
```

**Training stages:**
```
  Stage 1 (NOW):
    Train on synthetic patient data + doctor ratings as proxy labels.
    This gives a real model with meaningful feature variation,
    even before ClinicalOutcomeScore rows exist.
    Label: Accurate → 80, Needs Changes → 40.

  Stage 2 (as outcomes accumulate):
    Retrain on real ClinicalOutcomeScore rows.
    Doctor-rating proxy label is dropped for any visit
    that has a corresponding outcome score.

  Stage 3 (steady state):
    Both signals used together with outcome score
    as the higher-weight target.
```

**Key files to change:**
- `backend/services/ISHAAyush_service.py` — replace `_calculate_improvement()` with call to new service
- `backend/services/` — add `improvement_model_service.py`
- `backend/data/models/` — add `improvement_model.pkl`

---

### Layer 5 — LLM Narration

**Purpose:** Explain the treatment plan to the doctor in plain language. Not to generate the plan — to explain it.

**Current state:** No LLM in the recommendation pipeline. Explainability is structured strings only.

**Target state:**

```
  AFTER Layer 4 finalises the herb list (immutable at this point):

  LLM prompt template:
  ┌──────────────────────────────────────────────────────────┐
  │ System: You are an Ayurvedic clinical explainer.         │
  │ Your role is to explain treatment choices, not to make   │
  │ them. Do not suggest, add, or remove any herbs.          │
  │                                                          │
  │ User: Patient profile:                                   │
  │   Disease: {disease} (NAMC: {namc_code})                 │
  │   Prakriti: {prakriti}, Vikriti: {vikriti}               │
  │   Age: {age}, Severity: {severity}/10                    │
  │                                                          │
  │ Prescribed herbs: {herb_list}                            │
  │ Prescribed yoga: {yoga_list}                             │
  │                                                          │
  │ In 2-3 sentences, explain why these specific herbs       │
  │ were chosen for this patient's dosha profile and         │
  │ disease. Be concise and clinically grounded.             │
  └──────────────────────────────────────────────────────────┘

  Output field: explanation_text (string, max ~200 words)

  Constraints enforced in code (not just prompt):
    · LLM call happens AFTER herb list is frozen
    · LLM output stored in explanation_text only
    · Herb list is never re-parsed from LLM output
    · If LLM call fails or times out: explanation_text
      falls back to joined explainability[] strings

  Feature flag: ENABLE_LLM_NARRATION (default: false)
  This allows gradual rollout and easy rollback.
```

**Model choice:** Gemma-4-12B (already in stack) preferred for latency and privacy. Claude API as fallback for higher quality.

---

## 5. Data Flow Sequence

```
  Doctor                   Next.js             FastAPI            PostgreSQL
    │                         │                   │                   │
    │  Fill clinical form      │                   │                   │
    │─────────────────────────►│                   │                   │
    │                         │  POST /api/ml/recommend               │
    │                         │──────────────────►│                   │
    │                         │                   │ Layer 1: embed    │
    │                         │                   │   disease query   │
    │                         │                   │ Layer 2: CSV      │
    │                         │                   │   row lookup      │
    │                         │                   │ Layer 3: K-Means  │
    │                         │                   │   predict cluster │
    │                         │                   │ Layer 4: Q-table  │
    │                         │                   │   lookup          │
    │                         │                   │ Layer 5: GBM      │
    │                         │                   │   predict         │
    │                         │                   │ Layer 6: LLM      │
    │                         │                   │   narration       │
    │                         │  Treatment plan   │                   │
    │                         │◄──────────────────│                   │
    │  View & edit plan        │                   │                   │
    │◄─────────────────────────│                   │                   │
    │                         │                   │                   │
    │  Rate: Accurate /        │                   │                   │
    │  Needs Changes           │                   │                   │
    │─────────────────────────►│                   │                   │
    │                         │  POST /api/prescribe                  │
    │                         │──────────────────►│                   │
    │                         │                   │ Save:             │
    │                         │                   │  MedicalRecord    │
    │                         │                   │  AyushTreatment   │
    │                         │                   │  TreatmentFeedback│
    │                         │                   │  (ml_context with │
    │                         │                   │   namc_code +     │
    │                         │                   │   dosha_state)    │
    │                         │                   │──────────────────►│
    │                         │                   │                   │
    │                         │                   │ Background:       │
    │                         │                   │  retrain RL       │
    │                         │                   │  retrain clusters │
    │                         │                   │                   │
    │  ~4 weeks later:         │                   │                   │
    │  Enter follow-up vitals  │                   │                   │
    │─────────────────────────►│                   │                   │
    │                         │  POST /api/outcomes                   │
    │                         │──────────────────►│                   │
    │                         │                   │ Save:             │
    │                         │                   │  ClinicalOutcome  │
    │                         │                   │  Score            │
    │                         │                   │──────────────────►│
    │                         │                   │ Background:       │
    │                         │                   │  retrain RL       │
    │                         │                   │  retrain GBM      │
```

---

## 6. Follow-Up Vitals (ClinicalOutcomeScore)

### Current state of the DB schema

The `clinical_outcome_scores` table already exists and is fully designed:

```
  clinical_outcome_scores
  ─────────────────────────────────────────────────────────
  id                  UUID
  patient_id          FK → patients
  medical_record_id   FK → medical_records
  disease             str   (e.g. "Madhumeha")
  target_vital        str   (e.g. "HbA1c (%)")
  baseline_value      float (value at prescription time)
  followup_value      float (value at follow-up, ~4 weeks)
  percentage_change   float (computed: improvement %)
  calculated_reward   float (normalised 0–1 for RL)
  is_retrained        bool  (has RL consumed this row?)
  created_at          datetime
```

**Status: 0 rows.** The schema is there; the pipeline to populate it is not.

### Disease → Vital mapping (already in mock_outcome_data.py)

```
  ┌──────────────────────────────────┬─────────────────────┬──────────────────────────────────┐
  │ Disease pattern                  │ target_vital        │ Direction (improvement = ?)       │
  ├──────────────────────────────────┼─────────────────────┼──────────────────────────────────┤
  │ Asthma / Tamaka Shwasa           │ PEFR (L/min)        │ Higher is better                 │
  │ Diabetes / Madhumeha             │ HbA1c (%)           │ Lower is better                  │
  │ Hypertension / Raktachapa        │ Systolic BP (mmHg)  │ Lower is better                  │
  │ Obesity / Sthoulya               │ BMI (kg/m²)         │ Lower is better                  │
  │ All other diseases               │ Symptom Severity    │ Lower is better (scale 1–10)     │
  │                                  │   (1–10)            │                                  │
  └──────────────────────────────────┴─────────────────────┴──────────────────────────────────┘
  Extend this table as more diseases are tracked objectively.
```

### What needs to be built (baseline capture + follow-up entry)

**Step A — Baseline capture at prescription time:**

```
  When /api/prescribe is called:
    · Look up target_vital for the prescribed disease
    · If vitals are available in the patient's medical_record
      (e.g. HbA1c was recorded in the clinical assessment form)
      → auto-populate baseline_value from MedicalRecord data
    · If not available in record:
      → store NULL baseline; doctor fills it manually in the UI

  A ClinicalOutcomeScore row is created at prescription time
  with baseline_value filled (or NULL) and followup_value = NULL.
  This row is the "pending outcome" for this visit.
```

**Step B — Follow-up entry (new UI + endpoint):**

```
  UI location: Patient visit page → "Follow-up" tab
  Shown when:  prescription date > 28 days ago AND
               followup_value IS NULL for that visit

  UI shows:
  ┌────────────────────────────────────────────────────┐
  │  Follow-up Outcome — Visit: 2026-06-01              │
  │  Disease: Madhumeha (Diabetes Mellitus)             │
  │  Prescribed: Gymnema, Bitter Melon, Guchi Powder    │
  │                                                     │
  │  Baseline HbA1c (%):   [8.2]  (recorded at visit)  │
  │  Current HbA1c (%):    [____]  ← doctor enters     │
  │                                                     │
  │  Duration adherence: [Full / Partial / None]        │
  │  Doctor notes: [___________________________]        │
  │                                                     │
  │                              [Save Follow-up]       │
  └────────────────────────────────────────────────────┘

  POST /api/outcomes
  Body: { medical_record_id, followup_value, adherence, notes }

  Backend:
    1. Load the pending ClinicalOutcomeScore for this visit
    2. Set followup_value = submitted value
    3. Compute percentage_change:
         For "lower is better" vitals:
           pct = ((baseline - followup) / baseline) * 100
         For "higher is better" vitals:
           pct = ((followup - baseline) / baseline) * 100
    4. Compute calculated_reward = min(1.0, pct / normaliser)
         (normaliser per vital: HbA1c → 10%, PEFR → 20%, etc.)
    5. Mark is_retrained = False (ready for RL consumption)
    6. Trigger background: retrain_from_outcomes() + GBM retrain
```

**Step C — How outcome feeds back into RL:**

```
  retrain_from_outcomes() (rl_service.py):
    1. Query ClinicalOutcomeScore WHERE is_retrained = False
       AND followup_value IS NOT NULL
    2. JOIN to TreatmentFeedback on medical_record_id
       to get the namc_code + dosha_state
    3. Parse final_plan.herbs from TreatmentFeedback
    4. For each herb in final_plan:
         Q(namc+dosha, herb) += 0.1 × (reward − Q)
    5. For each herb in added_by_doctor (if available):
         apply extra +0.5 weight on top
    6. Mark ClinicalOutcomeScore.is_retrained = True
```

---

## 7. Feedback & Continuous Learning Loop

The learning loop has four independent cycles:

```
  ┌─── CYCLE A: RL from Doctor Feedback (immediate) ───────┐
  │                                                         │
  │  Trigger: every POST /api/prescribe                     │
  │  Input: TreatmentFeedback rows with is_retrained=False  │
  │  Reward: diff-aware (added/kept/removed × rating)       │
  │  State key: namc_code + dosha_state (stable)            │
  │  Update: Q(s,a) += 0.1 × (reward − Q(s,a))             │
  │  Effect: next patient with same namc+dosha gets         │
  │          a recommendation shaped by past edits          │
  └─────────────────────────────────────────────────────────┘

  ┌─── CYCLE B: RL from Clinical Outcomes (delayed) ───────┐
  │                                                         │
  │  Trigger: POST /api/outcomes (follow-up vitals saved)   │
  │  Input: ClinicalOutcomeScore.calculated_reward          │
  │         (objective: HbA1c, PEFR, BP, symptom score)    │
  │  State key: namc_code + dosha_state                     │
  │  Same Q-update, overrides rating-based reward           │
  │  Effect: real clinical improvement drives herb rankings │
  └─────────────────────────────────────────────────────────┘

  ┌─── CYCLE C: Improvement Model Refit ───────────────────┐
  │                                                         │
  │  Trigger: new ClinicalOutcomeScore OR feedback row      │
  │  GBM: refit on expanded dataset                         │
  │  Effect: predicted_improvement + CI become more         │
  │          calibrated as real outcomes accumulate         │
  └─────────────────────────────────────────────────────────┘

  ┌─── CYCLE D: Cluster Refit (independent) ───────────────┐
  │                                                         │
  │  Trigger: every POST /api/prescribe                     │
  │  K-Means: refit on all MedicalRecord rows               │
  │  Effect: cohort assignments stay current                │
  │  NO EFFECT on RL or improvement model                   │
  └─────────────────────────────────────────────────────────┘
```

---

## 8. Migration Path

Steps are ordered so each is non-breaking relative to the previous.

```
  Step 1 — Non-breaking: capture new RL keys going forward
  ──────────────────────────────────────────────────────────
  · In /api/prescribe, add namc_code + dosha_state to
    ml_context JSON alongside existing fields.
  · Existing rl_service.py still uses old keys; no RL logic
    touched yet. This step just enriches new rows.

  Step 2 — Fix the ai_plan / original_ai_plan split (CRITICAL)
  ──────────────────────────────────────────────────────────
  · In /api/recommend response, include original_ai_plan
    (the AI's output before any doctor editing)
  · Frontend stores this and sends it back with /api/prescribe
  · csv_service.py:
    - Store original_ai_plan in new TreatmentFeedback column
    - Compute added_herbs = final_herbs − original_herbs
    - Compute removed_herbs = original_herbs − final_herbs
    - Store both in TreatmentFeedback
  · Add DB migration: ALTER TABLE treatment_feedbacks ADD
    COLUMN original_ai_plan TEXT, added_herbs TEXT,
    removed_herbs TEXT
  · Rename existing ai_plan column to final_plan for clarity

  Step 3 — Migration: backfill historical feedback rows
  ──────────────────────────────────────────────────────────
  · Run scripts/backfill_rl_state_keys.py
  · Re-derives namc_code from stored disease string
    for all 14,688 TreatmentFeedback rows
  · Marks each row's ml_context with new keys
  · Zero downtime: read-only scan + JSON patch per row
  · Note: added_herbs/removed_herbs cannot be backfilled
    (original plan was never stored). Historical rows use
    simple flat reward. Only new rows get diff-aware rewards.

  Step 4 — RL state key switch + diff-aware rewards
  ──────────────────────────────────────────────────────────
  · Update rl_service.py to build state from namc_code
    + dosha_state instead of cluster_id + disease
  · Implement diff-aware reward table (see Layer 4 above)
  · Run retrain_from_feedback() once to rebuild Q-table
    from all 14,688 now-usable rows
  · Old q_table.pkl archived, new one written

  Step 5 — Cluster / RL decoupling + cohort analytics
  ──────────────────────────────────────────────────────────
  · Remove cluster_id from rl_service.py state construction
  · Add centroid-alignment label stability to
    patient_clustering_service.py
  · Add cohort performance aggregation query for display
  · Add anomaly distance check at inference time

  Step 6 — Follow-up vitals (ClinicalOutcomeScore pipeline)
  ──────────────────────────────────────────────────────────
  · At /api/prescribe: create pending ClinicalOutcomeScore
    row with baseline_value auto-populated where available
  · Add POST /api/outcomes endpoint
  · Add Follow-up tab to patient visit page in frontend
  · Extend retrain_from_outcomes() to use diff-aware herbs
    (if added_herbs available in the linked feedback row)

  Step 7 — Improvement model
  ──────────────────────────────────────────────────────────
  · Add improvement_model_service.py with GBM
  · Train on synthetic data + doctor rating proxy labels
  · Replace _calculate_improvement() in ISHAAyush_service.py
  · Response schema: add confidence_interval field

  Step 8 — Semantic disease matching
  ──────────────────────────────────────────────────────────
  · Pre-compute embeddings for all CSV disease names
  · Add _semantic_search() to ISHAAyush_service.py
  · Use as primary method; keep TF-IDF as fallback
  · Surface low-confidence alternatives in /api/recommend

  Step 9 — LLM narration (feature-flagged)
  ──────────────────────────────────────────────────────────
  · Add narration call in hybrid_service.py after Layer 4
  · ENABLE_LLM_NARRATION=false by default
  · Fallback to explainability[] strings when flag is off
  · Enable in staging, verify, then enable in production
```

---

## 9. Gap Resolution Map

| Gap | Root Cause | Fixed By |
|---|---|---|
| RL has never learned from 14,688 real feedback rows | `cluster_id` absent from ml_context of historical rows | Steps 3 + 4: backfill + new state key |
| Q-table goes stale after every K-Means refit | State key contains unstable cluster_id | Step 4: switch to namc_code + dosha_state |
| `TreatmentFeedback.ai_plan` stores edited plan, not original AI output | `csv_service.py:220` writes the submitted `treatment_plan` (post-edit) as `ai_plan` | Step 2: split into `original_ai_plan` + `final_plan`; add diff fields |
| Doctor herb additions/removals produce no differential RL signal | No diff computed; all herbs rewarded equally regardless of who added them | Step 4: diff-aware reward table |
| Improvement % always 75.0 or 85.0 | Simple heuristic, not a model | Step 7: GBM regressor |
| ClinicalOutcomeScore has 0 rows | No UI to enter follow-up vitals; no endpoint; no baseline capture at prescribe time | Step 6: pending outcome row at prescribe time + follow-up vitals UI |
| Clustering has no visible value to doctors | Cohort ID stored in ml_context but never displayed or used for insights | Step 5: cohort display + performance table + anomaly flagging |
| Disease matching passes wrong row silently | No confidence score, single match returned | Step 8: top-3 with confidence thresholds |
| Doctor's prakriti/vikriti silently overridden | CSV columns override input without logging (`ISHAAyush_service.py:169-180`) | Step 5 (minor: log warning instead of substituting) |
| No explanation of why specific herbs were chosen | No narration layer | Step 9: LLM narration |

---

## 10. Model Intelligence Dashboard

**Primary use case: live demo in front of doctors.**
A doctor adds a herb or yoga. The model learns. The very next recommendation includes it — flagged as AI-learned. That moment, witnessed live, is the story.

Everything else in the dashboard supports or extends that story.

---

### The Demo Flow (60 seconds, live)

```
  Act 1 — Show the base knowledge (15 sec)
  ──────────────────────────────────────────
  "For Madhumeha, Vata-Pitta constitution, our AI recommends
   Gymnema and Bitter Melon — pulled from the NAMASTE clinical
   dataset, the same standard used by AYUSH Ministry."

  Act 2 — Doctor adds their expertise (15 sec)
  ──────────────────────────────────────────────
  Doctor types: Guchi Mushroom Powder
  Submits prescription, rates Accurate.
  On screen: Q(Guchi Powder) bar rises from 0 → 0.15 (animated).
  "The model just absorbed your expertise."

  Act 3 — The learning is real (30 sec)
  ──────────────────────────────────────
  Click [Next Patient — Same Profile].
  New recommendation loads.
  Guchi Powder appears at rank 1, flagged [AI-learned *].
  "Your knowledge is now embedded. Every future Vata-Pitta
   Madhumeha patient will receive your recommendation."
```

**Why one submission is enough:**
Q starts at 0. First update: `Q = 0 + 0.1 × (1.5 − 0) = 0.15`.
Threshold to surface a learned herb is `Q > 0`. Crossed immediately.
One expert addition = one model update = visible in the next patient.

---

### Technical requirement: Fast Single-Record Update

The current `retrain_from_feedback()` processes ALL feedback rows on every call. At 14,688 rows this takes 10–30 seconds — unacceptable for a live demo.

**Solution: two retraining modes**

```
  STANDARD retrain (background, after each prescription in production):
    Process all is_retrained=False rows. Full Q-table rebuild.
    Used for: scheduled retraining, correctness guarantees.

  INSTANT retrain (foreground, triggered live during demo):
    Process only the SINGLE feedback row just created.
    Apply Q-update in-memory to the loaded Q-table.
    Persist updated Q-table immediately.
    Target latency: < 500ms.
    Used for: demo mode, and optionally for all future production
    prescriptions (safe — it's a strict subset of the full retrain).

  Backend: add POST /api/ml/retrain-instant
    Body: { feedback_id }
    Applies single-row Q-update and returns new Q-value for that
    action, so the frontend can animate the bar rising.
```

---

### The Live Demo Screen

This is the main screen. Not a tab — it IS the dashboard when demo mode is active.

```
  +================================================================+
  |  AI Learning Dashboard          [DEMO MODE]  [Reset]          |
  +================================+===============================+
  |  PRESCRIPTION                  |  WHAT THE MODEL KNOWS NOW    |
  |                                |                              |
  |  Disease: Madhumeha            |  State: AM-042_Vata_Pitta    |
  |  Dosha: Vata / Pitta           |  23 prescriptions in memory  |
  |                                |                              |
  |  AI Recommendation:            |  Gymnema Sylvestre           |
  |  1. Gymnema Sylvestre  [base]  |  0.81  ||||||||||||||||||||  |
  |  2. Bitter Melon       [base]  |  Bitter Melon                |
  |  3. Karela             [base]  |  0.55  ||||||||||||||        |
  |                                |  Karela                      |
  |  + [Add herb or yoga...]       |  0.31  ||||||||              |
  |                                |  Guchi Mushroom Powder       |
  |  [  Rate: Accurate  ]          |  0.00  ................      |
  |  [Submit Prescription]         |                              |
  +--------------------------------+------------------------------+

  DOCTOR TYPES "Guchi Mushroom Powder" AND SUBMITS:

  +================================================================+
  |  AI Learning Dashboard          [DEMO MODE]  [Reset]          |
  +================================+===============================+
  |  NEXT PATIENT (same profile)   |  WHAT THE MODEL KNOWS NOW    |
  |                                |                              |
  |  Disease: Madhumeha            |  State: AM-042_Vata_Pitta    |
  |  Dosha: Vata / Pitta           |  24 prescriptions in memory  |
  |                                |                              |
  |  AI Recommendation:            |  Gymnema Sylvestre           |
  |  1. [AI-learned *]             |  0.81  ||||||||||||||||||||  |
  |     Guchi Mushroom Powder      |  Bitter Melon                |
  |  2. Gymnema Sylvestre  [base]  |  0.55  ||||||||||||||        |
  |  3. Bitter Melon       [base]  |  Karela                      |
  |  4. Karela             [base]  |  0.31  ||||||||              |
  |                                |  Guchi Mushroom Powder       |
  |  [Add more] [Submit]           |  0.15  ||||  <- just learned |
  |                                |                              |
  +--------------------------------+------------------------------+
```

**Key UI behaviours:**
- When doctor submits: right panel animates — Guchi bar rises from 0 to 0.15 in ~800ms
- "Next Patient" button loads a fresh recommendation instantly using the updated Q-table
- The `[AI-learned *]` badge on the herb is visually distinct (gold/highlighted)
- A timestamp: "Learned from: Dr. [name], 12 seconds ago"
- "Reset Demo State" button: clears only the demo-session Q-table entries, restoring the pre-demo baseline. Does NOT affect production data.

---

### Demo Mode Architecture

The live demo must not contaminate production learning with synthetic/staged inputs.

```
  DEMO MODE flag in session / env:
    DEMO_MODE = true → use demo_q_table.pkl (copy of production)
    DEMO_MODE = false → use q_table.pkl (production)

  On [Reset Demo State]:
    Copy q_table.pkl → demo_q_table.pkl  (fresh baseline)
    Clear demo session Q-value changes
    UI resets to pre-demo state

  All demo prescriptions:
    · Written to DB normally (real TreatmentFeedback rows)
    · Flagged: demo_session = true in ml_context
    · Excluded from production retrain (WHERE demo_session IS NULL)
    · Can be optionally promoted: "Keep these learnings in production?"
      button after demo — doctor's additions are real expertise,
      keeping them is valid.
```

---

### Supporting Tabs (non-demo, for deeper exploration)

After the live moment lands, these tabs let expert doctors explore further.

**Tab: State History**

```
  Pick any state (namc + dosha). See the full timeline of how
  Q-values evolved — prescription by prescription.

  "Guchi Powder: 7 doctors added it before the AI learned.
   Turmeric: 4 doctors removed it. Q-value now negative."

  Useful for: answering "why is this herb in the recommendation?"
  with a complete audit trail.
```

**Tab: Compare Two States**

```
  "Vata-Pitta Madhumeha vs Kapha-Kapha Madhumeha — what's different?"
  Side-by-side Q-value bars for the same disease, different doshas.
  Shows: the model treats the same disease differently
  based on constitution — which is correct Ayurvedic practice.
```

**Tab: Cohort Analytics**

```
  Post-hoc K-Means analysis. Which patient profiles get
  the most "Needs Changes" ratings? Where is the model weakest?
  Separate from the pipeline — analytical view only.
```

**Tab: Outcome Tracker**

```
  All pending follow-ups (prescriptions > 28 days, no vitals entered).
  Sorted by disease. One-click to enter follow-up value.
  Shows how many outcome scores are feeding the improvement model.
```

---

### What Makes the Demo Defensible to Doctors

Anticipate the hard questions:

```
  Q: "So the AI just blindly adds whatever any doctor types?"
  A: "No. The herb needs Q > 0 — which requires positive signals
      from multiple independent prescriptions for the same
      disease-dosha state. One outlier doctor can't override
      the model. And every herb is always traceable to who added
      it and when — nothing is anonymous."

  Q: "What stops a doctor from teaching the model bad habits?"
  A: "Clinical outcome scores — objective vitals like HbA1c —
      override subjective ratings. If a doctor keeps rating a
      bad herb as Accurate but patient outcomes don't improve,
      the outcome signal will eventually pull the Q-value back
      down. The model self-corrects."

  Q: "Is this going into the official Ayurvedic knowledge base?"
  A: "No. AI-learned herbs are always flagged separately. They
      never modify the NAMASTE CSV. They can be reviewed and
      submitted for formal inclusion through the normal AYUSH
      process — the model surfaces them, humans curate them."
```

## 11. What We Are NOT Changing (and why)

| Component | Why it stays |
|---|---|
| **ISHAAyush CSV as knowledge source** | Every herb output is traceable to a verified, curated clinical row. This is the system's safety anchor. |
| **No LLM for herb selection** | LLMs can hallucinate herb combinations that are contraindicated. The retrieval layer eliminates this risk entirely. |
| **Epsilon-greedy bandit** | Simple, interpretable, auditable. Complex RL (PPO, SAC) would require far more data and make individual decisions harder to explain to clinicians. |
| **K-Means for clustering** | Sufficient for cohort grouping. The clustering role is now purely descriptive/analytic, so algorithm complexity is unwarranted. |
| **PostgreSQL + SQLAlchemy** | No change to data layer needed for any of the above. |

---

## 12. Response Schema (post-revamp)

```json
{
  "namc_code": "AM-042",
  "namc_term": "Madhumeha",
  "namc_term_devanagari": "मधुमेह",
  "source_disease": "Diabetes Mellitus (Madhumeha)",
  "match_confidence": 0.94,
  "match_alternatives": [],

  "herbs": [
    {
      "name": "Gymnema Sylvestre",
      "dosage": "400mg twice daily",
      "benefits": "Reduces sugar absorption; primary herb for Madhumeha",
      "source": "ISHAAyush:AM-042",
      "ai_learned": false
    },
    {
      "name": "Turmeric",
      "dosage": "500mg with warm water",
      "benefits": "Anti-inflammatory; AI-discovered for Vata_Pitta Madhumeha",
      "source": "RL:AM-042_Vata_Pitta",
      "ai_learned": true
    }
  ],

  "yoga": [...],
  "diet": [...],
  "lifestyle": [...],
  "formulation": "...",
  "prognosis": "...",

  "predicted_improvement": 72.4,
  "confidence_interval": [64.1, 80.7],
  "improvement_model_samples": 342,

  "recommended_duration_weeks": 12,
  "cohort_id": 4,
  "cohort_size": 89,
  "is_rl_modified": true,

  "explanation_text": "Gymnema Sylvestre is the cornerstone herb for Madhumeha, directly addressing elevated blood glucose by inhibiting intestinal sugar absorption — particularly important for the Pitta vikriti imbalance present here. Turmeric has been added based on positive outcomes in 23 similar Vata-Pitta Madhumeha patients, where it addressed the inflammatory component associated with this dosha combination.",

  "explainability": [
    "Matched Madhumeha (AM-042) with 0.94 confidence via semantic search.",
    "Patient assigned to cohort 4 (89 similar patients: Vata prakriti, adult, moderate severity).",
    "Turmeric added by RL — Q(AM-042_Vata_Pitta, Turmeric) = 0.73, based on 23 positive feedback signals.",
    "Predicted improvement 72.4% (CI: 64–80%) based on 342 training cases; features: age=45, severity=6, dosha_match=false, comorbidities=1."
  ]
}
```

---

## 13. Verification Checklist

After each step in the migration path, verify:

```
  Step 2 (backfill):
  □ SELECT COUNT(*) FROM treatment_feedbacks
      WHERE ml_context->>'namc_code' IS NOT NULL
    → should equal total feedback row count

  Step 3 (new RL keys):
  □ Run model_report.py → Q-table states should show
    format "AM-XXX_Prakriti_Vikriti" not "N_disease"
  □ Q-table should be non-empty (first real learning)

  Step 5 (improvement model):
  □ /api/recommend response should contain
    confidence_interval field with [low, high]
  □ Two patients with same prakriti/vikriti but
    different severity should get different scores

  Step 6 (semantic matching):
  □ Query "madhu" → confidence < 0.85 → alternatives shown
  □ Query "Madhumeha" → confidence ≥ 0.85 → auto-select

  Step 7 (LLM narration):
  □ ENABLE_LLM_NARRATION=true → explanation_text populated
  □ ENABLE_LLM_NARRATION=false → explanation_text falls
    back to joined explainability[] strings
  □ LLM output contains no herb names not already in
    the herbs[] list

  Step 8 (outcomes):
  □ Submit a ClinicalOutcomeScore row →
    improvement_model_service retrains →
    model_report.py shows updated training sample count
```
