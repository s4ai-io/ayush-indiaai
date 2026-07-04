# Public Health Dashboard — Open Issues (Current Status)

Scope: everything on [`/public-health/dashboard`](src/app/public-health/dashboard/page.tsx) as
verified against the live codebase **and** a live query of the Postgres database on **2026-07-04**.
The database was **regenerated and migrated** on this date (see "Dataset regeneration" below) — it now
holds 3,500 patients / 12,666 medical records spanning 2024-01-01 to 2026-07-03 (~2.5 years), replacing
the prior 900-patient / 18-month dataset. Figures in this file reflect the new dataset unless marked
otherwise. For what each panel shows and why, see `PUBLIC_HEALTH_DASHBOARD_INSIGHTS.md`. For the original
pre-Phase-1 deep-dive, see `PUBLIC_HEALTH_DASHBOARD.md` (historical — not kept in sync with this file).

---

## Status at a glance

| # | Item | Status |
|---|---|---|
| 1 | Hotspots fragmented to near-patient granularity | ✅ Fixed |
| 2 | Emerging Threats tooltip vs. code threshold mismatch | ✅ Fixed |
| 3 | Weekly-alerts docstring stale window sizes | ✅ Fixed |
| 4 | Forecast confidence intervals always null | ⬜ Open |
| 5 | `GNNService` name/docstring misleading | ✅ Fixed (docstring + inline note; class name kept) |
| 6 | `clustering_service.py` naming collision | ✅ Fixed (renamed to `patient_clustering_service.py`) |
| 7 | `clusters` state untyped (`any[]`) | ✅ Fixed |
| 8 | Dead weather-panel imports | ✅ Fixed |
| 9 | No accuracy/backtesting for forecast/spread models | ⬜ Open |
| 10 | Two diseases with bare "None specific" yoga field | ✅ Fixed |
| 11 | `severity` column mixed two incompatible formats | ✅ Fixed |
| 12 | "Clinical Records" KPI subtext claimed a time scope the query doesn't apply | ✅ Fixed |
| 13 | **New** — weekly-surge-seeded visits all timestamped at the exact same minute | ✅ Fixed |
| 14 | **New** — clinical notes literally contained generator bookkeeping text | ✅ Fixed |
| 15 | **New** — every patient sharing a diagnosis had byte-identical symptoms text | ✅ Fixed |
| 16 | **New** — `prescription` field was always the literal empty string `"{}"` | ✅ Fixed |

---

## Dataset regeneration (2026-07-04)

