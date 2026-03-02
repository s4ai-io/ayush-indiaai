"""
FastAPI Backend for AYUSH ML Pipeline
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
import os
import json
import csv
import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from config import (
    ASR_REQUEST_TIMEOUT, TRANSLATE_REQUEST_TIMEOUT,
    DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT,
    DEFAULT_ALLOWED_ORIGINS,
)
from utils.run_logger import RunLogger, VOICE_DIR

from utils.validators import (
    PatientProfile,
    TreatmentRecommendation,
    TreatmentFeedback,
    PrescriptionRequest,
    ForecastResponse,
    TrendsResponse,
    HealthCheckResponse
)
from services.ayurgenix_service import ayurgenix_service
from services.hybrid_service import hybrid_service
from services.clustering_service import clustering_service
from services.rl_service import rl_service
from services.forecast_service import forecast_service
from services.csv_service import csv_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    print("\n" + "="*60)
    print("Starting AYUSH ML Backend API")
    print("="*60)
    
    # Initialize AyurGenix Treatment Service
    ayurgenix_service.initialize()
    
    # Initialize Forecast Service
    forecast_service.initialize()
    
    print("\n✓ Backend API ready!")
    print("="*60 + "\n")
    
    yield
    
    # Cleanup on shutdown
    print("\nShutting down AYUSH ML Backend API...")


# Create FastAPI app
app = FastAPI(
    title="AYUSH ML Pipeline API",
    description="AI-powered AYUSH treatment recommendations and disease forecasting",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
_raw_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins + ["*"],  # Keep wildcard for local network testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "AYUSH ML Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    ayurgenix_health = ayurgenix_service.health_check()
    
    return {
        "status": "healthy" if ayurgenix_health["initialized"] else "degraded",
        "models_loaded": ayurgenix_health["dataset_loaded"],
        "storage": "csv",
        "version": "3.0.0"
    }


@app.get("/api/diseases", tags=["Treatment Recommendations"])
async def get_disease_list(q: str = None):
    """
    Get list of all disease names from the AyurGenix dataset.
    
    Args:
        q: Optional search query to filter disease names
        
    Returns:
        List of disease name strings
    """
    diseases = ayurgenix_service.get_disease_list()
    if q:
        q_lower = q.strip().lower()
        diseases = [d for d in diseases if q_lower in d.lower()]
    return {"diseases": diseases}


@app.get("/api/diseases/suggestions", tags=["Treatment Recommendations"])
async def get_disease_suggestions(q: str = None, limit: int = 3):
    """
    Get fuzzy-matched suggestions for a disease name.
    
    Args:
        q: The disease name to find matches for
        limit: Max number of suggestions (default 3)
        
    Returns:
        List of suggested disease name strings
    """
    if not q:
        return {"suggestions": []}
    suggestions = ayurgenix_service.get_suggestions(q, limit=limit)
    return {"suggestions": suggestions}


@app.get("/api/dietary-plan", tags=["Treatment Recommendations"])
async def get_dietary_plan(disease: str, prakriti: str):
    """
    Get Ayurvedic dietary plan based on disease (partial match) and prakriti (exact match).

    Args:
        disease: Disease name to lookup (partial, case-insensitive)
        prakriti: Patient's Prakriti constitution (e.g. Vata, Pitta-Kapha)

    Returns:
        Matched dietary plan text, matched disease name, and prakriti, or null fields if no match.
    """
    try:
        dietary_csv_path = os.path.join(BASE_DIR, "data", "Ayurvedic_Dietary_Plan.csv")
        if not os.path.exists(dietary_csv_path):
            return {"dietary_plan": None, "disease_matched": None, "prakriti": prakriti}

        disease_lower = disease.strip().lower()
        prakriti_clean = prakriti.strip()

        current_disease = None
        with open(dietary_csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # The CSV uses a blank Disease cell for subsequent Prakriti rows of the same disease
                disease_cell = row.get("Disease", "").strip()
                if disease_cell:
                    current_disease = disease_cell

                if current_disease is None:
                    continue

                # Partial disease match (e.g. "Skin" matches "Skin Diseases")
                disease_matches = (
                    disease_lower in current_disease.lower()
                    or current_disease.lower() in disease_lower
                )
                prakriti_matches = row.get("Prakriti", "").strip().lower() == prakriti_clean.lower()

                if disease_matches and prakriti_matches:
                    return {
                        "dietary_plan": row.get("Dietary Plan", "").strip(),
                        "disease_matched": current_disease,
                        "prakriti": prakriti_clean,
                    }

        return {"dietary_plan": None, "disease_matched": None, "prakriti": prakriti_clean}

    except Exception as e:
        print(f"Error reading dietary plan CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dietary plan: {str(e)}")


@app.post("/api/recommend", response_model=TreatmentRecommendation, tags=["Treatment Recommendations"])
async def get_recommendation(patient: PatientProfile):
    """
    Get personalized AYUSH treatment recommendation using Hybrid Engine (Clustering + RL + Codified Data).
    
    Args:
        patient: Patient profile with disease, symptoms, prakriti, vikriti, severity, age, gender
        
    Returns:
        Treatment plan with herbs, yoga, diet, lifestyle, formulation, prevention, prognosis
    """
    try:
        patient_data = patient.model_dump()
        recommendation = hybrid_service.get_recommendation(patient_data)
        return recommendation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/ml/retrain", tags=["Continuous Learning"])
async def trigger_retraining():
    """
    Manually trigger the ML retraining pipeline:
    1. Retrain Patient Clustering (K-Means) on all historical AHIMS data.
    2. Retrain Reinforcement Learning (Bandits) on unprocessed clinician feedback.
    """
    try:
        cluster_res = clustering_service.retrain_clusters()
        rl_feedback_res = rl_service.retrain_from_feedback()
        rl_outcomes_res = rl_service.retrain_from_outcomes()
        
        return {
            "status": "success",
            "clustering": cluster_res,
            "reinforcement_learning_feedback": rl_feedback_res,
            "reinforcement_learning_outcomes": rl_outcomes_res
        }
    except Exception as e:
        print(f"❌ Error triggering ML retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger retraining: {str(e)}")


@app.post("/api/feedback", tags=["Continuous Learning"])
async def submit_feedback(feedback: TreatmentFeedback):
    """
    Submit doctor feedback for model retraining
    
    Args:
        feedback: Feedback data including patient ID, rating, comments, and final plan
    """
    try:
        # Save to Database
        csv_service.save_treatment_feedback(feedback.model_dump())
        print(f"✓ Feedback saved for Patient {feedback.patientId}")

        # Also keep CSV for backup/backward compatibility for now? 
        # Optional: We can remove this block if we are fully cutover. 
        # Keeping it as a fallback might be safe, but let's rely on DB as source of truth.
        
        return {"status": "success", "message": "Feedback recorded for continuous learning"}
        
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")


@app.post("/api/prescribe", tags=["Prescriptions"])
async def save_prescription(data: PrescriptionRequest, background_tasks: BackgroundTasks):
    """
    Save a doctor's full prescription.

    Creates 3 linked rows in a single transaction:
      - medical_records  (diagnosis + symptoms → feeds trends, alerts, hotspots)
      - ayush_treatments (herbs, yoga, diet details)
      - treatment_feedback (AI plan + doctor rating for ML loop)
    """
    try:
        result = csv_service.save_prescription(data.model_dump())
        
        # Trigger background retraining so that the newly saved feedback and records
        # instantly influence the RL and Clustering models for the next patient.
        background_tasks.add_task(trigger_retraining)
        
        return {
            "status": "success",
            "message": "Prescription saved successfully",
            **result,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"❌ Error saving prescription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save prescription: {str(e)}")


@app.get("/api/forecast", response_model=ForecastResponse, tags=["Disease Forecasting"])
async def get_forecast(disease: str = None, months: int = 3):
    """
    Get disease forecast for next N months
    
    Args:
        disease: Specific disease to forecast (optional, defaults to all diseases)
        months: Number of months to forecast (default: 3, max: 12)
        
    Returns:
        Forecast data with predicted cases, trend, and risk level
    """
    try:
        # Validate months
        if months < 1 or months > 12:
            raise HTTPException(status_code=400, detail="Months must be between 1 and 12")

        # Get forecast from service
        forecast = forecast_service.get_forecast(disease=disease, months=months)

        # ── Enrich with by_disease + real calendar month names ────────────────
        # (Works even if the service singleton was cached before recent changes)
        import calendar as _cal
        from datetime import datetime as _dt
        now = _dt.now()
        def _month_name(offset: int) -> str:
            m = (now.month - 1 + offset) % 12 + 1
            y = now.year + (now.month - 1 + offset) // 12
            return f"{_cal.month_abbr[m]} {y}"

        forecast_data = forecast.get("forecast_data", [])
        # Add month_name to each entry if missing
        for entry in forecast_data:
            if "month_name" not in entry:
                entry["month_name"] = _month_name(int(entry.get("month", "Month 1").split()[-1]))

        # Build by_disease grouping if missing
        if not forecast.get("by_disease"):
            by_disease: dict = {}
            for entry in forecast_data:
                dk = entry.get("disease", disease or "All Diseases")
                if dk not in by_disease:
                    by_disease[dk] = []
                by_disease[dk].append({
                    "month_name":      entry["month_name"],
                    "predicted_cases": entry["predicted_cases"],
                    "season":          entry.get("season", ""),
                    "ritu_sandhi":     entry.get("ritu_sandhi", False),
                })
            forecast["by_disease"] = by_disease

        return forecast

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ... existing imports ...

# ... existing code ...

@app.get("/api/trends", response_model=TrendsResponse, tags=["Disease Forecasting"])
async def get_emerging_trends():
    """
    Get emerging disease trends
    
    Returns:
        List of emerging disease trends with growth rates and risk scores
    """
    try:
        trends = forecast_service.get_emerging_trends()
        return trends
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/forecast/emerging", tags=["Disease Forecasting"])
async def get_emerging_trends_alias():
    """Alias for /api/trends — returns emerging disease trends with growth rates."""
    try:
        return forecast_service.get_emerging_trends()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# --- Analytics Endpoints ---
from services.analytics_service import analytics_service
from services.disease_names import DISEASE_NAMES, enrich_with_devanagari, get_full_name
from utils.validators import HotspotResponse, AlertResponse, DashboardSummaryResponse

@app.get("/api/analytics/disease-names", tags=["Public Health Analytics"])
async def get_disease_name_map():
    """
    Returns the full Sanskrit/Devanāgarī name lookup for all tracked diseases.
    Shape: { "<stored_diagnosis>": { devanagari, iast, hindi, english } }
    """
    return DISEASE_NAMES

@app.get("/api/analytics/trends", tags=["Public Health Analytics"])
async def get_disease_trends(days: int = 30):
    """Get disease trends over time"""
    try:
        trends = analytics_service.get_disease_trends(days=days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/hotspots", response_model=list[HotspotResponse], tags=["Public Health Analytics"])
async def get_disease_hotspots(disease: str = None):
    """Get location-based disease hotspots enriched with Devanāgarī names"""
    try:
        hotspots = analytics_service.get_hotspots(disease=disease)
        # Add devanagari/iast/hindi fields to each hotspot using diagnosis key
        for h in hotspots:
            entry = get_full_name(h.get("diagnosis", ""))
            h["devanagari"] = entry["devanagari"]
            h["iast"]       = entry["iast"]
            h["hindi"]      = entry["hindi"]
        return hotspots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/alerts", response_model=list[AlertResponse], tags=["Public Health Analytics"])
async def get_public_health_alerts():
    """Get active outbreak alerts enriched with Devanāgarī disease names"""
    try:
        alerts = analytics_service.detect_anomalies()
        for a in alerts:
            entry = get_full_name(a.get("disease", ""))
            a["devanagari"] = entry["devanagari"]
            a["iast"]       = entry["iast"]
            a["hindi"]      = entry["hindi"]
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard", response_model=DashboardSummaryResponse, tags=["Public Health Analytics"])
async def get_dashboard_summary():
    """Get overall analytics dashboard summary"""
    try:
        summary = analytics_service.get_dashboard_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from services.spatial_service import spatial_service

@app.get("/api/analytics/weekly-alerts", response_model=list[AlertResponse], tags=["Public Health Analytics"])
async def get_weekly_alerts():
    """
    Weekly rolling Z-score anomaly detection.
    Detects disease surges 3–4 weeks earlier than the monthly detector.
    Uses a 4-week recent window vs 12-week baseline window.
    """
    try:
        alerts = analytics_service.detect_weekly_anomalies()
        for a in alerts:
            entry = get_full_name(a.get("disease", ""))
            a["devanagari"] = entry["devanagari"]
            a["iast"]       = entry["iast"]
            a["hindi"]      = entry["hindi"]
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/clusters", tags=["Public Health Analytics"])
async def get_disease_clusters(days: int = 90):
    """
    DBSCAN geospatial clustering of disease burden across Indian cities.
    Groups cities within 400 km that share elevated disease burden.
    Returns cluster list with centroid, radius, cities, and total cases.
    """
    try:
        result = spatial_service.get_cluster_summary(days=days)
        # Enrich each cluster's disease name
        for cluster in result.get("clusters", []):
            entry = get_full_name(cluster.get("disease", ""))
            cluster["devanagari"] = entry["devanagari"]
            cluster["iast"]       = entry["iast"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



from services.gnn_service import gnn_service

@app.get("/api/analytics/predictions", tags=["Public Health Analytics"])
async def get_disease_spread_prediction(disease: str = None):
    """
    Predict short-term regional disease spread using graph diffusion on real DB data.
    Builds a dynamic city-level graph from actual patient records.

    Args:
        disease: Optional disease name filter (e.g. 'Dengue', 'Fever')
    """
    try:
        # Load real case loads from DB and simulate 7-day spread
        predictions = gnn_service.predict_spread(current_hotspots=[], disease=disease)
        graph_summary = gnn_service.get_spread_graph_summary(disease=disease)
        return {
            "predictions": predictions,
            "graph_summary": graph_summary,
            "disease_filter": disease or "All diseases",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




from services.registration_agent import registration_agent_router
from services.treatment_agent import treatment_agent_router
from services.admin_router import admin_router

app.include_router(registration_agent_router, prefix="/api/copilot/registration", tags=["Copilot Agent"])
app.include_router(treatment_agent_router, prefix="/api/copilot/treatment", tags=["Copilot Agent"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

from utils.validators import RegistrationData, ConsultationData

@app.post("/api/consultations", tags=["Consultations"])
async def create_consultation(data: ConsultationData):
    """
    Save a new consultation (visit) for a patient.
    """
    try:
        visit_id = csv_service.create_consultation(data.patientId, data.assessment.model_dump())
        return {
            "status": "success",
            "message": "Consultation saved successfully",
            "visitId": visit_id
        }
    except Exception as e:
        print(f"Error creating consultation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/consultations/{visit_id}/treatment", tags=["Consultations"])
async def get_consultation_context(visit_id: str):
    """
    Get the context (symptoms, diagnosis, notes) for a specific visit ID 
    to populate the treatment generation page.
    """
    try:
        record = csv_service.get_medical_record_by_id(visit_id)
        if not record:
            raise HTTPException(status_code=404, detail="Visit not found")
            
        patient_id = record.get("patient_id")
        patient = csv_service.get_patient_by_id(patient_id)
        
        # _DictObj exposes fields as attributes, not dict keys
        first_name = getattr(patient, "first_name", "Unknown") if patient else "Unknown"
        last_name  = getattr(patient, "last_name",  "") if patient else ""
        mobile     = getattr(patient, "mobile",     "Unknown") if patient else "Unknown"
        
        return {
            "patientId": patient_id,
            "patientName": f"{first_name} {last_name}".strip(),
            "patientMobile": mobile,
            "symptoms":     record.get("symptoms", ""),
            "diagnosis":    record.get("diagnosis", ""),
            "doctorNotes":  record.get("notes", ""),
            "prakriti":     record.get("prakriti", ""),
            "vikriti":      record.get("vikriti", ""),
            "severity":     record.get("severity", ""),
            "comorbidities": record.get("comorbidities", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching visit context: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/visits/{visit_id}", tags=["Consultations"])
async def get_visit_details(visit_id: str):
    """
    Get complete details for a single visit — patient info + medical record + AYUSH treatment.
    Used for the read-only Visit Details page.
    """
    try:
        import json as _json

        record = csv_service.get_medical_record_by_id(visit_id)
        if not record:
            raise HTTPException(status_code=404, detail="Visit not found")

        patient_id = record.get("patient_id")
        patient = csv_service.get_patient_by_id(patient_id)

        # Safely parse prescription JSON
        raw_prescription = record.get("prescription", "")
        try:
            prescription = _json.loads(raw_prescription) if raw_prescription and raw_prescription != "{}" else {}
        except Exception:
            prescription = {}

        # Look up linked AYUSH treatment and feedback from Postgres
        from models import SessionLocal, AyushTreatment, TreatmentFeedback
        from services.csv_service import _safe_json_parse
        with SessionLocal() as db:
            ayush = db.query(AyushTreatment).filter(
                AyushTreatment.medical_record_id == visit_id
            ).first()
            feedback_row = db.query(TreatmentFeedback).filter(
                TreatmentFeedback.medical_record_id == visit_id
            ).first()

        # _DictObj stores fields as attributes, not dict keys — use getattr()
        g = lambda attr, d='': str(getattr(patient, attr, d) or d) if patient else d
        return {
            # Patient demographics
            "patient": {
                "id": patient_id,
                "firstName":     g("first_name"),
                "lastName":      g("last_name"),
                "gender":        g("gender"),
                "age":           g("age"),
                "maritalStatus": g("marital_status"),
                "mobile":        g("mobile"),
                "address":       g("address"),
                "city":          g("city"),
                "state":         g("state"),
                "pincode":       g("pincode"),
                "bloodGroup":    g("blood_group"),
                "occupation":    g("occupation"),
                "idType":        g("id_type"),
                "idNumber":      g("id_number"),
            },
            # Clinical assessment
            "visit": {
                "id": visit_id,
                "visitDate": record.get("visit_date", ""),
                "symptoms": record.get("symptoms", ""),
                "diagnosis": record.get("diagnosis", ""),
                "prakriti": record.get("prakriti", ""),
                "vikriti": record.get("vikriti", ""),
                "severity": record.get("severity", ""),
                "comorbidities": record.get("comorbidities", ""),
                "notes": record.get("notes", ""),
                "prescription": prescription,
            },
            # AYUSH treatment plan
            "treatment": {
                "herbs":                ayush.herbs_prescribed if ayush else "",
                "yoga":                 ayush.yoga_prescribed if ayush else "",
                "diet":                 ayush.diet_plan if ayush else "",
                "durationWeeks":        ayush.treatment_duration_weeks if ayush else "",
                "predictedImprovement": ayush.improvement_percentage if ayush else "",
                "outcome":              ayush.outcome if ayush else "",
            },
            # Doctor feedback (if any)
            "feedback": {
                "rating":   feedback_row.doctor_rating if feedback_row else "",
                "comments": feedback_row.doctor_comments if feedback_row else "",
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching visit details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/patients", tags=["Patient Management"])
async def create_patient(data: RegistrationData):
    """
    Create a new patient registration
    """
    try:
        basic_info = data.basicInfo.model_dump()
        contact_info = data.contactInfo.model_dump()
        other_info = data.otherInfo.model_dump()
        
        patient = csv_service.create_patient(basic_info, contact_info, other_info)
        
        return {
            "status": "success",
            "message": "Patient registered successfully",
            "patient_id": str(patient.id),
            "mobile": patient.mobile
        }
    except Exception as e:
        print(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients/search", tags=["Patient Management"])
async def search_patients(q: str):
    """
    Search patients by name or mobile number.
    """
    try:
        if not q or len(q) < 3:
            return []
        results = csv_service.search_patients(query=q)
        return results
    except Exception as e:
        print(f"Error searching patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients", tags=["Patient Management"])
async def get_patients(status: str = None):
    """
    Get patients, optionally filtered by diagnosis status.

    Query params:
      - status=pending   → patients NOT yet diagnosed
      - status=completed → patients already diagnosed
      - (none)           → all patients
    """
    try:
        if status == "pending":
            patients = csv_service.get_patients_by_status(diagnosis_done=False)
        elif status == "completed":
            patients = csv_service.get_patients_by_status(diagnosis_done=True)
        else:
            patients = csv_service.get_all_patients()
        return patients
    except Exception as e:
        print(f"Error fetching patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients/{patient_id}", tags=["Patient Management"])
async def get_patient(patient_id: str):
    """
    Get patient by ID
    """
    try:
        patient = csv_service.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    except Exception as e:
        print(f"Error fetching patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients/{patient_id}/diagnoses", tags=["Patient Management"])
async def get_patient_diagnoses(patient_id: str):
    """Get all diagnoses (medical records + AYUSH treatment) for a patient."""
    try:
        diagnoses = csv_service.get_patient_diagnoses(patient_id)
        return diagnoses
    except Exception as e:
        print(f"Error fetching diagnoses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patients/{patient_id}/history", tags=["Patient Management"])
async def get_patient_history(patient_id: str):
    """
    Get full visit history for a patient.
    For now, this delegates to the existing `get_patient_diagnoses` which fetches Medical Records + Treatments.
    """
    try:
        patient = csv_service.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
            
        history = csv_service.get_patient_diagnoses(patient_id)
        return {
            "patientId": patient_id,
            "patientName": f'{getattr(patient, "first_name", "")} {getattr(patient, "last_name", "")}'.strip(),
            "history": history
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching patient history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/diagnoses/completed", tags=["Patient Management"])
async def get_completed_diagnoses():
    """Get summary of completed diagnoses for card-based display."""
    try:
        return csv_service.get_completed_diagnoses_summary()
    except Exception as e:
        print(f"Error fetching completed diagnoses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Voice Pipeline ─────────────────────────────────────────────────────────────
# Frontend → FastAPI → Modal ASR / IndicTrans2
# All steps logged into a single per-run JSON in backend/logs/runs/
# ──────────────────────────────────────────────────────────────────────────────

class BindRunIdRequest(BaseModel):
    run_id: str

@app.post("/api/bind-run-id", tags=["Voice Pipeline"])
async def bind_run_id(req: BindRunIdRequest):
    """
    Bind a voice-pipeline run_id so the next LLM call in AGUIChatWorkflow
    can link its log entry to the same run JSON.
    Called by the frontend *before* appending the transcript to CopilotKit chat.
    """
    try:
        from utils.llm_logger import set_current_run_id
        set_current_run_id(req.run_id)
    except Exception:
        pass
    return {"status": "ok"}

class TranslateRequest(BaseModel):
    text: str
    src_lang: str
    run_id: str | None = None   # carry-over from /api/transcribe for chained logging


@app.post("/api/transcribe", tags=["Voice Pipeline"])
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(None),
):
    """
    Receive an audio recording from the frontend, save it to disk,
    forward to Modal AI4Bharat ASR, and return the transcription.
    A RunLogger is created here; the run_id is returned so that
    /api/translate can append its step to the same JSON file.
    """
    modal_asr_url = os.getenv("MODAL_ASR_URL")
    if not modal_asr_url:
        raise HTTPException(status_code=500, detail="MODAL_ASR_URL not configured in backend .env")

    rl = RunLogger()

    # ── 1. Save raw voice input ────────────────────────────────────────────────
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:23].replace(":", "-")
    ext = (audio.filename or "audio.webm").rsplit(".", 1)[-1]
    voice_filename = f"{ts}_{rl.run_id}.{ext}"
    voice_path = os.path.join(VOICE_DIR, voice_filename)

    audio_bytes = await audio.read()
    with open(voice_path, "wb") as f:
        f.write(audio_bytes)

    rl.set_voice_file(voice_path)

    # ── 2. Call Modal ASR ──────────────────────────────────────────────────────
    file_size_kb = round(len(audio_bytes) / 1024, 1)
    # webm/opus at 128 kbps → ~16 KB/s; rough estimate for logging only
    estimated_duration_s = round(len(audio_bytes) / (128 * 1024 / 8), 1)
    transcriptor_input = {
        "voice_file": voice_path,
        "file_name": audio.filename or "audio.webm",
        "language": language,
        "file_size_kb": file_size_kb,
        "estimated_duration_s": estimated_duration_s,
        "modal_asr_url": modal_asr_url,
    }

    try:
        async with httpx.AsyncClient(timeout=ASR_REQUEST_TIMEOUT) as client:
            form_data = {"language": language} if language else {}
            files = {"audio": (audio.filename or "audio.webm", audio_bytes, audio.content_type or "audio/webm")}
            resp = await client.post(modal_asr_url, data=form_data, files=files)

        if resp.status_code != 200:
            rl.update_step(
                "transcriptor",
                input=transcriptor_input,
                output=None,
                error=f"Modal ASR error {resp.status_code}: {resp.text[:500]}",
            )
            rl.finalize()
            raise HTTPException(status_code=resp.status_code, detail=f"Modal ASR error: {resp.text[:300]}")

        asr_data = resp.json()
        rl.update_step("transcriptor", input=transcriptor_input, output=asr_data, error=None)

        # Flush now — the file exists even if translation is skipped (English audio)
        rl.flush()

        return {**asr_data, "run_id": rl.run_id}

    except httpx.TimeoutException:
        rl.update_step("transcriptor", input=transcriptor_input, output=None, error="Modal ASR request timed out")
        rl.finalize()
        raise HTTPException(status_code=504, detail="Modal ASR request timed out")
    except HTTPException:
        raise
    except Exception as exc:
        rl.update_step("transcriptor", input=transcriptor_input, output=None, error=str(exc))
        rl.finalize()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")


@app.post("/api/translate", tags=["Voice Pipeline"])
async def translate_text(req: TranslateRequest):
    """
    Translate Indian-language text to English using Modal IndicTrans2.
    Accepts an optional run_id; if provided, the translator step is appended
    to the existing run JSON produced by /api/transcribe, giving a single
    combined log file for the complete voice pipeline.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="No text provided for translation")

    modal_translate_url = os.getenv("MODAL_TRANSLATE_URL")
    if not modal_translate_url:
        raise HTTPException(status_code=500, detail="MODAL_TRANSLATE_URL not configured in backend .env")

    # Re-attach to the existing run JSON written by /api/transcribe.
    # load_existing() scans RUNS_DIR for the file whose name contains run_id
    # and reopens it — so the translator step is appended to the same file.
    # Fall back to a fresh run if no run_id was supplied (standalone translate call).
    if req.run_id:
        rl = RunLogger.load_existing(req.run_id) or RunLogger()
    else:
        rl = RunLogger()

    translator_input = {
        "text": req.text,
        "src_lang": req.src_lang,
        "modal_translate_url": modal_translate_url,
    }

    try:
        async with httpx.AsyncClient(timeout=TRANSLATE_REQUEST_TIMEOUT) as client:
            resp = await client.post(
                modal_translate_url,
                json={"text": req.text, "src_lang": req.src_lang},
            )

        if resp.status_code != 200:
            rl.update_step(
                "translator",
                input=translator_input,
                output=None,
                error=f"Modal Translate error {resp.status_code}: {resp.text[:500]}",
            )
            rl.finalize()
            raise HTTPException(status_code=resp.status_code, detail=f"Translation error: {resp.text[:300]}")

        translate_data = resp.json()
        rl.update_step("translator", input=translator_input, output=translate_data, error=None)
        rl.finalize()

        return translate_data

    except httpx.TimeoutException:
        rl.update_step("translator", input=translator_input, output=None, error="Modal Translate request timed out")
        rl.finalize()
        raise HTTPException(status_code=504, detail="Modal Translate request timed out")
    except HTTPException:
        raise
    except Exception as exc:
        rl.update_step("translator", input=translator_input, output=None, error=str(exc))
        rl.finalize()
        raise HTTPException(status_code=500, detail=f"Translation failed: {exc}")


if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", DEFAULT_BACKEND_HOST)
    port = int(os.getenv("BACKEND_PORT", str(DEFAULT_BACKEND_PORT)))
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
