# Public Health Dashboard — Insights Reference

What every panel on [`/public-health/dashboard`](src/app/public-health/dashboard/page.tsx)
actually shows, why it's there, and exactly how the number on screen gets computed.
Written against the dashboard's current state — after the data-realism pass
(140 cities, 109 diseases, real pincodes), the episode-based case-counting fix,
and the case-level drill-down feature. For known bugs/gaps still open, see
`PUBLIC_HEALTH_DASHBOARD_ISSUES.md`. For the original deep-dive into what
backs each panel at the code level, see `PUBLIC_HEALTH_DASHBOARD.md`.

---

## Quick map

| Panel | Answers | Counts by |
|---|---|---|
| KPI Strip | "How big is the surveillance base, and is anything on fire right now?" | Raw totals / active alert count |
| Active Alerts | "Which diseases are surging *right now*, and how sure are we?" | Distinct patients (episode-deduped, 14-day window) |
| Geospatial Clusters | "Is a disease spreading across a region, or stuck in one city?" | Distinct patients, last 90 days |
| Disease Trends | "Is this disease's case count rising, falling, or flat over 90 days?" | Raw daily visit volume |
| Emerging Threats | "What's accelerating before it's officially an alert?" | Distinct patients (episode-deduped, 14-day window) |
| Disease Hotspots | "Which city has the most people sick with X, all-time?" | Distinct patients, all-time |
| 7-Day Spread Forecast | "If nothing changes, how will load move between cities this week?" | Deterministic diffusion over raw case load |
| 3-Month Forecast | "How many cases should we plan for, per disease, next quarter?" | RandomForest over episode-deduped monthly counts |
| Disease Load Radar | "What's the overall clinical workload mix?" | Raw visit volume (intentionally — see note below) |
| Top Cities | "Where are our patients based?" | Distinct patients (by registration city) |
| View Cases (any panel) | "Show me the actual people/visits behind this number." | Raw, undeduped evidence |

The "counts by" column matters — see **Why some panels count differently**
near the bottom before assuming two panels disagreeing is a bug.

---

## KPI Summary Strip

**What it shows**: four numbers at the very top — Total Patients, Clinical
Records, Active Alerts, Cities Monitored.

**Why it helps**: the first thing anyone should see — the scale of what's
being monitored, and whether there's anything urgent before drilling into any
specific panel.

**How it works**: `Total Patients`/`Clinical Records` are plain row counts on
the `patients`/`medical_records` tables (`analytics_service.get_dashboard_summary()`).
`Active Alerts` is the length of the monthly alerts list (the same list shown
in the banner below). `Cities Monitored` is the count of distinct cities
appearing in the Hotspots data.

---

## Active Alerts (Monthly / Weekly tabs)

**What it shows**: diseases with a statistically unusual case-count surge,
each tagged Critical/High/Medium/Low. Two tabs: **Monthly** (established,
already-happened surges) and **Weekly** (early warning, fires 3–6 weeks
before the monthly detector would).

**Why it helps**: this is the "what needs attention today" list — ranked by
how anomalous the signal is, not just raw case count, so a small disease with
a huge relative spike surfaces alongside a big disease with a huge absolute
one.

**How it works**:
- *Monthly*: groups visits by `(disease, calendar month)`, then scores each
  month with a **leave-one-out Z-score** — how many standard deviations that
  month's count is from the mean of every *other* month for that disease.
  **CUSUM** runs alongside to catch slow-building drift a single-month Z-score
  would miss. Fires if `Z ≥ 2.0` or a CUSUM threshold is crossed. Severity:
  Critical `Z≥3.5`, High `Z≥2.5`, Medium `Z≥2.0`, Low otherwise.
- *Weekly*: buckets visits into 2-week windows, compares the last 6 weeks'
  average against the preceding 20-week baseline, `Z ≥ 1.6` threshold.
- Both detectors collapse a single patient's repeat visits for the same
  disease within a **14-day** window into one case before counting — a
  follow-up visit 3 days later doesn't get double-counted as a second case,
  but a genuine recurrence 2 months later still does (see the counting-modes
  note below).
- Click **View Cases** on any alert to see the literal patient visits (name,
  city, date, severity) that produced that Z-score.

---

## Geospatial Disease Clusters (DBSCAN)

