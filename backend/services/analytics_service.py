"""
Analytics Service — CSV-backed disease trends, hotspots, and anomaly detection
"""
import csv
import os
from datetime import datetime, timedelta, date
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
MEDICAL_RECORDS_CSV = os.path.join(DATA_DIR, "medical_records.csv")


def _read_csv(filepath: str) -> list[dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_date(date_str: str):
    """Parse various date formats to a date object."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


class AnalyticsService:
    def __init__(self):
        pass

    def get_disease_trends(self, days=30):
        """Aggregate daily case counts for diseases from medical_records CSV"""
        records = _read_csv(MEDICAL_RECORDS_CSV)
        cutoff = date.today() - timedelta(days=days)

        date_map = {}
        for r in records:
            d = _parse_date(r.get("visit_date", ""))
            diagnosis = r.get("diagnosis", "").strip()
            if not d or not diagnosis or d < cutoff:
                continue
            date_str = d.isoformat()
            if date_str not in date_map:
                date_map[date_str] = {"date": date_str}
            date_map[date_str][diagnosis] = date_map[date_str].get(diagnosis, 0) + 1

        return sorted(date_map.values(), key=lambda x: x["date"])

    def get_hotspots(self, disease=None):
        """Identify locations with high case counts from CSV"""
        patients = _read_csv(PATIENTS_CSV)
        records = _read_csv(MEDICAL_RECORDS_CSV)

        patient_map = {p["id"]: p for p in patients}

        counts = defaultdict(int)
        for r in records:
            diag = r.get("diagnosis", "").strip()
            if not diag:
                continue
            if disease and diag != disease:
                continue
            p = patient_map.get(r["patient_id"], {})
            city = p.get("city", "Unknown")
            pincode = p.get("pincode", "")
            key = (city, pincode, diag)
            counts[key] += 1

        results = [
            {"city": k[0], "pincode": k[1], "diagnosis": k[2], "count": v}
            for k, v in counts.items()
        ]
        results.sort(key=lambda x: x["count"], reverse=True)
        return results

    def detect_anomalies(self):
        """Detect sudden spikes in disease cases using CSV data"""
        records = _read_csv(MEDICAL_RECORDS_CSV)

        # Parse all dates
        all_dates = set()
        disease_date_counts = defaultdict(lambda: defaultdict(int))
        for r in records:
            d = _parse_date(r.get("visit_date", ""))
            diag = r.get("diagnosis", "").strip()
            if not d or not diag:
                continue
            all_dates.add(d)
            disease_date_counts[diag][d] += 1

        if not all_dates:
            return []

        latest_date = max(all_dates)

        alerts = []
        for disease, date_counts in disease_date_counts.items():
            today_count = date_counts.get(latest_date, 0)
            if today_count == 0:
                continue

            baseline = []
            for i in range(1, 8):
                d = latest_date - timedelta(days=i)
                if d in date_counts:
                    baseline.append(date_counts[d])

            avg = sum(baseline) / len(baseline) if baseline else 0

            if today_count > max(5, avg * 1.5) or today_count > 15:
                alerts.append({
                    "disease": disease,
                    "severity": "High",
                    "message": f"Potential outbreak of {disease} detected. Cases today ({today_count}) remain critically high (Weekly Avg: {avg:.1f}).",
                    "date": latest_date.isoformat(),
                })

        return alerts

    def get_dashboard_summary(self):
        """Get overall analytics dashboard summary from CSV"""
        patients = _read_csv(PATIENTS_CSV)
        records = _read_csv(MEDICAL_RECORDS_CSV)

        total_patients = len(patients)
        total_records = len(records)

        # Top diseases
        disease_counts = defaultdict(int)
        for r in records:
            diag = r.get("diagnosis", "").strip()
            if diag:
                disease_counts[diag] += 1

        top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Top cities
        city_counts = defaultdict(int)
        for p in patients:
            city = p.get("city", "").strip()
            if city:
                city_counts[city] += 1

        top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_patients": total_patients,
            "total_medical_records": total_records,
            "total_health_records": 0,
            "top_diseases": [{"disease": d, "count": c} for d, c in top_diseases],
            "top_cities": [{"city": c, "count": n} for c, n in top_cities],
        }


# Singleton instance
analytics_service = AnalyticsService()
