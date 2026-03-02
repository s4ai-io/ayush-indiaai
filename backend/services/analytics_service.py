"""
Analytics Service — PostgreSQL-backed disease trends, hotspots, and anomaly detection.

Anomaly Detection uses:
  - Z-Score (month-over-month, leave-one-out baseline) to catch sharp historical surges
  - CUSUM (Cumulative Sum) to catch slow-building drift that Z-Score misses
  - 4-level severity grading: Low / Medium / High / Critical
"""
from datetime import datetime, timedelta, date
from collections import defaultdict
import math
from models import SessionLocal, Patient, MedicalRecord


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
        """Aggregate daily case counts per disease (7-day rolling average)."""
        # Fetch data for `days + 7` to allow a smooth 7-day rolling window
        start_date = (datetime.utcnow() - timedelta(days=days + 7)).date()

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

        # 2. Compute 7-day rolling average for the requested `days`
        results = []
        today = datetime.utcnow().date()

        # Output exactly `days` rows, from (today - days + 1) to today
        for i in range(days - 1, -1, -1):
            target_date = today - timedelta(days=i)

            # calculate sum over [target_date - 6 days, target_date]
            window_sum = defaultdict(int)
            for j in range(7):
                w_date = target_date - timedelta(days=j)
                for diag, count in raw_counts[w_date].items():
                    window_sum[diag] += count

            day_data = {"date": target_date.isoformat()}
            for diag in all_diseases:
                # 7-day average, rounded to 2 decimals
                avg = window_sum[diag] / 7.0
                day_data[diag] = round(avg, 2)

            results.append(day_data)

        return results

    # ─── Hotspots ─────────────────────────────────────────────────────────────

    def get_hotspots(self, disease: str = None) -> list:
        """Identify city-level locations with high case counts from real DB."""
        with SessionLocal() as db:
            query = (
                db.query(Patient.city, Patient.pincode, MedicalRecord.diagnosis)
                .join(MedicalRecord, MedicalRecord.patient_id == Patient.id)
                .filter(MedicalRecord.diagnosis != None, MedicalRecord.diagnosis != "")
            )
            if disease:
                query = query.filter(MedicalRecord.diagnosis.ilike(f"%{disease}%"))
            rows = query.all()

        counts: dict = defaultdict(int)
        for city, pincode, diagnosis in rows:
            city      = (city or "Unknown").strip()
            pincode   = (pincode or "").strip()
            diagnosis = (diagnosis or "").strip()
            if not diagnosis:
                continue
            counts[(city, pincode, diagnosis)] += 1

        results = [
            {"city": k[0], "pincode": k[1], "diagnosis": k[2], "count": v}
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
                db.query(MedicalRecord.visit_date, MedicalRecord.diagnosis)
                .filter(
                    MedicalRecord.visit_date != None,
                    MedicalRecord.diagnosis  != None,
                    MedicalRecord.diagnosis  != "",
                )
                .all()
            )

        if not rows:
            return []

        # ── Build disease → { YYYY-MM → count } ─────────────────────────────
        disease_monthly: dict = defaultdict(lambda: defaultdict(int))
        for visit_date, diagnosis in rows:
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
                db.query(MedicalRecord.visit_date, MedicalRecord.diagnosis)
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

        # ── Build disease → { bi-week-bucket → count } ──────────────────────
        # Bi-weekly bucket label: "YYYY-B{n}" where n = ISO-week // 2
        disease_biweekly: dict = defaultdict(lambda: defaultdict(int))
        for visit_date, diagnosis in rows:
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
            week_start = int(bnum) * 2
            week_label = f"{year} W{week_start}–W{week_start + 1}"

            alerts.append({
                "disease":        disease,
                "severity":       severity,
                "recent_cases":   int(recent_sum),
                "surge_month":    week_label,
                "week":           week_label,
                "date":           week_label,
                "anchor_date":    week_label,
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


    # ─── Dashboard Summary ────────────────────────────────────────────────────

    def get_dashboard_summary(self) -> dict:
        """Overall analytics summary from real PostgreSQL data."""
        with SessionLocal() as db:
            total_patients = db.query(Patient).count()
            total_records  = db.query(MedicalRecord).count()

            disease_rows = (
                db.query(MedicalRecord.diagnosis)
                .filter(MedicalRecord.diagnosis != None, MedicalRecord.diagnosis != "")
                .all()
            )
            disease_counts: dict = defaultdict(int)
            for (diag,) in disease_rows:
                if diag and diag.strip():
                    disease_counts[diag.strip()] += 1

            top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            city_rows = db.query(Patient.city).filter(Patient.city != None, Patient.city != "").all()
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