**What it shows**: cities within 400km of each other sharing an elevated
burden of the *same* disease get grouped into a numbered "cluster" (≥2
cities); a single very-affected city with no nearby peers becomes an isolated
"hotspot" card.

**Why it helps**: distinguishes a regionally-spreading outbreak (a real
cluster — needs a coordinated, multi-city response) from a one-off local
spike (a hotspot — probably a local cause, not spread).

**How it works**: a pure-Python DBSCAN (`eps=400km`, `min_samples=2`) runs
independently per disease over the last 90 days. Each city is a point,
positioned by its centroid from `services/geo_reference.py` (~140 Indian
cities across every state/UT) and weighted by its (deduped) patient count for
that disease. Click **View Cases** on a cluster to see the patients across
*all* cities in that cluster for the window shown.

---

## Disease Trends (90 Days)

**What it shows**: a 90-day line chart, one line per disease, for the 6
highest-volume diseases currently in the data.

**Why it helps**: the fastest way to eyeball whether a disease is trending up,
down, or flat, and to spot timing relationships between diseases (e.g. a
Fever bump a few days before a Dengue bump).

**How it works**: visit counts per disease, aggregated into 7-day calendar weeks over the last 90 days to highlight trends clearly and avoid daily noise.
Raw visit volume — not deduped (a chart about "how busy has this disease kept
the clinic" is a workload question, not an affected-people question).

---

## Emerging Threats

**What it shows**: diseases whose case count is growing fastest month over
month, ranked by growth rate with a Low/Medium/High/Critical label.

**Why it helps**: catches diseases that haven't crossed the Alerts panel's
statistical bar yet but are clearly trending toward it — an earlier, softer
warning than a full Z-score alert.

**How it works**: `growth_rate = (recent 3-month avg − prior period avg) / prior × 100`,
computed from the same monthly, episode-deduped case counts the forecaster
uses. Each row exposes the exact 3 months it's based on (`window_start`/
`window_end`) rather than guessing off today's date — click **View Cases** to
see those months' actual visits.

---

## Disease Hotspots

**What it shows**: a ranked list of `(city, disease)` pairs by number of
distinct affected patients, all-time, filterable to one disease via the
dropdown.

**Why it helps**: the most direct "where is this actually happening"
signal — useful for deciding where to route outreach or supplies.

**How it works**: counts **distinct patients** per `(city, disease)`, not raw
visit rows — a patient with 3 visits for the same disease is one affected
person, counted once, using their most recent visit. This was a real bug
fixed this pass: before, grouping also included each patient's individual
pincode, which fragmented a city's true count across dozens of near-duplicate
rows; and raw visit counting meant a single chronic patient's repeat visits
alone could make a city look like a hotspot. Click **View Cases** to see the
underlying visits — which may show *more* rows than the hotspot's count, since
the count is people, not visits.

---

## 7-Day Regional Spread Forecast

**What it shows**: a bar chart predicting each major city's case load for the
next 7 days if nothing changes.

**Why it helps**: a short operational planning horizon — which cities might
need more clinical capacity in the coming week.

**How it works**: **not a trained model** — deterministic graph diffusion,
self-disclosed in the tooltip and code. Cities within 300km of each other are
connected in a graph (edge weight ∝ proximity, from the same `geo_reference.py`
centroid table used by Clusters). Each simulated day: `next_load = current_load × 0.88
+ Σ(neighbor_load × edge_weight × 0.25)` — a flat 12%/day decay plus a fixed
0.25 transmission-rate proxy, identical for every disease. A real trained
spatio-temporal GNN is planned once 6+ months of live data exists.

---

## 3-Month Disease Forecast

**What it shows**: a table of predicted case counts per disease for each of
the next 3 months.

**Why it helps**: a medium-term planning view — staffing, herb/medicine
stock, outreach — beyond the reactive week-to-week signals above.

**How it works**: a `RandomForestRegressor` (200 trees, depth 10) trained
fresh on every request over the full episode-deduped monthly history, using
lag-1/2/3 month features, the Ayurvedic *Ritu* (season) as a categorical
feature, and a *ritu sandhi* (seasonal-transition — historically higher risk)
flag. Predicts recursively, feeding each month's prediction back in as the
next month's lag. **Known limitation**: the `confidence_lower`/`confidence_upper`
fields in the response are always `null` — the model gives point estimates
only right now (tracked in `PUBLIC_HEALTH_DASHBOARD_ISSUES.md`).

