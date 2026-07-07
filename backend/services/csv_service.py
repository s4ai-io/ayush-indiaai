"""
Database service — replaces the CSV-based csv_service.
Reads/writes patients, medical_records, ayush_treatments, treatment_feedback via PostgreSQL.
"""
import os
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from models import SessionLocal, Patient, MedicalRecord, AyushTreatment, TreatmentFeedback, ClinicalOutcomeScore


# ─── Vital target helpers ────────────────────────────────────────────────────

_VITAL_MAP = {
    "diabetes": ("HbA1c (%)", False),      # False = lower is better
    "madhumeha": ("HbA1c (%)", False),
    "asthma": ("PEFR (L/min)", True),      # True = higher is better
    "tamaka": ("PEFR (L/min)", True),
    "shwasa": ("PEFR (L/min)", True),
    "hypertension": ("Systolic BP (mmHg)", False),
    "raktachapa": ("Systolic BP (mmHg)", False),
    "obesity": ("BMI (kg/m²)", False),
    "sthoulya": ("BMI (kg/m²)", False),
}


def _get_target_vital(disease: str):
    d = disease.lower()
    for key, val in _VITAL_MAP.items():
        if key in d:
            return val[0]
    return "Symptom Severity (1-10)"

class DBService:
    """PostgreSQL-backed data service."""

    # ─── Patient Operations ──────────────────────────────────────

    def create_patient(self, basic_info: dict, contact_info: dict, other_info: dict):
        """Create a new patient."""
        patient_id = str(uuid.uuid4())
        
        age_str = basic_info.get("age", "")
        age_val = None
        if str(age_str).strip():
            try:
                age_val = int(age_str)
            except ValueError:
                pass

        p = Patient(
            id=patient_id,
            first_name=basic_info.get("firstName", ""),
            last_name=basic_info.get("lastName", ""),
            gender=basic_info.get("gender", ""),
            age=age_val,
            marital_status=basic_info.get("maritalStatus", ""),
            mobile=contact_info.get("mobileNumber", ""),
            address=contact_info.get("address", ""),
            city=contact_info.get("city", ""),
            state=contact_info.get("state", ""),
            pincode=contact_info.get("pincode", ""),
            blood_group=(other_info or {}).get("bloodGroup", ""),
            occupation=(other_info or {}).get("occupation", ""),
            id_type=(other_info or {}).get("idType", ""),
            id_number=(other_info or {}).get("idNumber", ""),
            diagnosis_done=False
        )

        with SessionLocal() as db:
            db.add(p)
            db.commit()
            db.refresh(p)
            print(f"✓ Patient created via Postgres: {p.first_name} {p.last_name} ({patient_id})")
            # Convert to dict object for original compatibility
            return _DictObj(self._row_to_dict(p))

    def get_patient_by_id(self, patient_id: str):
        with SessionLocal() as db:
            p = db.query(Patient).filter(Patient.id == str(patient_id)).first()
            if p:
                return _DictObj(self._row_to_dict(p))
            return None

    def get_all_patients(self, limit: int = 5000):
        with SessionLocal() as db:
            patients = db.query(Patient).order_by(desc(Patient.created_at)).limit(limit).all()
            return [_DictObj(self._row_to_dict(p)) for p in patients]

    def search_patients(self, query: str, limit: int = 20):
        with SessionLocal() as db:
            q = query.lower()
            patients = db.query(Patient).filter(
                or_(
                    Patient.first_name.ilike(f"%{q}%"),
                    Patient.last_name.ilike(f"%{q}%"),
                    Patient.mobile.ilike(f"%{q}%")
                )
            ).limit(limit).all()
            return [_DictObj(self._row_to_dict(p)) for p in patients]

    # ─── Prescription / Diagnosis ────────────────────────────────

    def create_consultation(self, patient_id: str, assessment: dict) -> str:
        record_id = str(uuid.uuid4())
        parent_visit_id = assessment.get("parent_visit_id") or None

        # Follow-up: pre-populate the new visit from the condition being followed up,
        # so the doctor doesn't retype the same clinical picture each visit.
        diagnosis = assessment.get("diagnosis", "")
        symptoms = assessment.get("symptoms", "")
        prakriti = assessment.get("prakriti", "")
        vikriti = assessment.get("vikriti", "")
        comorbidities = assessment.get("comorbidities", "")
        notes = assessment.get("notes", "")

        if parent_visit_id:
            with SessionLocal() as db:
                parent = db.query(MedicalRecord).filter(MedicalRecord.id == parent_visit_id).first()
                if parent:
                    diagnosis = diagnosis or parent.diagnosis or ""
                    symptoms = symptoms or parent.symptoms or ""
                    prakriti = prakriti or parent.prakriti or ""
                    vikriti = vikriti or parent.vikriti or ""
                    comorbidities = comorbidities or parent.comorbidities or ""
                    notes = notes or parent.notes or ""

        m = MedicalRecord(
            id=record_id,
            patient_id=patient_id,
            visit_date=datetime.utcnow(),
            diagnosis=diagnosis,
            symptoms=symptoms,
            prakriti=prakriti,
            vikriti=vikriti,
            severity=str(assessment.get("severity", 5)),
            comorbidities=comorbidities,
            notes=notes,
            prescription="{}",
            parent_visit_id=parent_visit_id,
        )

        with SessionLocal() as db:
            db.add(m)
            db.commit()
            print(f"✓ Consultation saved (Postgres): patient={patient_id}, visit={record_id}")
            return record_id

    def save_prescription(self, data: dict) -> dict:
        patient_id = data.get("patientId")
        record_id = data.get("visitId")

        patient = self.get_patient_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        treatment_plan = data.get("treatmentPlan") or {}
        original_ai_plan = data.get("original_ai_plan") or {}
        disease = data.get("disease", "")
        symptoms = data.get("symptoms", "")
        doctor_notes = data.get("doctorNotes", "")

        # Diff every plan category (herbs, yoga, diet, lifestyle) between the original
        # AI plan and the final (possibly doctor-edited) plan, as canonical action keys
        from services.rl_service import rl_service
        added_herbs, removed_herbs = rl_service.compute_plan_diff(original_ai_plan, treatment_plan)
        
        treatment_id = str(uuid.uuid4())
        feedback_id = str(uuid.uuid4())

        prescription_json = {
            "ai_plan": treatment_plan,
            "doctor_notes": data.get("doctorPrescription", ""),
        }

        with SessionLocal() as db:
            # 1. Update or Create Medical Record
            m = None
            if record_id:
                m = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
                if m:
                    m.prescription = json.dumps(prescription_json)
                    if doctor_notes:
                        m.notes = (m.notes or "") + f"\n\n[Treatment Phase]: {doctor_notes}"
                    if disease:
                        m.diagnosis = disease
                    
                    if symptoms:
                        m.symptoms = symptoms
                    if data.get("prakriti"):
                        m.prakriti = data.get("prakriti")
                    if data.get("vikriti"):
                        m.vikriti = data.get("vikriti")
                    if data.get("severity") is not None:
                        m.severity = str(data.get("severity"))
                    if data.get("comorbidities"):
                        m.comorbidities = data.get("comorbidities")
                    self._apply_vitals(m, data)

                    disease = disease or m.diagnosis

            if not m:
                record_id = record_id or str(uuid.uuid4())
                m = MedicalRecord(
                    id=record_id,
                    patient_id=patient_id,
                    visit_date=datetime.utcnow(),
                    diagnosis=disease or (treatment_plan.get("source_disease") or "Unknown"),
                    symptoms=symptoms,
                    prakriti=data.get("prakriti", ""),
                    vikriti=data.get("vikriti", ""),
                    severity=str(data.get("severity", 5)),
                    comorbidities="",
                    notes=doctor_notes,
                    prescription=json.dumps(prescription_json),
                )
                self._apply_vitals(m, data)
                db.add(m)

            # 2. AYUSH Treatment
            herbs_list = treatment_plan.get("herbs", [])
            yoga_list = treatment_plan.get("yoga", [])
            diet_list = treatment_plan.get("diet", [])

            herbs_text = ", ".join(
                h.get("name", "") if isinstance(h, dict) else str(h) for h in herbs_list
            )
            yoga_text = ", ".join(
                y.get("practice", "") if isinstance(y, dict) else str(y) for y in yoga_list
            )
            diet_text = "; ".join(diet_list) if diet_list else ""

            a = AyushTreatment(
                id=treatment_id,
                patient_id=patient_id,
                medical_record_id=record_id,
                visit_date=datetime.utcnow(),
                disease=disease,
                herbs_prescribed=herbs_text,
                yoga_prescribed=yoga_text,
                diet_plan=diet_text,
                treatment_duration_weeks=str(treatment_plan.get("recommended_duration_weeks", "")),
                improvement_percentage=str(treatment_plan.get("predicted_improvement", "")),
                outcome="Prescribed"
            )
            db.add(a)

            # 3. Treatment Feedback
            ml_context = {
                "disease": disease,
                "symptoms": symptoms,
                "severity": data.get("severity"),
                "prakriti": data.get("prakriti"),
                "vikriti": data.get("vikriti"),
                "namc_code": treatment_plan.get("namc_code") or original_ai_plan.get("namc_code"),
                "match_method": treatment_plan.get("match_method"),
                "match_confidence": treatment_plan.get("match_confidence"),
                "cluster_id": data.get("cluster_id") or treatment_plan.get("cluster_id")
            }

            f = TreatmentFeedback(
                id=feedback_id,
                patient_id=patient_id,
                medical_record_id=record_id,
                ai_plan=json.dumps(treatment_plan),
                ml_context=json.dumps(ml_context),
                doctor_rating=str(data.get("rating", "")),
                doctor_comments=str(data.get("feedback", "")),
                is_retrained=False,
                original_ai_plan=json.dumps(original_ai_plan),
                final_plan=json.dumps(treatment_plan),
                added_herbs=json.dumps(added_herbs),
                removed_herbs=json.dumps(removed_herbs),
                demo_session=bool(data.get("demo_session", False)),
            )
            db.add(f)

            # Create a pending ClinicalOutcomeScore row for this visit
            pending_outcome = ClinicalOutcomeScore(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                medical_record_id=record_id,
                disease=disease,
                target_vital=_get_target_vital(disease),
                baseline_value=None,
                followup_value=None,
                percentage_change=None,
                calculated_reward=0.0,
                is_retrained=False,
            )
            db.add(pending_outcome)

            # Mark patient as diagnosed
            p = db.query(Patient).filter(Patient.id == patient_id).first()
            if p:
                p.diagnosis_done = True

            db.commit()

        print(f"✓ Treatment saved (Postgres): patient={patient_id}, diagnosis={disease}")

        return {
            "medical_record_id": record_id,
            "ayush_treatment_id": treatment_id,
            "treatment_feedback_id": feedback_id,
            "feedback_id": feedback_id,
        }

    @staticmethod
    def _apply_vitals(record: MedicalRecord, data: dict) -> None:
        """Copy any provided vitals fields onto a MedicalRecord row (leaves existing values untouched if omitted)."""
        for field in ("bpm", "sugar_level", "spo2", "temperature", "systolic_bp", "diastolic_bp"):
            if data.get(field) is not None:
                setattr(record, field, data.get(field))

    def save_treatment_feedback(self, feedback_data: dict):
        f = TreatmentFeedback(
            id=str(uuid.uuid4()),
            patient_id=feedback_data.get("patientId", ""),
            medical_record_id="",
            ai_plan=json.dumps(feedback_data.get("finalPlan", {})),
            ml_context=json.dumps({}),
            doctor_rating=feedback_data.get("rating", ""),
            doctor_comments=feedback_data.get("comments", ""),
            is_retrained=False
        )

        with SessionLocal() as db:
            db.add(f)
            db.commit()
            db.refresh(f)

        print(f"✓ Feedback saved (Postgres)")
        return self._row_to_dict(f)

    # ─── Diagnosis Queries ───────────────────────────────────────

    def get_medical_record_by_id(self, record_id: str):
        with SessionLocal() as db:
            m = db.query(MedicalRecord).filter(MedicalRecord.id == str(record_id)).first()
            if m:
                return self._row_to_dict(m)
            return None

    def get_patient_diagnoses(self, patient_id_str: str) -> list:
        with SessionLocal() as db:
            records = db.query(MedicalRecord).filter(
                MedicalRecord.patient_id == patient_id_str
            ).order_by(desc(MedicalRecord.visit_date)).all()
            
            treatments = db.query(AyushTreatment).filter(
                AyushTreatment.patient_id == patient_id_str
            ).all()

            treatments_map = {t.medical_record_id: t for t in treatments}

            result = []
            for r in records:
                ayush = treatments_map.get(r.id)
                result.append({
                    "id": r.id,
                    "diagnosis": r.diagnosis or "",
                    "symptoms": r.symptoms or "",
                    "notes": r.notes or "",
                    "prescription": _safe_json_parse(r.prescription),
                    "visit_date": r.visit_date.isoformat() if r.visit_date else None,
                    "herbs": ayush.herbs_prescribed if ayush else None,
                    "yoga": ayush.yoga_prescribed if ayush else None,
                    "diet": ayush.diet_plan if ayush else None,
                    "duration_weeks": _safe_int(ayush.treatment_duration_weeks) if ayush else None,
                    "improvement": _safe_float(ayush.improvement_percentage) if ayush else None,
                    "outcome": ayush.outcome if ayush else None,
                    "parent_visit_id": r.parent_visit_id,
                    "bpm": r.bpm,
                    "sugar_level": r.sugar_level,
                    "spo2": r.spo2,
                    "temperature": r.temperature,
                    "systolic_bp": r.systolic_bp,
                    "diastolic_bp": r.diastolic_bp,
                })
            return result

    # A visit counts as "awaiting a prescription" regardless of the patient's
    # overall diagnosis_done flag — that flag is patient-level and stays True
    # forever after the first diagnosis, which used to hide every follow-up
    # visit (and any second pending visit) from the doctor's queue entirely.
    _EMPTY_PRESCRIPTION = or_(
        MedicalRecord.prescription.is_(None),
        MedicalRecord.prescription == "",
        MedicalRecord.prescription == "{}",
    )

    def _visit_queue(self, pending: bool, limit: int = 200) -> list:
        with SessionLocal() as db:
            condition = self._EMPTY_PRESCRIPTION if pending else and_(
                MedicalRecord.prescription.isnot(None),
                MedicalRecord.prescription != "",
                MedicalRecord.prescription != "{}",
            )
            records = db.query(MedicalRecord, Patient).join(
                Patient, MedicalRecord.patient_id == Patient.id
            ).filter(condition).order_by(desc(MedicalRecord.visit_date)).limit(limit).all()

            result = []
            for r, p in records:
                result.append({
                    "record_id": r.id,
                    "patient_id": r.patient_id,
                    "patient_name": f"{p.first_name or ''} {p.last_name or ''}".strip(),
                    "patient_age": p.age,
                    "patient_gender": p.gender or "",
                    "patient_city": p.city or "",
                    "patient_mobile": p.mobile or "",
                    "blood_group": p.blood_group or "",
                    "occupation": p.occupation or "",
                    "diagnosis": r.diagnosis or "",
                    "symptoms": r.symptoms or "",
                    "visit_date": r.visit_date.isoformat() if r.visit_date else None,
                    "parent_visit_id": r.parent_visit_id,
                    "is_followup": bool(r.parent_visit_id),
                })
            return result

    def get_completed_diagnoses_summary(self, limit: int = 200) -> list:
        return self._visit_queue(pending=False, limit=limit)

    def get_pending_visit_queue(self, limit: int = 200) -> list:
        """Doctor's Pending Queue: visits awaiting a prescription (first-time
        or follow-up) PLUS patients who have never had any visit started yet.
        """
        with SessionLocal() as db:
            pending_visits = db.query(MedicalRecord, Patient).join(
                Patient, MedicalRecord.patient_id == Patient.id
            ).filter(self._EMPTY_PRESCRIPTION).order_by(desc(MedicalRecord.visit_date)).all()

            result = []
            for r, p in pending_visits:
                result.append({
                    "record_id": r.id,
                    "patient_id": r.patient_id,
                    "patient_name": f"{p.first_name or ''} {p.last_name or ''}".strip(),
                    "patient_age": p.age,
                    "patient_gender": p.gender or "",
                    "patient_city": p.city or "",
                    "patient_mobile": p.mobile or "",
                    "blood_group": p.blood_group or "",
                    "occupation": p.occupation or "",
                    "diagnosis": r.diagnosis or "",
                    "visit_date": r.visit_date.isoformat() if r.visit_date else None,
                    "parent_visit_id": r.parent_visit_id,
                    "is_followup": bool(r.parent_visit_id),
                })

            never_consulted = db.query(Patient).filter(
                Patient.id.notin_(db.query(MedicalRecord.patient_id).distinct())
            ).all()
            for p in never_consulted:
                result.append({
                    "record_id": None,
                    "patient_id": p.id,
                    "patient_name": f"{p.first_name or ''} {p.last_name or ''}".strip(),
                    "patient_age": p.age,
                    "patient_gender": p.gender or "",
                    "patient_city": p.city or "",
                    "patient_mobile": p.mobile or "",
                    "blood_group": p.blood_group or "",
                    "occupation": p.occupation or "",
                    "diagnosis": "",
                    "visit_date": p.created_at.isoformat() if p.created_at else None,
                    "parent_visit_id": None,
                    "is_followup": False,
                })

            result.sort(key=lambda x: x["visit_date"] or "", reverse=True)
            return result[:limit]

    def get_patient_conditions(self, patient_id_str: str) -> list:
        """Distinct past diagnoses for a patient — diagnosis name + visit id/date
        only, deliberately no symptoms/notes/prescription/vitals. Safe for any
        role (receptionist included) to power the New-vs-Follow-up picker
        without exposing full clinical history.
        """
        with SessionLocal() as db:
            records = db.query(MedicalRecord).filter(
                MedicalRecord.patient_id == patient_id_str
            ).order_by(desc(MedicalRecord.visit_date)).all()

            seen = set()
            result = []
            for r in records:
                name = (r.diagnosis or "").strip()
                key = name.lower()
                if not name or key in seen:
                    continue
                seen.add(key)
                result.append({
                    "visit_id": r.id,
                    "diagnosis": name,
                    "visit_date": r.visit_date.isoformat() if r.visit_date else None,
                })
            return result

    def _row_to_dict(self, row):
        d = {}
        for column in row.__table__.columns:
            val = getattr(row, column.name)
            if isinstance(val, datetime):
                # map datetime to standard string format expected by UI
                d[column.name] = val.isoformat()
            else:
                d[column.name] = val
        return d


class _DictObj:
    """Wrapper so dict values are accessible as attributes (patient.id, patient.mobile)."""
    def __init__(self, d: dict):
        self.__dict__.update(d)
        if hasattr(self, 'diagnosis_done') and isinstance(self.diagnosis_done, str):
            self.diagnosis_done = self.diagnosis_done == "True"
        if hasattr(self, 'age') and self.age:
            try:
                self.age = int(float(self.age))
            except (ValueError, TypeError):
                pass


def _safe_json_parse(val):
    if not val:
        return None
    try:
        if isinstance(val, dict):
             return val
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


def _safe_int(val):
    if not val:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val):
    if not val:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ─── Singleton ───────────────────────────────────────────────────
csv_service = DBService()
