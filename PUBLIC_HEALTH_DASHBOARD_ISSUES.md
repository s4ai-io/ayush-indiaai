# Public Health Dashboard — Open Issues (Post Data-Fix)

Scope: everything still wrong on [`/public-health/dashboard`](src/app/public-health/dashboard/page.tsx) *after* the Phase 1 data-realism pass (`services/geo_reference.py`, `services/disease_pool.py`, `services/disease_names.py`, `services/name_pool.py`, `generate_historical_data_v2.py`, `seed_weekly_surge_data_v2.py`). Each item below was re-checked against the current code, not copied from the original audit — line/behavior references are current as of this file.

---

## 0. Already fixed by the data pass (context, not action items)

These were flagged in the original `PUBLIC_HEALTH_DASHBOARD.md` audit and are now resolved:

- **30-city coverage cap** → `services/geo_reference.py` now covers 140 cities/33 states/UTs; `gnn_service.py` and `spatial_service.py` both read from it.
- **Engineered/guaranteed alert spikes** → `seed_weekly_surge_data_v2.py` defaults to organic Poisson-sampled weekly noise; the old guaranteed-spike behavior is now opt-in via `--demo-spike`.
- **Disease-name coverage** → `disease_names.py` now covers 109 diagnoses (28 seasonal + 81 chronic) instead of ~30.

---

## 1. New finding — Hotspots panel is fragmented down to near-patient granularity (highest priority)

**Where**: [`backend/services/analytics_service.py`](backend/services/analytics_service.py) `get_hotspots()` groups by the tuple `(city, pincode, diagnosis)`, not by `(city, diagnosis)`.

**What's wrong**: checked live against the current dataset — of 2157 hotspot rows returned by `/api/analytics/hotspots`, **2011 (93%) have `count == 1`**. Because pincodes are now realistically varied per patient within a city (a Phase 1 improvement — see `geo_reference.sample_pincode`), almost no two patients in the same city share both a pincode and a diagnosis, so nearly every "hotspot" is really just one patient's one visit. The frontend's `topHotspots` ([page.tsx:278](src/app/public-health/dashboard/page.tsx#L278)) takes the raw sorted list and slices the top 8 — with 93% of rows tied at count 1, the panel is close to arbitrary rather than surfacing genuine high-burden cities.

**Note**: this bug pattern likely existed before Phase 1 too (old pincodes were also effectively random per patient), just wasn't caught because it wasn't checked against live counts in the original audit.

**Suggested fix**: change the group-by key to `(city, diagnosis)` (drop pincode from the grouping, keep it only as a display/example field if wanted), so hotspots aggregate at the level the panel's own UI copy claims ("hotspot = isolated high-burden **city**").

---

## 2. Emerging Threats: tooltip thresholds don't match the code

