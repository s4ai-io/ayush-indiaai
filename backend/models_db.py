"""
SQLAlchemy Models for AYUSH India AI
8-table schema covering patients, medical records, health records,
AYUSH treatments, treatment feedback, public health trends,
location nodes, and disease spread predictions.
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    abha_id = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)

    # AYUSH-specific
    prakriti = Column(String, nullable=True)      # Natural constitution
    vikriti = Column(String, nullable=True)       # Current dosha imbalance
    bmi = Column(Float, nullable=True)

    # Demographics
    occupation = Column(String, nullable=True)
    nationality = Column(String, nullable=True, default="Indian")
    insurance_provider = Column(String, nullable=True)

    # Contact Info
    mobile = Column(String, index=True, nullable=True)
    email = Column(String, nullable=True)

    # Address (Correspondence)
    city = Column(String, index=True, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, index=True, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    medical_records = relationship("MedicalRecord", back_populates="patient")
    health_records = relationship("HealthRecord", back_populates="patient")
    ayush_treatments = relationship("AyushTreatment", back_populates="patient")
    treatment_feedbacks = relationship("TreatmentFeedback", back_populates="patient")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    symptoms = Column(Text, nullable=True)
    diagnosis = Column(String, index=True, nullable=True)
    notes = Column(Text, nullable=True)
    prescription = Column(JSON, nullable=True)

    visit_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    ayush_treatments = relationship("AyushTreatment", back_populates="medical_record")
    treatment_feedbacks = relationship("TreatmentFeedback", back_populates="medical_record")


class HealthRecord(Base):
    """Maps to health_records.csv — lifestyle and severity data per visit"""
    __tablename__ = "health_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))

    visit_date = Column(Date, nullable=True)
    disease = Column(String, index=True, nullable=True)
    disease_category = Column(String, nullable=True)
    season = Column(String, nullable=True)
    severity = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)

    # Lifestyle factors
    sleep_hours = Column(Float, nullable=True)
    exercise_days_week = Column(Integer, nullable=True)
    stress_level = Column(String, nullable=True)
    diet_type = Column(String, nullable=True)
    water_intake_liters = Column(Float, nullable=True)
    meditation_minutes = Column(Integer, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="health_records")


class AyushTreatment(Base):
    """Maps to treatments.csv — herbs, yoga, diet plans with outcomes"""
    __tablename__ = "ayush_treatments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    medical_record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True)

    visit_date = Column(Date, nullable=True)
    disease = Column(String, index=True, nullable=True)
    herbs_prescribed = Column(Text, nullable=True)
    yoga_prescribed = Column(Text, nullable=True)
    diet_plan = Column(Text, nullable=True)
    treatment_duration_weeks = Column(Integer, nullable=True)
    compliance_rate = Column(Float, nullable=True)
    improvement_percentage = Column(Float, nullable=True)
    outcome = Column(String, nullable=True)
    follow_up_required = Column(String, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="ayush_treatments")
    medical_record = relationship("MedicalRecord", back_populates="ayush_treatments")


class TreatmentFeedback(Base):
    """ML feedback loop — stores AI plans and doctor feedback for retraining"""
    __tablename__ = "treatment_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medical_record_id = Column(UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)

    # AI Plans
    ai_plan = Column(JSON, nullable=False)       # { herbs: [], yoga: [], diet: [] }
    ml_context = Column(JSON, nullable=False)     # Feature Vector

    # Doctor Feedback
    doctor_rating = Column(String, nullable=True)  # positive/negative
    doctor_comments = Column(Text, nullable=True)

    is_retrained = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    medical_record = relationship("MedicalRecord", back_populates="treatment_feedbacks")
    patient = relationship("Patient", back_populates="treatment_feedbacks")


class PublicHealthTrend(Base):
    """Maps to public_health_trends.csv — aggregated epidemiological data"""
    __tablename__ = "public_health_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    month = Column(Date, nullable=True)
    season = Column(String, nullable=True)
    disease_category = Column(String, nullable=True)
    disease = Column(String, index=True, nullable=True)
    cases_reported = Column(Integer, nullable=True)
    avg_severity = Column(Float, nullable=True)
    avg_age = Column(Float, nullable=True)
    recovery_rate = Column(Float, nullable=True)
    treatment_success_rate = Column(Float, nullable=True)
    top_herb = Column(String, nullable=True)
    top_yoga = Column(String, nullable=True)


class LocationNode(Base):
    """Graph nodes for GNN-based disease spread prediction"""
    __tablename__ = "location_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pincode = Column(String, unique=True, index=True, nullable=False)
    area_name = Column(String, nullable=True)
    city = Column(String, nullable=True)
    adjacency = Column(JSON, nullable=True)  # { "110002": 0.8, "110003": 0.7 }


class DiseaseSpreadPrediction(Base):
    """Stores GNN prediction outputs"""
    __tablename__ = "disease_spread_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pincode = Column(String, index=True, nullable=False)
    disease = Column(String, nullable=True)
    predicted_cases = Column(Integer, nullable=True)
    risk_level = Column(String, nullable=True)
    day_offset = Column(Integer, nullable=True)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())
