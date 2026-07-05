"""
Analytics Service — PostgreSQL-backed disease trends, hotspots, and anomaly detection.

Anomaly Detection uses:
  - Z-Score (month-over-month, leave-one-out baseline) to catch sharp historical surges
  - CUSUM (Cumulative Sum) to catch slow-building drift that Z-Score misses
  - 4-level severity grading: Low / Medium / High / Critical
"""
from datetime import datetime, timedelta, date
from collections import defaultdict
import calendar
import math
from sqlalchemy import func
from models import SessionLocal, Patient, MedicalRecord
from utils.episode_dedup import dedupe_repeat_diagnoses


# ─── Statistical helpers ─────────────────────────────────────────────────────

def _mean(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def _z_score(value: float, mean: float, std: float) -> float:
    """Z = (x - μ) / σ.  Returns 0 if σ too small (stable baseline)."""
    return (value - mean) / std if std > 0.5 else 0.0


def _cusum(series: list, target_mean: float, k_factor: float = 0.5) -> float:
    """
    One-sided CUSUM — detects upward drift.
    k_factor=0.5 is standard. Lower = more sensitive.
    Returns final cumulative sum (positive = upward drift detected).
    """
    s = 0.0
    for c in series:
        s = max(0, s + (c - target_mean) - k_factor)
    return s


def _severity_from_z(z: float) -> str:
    """Map Z-score to 4-level severity."""
    if z >= 3.5:
        return "Critical"   # < 0.02% probability under H0
    if z >= 2.5:
        return "High"       # < 0.6%
    if z >= 2.0:
        return "Medium"     # < 2.3%
    return "Low"


# ─── Analytics Service ────────────────────────────────────────────────────────

class AnalyticsService:

    # ─── Disease Trends ───────────────────────────────────────────────────────

    def get_disease_trends(self, days: int = 30) -> list:
        """Aggregate weekly case counts per disease."""
        # Calculate how many 7-day weeks we need to cover the requested days
        num_weeks = (days + 6) // 7
        start_date = (datetime.utcnow() - timedelta(days=num_weeks * 7)).date()

        with SessionLocal() as db:
            rows = (
                db.query(MedicalRecord.visit_date, MedicalRecord.diagnosis)
                .filter(
                    MedicalRecord.visit_date >= start_date,
                    MedicalRecord.diagnosis  != None,
                    MedicalRecord.diagnosis  != "",
                )
                .all()
            )

        # 1. Tally raw counts per day per disease
        from collections import defaultdict
        raw_counts = defaultdict(lambda: defaultdict(int))
        all_diseases = set()

        for visit_date, diagnosis in rows:
            if not visit_date or not diagnosis:
                continue
            d = visit_date.date() if hasattr(visit_date, "date") else visit_date
            diagnosis = diagnosis.strip()
            raw_counts[d][diagnosis] += 1
            all_diseases.add(diagnosis)

        # 2. Build weekly segments going backward from today
        results = []
        today = datetime.utcnow().date()

        for w in range(num_weeks - 1, -1, -1):
            # Each week is a 7-day window ending at today - w*7
            week_end = today - timedelta(days=w * 7)
            week_start = week_end - timedelta(days=6)

            # Sum counts for each disease over this 7-day window
            week_sum = defaultdict(int)
            for j in range(7):
                w_date = week_start + timedelta(days=j)
                for diag, count in raw_counts[w_date].items():
                    week_sum[diag] += count

            day_data = {"date": week_end.isoformat()}
            for diag in all_diseases:
                day_data[diag] = week_sum[diag]

            results.append(day_data)

        return results

    # ─── Hotspots ─────────────────────────────────────────────────────────────

    def get_hotspots(self, disease: str = None) -> list:
        """
        Identify city-level locations with high case counts from real DB.

        Counts DISTINCT PATIENTS per (city, diagnosis), not raw visit rows —
        a patient who visits 3 times for the same complaint is one affected
        person, not 3 cases (dedupe_repeat_diagnoses with gap_days=None
        collapses their whole history for that diagnosis to their latest
        visit). Grouped by (city, diagnosis) rather than (city, pincode,
        diagnosis) — pincode varies patient-to-patient within the same city,
        so grouping by it fragmented what should be one city-level count into
        many single-patient rows.
        """
        with SessionLocal() as db:
            query = (
                db.query(Patient.id, Patient.city, Patient.pincode, MedicalRecord.diagnosis, MedicalRecord.visit_date)
                .join(MedicalRecord, MedicalRecord.patient_id == Patient.id)
                .filter(MedicalRecord.diagnosis != None, MedicalRecord.diagnosis != "", MedicalRecord.visit_date != None)
            )
            if disease:
                query = query.filter(MedicalRecord.diagnosis.ilike(f"%{disease}%"))
            rows = query.all()

        deduped = dedupe_repeat_diagnoses(rows, patient_idx=0, diagnosis_idx=3, date_idx=4, gap_days=None)

        counts: dict = defaultdict(int)
        example_pincode: dict = {}
        for _patient_id, city, pincode, diagnosis, _visit_date in deduped:
            city      = (city or "Unknown").strip()
            diagnosis = (diagnosis or "").strip()
            if not diagnosis:
                continue
            key = (city, diagnosis)
            counts[key] += 1
            example_pincode[key] = (pincode or "").strip()

        results = [
            {"city": k[0], "pincode": example_pincode[k], "diagnosis": k[1], "count": v}
            for k, v in counts.items()
        ]
        results.sort(key=lambda x: x["count"], reverse=True)
        return results

    # ─── Anomaly Detection — Z-Score + CUSUM ─────────────────────────────────

    def detect_anomalies(
        self,
        recent_window_days: int = 30,
        baseline_window_days: int = 180,
        z_threshold: float = 2.0,
        min_recent_cases: int = 3,
    ) -> list:
        """
        Detect disease surges using MONTHLY Z-Score + CUSUM.

        Strategy:
          Aggregates all records by (disease, year-month), then applies a
          leave-one-out Z-Score: each month's count is scored against the
          distribution of all OTHER months for that disease.

          This allows historical surge months (e.g. Aug 2025 Dengue spike) to
          be detected regardless of today's date.

        CUSUM is additionally run on the monthly time-series per disease to
        catch slow-building drift that Z-Score alone would miss.

        Severity levels:
          Critical: Z ≥ 3.5  (< 0.02% chance under H0)
          High:     Z ≥ 2.5  (< 0.6%)
          Medium:   Z ≥ 2.0  (< 2.3%)
          Low:      Z ≥ 1.5  (< 6.7%)
        """
        with SessionLocal() as db:
            rows = (
                db.query(MedicalRecord.visit_date, MedicalRecord.diagnosis, MedicalRecord.patient_id)
                .filter(
                    MedicalRecord.visit_date != None,
                    MedicalRecord.diagnosis  != None,
                    MedicalRecord.diagnosis  != "",
                )
                .all()
            )

        if not rows:
            return []

        # Collapse tight-together repeat/follow-up visits (same patient, same
        # diagnosis, within 14 days) into one episode so a single patient's
        # follow-up doesn't get counted as a second case in the same month —
        # but a genuine recurrence weeks/months later still counts, since
        # that's real distinct incidence for surge detection.
        rows = dedupe_repeat_diagnoses(rows, patient_idx=2, diagnosis_idx=1, date_idx=0, gap_days=14)

        # ── Build disease → { YYYY-MM → count } ─────────────────────────────
        disease_monthly: dict = defaultdict(lambda: defaultdict(int))
        for visit_date, diagnosis, _patient_id in rows:
            if not visit_date or not diagnosis:
                continue
            d  = visit_date.date() if hasattr(visit_date, "date") else visit_date
            ym = d.strftime("%Y-%m")
            disease_monthly[diagnosis.strip()][ym] += 1

        alerts = []

        for disease, monthly_counts in disease_monthly.items():
            if len(monthly_counts) < 3:
                continue  # need ≥3 months for statistics

            sorted_months = sorted(monthly_counts.keys())
            counts        = [float(monthly_counts[m]) for m in sorted_months]
            overall_mean  = _mean(counts)

            # ── CUSUM on the full monthly series ──────────────────────────────
            cusum_total     = _cusum(counts, overall_mean, k_factor=0.5)
            cusum_threshold = max(5.0, overall_mean * 5)

            # ── Leave-one-out Z-Score per month ───────────────────────────────
            best_alert = None

            for i, (ym, count) in enumerate(zip(sorted_months, counts)):
                if count < min_recent_cases:
                    continue

                # Baseline = every other month
                others    = counts[:i] + counts[i + 1:]
                if len(others) < 2:
                    continue

                base_mean = _mean(others)
                base_std  = _std(others)
                z         = _z_score(count, base_mean, base_std)

                # CUSUM up to and including this month
                cusum_here = _cusum(counts[:i + 1], base_mean, k_factor=0.5) >= cusum_threshold

                if z < z_threshold and not cusum_here:
                    continue

                severity     = _severity_from_z(z)
                pct_increase = (
                    round((count - base_mean) / base_mean * 100, 1)
                    if base_mean > 0 else 100.0
                )

                triggers = []
                if z >= z_threshold:
                    triggers.append(f"Z={z:.1f}")
                if cusum_here:
                    triggers.append("CUSUM drift")

                candidate = {
                    "disease":      disease,
                    "severity":     severity,
                    "recent_cases": int(count),
                    "surge_month":  ym,
                    "recent_avg":   round(count / 30, 2),      # per-day avg for that month
                    "baseline_avg": round(base_mean / 30, 2),
                    "baseline_std": round(base_std, 2),
                    "z_score":      round(z, 2),
                    "cusum_value":  round(cusum_total, 2),
                    "pct_increase": pct_increase,
                    "triggered_by": ", ".join(triggers),
                    "anchor_date":  ym,
                    "date":         ym,
                    "window_start": f"{ym}-01",
                    "window_end":   f"{ym}-{calendar.monthrange(*map(int, ym.split('-')))[1]:02d}",
                    "message": (
                        f"{severity} surge: {disease} in {ym}. "
                        f"{int(count)} cases ({pct_increase:+.0f}% vs "
                        f"{base_mean:.0f}-case monthly baseline). "
                        f"Z={z:.1f}. Signals: {', '.join(triggers)}."
                    ),
                }

                # Keep only the most anomalous month per disease
                if best_alert is None or z > best_alert["z_score"]:
                    best_alert = candidate

            if best_alert:
                alerts.append(best_alert)

        alerts.sort(key=lambda x: x["z_score"], reverse=True)
        return alerts

    # ─── Weekly Z-Score Anomaly Detection ────────────────────────────────────

    def detect_weekly_anomalies(
        self,
        lookback_weeks: int = 52,
        recent_windows: int = 3,      # recent bi-weekly windows  (= 6 weeks)
        baseline_windows: int = 10,   # baseline bi-weekly windows (= 20 weeks)
        z_threshold: float = 1.6,
        min_recent_cases: int = 1,
    ) -> list:
        """
        Detect disease surges using a BI-WEEKLY rolling Z-Score.

        Aggregates records into 2-week buckets (bi-weekly) to handle the
        sparse case counts typical in Ayurvedic clinical datasets.

        Strategy:
          - Buckets: ISO-week // 2  → 26 bi-weekly periods per year
          - recent_avg  = mean of last `recent_windows` bi-weekly buckets
          - base_avg    = mean of preceding `baseline_windows` buckets
          - Z           = (recent_avg - base_avg) / base_std

        Returns the same schema as detect_anomalies() for UI compatibility.
        """
        cutoff = datetime.utcnow() - timedelta(weeks=lookback_weeks)

        with SessionLocal() as db:
            rows = (
                db.query(MedicalRecord.visit_date, MedicalRecord.diagnosis, MedicalRecord.patient_id)
                .filter(
                    MedicalRecord.visit_date >= cutoff,
                    MedicalRecord.visit_date != None,
                    MedicalRecord.diagnosis  != None,
                    MedicalRecord.diagnosis  != "",
                )
                .all()
            )

        if not rows:
            return []

        # Same tight-follow-up collapse as detect_anomalies() — see comment there.
        rows = dedupe_repeat_diagnoses(rows, patient_idx=2, diagnosis_idx=1, date_idx=0, gap_days=14)

        # ── Build disease → { bi-week-bucket → count } ──────────────────────
        # Bi-weekly bucket label: "YYYY-B{n}" where n = ISO-week // 2
        disease_biweekly: dict = defaultdict(lambda: defaultdict(int))
        for visit_date, diagnosis, _patient_id in rows:
            if not visit_date or not diagnosis:
                continue
            d   = visit_date.date() if hasattr(visit_date, "date") else visit_date
            iso = d.isocalendar()
            bw  = iso.week // 2
            bucket = f"{iso.year}-B{bw:02d}"
            disease_biweekly[diagnosis.strip()][bucket] += 1

        alerts = []
        min_buckets_needed = recent_windows + baseline_windows

        for disease, bucket_counts in disease_biweekly.items():
            sorted_buckets = sorted(bucket_counts.keys())
            if len(sorted_buckets) < min_buckets_needed:
                continue

            counts = [float(bucket_counts[b]) for b in sorted_buckets]

            recent_slice   = counts[-recent_windows:]
            baseline_slice = counts[-(recent_windows + baseline_windows):-recent_windows]

            if len(baseline_slice) < 3:
                continue

            recent_sum = sum(recent_slice)
            if recent_sum < min_recent_cases:
                continue

            recent_avg  = _mean(recent_slice)
            base_avg    = _mean(baseline_slice)
            base_std    = _std(baseline_slice)

            z = _z_score(recent_avg, base_avg, base_std)
            if z < z_threshold:
                continue

            severity     = _severity_from_z(z)
            pct_increase = (
                round((recent_avg - base_avg) / base_avg * 100, 1)
                if base_avg > 0 else 100.0
            )

            latest_bucket = sorted_buckets[-1]
            # Convert bucket label to human week range
            year, bnum = latest_bucket.split("-B")
            year_int = int(year)
            week_start = int(bnum) * 2
            week_label = f"{year} W{week_start}–W{week_start + 1}"

            # ISO week 0 isn't valid — clamp into range for the date conversion below
            iso_week = max(1, min(53, week_start))
            window_start_dt = datetime.fromisocalendar(year_int, iso_week, 1)
            window_end_dt = window_start_dt + timedelta(days=13)

            alerts.append({
                "disease":        disease,
                "severity":       severity,
                "recent_cases":   int(recent_sum),
                "surge_month":    week_label,
                "week":           week_label,
                "date":           week_label,
                "anchor_date":    week_label,
                "window_start":   window_start_dt.date().isoformat(),
                "window_end":     window_end_dt.date().isoformat(),
                "recent_weeks":   recent_windows * 2,
                "recent_avg":     round(recent_avg, 2),
                "baseline_avg":   round(base_avg, 2),
                "baseline_std":   round(base_std, 2),
                "z_score":        round(z, 2),
                "cusum_value":    0.0,
                "pct_increase":   pct_increase,
                "triggered_by":   f"Weekly Z={z:.1f}",
                "detection_type": "weekly",
                "message": (
                    f"{severity} bi-weekly surge: {disease}. "
                    f"Recent 6-week avg={recent_avg:.1f} cases "
                    f"(+{pct_increase:.0f}% vs {base_avg:.1f} baseline). "
                    f"Z={z:.1f}."
                ),
            })

        alerts.sort(key=lambda x: x["z_score"], reverse=True)
        return alerts

    # ─── Case-level drill-down ────────────────────────────────────────────────
    # NOTE: returns patient-identifying fields (name, age, gender, city). Safe
    # only because this dataset is synthetic — a real deployment would need
    # access control in front of this endpoint before it touched real PHI.

    def get_case_details(
        self,
        disease: str,
        cities: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        days: int | None = None,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """
        Return the individual patient visits backing a signal (alert, emerging
        threat, hotspot, or cluster), plus the total matching count.

        Date scoping (mutually exclusive, checked in this order):
          - `days`: relative window, `visit_date >= utcnow() - days` (clusters).
          - `start_date`/`end_date`: explicit window (alerts, emerging threats).
          - neither: all-time, matching get_hotspots()'s existing semantics.
        """
        with SessionLocal() as db:
            query = (
                db.query(Patient, MedicalRecord)
                .join(MedicalRecord, MedicalRecord.patient_id == Patient.id)
                .filter(MedicalRecord.diagnosis == disease)
            )
            if cities:
                query = query.filter(
                    func.lower(Patient.city).in_([c.strip().lower() for c in cities])
                )
            if days is not None:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = query.filter(MedicalRecord.visit_date >= cutoff)
            elif start_date or end_date:
                if start_date:
                    query = query.filter(MedicalRecord.visit_date >= start_date)
                if end_date:
                    query = query.filter(MedicalRecord.visit_date <= f"{end_date} 23:59:59")

            rows = query.order_by(MedicalRecord.visit_date.desc()).all()

        # Collapse a patient's repeat visits for this diagnosis into one episode
        # before counting/limiting — otherwise the same person's follow-up visits
        # (different dates, slightly reworded symptoms) show up as separate
        # "cases" here even though get_hotspots()/get_disease_clusters() already
        # count them as one. gap_days mirrors whichever aggregate triggered this
        # drill-down: alerts/emerging-threats (start/end date) use the same
        # 14-day tight-follow-up window as detect_anomalies(); hotspots/clusters
        # (days or neither) collapse the whole matching window to one episode.
        gap_days = 14 if (start_date or end_date) else None
        flat_rows = [(p.id, m.diagnosis, m.visit_date, p, m) for p, m in rows]
        deduped = dedupe_repeat_diagnoses(
            flat_rows, patient_idx=0, diagnosis_idx=1, date_idx=2, gap_days=gap_days
        )
        deduped.sort(key=lambda r: r[2], reverse=True)

        total_count = len(deduped)
        limited = deduped[:limit]

        cases = [
            {
                "patient_id":    p.id,
                "name":          f"{p.first_name} {p.last_name}".strip(),
                "age":           p.age,
                "gender":        p.gender,
                "city":          p.city,
                "state":         p.state,
                "visit_date":    m.visit_date.isoformat() if m.visit_date else None,
                "severity":      m.severity,
                "symptoms":      m.symptoms,
                "prakriti":      m.prakriti,
                "vikriti":       m.vikriti,
                "comorbidities": m.comorbidities,
            }
            for _pid, _diag, _date, p, m in limited
        ]
        return cases, total_count

    # ─── Dashboard Summary ────────────────────────────────────────────────────

    def get_dashboard_summary(self, days: int = None) -> dict:
        """Overall analytics summary from real PostgreSQL data, optionally scoped to the last `days` days."""
        with SessionLocal() as db:
            cutoff = datetime.utcnow() - timedelta(days=days) if days else None

            total_patients = db.query(Patient).count()
            total_records  = db.query(MedicalRecord).count()

            disease_query = db.query(MedicalRecord.diagnosis).filter(
                MedicalRecord.diagnosis != None, MedicalRecord.diagnosis != ""
            )
            if cutoff:
                disease_query = disease_query.filter(MedicalRecord.visit_date >= cutoff)
            disease_rows = disease_query.all()
            disease_counts: dict = defaultdict(int)
            for (diag,) in disease_rows:
                if diag and diag.strip():
                    disease_counts[diag.strip()] += 1

            top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            city_query = db.query(Patient.city).filter(Patient.city != None, Patient.city != "")
            if cutoff:
                city_query = city_query.join(
                    MedicalRecord, MedicalRecord.patient_id == Patient.id
                ).filter(MedicalRecord.visit_date >= cutoff)
            city_rows = city_query.all()
            city_counts: dict = defaultdict(int)
            for (city,) in city_rows:
                if city and city.strip():
                    city_counts[city.strip()] += 1

            top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_patients":         total_patients,
            "total_medical_records":  total_records,
            "total_health_records":   total_records,
            "top_diseases": [{"disease": d, "count": c} for d, c in top_diseases],
            "top_cities":   [{"city": c, "count": n} for c, n in top_cities],
        }


# ─── Singleton ────────────────────────────────────────────────────────────────
analytics_service = AnalyticsService()