---

## Disease Load Distribution (Radar)

**What it shows**: a radar/spider chart of the top 6 diseases by total case
volume.

**Why it helps**: one glance at whether clinical load is concentrated in a
couple of dominant diseases or spread evenly.

**How it works**: raw visit-row counts per diagnosis, all-time — deliberately
*not* deduped. This chart is answering "how much of the clinic's total work is
this disease", which is a workload question (every visit is real clinical
work), not "how many distinct people have this disease" (which is what
Hotspots answers, and does dedupe).

---

## Top Cities by Patient Load

**What it shows**: a ranked bar-list of cities by number of patients based
there.

**Why it helps**: where the patient base itself is concentrated — a
registration/demographics view, distinct from Hotspots' disease-concentration
view.

**How it works**: counts rows in the `patients` table grouped by city (not
joined to visits at all), so it's inherently one count per patient regardless
of how many times they've visited for anything.

---

## Case-Level Drill-Down ("🔍 View Cases")

**What it shows**: click it on any alert, emerging threat, hotspot, or
cluster card, and a modal opens showing the literal patient visits behind
that number — name, age/gender, city, visit date, severity, symptoms — plus
a "Showing N of Total" count.

**Why it helps**: every aggregate number on this dashboard is now auditable.
Instead of trusting a Z-score or a "12 cases" hotspot count on faith, you can
see exactly which patients and visits produced it — which matters for
building trust in a synthetic/demo dataset, and would matter even more once
this points at real clinical data.

**How it works**: one generic endpoint, `/api/analytics/case-details`,
parameterized differently per signal:
- Alerts / Emerging Threats: exact date window the signal was computed from
  (`window_start`/`window_end`, added server-side so the UI never has to
  guess a date range off today's date).
- Hotspots: disease + city, no date window (matches the panel's own all-time
  scope).
- Clusters: disease + every city in the cluster + the cluster's own relative
  `days` window.

This endpoint deliberately returns **raw, undeduped** visits — it's the one
place that should show you every visit, including repeats, so you can see for
yourself when a count like a hotspot's "12" is backed by 12 people or (as
shown in testing) 12 people and one of them visiting twice.

---

## Why some panels count differently

Two different questions get asked across this dashboard, and each panel
answers exactly one of them — not a bug when their numbers don't match:

1. **"How many distinct people are affected?"** — Alerts, Emerging Threats,
   Clusters, Hotspots, the 3-Month Forecast. These *episode-dedupe*: a
   patient's repeat visits for the same disease collapse into one case.
   - Hotspots/Clusters use a **no-time-limit** episode (their whole history
     of that diagnosis → their single latest visit) — the question is "is
     this person currently/ever affected", not "when".
   - Alerts/Emerging Threats/Forecast use a **14-day** episode window — a
     follow-up visit days later isn't a new case, but a recurrence months
     later genuinely is, for surge-tracking purposes.
2. **"How much clinical work has this generated?"** — the KPI's "Clinical
   Records" count, Disease Trends, the Disease Load Radar, and the raw rows
   the View Cases modal shows. These count every visit, because every visit
   is real clinical work regardless of whether it's a new case or a
   follow-up.

If a hotspot says a city has 12 cases of a disease but the View Cases modal
under it shows 13 rows, that's the two questions in action: 12 distinct
people, one of whom came twice.

---

## Shared building blocks

- **Devanāgarī/IAST naming** (`services/disease_names.py`): every one of the
  109 diagnoses tracked (28 seasonal/acute + 81 chronic/long-tail) has a
  Sanskrit name, sourced from the government NAMC dataset already in the repo
  (`data/Codified_Ayurvedic_disease.csv`), with a handful of corrections where
  NAMC's own crosswalk mapped a term with no real clinical relationship to
  the English name (documented in the source comments there).
- **Geographic reference** (`services/geo_reference.py`): ~140 Indian cities
  across every state/UT, population-tiered weights, and real India-Post
  postal-range-based pincodes — shared by Hotspots, Clusters, and the Spread
  Forecast so they all agree on where a city actually is.
