# Public Health Dashboard — Implementation Deep-Dive

Scope: the "Dashboard" tab at [`/public-health/dashboard`](src/app/public-health/dashboard/page.tsx), what it renders, which backend service/model produces each number, what the data is actually based on, and what is misleading, stale, or unfinished.

---

## 1. What's on the page

File: [src/app/public-health/dashboard/page.tsx](src/app/public-health/dashboard/page.tsx)

On mount, `loadData()` fires 10 parallel requests (`Promise.allSettled`) against the FastAPI backend (`API_BASE`, from [src/lib/config.ts](src/lib/config.ts)) and fans the results into these UI sections, top to bottom:

| Section | Source endpoint | Backend service |
|---|---|---|
| Active Alerts banner (Monthly / Weekly tabs) | `GET /api/analytics/alerts`, `GET /api/analytics/weekly-alerts` | `analytics_service.detect_anomalies()`, `.detect_weekly_anomalies()` |
| KPI strip (Total Patients, Clinical Records, Active Alerts, Cities Monitored) | `GET /api/analytics/dashboard` (+ derived from hotspots) | `analytics_service.get_dashboard_summary()` |
| Geospatial Disease Clusters (DBSCAN) | `GET /api/analytics/clusters?days=90` | `spatial_service.get_cluster_summary()` |
| Disease Trends (90 days, line chart) | `GET /api/analytics/trends?days=90` | `analytics_service.get_disease_trends()` |
| Emerging Threats panel | `GET /api/forecast/emerging` | `forecast_service.get_emerging_trends()` → `DiseaseForecaster.detect_emerging_trends()` |
| Disease Hotspots (city list + filter) | `GET /api/analytics/hotspots` | `analytics_service.get_hotspots()` |
| 7-Day Regional Spread Forecast (bar chart) | `GET /api/analytics/predictions` | `gnn_service.predict_spread()` / `.get_spread_graph_summary()` |
| 3-Month Disease Forecast (table) | `GET /api/forecast?months=3` | `forecast_service.get_forecast()` → `DiseaseForecaster.forecast_next_months()` |
| Disease Load Distribution (radar) | derived client-side from `summary.top_diseases` | `analytics_service.get_dashboard_summary()` |
| Top Cities by Patient Load | derived client-side from `summary.top_cities` | `analytics_service.get_dashboard_summary()` |
| Devanāgarī/IAST disease name labels everywhere | `GET /api/analytics/disease-names` | `services/disease_names.py` (static dict) |

Every fetch is wrapped in `Promise.allSettled`, so a failing endpoint just leaves that section empty/loading — it doesn't break the rest of the page.

---

## 2. The ML/statistical models behind each panel

### 2.1 Monthly Alerts — Z-Score + CUSUM (statistical, not ML)
[backend/services/analytics_service.py](backend/services/analytics_service.py) `detect_anomalies()`

- Aggregates `medical_records` by `(disease, year-month)`.
- **Leave-one-out Z-score**: each month's count is scored against the mean/std of *every other* month for that disease — `Z = (x − μ) / σ`. Requires ≥3 months of history per disease.
- **CUSUM** (one-sided, `k=0.5`) runs on the same monthly series to catch slow drift Z-score would miss.
- An alert fires if `Z ≥ 2.0` **or** CUSUM crosses `max(5, mean×5)`.
- Severity bands: Critical `Z≥3.5`, High `Z≥2.5`, Medium `Z≥2.0`, Low otherwise (only reachable via the CUSUM-only path).

### 2.2 Weekly Alerts — bi-weekly rolling Z-score (early warning)
Same file, `detect_weekly_anomalies()`.

- Buckets visits into 2-week windows (`ISO week // 2`).
- Recent = mean of last 3 buckets (6 weeks), baseline = mean of the preceding 10 buckets (20 weeks), `Z = (recent_avg − base_avg) / base_std`, threshold `Z ≥ 1.6`.
- Purpose per the code/UI: fire 3–6 weeks before the monthly detector would.

### 2.3 3-Month Disease Forecast — RandomForestRegressor
[backend/disease_forecaster.py](backend/disease_forecaster.py) `forecast_next_months()`, wrapped by [backend/services/forecast_service.py](backend/services/forecast_service.py)

- Builds monthly `(disease, month)` case counts from `medical_records` + `patients`, adds lag-1/2/3 features, Ayurvedic Ritu (season) as a categorical feature, and `ritu_sandhi` (seasonal-transition) flag.
- Trains a single `RandomForestRegressor(n_estimators=200, max_depth=10)` **on every request** (not persisted/cached) over all diseases at once, encodes disease/category/season with `LabelEncoder`.
- Recursively predicts 1..N months ahead per disease using the last known lag values.
- `confidence_lower`/`confidence_upper` fields exist in the response schema but are always set to `None` — RandomForest here produces no prediction interval.
- Needs ≥3 months of history per disease or the whole call raises.

### 2.4 Emerging Threats — simple growth-rate math (not ML)
`DiseaseForecaster.detect_emerging_trends()`