Requested: scale to ~3,500 patients with case volume scaled accordingly, spanning 2–3 years back from
today, replacing the old dataset outright. Before regenerating, the generator scripts were audited for
anything that would make the data obviously synthetic on casual inspection (not just structurally
inconsistent) — four real issues turned up (#13–16 below), all fixed prior to generating.

**Volume-scaling fix required first**: `generate_historical_data_v2.py`'s monthly case-count Poisson
means (`seasonal_means`, `chronic_mean`) were hardcoded constants, completely independent of the
`--patients` argument — raising `--patients` alone would have just spread the same fixed ~1,500
records/year across a bigger pool (diluting hotspot/alert density further, the opposite of the goal).
Fixed by scaling both by `n_patients / 900` (900 being the constants' original calibration baseline), so
per-capita monthly incidence stays constant as population size changes. Verified: 3,500 patients → ~5,800
base records/year vs. ~1,500-2,300 at 900 patients — proportional as expected.

**Multi-year support added**: the generator only ever took a single `--year`. Added `--years` (accepts
multiple, e.g. `--years 2024 2025`) so the *same* generated patient pool gets a full year of visits for
each year listed — patients (including chronic-disease patients) realistically recur across years instead
of each year getting a disjoint patient set.

**Run performed**:
```
generate_historical_data_v2.py --seed 42 --years 2024 2025 --patients 3500
seed_weekly_surge_data_v2.py --seed 42          # rolling last-52-weeks overlay, ends "today"
migrate_synthetic_v2_postgres.py                 # clears + reloads patients/medical_records/
                                                  # ayush_treatments/treatment_feedbacks
```
This gives 2024-01-01 through the weekly-surge seeder's rolling window ending 2026-07-03 — about 2.5
years total, inside the requested 2–3 year range, with zero future-dated rows (verified).

**Post-migration verification** (all passed): 3,500 patients / 12,666 records; 0 orphaned records; 0
future-dated visits; severity 100% numeric; all 140 distinct patient cities covered by
`geo_reference.CITY_INFO` with 0 city/state mismatches; all 109 diagnoses covered by both
`disease_names.py` and `disease_pool.py`. Hotspots panel: top count went from 12 → 36 (3× headroom, as
expected from the ~3.9× population scale-up), count==1 share of the full list dropped from 74% → 57%.
Monthly alerts went from 15 → 77 (more months of history per disease → less small-sample Z-score noise).

---

## 13. Weekly-surge-seeded visits were all timestamped at the exact same minute — FIXED

**Where**: [`seed_weekly_surge_data_v2.py:115-136`](backend/seed_weekly_surge_data_v2.py#L115) (and the
same pattern in the older `seed_weekly_surge_data.py`). `now = datetime.utcnow()` was captured once, and
every record's `visit_day` was built by adding whole-day `timedelta`s to it — never touching the
hour/minute — so every seeded record inherited the exact wall-clock time the script happened to run at.

**Verified live (pre-fix)**: 793 of 2,310 records (the entire weekly-surge-seeded set) shared the
identical timestamp `11:06` down to the minute. Visually scanning visit times or plotting a
time-of-day histogram would immediately reveal ~34% of "patient visits" clustered on one specific minute
— not physically possible for a real clinic.

**Fix applied**: `visit_day` now gets an explicit randomized `hour` (8–18) and `minute` ({0,15,30,45}),
matching the convention `_sample_visit_date()` already used in the main generator. Verified post-fix:
hour distribution across the full 12,666-row regenerated dataset is flat (1,106–1,219 per hour across
8–18), no spike.

---

## 14. Clinical notes literally contained generator bookkeeping text — FIXED

**Where**: [`seed_weekly_surge_data_v2.py:147`](backend/seed_weekly_surge_data_v2.py#L147) wrote
`notes = f"Weekly-seed record (v2, {'demo-spike' if demo_spike else 'organic'}) - week {week_idx+1}/52"`
directly into the same `notes` column real clinical text lives in.

**Verified live (pre-fix)**: all 793 weekly-surge-seeded rows had notes reading e.g.
`"Weekly-seed record (v2, organic) - week 34/52"`. This field isn't rendered by the public-health
dashboard's own case-details modal (confirmed — that modal only shows `symptoms`, not `notes`), but it's
surfaced by other parts of the app (`/api/analytics/case-context`-style endpoints feeding treatment
flows) and is about as unambiguous a "this row is fake" tell as data can contain.

**Fix applied**: replaced with the same clinical-style template the main generator uses —
`"Patient presents with {severity} {disease}."`

---

## 15. Every patient sharing a diagnosis had byte-identical symptoms text — FIXED

**Where**: both `generate_historical_data_v2.py` and `seed_weekly_surge_data_v2.py` pulled `symptoms`
from a static per-disease string (`SEASONAL_SYMPTOMS` / `SYMPTOMS_MAP` / disease_pool's chronic-disease
tuples) and wrote it verbatim into every record for that diagnosis.

**Verified live (pre-fix)**: `SELECT diagnosis, count(distinct symptoms), count(*) FROM medical_records
GROUP BY diagnosis` showed `count(distinct symptoms) = 1` for every top diagnosis — e.g. all 188 "Cough
(Kasa)" rows shared one identical sentence. This field *is* rendered directly in the case-details
drill-down modal, so opening any hotspot/alert/cluster and looking at several patients for the same
disease showed the exact same sentence repeated verbatim — an obvious tell when actually browsing the
dashboard, unlike #13/#14 which required looking at raw data.

**Fix applied**: added `vary_symptoms()` to `services/disease_pool.py` — lightly perturbs the canonical
symptom string per record (occasionally drops one clause, occasionally reorders clauses, ~45% chance of
appending a duration/quality qualifier like "for the past 2 days" or "worsening over the last few days").
Applied in both generator scripts. Verified post-fix: the most-common diagnosis in the regenerated data
has 311 distinct symptom phrasings instead of 1.

---

## 16. `prescription` field was always the literal empty string `"{}"` — FIXED

**Where**: all three record-producing code paths (`_make_record()` in `generate_historical_data_v2.py`,
the follow-up-visit branch in the same function, and `seed_weekly_surge_data_v2.py`) hardcoded
`"prescription": "{}"`, even though the real herb/yoga recommendation for that exact diagnosis was
already computed a few lines earlier in the same function (and written correctly to the sibling
`ayush_treatments` table).

**Verified live (pre-fix)**: 100% of 2,310 records (not just the weekly-surge subset) had `prescription
== "{}"`. Not currently rendered by the public-health dashboard's case-details modal, so lower visibility
there, but a real field on every record that was unconditionally blank is still a tell if anyone inspects
raw records, and it's inconsistent with the herb/yoga data that already exists one table over.

**Fix applied**: `generate_historical_data_v2.py` now writes `json.dumps({"herbs": herbs, "yoga": yoga})`
using the same values passed to the `ayush_treatments` row. `seed_weekly_surge_data_v2.py` gained a small
`HERBS_YOGA_MAP` for its 8 surge diseases (sourced from `disease_pool.py`'s existing entries for those
exact diagnoses) and does the same. Verified post-fix: 0% of the regenerated 12,666 records have an empty
prescription.

---

## 11. `medical_records.severity` stores two incompatible encodings in the same column — FIXED (2026-07-04)

**Where**: `generate_historical_data.py`/`generate_historical_data_v2.py` defined
`SEVERITY_SCORES = {"Mild": "3", "Moderate": "6", "Severe": "9"}` and wrote the **numeric string**;
`seed_weekly_surge_data.py`/`seed_weekly_surge_data_v2.py` wrote the **raw text label** instead, into the
same column.

**Verified live (pre-fix, on the old 900-patient dataset)**: 1,517 rows (66%) numeric, 793 rows (34%)
text label, for the identical concept — causing inconsistent case-detail severity badges and silently
defaulting `patient_clustering_service.py`'s severity feature to `5` for every text-labeled row (the
`int(r.severity)` parse there raises and is swallowed by a bare `except ValueError: pass`).

**Fix applied**: numeric encoding chosen as canonical (it already matched the real
registration/voice-pipeline convention in `csv_service.py` and what `patient_clustering_service.py`
expected). Both seed scripts now map through the same `SEVERITY_SCORES` table the main generator uses.
The 793 existing text-labeled rows in the (then-live) DB were backfilled with the same 1:1 mapping before
the full dataset regeneration superseded them anyway. The regenerated dataset's severity column is 100%
numeric by construction (verified: `{'3': 4223, '6': 5488, '9': 2955}`, no text values at all).

---

## 12. "Clinical Records" KPI subtext said "last 12 months" but the query is unscoped, all-time — FIXED (2026-07-04)

**Where**: `page.tsx` rendered the KPI with `sub="last 12 months"`, backed by
`analytics_service.get_dashboard_summary()`'s `total_records = db.query(MedicalRecord).count()` — a
plain, unfiltered `COUNT(*)`, no date predicate at all.

**Fix applied**: changed the subtext to `"all-time"`, matching the actual unfiltered `COUNT(*)` behavior,
rather than adding a date filter (which would silently drop older seasonal history the anomaly detectors
and forecaster rely on).

---

## Verified clean — checked live against the regenerated dataset, no issue found

- **No orphaned medical records**, no null/empty city, diagnosis, or visit_date, no future-dated visits.
- **City/state consistency**: all 140 distinct `(city, state)` pairs in `patients` match
  `geo_reference.CITY_INFO` — zero mismatches.
- **Geo coverage**: all 140 patient cities exist in `geo_reference.CITY_COORDS` — none silently dropped
  from the spread-forecast graph or DBSCAN clustering.
- **Disease-name / disease-pool coverage**: all 109 distinct diagnoses have both a `disease_names.py`
  entry and a `disease_pool.py` source-data entry.
- **Hotspots panel**: still shows the majority of the full (city, diagnosis) list at `count == 1` (57%,
  down from 74% pre-regeneration) — this is data sparsity (population still spread across 140 cities ×
  109 diseases), not a fragmentation bug. The panel only ever surfaces the top 8 by count, which are
  cleanly, non-arbitrarily ordered.

---

## 4. Forecast confidence intervals are schema fields that never get populated

**Where**: [`services/forecast_service.py:85-86`](backend/services/forecast_service.py#L85) —
`confidence_lower`/`confidence_upper` hardcoded to `None` in every forecast response. Still true,
unaffected by the dataset regeneration.

**Suggested fix**: two real options —
  (a) populate them cheaply via per-tree prediction spread (`RandomForestRegressor.estimators_[i].predict(...)`
  → take a low/high percentile across trees) — no retraining architecture change needed, or
  (b) drop the two fields from the response schema so the UI doesn't imply unshipped functionality.

---

## 9. No accuracy/backtesting for the dashboard's own models

**Where**: [`backend/services/admin_router.py`](backend/services/admin_router.py) — still only covers
voice/ASR transcription accuracy and the ISHAAyush treatment-recommendation engine. No equivalent for the
RandomForest disease forecast or the graph-diffusion spread model.

**Suggested fix**: extend the `/api/admin/accuracy`-style pattern with a backtest that holds out the most
recent N weeks, trains on everything before, and scores predicted vs. actual case counts (MAE/MAPE) for
both the forecast and spread models. The dataset now has 2 full historical years (2024, 2025) plus a
partial 2026 — enough to hold out, say, all of 2025 as a test set while training on 2024.

---

## Fixed to date

- **#1 Hotspots fragmentation** — grouped by `(city, diagnosis)` instead of `(city, pincode, diagnosis)`.
- **#2 Emerging Threats threshold mismatch** — tooltip now matches `forecast_service.py`'s real cutoffs.
- **#3 Weekly-alerts docstring** — now says "6-week recent vs 20-week baseline", matching the code.
- **#5 `GNNService` staleness** — docstring rewritten; `# NOTE:` added at the class definition.
- **#6 Naming collision** — `clustering_service.py` renamed to `patient_clustering_service.py`.
- **#7 Untyped `clusters` state** — added a `ClusterData` interface.
- **#8 Dead weather imports** — removed `Thermometer`, `Wind`, `Droplets`.
- **#10 Generic yoga fields** — Warts and Leprosy entries given real/explicit yoga guidance.
- **#11 `severity` format split** — canonicalized to numeric; regenerated dataset is 100% numeric.
- **#12 KPI subtext mismatch** — "all-time" instead of "last 12 months".
- **#13 Fixed-timestamp giveaway** — weekly-surge visits now have randomized time-of-day.
- **#14 Bookkeeping text in notes** — replaced with clinical-style notes.
- **#15 Identical symptoms per diagnosis** — added per-record symptom variation.
- **#16 Always-empty prescription field** — now populated from the real herb/yoga data.

---

## Already fixed by the original Phase 1 data pass (older context)

- **30-city coverage cap** → `services/geo_reference.py` covers every patient city; confirmed live on the
  regenerated 140-city dataset.
- **Engineered/guaranteed alert spikes** → `seed_weekly_surge_data_v2.py` defaults to organic
  Poisson-sampled weekly noise; the old guaranteed-spike behavior is opt-in via `--demo-spike`.
- **Disease-name coverage** → confirmed live: all 109 diagnoses in the regenerated dataset resolve to a
  real Devanāgarī/IAST name.

---

## Suggested order of attack (remaining)

1. **#4 (confidence intervals)** — needs a decision on compute-vs-drop before touching
   `forecast_service.py`.
2. **#9 (backtesting)** — now has enough historical depth (2 full years) to hold out a real test period;
   largest remaining item, deserves its own plan.