**Where**: tooltip copy at [page.tsx:615](src/app/public-health/dashboard/page.tsx#L615) vs. logic in [`services/forecast_service.py:124-128`](backend/services/forecast_service.py#L124).

**What's wrong** (re-verified): tooltip says *"Low < 25%, Medium 25–50%, High 50–100%, Critical > 100%"*. Actual code: `critical if growth > 50, else high if growth > 25, else medium if growth > 10, else low`. Displayed methodology and computed behavior disagree at every band.

**Suggested fix**: pick one and make the other match — either update the tooltip string to `Low < 10%, Medium 10–25%, High 25–50%, Critical > 50%`, or change the code's cutoffs to match the tooltip. Tooltip-match is lower risk (no model/alert behavior change, just a copy edit) unless the 25/50/100 bands were the intended design.

---

## 3. Weekly-alerts docstring still says the old window sizes

**Where**: [`backend/main.py:458-464`](backend/main.py#L458), docstring on `/api/analytics/weekly-alerts`.

**What's wrong** (re-verified): docstring says *"Uses a 4-week recent window vs 12-week baseline window."* Actual defaults in [`services/analytics_service.py:280-286`](backend/services/analytics_service.py#L280) are `recent_windows=3` / `baseline_windows=10` bi-weekly buckets = **6-week recent vs 20-week baseline** (matches the frontend tooltip, just not this docstring).

**Suggested fix**: one-line docstring edit: "Uses a 6-week recent window vs 20-week baseline window."

---

## 4. Forecast confidence intervals are schema fields that never get populated

**Where**: [`services/forecast_service.py:71-72`](backend/services/forecast_service.py#L71) — `confidence_lower`/`confidence_upper` hardcoded to `None` in every forecast response.

**What's wrong** (re-verified, still true): the response schema implies uncertainty bounds exist; the RandomForest point-estimate approach never computes them, so the API always serializes `null` for both fields.

**Suggested fix**: two real options, pick one —
  (a) populate them cheaply via per-tree prediction spread (`RandomForestRegressor.estimators_[i].predict(...)` → take a low/high percentile across trees) — no retraining architecture change needed, or
  (b) if that's out of scope for now, drop the two fields from the response schema so the UI doesn't imply unshipped functionality.

---

## 5. `GNNService` name and module docstring are misleading/stale

**Where**: [`backend/services/gnn_service.py`](backend/services/gnn_service.py) — class `GNNService` (line 74), module docstring (lines 1-6).

**What's wrong**: 
- No trained graph neural network exists — it's deterministic diffusion (self-disclosed in the module docstring and the dashboard tooltip, so not a "gotcha", but still a misleading class/file name for anyone skimming the codebase).
- The module docstring's second line — *"Replaces hardcoded 6 Delhi pincodes with actual cities/pincodes from PostgreSQL"* — is stale. That description predates even the original 30-city dict this file used to have; it no longer describes what the file does now that it reads from `geo_reference.py`. This is a new finding, not in the original audit.

**Suggested fix**: update the docstring to describe current behavior (shared `geo_reference` centroid table + graph diffusion), and either rename the class (e.g. `SpreadDiffusionService`) or leave the name but add a one-line `# NOTE:` at the class definition itself (not just the module docstring) so it's visible without scrolling up.

---

## 6. `clustering_service.py` / `spatial_service.py` naming collision

**Where**: [`backend/services/clustering_service.py`](backend/services/clustering_service.py) (KMeans patient clustering, used for treatment-recommendation flows) vs [`backend/services/spatial_service.py`](backend/services/spatial_service.py) (DBSCAN geospatial clustering — what actually powers the dashboard's "Geospatial Disease Clusters" panel).

**What's wrong** (re-verified, unchanged): the class inside `clustering_service.py` is already named `PatientClusteringService` (reasonably clear), but the **file name** `clustering_service.py` is still the collision point — a developer grepping for "the clustering service behind the dashboard" has no reason to prefer `spatial_service.py`.

**Suggested fix**: rename the file to `patient_clustering_service.py` and update its one import site; leave `PatientClusteringService` class name as-is.

---

## 7. `clusters` state is untyped (`any[]`) in the frontend

**Where**: [page.tsx:144](src/app/public-health/dashboard/page.tsx#L144) — `const [clusters, setClusters] = useState<any[]>([])`.

**What's wrong** (re-verified, unchanged): every other panel's data has a typed interface; the DBSCAN cluster shape from `spatial_service.get_cluster_summary()` isn't declared anywhere in the TypeScript layer, so cluster field access (`cluster.disease`, `cluster.cities`, `cluster.city_cases`, etc.) is unchecked.

**Suggested fix**: add a `ClusterData` interface matching the dict shape in `spatial_service.py`'s `get_disease_clusters()` (`cluster_id, disease, is_noise, cities, city_cases, total_cases, centroid_lat, centroid_lon, spread_km, period_days`), swap `any[]` for `ClusterData[]`.

---

## 8. Dead weather-panel imports

**Where**: [page.tsx:11](src/app/public-health/dashboard/page.tsx#L11) — `Thermometer, Wind, Droplets` imported from the icon library, never referenced anywhere else in the file (re-verified: zero other occurrences).

**What's wrong**: implies a planned weather/climate-correlation panel that was never built; there's still no weather-data endpoint anywhere in `main.py`.

**Suggested fix**: either delete the three unused imports (2-minute cleanup), or if a weather-correlation panel is actually on the roadmap, leave a `// TODO(weather-panel):` comment instead of silent dead imports.

---

## 9. No accuracy/backtesting for the dashboard's own models

**Where**: [`backend/services/admin_router.py`](backend/services/admin_router.py) — re-checked, still only covers voice/ASR transcription accuracy and the ISHAAyush treatment-recommendation engine (`treatment_feedback.csv`-based). No equivalent for the RandomForest disease forecast or the graph-diffusion spread model.

**What's wrong**: unchanged from the original audit — there's no way to know if the forecast or spread model actually generalizes to real outcomes; they've only ever been checked against synthetic data they were tuned on.

**Suggested fix**: this is the largest item here — extend the `/api/admin/accuracy`-style pattern with a backtest that holds out the most recent N weeks, trains on everything before, and scores predicted vs. actual case counts (MAE/MAPE) for both the forecast and spread models.

---

## 10. Minor — two chronic diseases still say "None specific" for yoga

**Where**: [`backend/services/disease_pool.py`](backend/services/disease_pool.py) — `Warts (Charmakeela)` and `Leprosy (Kushtha Roga)` still have `"None specific"` in the yoga field, slightly inconsistent with that file's own docstring claim that "None specific" source values were filled with a dosha-appropriate default everywhere.

**Suggested fix**: trivial one-line fix — e.g. `"Gentle skin care, avoid scratching"` for Warts, `"None specific (medical referral)"` explicitly labeled as intentional for Leprosy (a condition genuinely outside standard yoga therapy scope) rather than a bare "None specific" that reads as an oversight.

---

## My suggested order of attack

1. **#1 (hotspots fragmentation)** first — it's the one that's actually visibly broken right now (93% of rows tied at count 1), it's a one-line group-by-key change, and it directly affects what the dashboard's headline "Disease Hotspots" panel shows.
2. **#2 + #3 + #5's docstring + #10** as one small batch — all doc/copy/comment fixes, zero behavior risk, ~20 minutes total.
3. **#6 + #7** as a second small batch — a file rename and a TypeScript interface, mechanical, low risk.
4. **#8** — trivial, fold into whichever batch is convenient.
5. **#4 (confidence intervals)** on its own — the only one here that touches model code; I'd want to confirm which of the two options (compute vs. drop) you want before touching `forecast_service.py`.
6. **#9 (backtesting)** last and separately — meaningfully larger scope than everything else on this list combined, deserves its own plan rather than being bundled in.