- `growth_rate = (cases_this_month − cases_prev_month) / cases_prev_month × 100`, averaged over the last 3 months per disease.
- Alert level thresholds: Low <25%, Medium 25–50%, High 50–100%, Critical >100% (per the UI tooltip; the Python alert_level thresholds in `forecast_service.get_emerging_trends()` are actually >50/>25/>10, i.e. the UI tooltip copy and the backend thresholds don't match — see §3).

### 2.5 7-Day Regional Spread Forecast — deterministic graph diffusion, **not a trained GNN**
[backend/services/gnn_service.py](backend/services/gnn_service.py) `predict_spread()`

- Despite the module/class being named `GNNService`, this is plain graph diffusion via `networkx`, not a trained graph neural network. The code header and the dashboard's own info tooltip both say this explicitly ("Not a trained GNN — it is a deterministic graph diffusion (Phase 1)").
- Builds a graph where nodes = cities with recent case data, edges connect city pairs within 300 km (Haversine distance using a **hardcoded lat/lon table of ~30 major Indian cities**, `_CITY_COORDS`), edge weight = `1 − distance/300`.
- Simulates 7 daily steps: `next_load[city] = current_load[city]×0.88 + Σ(neighbor_load × edge_weight × 0.25)` — i.e. 12%/day decay plus a fixed 0.25 transmission-rate proxy for R₀, identical for every disease.
- Cities not in `_CITY_COORDS` are silently excluded from the graph entirely (no edges, no predictions).

### 2.6 Geospatial Disease Clusters — DBSCAN
[backend/services/spatial_service.py](backend/services/spatial_service.py) `get_disease_clusters()`

- Custom **pure-Python DBSCAN** implementation (not scikit-learn's), `eps=400km`, `min_samples=2`, run independently per disease.
- Points = the same hardcoded city-centroid table used by the GNN service (`_CITY_COORDS`), weighted by case count; there are no real lat/lon coordinates anywhere in the `patients` schema (`backend/models.py` has no lat/lon columns).
- Noise points (label `-1`) become singleton "hotspot" cards in the UI; real multi-city clusters get numbered.

### 2.7 KMeans Patient Clustering — present in the codebase, **not used on this dashboard**
[backend/services/clustering_service.py](backend/services/clustering_service.py)

- A `KMeans(n_clusters=10)` sklearn pipeline (StandardScaler + OneHotEncoder on age/severity/gender/prakriti/vikriti/disease), persisted to `backend/data/models/patient_cluster_model.pkl`, retrained via `/api/retrain`.
- This is a completely separate concept from the DBSCAN "clusters" shown on the dashboard, despite the similar name. It's used for patient-similarity/RL flows elsewhere in the app (treatment recommendation), not surfaced anywhere on `/public-health/dashboard`. Worth knowing so it isn't confused with §2.6.

### 2.8 Disease Names / Devanāgarī labels — static lookup, not generated
[backend/services/disease_names.py](backend/services/disease_names.py)

- A hand-maintained Python dict covering **~30 diagnosis strings** exactly as they're stored in `medical_records.diagnosis` (e.g. `"Fever (Jwara)"`).
- Anything not in the dict falls back to returning the raw diagnosis string as its own "devanagari"/"iast"/"hindi" value (`get_full_name`), and the frontend's `ayurvedicName()` helper further falls back to regex-extracting whatever is inside parentheses. So any new/misspelled diagnosis silently loses its Sanskrit rendering with no error.

---

## 3. Data basis — what the numbers actually come from

**All of it is synthetic, generated data — not real clinical activity.**

- [backend/generate_historical_data.py](backend/generate_historical_data.py): generates ~1 year of fake patients/visits with `random.seed(42)` for reproducibility, using a hand-authored `SEASONAL_DISEASES` calendar that **bakes in** seasonal surge patterns "so that anomaly detection, forecasting, and geospatial clustering have meaningful signals on day 1" (its own docstring).
- [backend/seed_weekly_surge_data.py](backend/seed_weekly_surge_data.py): explicitly injects an engineered spike pattern per disease — flat baseline for weeks −52..−7, "moderate rise" weeks −6..−1, "clear spike" at week 0 — specifically so the bi-weekly Z-score detector (§2.2) has something to fire on.
- `backend/db_dump/*.csv` (patients.csv, medical_records.csv, etc.) confirm this: patient names, addresses, and visit timestamps are procedurally generated, not imported from any real health system.
- City-level geography is a static 30-city centroid table (§2.5/2.6), not geocoded patient addresses.

**Implication:** every model on this dashboard (RandomForest forecast, Z-score/CUSUM alerts, DBSCAN clusters, diffusion-based spread) is validated only against data that was constructed to make those exact detectors succeed. There is no held-out real-world signal proving any of them generalizes, and the header copy "Real-time Ayurvedic epidemiological monitoring" overstates what's actually a demo/synthetic pipeline today.

---

## 4. Baseless / inconsistent / dead things found

1. **"GNN Service" name is misleading.** No graph neural network exists; it's deterministic diffusion (§2.5). This is at least self-disclosed in code and in the UI tooltip, but the class/module name (`GNNService`, `gnn_service.py`) will mislead anyone skimming the codebase without reading the tooltip.
2. **Engineered alerts.** The weekly-alert seed script (§3) manufactures the exact surge shape the weekly Z-score detector is tuned to catch — the "early warning" feature has never been tested against organic data.
3. **Emerging Threats threshold mismatch.** The dashboard info tooltip says alert levels are Low <25% / Medium 25–50% / High 50–100% / Critical >100%, but `forecast_service.get_emerging_trends()` actually computes `critical > 50, high > 25, medium > 10, else low` — the displayed methodology and the real thresholds disagree.
4. **Weekly-alerts docstring is stale.** [backend/main.py](backend/main.py) `/api/analytics/weekly-alerts` docstring says "4-week recent window vs 12-week baseline window", but the actual `analytics_service.detect_weekly_anomalies()` defaults (also matched by the frontend tooltip) are 6-week recent vs 20-week baseline. The endpoint docstring was never updated when the defaults changed.
5. **Forecast confidence interval fields are always null.** `ForecastResponse.forecast_data[].confidence_lower/upper` exist in the schema and imply uncertainty bounds, but `ForecastService.get_forecast()` never populates them — RandomForest here gives point estimates only.
6. **Hardcoded 30-city coverage gap.** Any patient whose city isn't one of the ~30 keys in `_CITY_COORDS` ([gnn_service.py](backend/services/gnn_service.py)) is silently dropped from both the spread-forecast graph and the DBSCAN clustering — no warning, no fallback geocoding, no error surfaced to the dashboard.
7. **Disease-name coverage is partial.** Only diagnoses in the static `DISEASE_NAMES` dict (~30 exact strings) get real Devanāgarī/IAST text; anything else falls back to displaying the raw diagnosis text as if it were the Sanskrit name.
8. **Unused imports suggest an abandoned feature.** `Thermometer`, `Wind`, `Droplets` icons are imported in [page.tsx](src/app/public-health/dashboard/page.tsx) but never referenced anywhere in the component — looks like a planned weather/climate-correlation panel that was never built (there's also no backend endpoint for weather data anywhere in `main.py`).
9. **No accuracy/backtesting for the dashboard's own models.** The README's `/api/admin/accuracy` endpoint only evaluates the ISHAAyush *treatment recommendation* engine against `treatment_feedback.csv` and voice/ASR transcription accuracy — there is no equivalent backtest or accuracy metric for the RandomForest disease forecast or the graph-diffusion spread model shown here.
10. **`clusters` state is untyped (`any[]`)** in the frontend while every other panel has a typed interface — the DBSCAN cluster shape isn't declared anywhere in the TypeScript layer.
11. **KMeans clustering service naming collision** (§2.7) — a developer could reasonably assume `clustering_service.py` backs the dashboard's "Geospatial Disease Clusters" panel; it doesn't. That panel is 100% `spatial_service.py` (DBSCAN).

---

## 5. Future changes required (per the code's own stated roadmap + gaps above)

- **Phase 2 GNN**: replace the diffusion simulation in `gnn_service.py` with a real trained PyTorch Geometric ST-GNN once "6+ months of live data" exists — this is explicitly called out in both the service docstring and the dashboard tooltip, so it's a known/accepted placeholder, not a surprise.
- **Real geocoding**: replace the static `_CITY_COORDS` table (shared by GNN spread and DBSCAN clustering) with actual lat/lon geocoded from patient addresses, so coverage isn't capped at ~30 pre-listed cities.
- **Real clinical data**: swap the synthetic `generate_historical_data.py` / `seed_weekly_surge_data.py` seeded dataset for genuine patient records before treating any alert, forecast, or cluster as production-trustworthy; add a held-out validation set so detectors are proven on data they weren't tuned against.
- **Forecast uncertainty**: either populate `confidence_lower/upper` (e.g. via quantile regression forests or bootstrapped RandomForest trees) or drop the fields from the schema so the UI doesn't imply unshipped functionality.
- **Reconcile documentation with code**: fix the `/api/analytics/weekly-alerts` docstring (4wk/12wk → 6wk/20wk) and the Emerging Threats alert-level thresholds (tooltip vs. actual `>50/>25/>10` cutoffs) so displayed methodology matches computed behavior.
- **Expand/automate Devanāgarī coverage**: either grow `DISEASE_NAMES` to cover all diagnoses the ISHAAyush dataset can produce, or add a transliteration fallback instead of silently echoing the raw English/parenthetical string.
- **Model accuracy tracking for public-health models**: extend the existing `/api/admin/accuracy` pattern (currently ISHAAyush + voice only) to backtest the RandomForest forecast and the spread-diffusion model against realized outcomes.
- **Finish or remove the weather-correlation panel**: `Thermometer`/`Wind`/`Droplets` imports imply a planned feature; either wire up a weather data source and panel or delete the dead imports.
- **Type the clusters payload**: add a `ClusterData` TypeScript interface matching `spatial_service.get_cluster_summary()`'s shape instead of `any[]`.
- **Disambiguate the two clustering systems**: rename `clustering_service.py`'s KMeans service (e.g. `patient_clustering_service.py`) to avoid confusion with the DBSCAN `spatial_service.py` that actually powers the dashboard's cluster panel.
