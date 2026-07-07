from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, DateTime, DateTime
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ayush_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, index=True)
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    gender = Column(String, default="")
    age = Column(Integer, nullable=True)
    marital_status = Column(String, default="")
    mobile = Column(String, default="")
    address = Column(String, default="")
    city = Column(String, default="")
    state = Column(String, default="")
    pincode = Column(String, default="")
    blood_group = Column(String, default="")
    occupation = Column(String, default="")
    id_type = Column(String, default="")
    id_number = Column(String, default="")
    diagnosis_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    visit_date = Column(DateTime, index=True)
    diagnosis = Column(String, default="", index=True)
    symptoms = Column(Text, default="")
    prakriti = Column(String, default="")
    vikriti = Column(String, default="")
    severity = Column(String, default="")
    comorbidities = Column(String, default="")
    notes = Column(Text, default="")
    prescription = Column(Text, default="")

    # Follow-up linkage — points at the MedicalRecord of the prior visit for
    # the same condition, so visits for one disease can be chained over time.
    parent_visit_id = Column(String, nullable=True, index=True)

    # Basic health parameters (vitals) captured at this visit.
    bpm = Column(Integer, nullable=True)               # Heart rate (beats/min)
    sugar_level = Column(Float, nullable=True)          # Blood glucose (mg/dL)
    spo2 = Column(Integer, nullable=True)               # Blood oxygen saturation (%)
    temperature = Column(Float, nullable=True)          # Body temperature (°C)
    systolic_bp = Column(Integer, nullable=True)        # Systolic BP (mmHg)
    diastolic_bp = Column(Integer, nullable=True)       # Diastolic BP (mmHg)

class AyushTreatment(Base):
    __tablename__ = "ayush_treatments"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    medical_record_id = Column(String, index=True)
    visit_date = Column(DateTime)
    disease = Column(String, default="")
    herbs_prescribed = Column(Text, default="")
    yoga_prescribed = Column(Text, default="")
    diet_plan = Column(Text, default="")
    treatment_duration_weeks = Column(String, default="")
    improvement_percentage = Column(String, default="")
    outcome = Column(String, default="")

class TreatmentFeedback(Base):
    __tablename__ = "treatment_feedbacks"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    medical_record_id = Column(String, index=True)
    ai_plan = Column(Text, default="")
    ml_context = Column(Text, default="")
    doctor_rating = Column(String, default="")
    doctor_comments = Column(Text, default="")
    is_retrained = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    original_ai_plan = Column(Text, nullable=True)
    final_plan = Column(Text, nullable=True)
    added_herbs = Column(Text, nullable=True)
    removed_herbs = Column(Text, nullable=True)
    demo_session = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, default="")
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'receptionist' | 'doctor' | 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClinicalOutcomeScore(Base):
    __tablename__ = "clinical_outcome_scores"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    medical_record_id = Column(String, index=True)
    disease = Column(String, default="")
    target_vital = Column(String, default="")
    baseline_value = Column(Float, nullable=True)
    followup_value = Column(Float, nullable=True)
    percentage_change = Column(Float, nullable=True)
    calculated_reward = Column(Float, default=0.0)
    is_retrained = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor_reported_outcome = Column(String, nullable=True)  # "improved" | "no_change" | "worsened"

def init_db():
    Base.metadata.create_all(bind=engine)
