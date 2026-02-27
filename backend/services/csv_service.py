"""
CSV-based data service — replaces the PostgreSQL db_service.
Reads/writes patients, medical_records, ayush_treatments, treatment_feedback as CSV files.
"""
import os
import csv
import uuid
import json
import threading
from datetime import datetime, date


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# CSV file paths
PATIENTS_CSV = os.path.join(DATA_DIR, "patients.csv")
MEDICAL_RECORDS_CSV = os.path.join(DATA_DIR, "medical_records.csv")
AYUSH_TREATMENTS_CSV = os.path.join(DATA_DIR, "ayush_treatments.csv")
TREATMENT_FEEDBACK_CSV = os.path.join(DATA_DIR, "treatment_feedback.csv")

# Thread lock for safe concurrent writes
_lock = threading.Lock()


# ─── CSV Helpers ─────────────────────────────────────────────────

def _read_csv(filepath: str) -> list[dict]:
    """Read a CSV file and return list of dicts."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(filepath: str, rows: list[dict], fieldnames: list[str]):
    """Write list of dicts to CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(filepath: str, row: dict, fieldnames: list[str]):
    """Append a single row to a CSV file."""
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ─── Field definitions ──────────────────────────────────────────

PATIENT_FIELDS = [
    "id", "first_name", "last_name", "gender", "age", "marital_status",
    "mobile", "address", "city", "state", "pincode",
    "blood_group", "occupation", "id_type", "id_number",
    "diagnosis_done", "created_at", "updated_at",
]

MEDICAL_RECORD_FIELDS = [
    "id", "patient_id", "visit_date", "diagnosis", "symptoms",
    "prakriti", "vikriti", "severity", "comorbidities",
    "notes", "prescription",
]

AYUSH_TREATMENT_FIELDS = [
    "id", "patient_id", "medical_record_id", "visit_date", "disease",
    "herbs_prescribed", "yoga_prescribed", "diet_plan",
    "treatment_duration_weeks", "improvement_percentage", "outcome",
]

TREATMENT_FEEDBACK_FIELDS = [
    "id", "patient_id", "medical_record_id",
    "ai_plan", "ml_context",
    "doctor_rating", "doctor_comments", "is_retrained",
    "created_at",
]


# ─── CSVService ──────────────────────────────────────────────────

