"""
Database Service — CRUD operations for all 8 tables
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from models_db import (
    Patient, MedicalRecord, HealthRecord, AyushTreatment,
    TreatmentFeedback, PublicHealthTrend, LocationNode, DiseaseSpreadPrediction
)
from database import SessionLocal
import uuid
from datetime import datetime, date
import json


class DBService:
    def __init__(self):
        self.db = SessionLocal()

    def get_db(self):
        return self.db

    # ─── Patient Operations ──────────────────────────────────────────

    def create_patient(self, basic_info: dict, contact_info: dict, other_info: dict = None):
        """Create or return existing patient (de-dup by Mobile or ID)"""
        # 1. Try deduplication by Mobile
        mobile = contact_info.get("mobileNumber")
        if mobile:
            existing = self.db.query(Patient).filter(Patient.mobile == mobile).first()
            if existing:
                return existing

        # 2. Try deduplication by ID Number if provided
        id_number = (other_info or {}).get("idNumber")
        if id_number:
            existing = self.db.query(Patient).filter(Patient.id_number == id_number).first()
            if existing:
                return existing

        new_patient = Patient(
            id=uuid.uuid4(),
            first_name=basic_info.get("firstName"),
            last_name=basic_info.get("lastName"),
            gender=basic_info.get("gender"),
            age=basic_info.get("age"),
            marital_status=basic_info.get("maritalStatus"),
            
            mobile=mobile,
            address=contact_info.get("address"),
            city=contact_info.get("city"),
            state=contact_info.get("state"),
            pincode=contact_info.get("pincode"),
            
            blood_group=(other_info or {}).get("bloodGroup"),
            occupation=(other_info or {}).get("occupation"),
            id_type=(other_info or {}).get("idType"),
            id_number=(other_info or {}).get("idNumber"),
        )
        self.db.add(new_patient)
        self.db.commit()
        self.db.refresh(new_patient)
        return new_patient

    def get_patient_by_id(self, patient_id):
        from sqlalchemy.orm import joinedload
        return self.db.query(Patient).options(joinedload(Patient.medical_records)).filter(Patient.id == patient_id).first()

    def get_patient_by_mobile(self, mobile: str):
        return self.db.query(Patient).filter(Patient.mobile == mobile).first()

    def get_patient_by_abha(self, abha_id: str):
        return self.db.query(Patient).filter(Patient.abha_id == abha_id).first()

    def get_all_patients(self, limit: int = 100):
        return self.db.query(Patient).order_by(Patient.created_at.desc()).limit(limit).all()

    # ─── Medical Record Operations ───────────────────────────────────

    def create_medical_record(self, patient_id: uuid.UUID, symptoms: str,
                               diagnosis: str, notes: str, prescription: list,
                               visit_date: datetime = None):
        new_record = MedicalRecord(
            id=uuid.uuid4(),
            patient_id=patient_id,
            symptoms=symptoms,
            diagnosis=diagnosis,
            notes=notes,
            prescription=prescription,
            visit_date=visit_date or datetime.utcnow(),
        )
        self.db.add(new_record)
        self.db.commit()
        self.db.refresh(new_record)
        return new_record

    def get_patient_history(self, patient_id: uuid.UUID):
        return (
            self.db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.visit_date.desc())
            .all()
        )

    # ─── Health Record Operations ────────────────────────────────────

    def create_health_record(self, data: dict):
        record = HealthRecord(
            id=uuid.uuid4(),
            patient_id=data.get("patient_id"),
            visit_date=data.get("visit_date"),
            disease=data.get("disease"),
            disease_category=data.get("disease_category"),
            season=data.get("season"),
            severity=data.get("severity"),
            sleep_hours=data.get("sleep_hours"),
            exercise_days_week=data.get("exercise_days_week"),
            stress_level=data.get("stress_level"),
            diet_type=data.get("diet_type"),
            water_intake_liters=data.get("water_intake_liters"),
            meditation_minutes=data.get("meditation_minutes"),
        )
        self.db.add(record)
        return record  # caller commits in bulk

    def get_health_records_by_patient(self, patient_id: uuid.UUID):
        return (
            self.db.query(HealthRecord)
            .filter(HealthRecord.patient_id == patient_id)
            .order_by(HealthRecord.visit_date.desc())
            .all()
        )

    # ─── AYUSH Treatment Operations ──────────────────────────────────

    def create_ayush_treatment(self, data: dict):
        treatment = AyushTreatment(
            id=uuid.uuid4(),
            patient_id=data.get("patient_id"),
            medical_record_id=data.get("medical_record_id"),
            visit_date=data.get("visit_date"),
            disease=data.get("disease"),
            herbs_prescribed=data.get("herbs_prescribed"),
            yoga_prescribed=data.get("yoga_prescribed"),
            diet_plan=data.get("diet_plan"),
            treatment_duration_weeks=data.get("treatment_duration_weeks"),
            compliance_rate=data.get("compliance_rate"),
            improvement_percentage=data.get("improvement_percentage"),
            outcome=data.get("outcome"),
        )
        self.db.add(treatment)
        return treatment  # caller commits in bulk

    def get_treatments_by_patient(self, patient_id: uuid.UUID):
        return (
            self.db.query(AyushTreatment)
            .filter(AyushTreatment.patient_id == patient_id)
            .order_by(AyushTreatment.visit_date.desc())
            .all()
        )

    # ─── Treatment Feedback (ML) Operations ──────────────────────────

    def save_treatment_feedback(self, feedback_data: dict):
        """Saves ML feedback. Links to patient if possible."""
        patient_id = None
        try:
            patient_uuid = uuid.UUID(feedback_data.get("patientId"))
            patient = self.get_patient_by_id(patient_uuid)
            if patient:
                patient_id = patient.id
        except Exception:
            pass

        new_feedback = TreatmentFeedback(
            id=uuid.uuid4(),
            patient_id=patient_id,
            ai_plan=feedback_data.get("treatmentPlan", {}),
            ml_context=feedback_data.get("context", {}),
            doctor_rating=feedback_data.get("rating"),
            doctor_comments=feedback_data.get("feedback"),
            is_retrained=False,
        )
        self.db.add(new_feedback)
        self.db.commit()
        return new_feedback

    # ─── Public Health Trend Operations ──────────────────────────────

    def create_public_health_trend(self, data: dict):
        trend = PublicHealthTrend(
            id=uuid.uuid4(),
            month=data.get("month"),
            season=data.get("season"),
            disease_category=data.get("disease_category"),
            disease=data.get("disease"),
            cases_reported=data.get("cases_reported"),
            avg_severity=data.get("avg_severity"),
            avg_age=data.get("avg_age"),
            recovery_rate=data.get("recovery_rate"),
            treatment_success_rate=data.get("treatment_success_rate"),
            top_herb=data.get("top_herb"),
            top_yoga=data.get("top_yoga"),
        )
        self.db.add(trend)
        return trend  # caller commits in bulk

    def get_trends_by_disease(self, disease: str):
        return (
            self.db.query(PublicHealthTrend)
            .filter(PublicHealthTrend.disease == disease)
            .order_by(PublicHealthTrend.month.desc())
            .all()
        )

    # ─── Location Node Operations ────────────────────────────────────

    def create_location_node(self, pincode: str, area_name: str = None,
                              city: str = None, adjacency: dict = None):
        node = LocationNode(
            id=uuid.uuid4(),
            pincode=pincode,
            area_name=area_name,
            city=city,
            adjacency=adjacency or {},
        )
        self.db.add(node)
        return node

    def get_all_location_nodes(self):
        return self.db.query(LocationNode).all()

    # ─── Analytics Queries ───────────────────────────────────────────

    def get_disease_trends_from_db(self, days: int = 30):
        """Aggregate daily case counts from medical_records"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = (
            self.db.query(
                func.date(MedicalRecord.visit_date).label("date"),
                MedicalRecord.diagnosis,
                func.count().label("count"),
            )
            .filter(MedicalRecord.visit_date >= cutoff)
            .group_by(func.date(MedicalRecord.visit_date), MedicalRecord.diagnosis)
            .order_by(func.date(MedicalRecord.visit_date))
            .all()
        )
        return [{"date": str(r.date), "diagnosis": r.diagnosis, "count": r.count} for r in results]

    def get_hotspots_from_db(self, disease: str = None):
        """Get location-based case counts"""
        query = (
            self.db.query(
                Patient.city,
                Patient.pincode,
                MedicalRecord.diagnosis,
                func.count().label("count"),
            )
            .join(MedicalRecord, Patient.id == MedicalRecord.patient_id)
            .group_by(Patient.city, Patient.pincode, MedicalRecord.diagnosis)
        )
        if disease:
            query = query.filter(MedicalRecord.diagnosis == disease)
        results = query.order_by(func.count().desc()).all()
        return [{"city": r.city, "pincode": r.pincode, "diagnosis": r.diagnosis, "count": r.count} for r in results]

    # ─── Bulk commit helper ──────────────────────────────────────────

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()


db_service = DBService()
