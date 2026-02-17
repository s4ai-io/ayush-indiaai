"""
Analytics Service — DB-backed disease trends, hotspots, and anomaly detection
"""
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import SessionLocal
from models_db import Patient, MedicalRecord, HealthRecord


class AnalyticsService:
    def __init__(self):
        pass

    def _get_db(self):
        return SessionLocal()

    def get_disease_trends(self, days=30):
        """Aggregate daily case counts for diseases from medical_records table"""
        db = self._get_db()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            results = (
                db.query(
                    func.date(MedicalRecord.visit_date).label("date"),
                    MedicalRecord.diagnosis,
                    func.count().label("count"),
                )
                .filter(MedicalRecord.visit_date >= cutoff)
                .filter(MedicalRecord.diagnosis.isnot(None))
                .group_by(func.date(MedicalRecord.visit_date), MedicalRecord.diagnosis)
                .order_by(func.date(MedicalRecord.visit_date))
                .all()
            )

            # Pivot into frontend format: [{date: '2026-02-01', Dengue: 5, Fever: 2}, ...]
            date_map = {}
            for r in results:
                date_str = str(r.date)
                if date_str not in date_map:
                    date_map[date_str] = {"date": date_str}
                date_map[date_str][r.diagnosis] = r.count

            return list(date_map.values())
        finally:
            db.close()

    def get_hotspots(self, disease=None):
        """Identify locations with high case counts from DB"""
        db = self._get_db()
        try:
            query = (
                db.query(
                    Patient.city,
                    Patient.pincode,
                    MedicalRecord.diagnosis,
                    func.count().label("count"),
                )
                .join(MedicalRecord, Patient.id == MedicalRecord.patient_id)
                .filter(Patient.city.isnot(None))
                .filter(MedicalRecord.diagnosis.isnot(None))
                .group_by(Patient.city, Patient.pincode, MedicalRecord.diagnosis)
            )

            if disease:
                query = query.filter(MedicalRecord.diagnosis == disease)

            results = query.order_by(func.count().desc()).all()

            return [
                {
                    "city": r.city,
                    "pincode": r.pincode,
                    "diagnosis": r.diagnosis,
                    "count": r.count,
                }
                for r in results
            ]
        finally:
            db.close()

    def detect_anomalies(self):
        """Detect sudden spikes in disease cases using DB data"""
        db = self._get_db()
        try:
            # Get the latest date in records
            latest_date_result = db.query(
                func.max(func.date(MedicalRecord.visit_date))
            ).scalar()

            if not latest_date_result:
                return []

            latest_date = latest_date_result

            # Get daily counts per disease for the last 8 days (1 day current + 7 baseline)
            start_date = latest_date - timedelta(days=8)

            daily_counts = (
                db.query(
                    func.date(MedicalRecord.visit_date).label("date"),
                    MedicalRecord.diagnosis,
                    func.count().label("count"),
                )
                .filter(func.date(MedicalRecord.visit_date) >= start_date)
                .filter(MedicalRecord.diagnosis.isnot(None))
                .group_by(func.date(MedicalRecord.visit_date), MedicalRecord.diagnosis)
                .all()
            )

            if not daily_counts:
                return []

            # Structure: {disease: {date: count}}
            disease_data = {}
            for r in daily_counts:
                d = r.diagnosis
                if d not in disease_data:
                    disease_data[d] = {}
                disease_data[d][r.date] = r.count

            alerts = []
            for disease, date_counts in disease_data.items():
                today_count = date_counts.get(latest_date, 0)
                if today_count == 0:
                    continue

                # Baseline: previous 7 days
                baseline_counts = []
                for i in range(1, 8):
                    d = latest_date - timedelta(days=i)
                    if d in date_counts:
                        baseline_counts.append(date_counts[d])

                avg_count = sum(baseline_counts) / len(baseline_counts) if baseline_counts else 0

                # Rule: spike if > 1.5x baseline (min 5) or absolute > 15
                if today_count > max(5, avg_count * 1.5) or today_count > 15:
                    alerts.append({
                        "disease": disease,
                        "severity": "High",
                        "message": f"Potential outbreak of {disease} detected. Cases today ({today_count}) remain critically high (Weekly Avg: {avg_count:.1f}).",
                        "date": latest_date.strftime("%Y-%m-%d") if hasattr(latest_date, 'strftime') else str(latest_date),
                    })

            return alerts
        finally:
            db.close()

    def get_dashboard_summary(self):
        """Get overall analytics dashboard summary from DB"""
        db = self._get_db()
        try:
            total_patients = db.query(func.count(Patient.id)).scalar() or 0
            total_records = db.query(func.count(MedicalRecord.id)).scalar() or 0
            total_health_records = db.query(func.count(HealthRecord.id)).scalar() or 0

            # Top diseases
            top_diseases = (
                db.query(
                    MedicalRecord.diagnosis,
                    func.count().label("count"),
                )
                .filter(MedicalRecord.diagnosis.isnot(None))
                .group_by(MedicalRecord.diagnosis)
                .order_by(func.count().desc())
                .limit(5)
                .all()
            )

            # Top cities by patients
            top_cities = (
                db.query(
                    Patient.city,
                    func.count().label("count"),
                )
                .filter(Patient.city.isnot(None))
                .group_by(Patient.city)
                .order_by(func.count().desc())
                .limit(5)
                .all()
            )

            return {
                "total_patients": total_patients,
                "total_medical_records": total_records,
                "total_health_records": total_health_records,
                "top_diseases": [{"disease": r.diagnosis, "count": r.count} for r in top_diseases],
                "top_cities": [{"city": r.city, "count": r.count} for r in top_cities],
            }
        finally:
            db.close()


# Singleton instance
analytics_service = AnalyticsService()