class CSVService:
    """CSV-backed data service matching the old db_service interface."""

    # ─── Patient Operations ──────────────────────────────────────

    def create_patient(self, basic_info: dict, contact_info: dict, other_info: dict):
        """Create a new patient and append to patients.csv."""
        patient_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        row = {
            "id": patient_id,
            "first_name": basic_info.get("firstName", ""),
            "last_name": basic_info.get("lastName", ""),
            "gender": basic_info.get("gender", ""),
            "age": basic_info.get("age", ""),
            "marital_status": basic_info.get("maritalStatus", ""),
            "mobile": contact_info.get("mobileNumber", ""),
            "address": contact_info.get("address", ""),
            "city": contact_info.get("city", ""),
            "state": contact_info.get("state", ""),
            "pincode": contact_info.get("pincode", ""),
            "blood_group": (other_info or {}).get("bloodGroup", ""),
            "occupation": (other_info or {}).get("occupation", ""),
            "id_type": (other_info or {}).get("idType", ""),
            "id_number": (other_info or {}).get("idNumber", ""),
            "diagnosis_done": "False",
            "created_at": now,
            "updated_at": now,
        }

        with _lock:
            _append_csv(PATIENTS_CSV, row, PATIENT_FIELDS)

        print(f"✓ Patient created via CSV: {row['first_name']} {row['last_name']} ({patient_id})")

        # Return an object-like dict so main.py can access .id and .mobile
        return _DictObj(row)

    def get_patient_by_id(self, patient_id: str):
        """Get a single patient by ID."""
        patients = _read_csv(PATIENTS_CSV)
        for p in patients:
            if p["id"] == str(patient_id):
                return _DictObj(p)
        return None

    def get_all_patients(self, limit: int = 5000):
        """Get all patients, sorted by created_at desc."""
        patients = _read_csv(PATIENTS_CSV)
        patients.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return [_DictObj(p) for p in patients[:limit]]

    def search_patients(self, query: str, limit: int = 20):
        """Search patients by name or mobile number."""
        patients = _read_csv(PATIENTS_CSV)
        query = query.lower()
        results = []
        for p in patients:
            name = f'{p.get("first_name", "")} {p.get("last_name", "")}'.lower()
            mobile = p.get("mobile", "").lower()
            if query in name or query in mobile:
                results.append(_DictObj(p))
                if len(results) >= limit:
                    break
        return results

    def get_patients_by_status(self, diagnosis_done: bool, limit: int = 200):
        """Get patients filtered by diagnosis status."""
        patients = _read_csv(PATIENTS_CSV)
        target = str(diagnosis_done)
        filtered = [p for p in patients if p.get("diagnosis_done", "False") == target]
        filtered.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return [_DictObj(p) for p in filtered[:limit]]

    # ─── Prescription / Diagnosis ────────────────────────────────

    def create_consultation(self, patient_id: str, assessment: dict) -> str:
        """
        Create a new medical record (visit) from the Consultation form.
        """
        record_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        row = {
            "id": record_id,
            "patient_id": patient_id,
            "visit_date": now,
            "diagnosis": assessment.get("diagnosis", ""),
            "symptoms": assessment.get("symptoms", ""),
            "prakriti": assessment.get("prakriti", ""),
            "vikriti": assessment.get("vikriti", ""),
            "severity": str(assessment.get("severity", 5)),
            "comorbidities": assessment.get("comorbidities", ""),
            "notes": assessment.get("notes", ""),
            "prescription": "{}",  # Empty initially
        }
        
        with _lock:
            _append_csv(MEDICAL_RECORDS_CSV, row, MEDICAL_RECORD_FIELDS)
            
        print(f"✓ Consultation saved (CSV): patient={patient_id}, visit={record_id}")
        return record_id

    def save_prescription(self, data: dict) -> dict:
        """
        Save a doctor's prescription.
        Creates 3 linked CSV rows (or updates medical record if visitId exists) + marks patient as diagnosed.
        """
        patient_id = data.get("patientId")
        record_id = data.get("visitId")

        # Verify patient exists
        patient = self.get_patient_by_id(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        treatment_plan = data.get("treatmentPlan") or {}
        disease = data.get("disease", "")
        symptoms = data.get("symptoms", "")
        doctor_notes = data.get("doctorNotes", "")
        
        treatment_id = str(uuid.uuid4())
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        prescription_json = {
            "ai_plan": treatment_plan,
            "doctor_notes": data.get("doctorPrescription", ""),
        }

        with _lock:
            # 1. Update or Create Medical Record
            record_found = False
            if record_id:
                records = _read_csv(MEDICAL_RECORDS_CSV)
                for r in records:
                    if r["id"] == record_id:
                        r["prescription"] = json.dumps(prescription_json)
                        if doctor_notes:
                            r["notes"] = r.get("notes", "") + f"\n\n[Treatment Phase]: {doctor_notes}"
                        if disease:
                            r["diagnosis"] = disease
                        
                        # Update additional fields that might be finalized during prescription
                        if symptoms:
                            r["symptoms"] = symptoms
                        if data.get("prakriti"):
                            r["prakriti"] = data.get("prakriti")
                        if data.get("vikriti"):
                            r["vikriti"] = data.get("vikriti")
                        if data.get("severity") is not None:
                            r["severity"] = str(data.get("severity"))
                        if data.get("comorbidities"):
                            r["comorbidities"] = data.get("comorbidities")
                        
                        record_found = True
                        disease = disease or r.get("diagnosis", "")
                        break
                
                if record_found:
                    _write_csv(MEDICAL_RECORDS_CSV, records, MEDICAL_RECORD_FIELDS)

            if not record_found:
                record_id = record_id or str(uuid.uuid4())
                medical_row = {
                    "id": record_id,
                    "patient_id": patient_id,
                    "visit_date": now,
                    "diagnosis": disease or (treatment_plan.get("source_disease") or "Unknown"),
                    "symptoms": symptoms,
                    "prakriti": data.get("prakriti", ""),
                    "vikriti": data.get("vikriti", ""),
                    "severity": str(data.get("severity", 5)),
                    "comorbidities": "",
                    "notes": doctor_notes,
                    "prescription": json.dumps(prescription_json),
                }
                _append_csv(MEDICAL_RECORDS_CSV, medical_row, MEDICAL_RECORD_FIELDS)

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

            ayush_row = {
                "id": treatment_id,
                "patient_id": patient_id,
                "medical_record_id": record_id,
                "visit_date": date.today().isoformat(),
                "disease": disease,
                "herbs_prescribed": herbs_text,
                "yoga_prescribed": yoga_text,
                "diet_plan": diet_text,
                "treatment_duration_weeks": treatment_plan.get("recommended_duration_weeks", ""),
                "improvement_percentage": treatment_plan.get("predicted_improvement", ""),
                "outcome": "Prescribed",
            }
            _append_csv(AYUSH_TREATMENTS_CSV, ayush_row, AYUSH_TREATMENT_FIELDS)

            # 3. Treatment Feedback
            ml_context = {
                "disease": disease,
                "symptoms": symptoms,
                "severity": data.get("severity"),
                "prakriti": data.get("prakriti"),
                "vikriti": data.get("vikriti"),
                "match_method": treatment_plan.get("match_method"),
                "match_confidence": treatment_plan.get("match_confidence"),
            }

            feedback_row = {
                "id": feedback_id,
                "patient_id": patient_id,
                "medical_record_id": record_id,
                "ai_plan": json.dumps(treatment_plan),
                "ml_context": json.dumps(ml_context),
                "doctor_rating": data.get("rating", ""),
                "doctor_comments": data.get("feedback", ""),
                "is_retrained": "False",
                "created_at": now,
            }
            _append_csv(TREATMENT_FEEDBACK_CSV, feedback_row, TREATMENT_FEEDBACK_FIELDS)
            
            # Mark patient as diagnosed
            self._set_patient_diagnosed(patient_id)

        print(f"✓ Treatment saved (CSV): patient={patient_id}, diagnosis={disease}")

        return {
            "medical_record_id": record_id,
            "ayush_treatment_id": treatment_id,
            "treatment_feedback_id": feedback_id,
        }

    def save_treatment_feedback(self, feedback_data: dict):
        """Save ML feedback to CSV."""
        feedback_row = {
            "id": str(uuid.uuid4()),
            "patient_id": feedback_data.get("patientId", ""),
            "medical_record_id": "",
            "ai_plan": json.dumps(feedback_data.get("finalPlan", {})),
            "ml_context": json.dumps({}),
            "doctor_rating": feedback_data.get("rating", ""),
            "doctor_comments": feedback_data.get("comments", ""),
            "is_retrained": "False",
            "created_at": datetime.utcnow().isoformat(),
        }

        with _lock:
            _append_csv(TREATMENT_FEEDBACK_CSV, feedback_row, TREATMENT_FEEDBACK_FIELDS)

        print(f"✓ Feedback saved (CSV)")
        return feedback_row

    # ─── Diagnosis Queries ───────────────────────────────────────

    def get_medical_record_by_id(self, record_id: str):
        """Get a specific medical record by ID."""
        records = _read_csv(MEDICAL_RECORDS_CSV)
        for r in records:
            if r["id"] == str(record_id):
                return r
        return None

    def get_patient_diagnoses(self, patient_id_str: str) -> list:
        """Get all diagnoses for a patient (medical records + AYUSH details)."""
        records = _read_csv(MEDICAL_RECORDS_CSV)
        treatments = _read_csv(AYUSH_TREATMENTS_CSV)

        # Index treatments by medical_record_id
        treatments_map = {}
        for t in treatments:
            treatments_map[t["medical_record_id"]] = t

        result = []
        patient_records = [r for r in records if r["patient_id"] == patient_id_str]
        patient_records.sort(key=lambda r: r.get("visit_date", ""), reverse=True)

        for r in patient_records:
            ayush = treatments_map.get(r["id"])
            result.append({
                "id": r["id"],
                "diagnosis": r.get("diagnosis", ""),
                "symptoms": r.get("symptoms", ""),
                "notes": r.get("notes", ""),
                "prescription": _safe_json_parse(r.get("prescription", "")),
                "visit_date": r.get("visit_date"),
                "herbs": ayush["herbs_prescribed"] if ayush else None,
                "yoga": ayush["yoga_prescribed"] if ayush else None,
                "diet": ayush["diet_plan"] if ayush else None,
                "duration_weeks": _safe_int(ayush.get("treatment_duration_weeks")) if ayush else None,
                "improvement": _safe_float(ayush.get("improvement_percentage")) if ayush else None,
                "outcome": ayush["outcome"] if ayush else None,
            })
        return result

    def get_completed_diagnoses_summary(self, limit: int = 200) -> list:
        """Get completed diagnoses with patient info for card display."""
        patients = _read_csv(PATIENTS_CSV)
        records = _read_csv(MEDICAL_RECORDS_CSV)

        # Index patients by ID
        patients_map = {p["id"]: p for p in patients}

        # Filter only records for diagnosed patients
        diagnosed_ids = {p["id"] for p in patients if p.get("diagnosis_done") == "True"}

        result = []
        for r in records:
            if r["patient_id"] in diagnosed_ids:
                p = patients_map.get(r["patient_id"], {})
                result.append({
                    "record_id": r["id"],
                    "patient_id": r["patient_id"],
                    "patient_name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                    "patient_age": _safe_int(p.get("age")),
                    "patient_gender": p.get("gender", ""),
                    "patient_city": p.get("city", ""),
                    "patient_mobile": p.get("mobile", ""),
                    "diagnosis": r.get("diagnosis", ""),
                    "symptoms": r.get("symptoms", ""),
                    "visit_date": r.get("visit_date"),
                })

        result.sort(key=lambda x: x.get("visit_date", ""), reverse=True)
        return result[:limit]

    # ─── Internal Helpers ────────────────────────────────────────

    def _set_patient_diagnosed(self, patient_id: str):
        """Update a patient's diagnosis_done to True in the CSV."""
        patients = _read_csv(PATIENTS_CSV)
        for p in patients:
            if p["id"] == patient_id:
                p["diagnosis_done"] = "True"
                p["updated_at"] = datetime.utcnow().isoformat()
                break
        _write_csv(PATIENTS_CSV, patients, PATIENT_FIELDS)


# ─── Utility classes/functions ───────────────────────────────────

class _DictObj:
    """Wrapper so dict values are accessible as attributes (patient.id, patient.mobile)."""
    def __init__(self, d: dict):
        self.__dict__.update(d)
        # Convert string booleans
        if hasattr(self, 'diagnosis_done'):
            self.diagnosis_done = str(self.diagnosis_done) == "True"
        # Convert age to int
        if hasattr(self, 'age') and self.age:
            try:
                self.age = int(self.age)
            except (ValueError, TypeError):
                pass


def _safe_json_parse(val):
    if not val:
        return None
    try:
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
csv_service = CSVService()
