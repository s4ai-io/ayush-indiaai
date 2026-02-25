"""
FastAPI Backend for AYUSH ML Pipeline
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import json
import csv

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "*", # Allow all for network testing
    ],
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


@app.post("/api/recommend", response_model=TreatmentRecommendation, tags=["Treatment Recommendations"])
async def get_recommendation(patient: PatientProfile):
    """
    Get personalized AYUSH treatment recommendation using AyurGenix dataset.
    
    Uses 3-tier matching: exact disease → fuzzy match → TF-IDF symptom similarity.
    
    Args:
        patient: Patient profile with disease, symptoms, prakriti, vikriti, severity, age, gender
        
    Returns:
        Treatment plan with herbs, yoga, diet, lifestyle, formulation, prevention, prognosis
    """
    try:
        patient_data = patient.model_dump()
        recommendation = ayurgenix_service.get_recommendation(patient_data)
        return recommendation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
async def save_prescription(data: PrescriptionRequest):
    """
    Save a doctor's full prescription.

    Creates 3 linked rows in a single transaction:
      - medical_records  (diagnosis + symptoms → feeds trends, alerts, hotspots)
      - ayush_treatments (herbs, yoga, diet details)
      - treatment_feedback (AI plan + doctor rating for ML loop)
    """
    try:
        result = csv_service.save_prescription(data.model_dump())
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




# --- Analytics Endpoints ---
from services.analytics_service import analytics_service
from utils.validators import HotspotResponse, AlertResponse, DashboardSummaryResponse

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
    """Get location-based disease hotspots"""
    try:
        hotspots = analytics_service.get_hotspots(disease=disease)
        return hotspots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/alerts", response_model=list[AlertResponse], tags=["Public Health Analytics"])
async def get_public_health_alerts():
    """Get active outbreak alerts"""
    try:
        alerts = analytics_service.detect_anomalies()
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


from services.gnn_service import gnn_service

@app.get("/api/analytics/predictions", tags=["Public Health Analytics"])
async def get_disease_spread_prediction():
    """Predict future disease spread using Spatiotemporal GNN"""
    try:
        # 1. Get current hotspots
        current_hotspots = analytics_service.get_hotspots(disease="Dengue") # Default to Dengue for demo
        
        # 2. Predict spread based on current state
        predictions = gnn_service.predict_spread(current_hotspots)
        
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Register CopilotKit Agent Router

from services.registration_agent import registration_agent_router
app.include_router(registration_agent_router, prefix="/api/copilot/registration", tags=["Copilot Agent"])

# --- Agents ---
from services.ehr_agent import ehr_agent_router
app.include_router(ehr_agent_router, prefix="/api/copilot/ehr", tags=["Copilot Agent"])

from services.doctor_agent import doctor_agent_router
app.include_router(doctor_agent_router, prefix="/api/copilot/doctor", tags=["Copilot Agent"])

from services.treatment_agent import treatment_agent_router
app.include_router(treatment_agent_router, prefix="/api/copilot/treatment", tags=["Copilot Agent"])

from utils.validators import RegistrationData

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


@app.get("/api/diagnoses/completed", tags=["Patient Management"])
async def get_completed_diagnoses():
    """Get summary of completed diagnoses for card-based display."""
    try:
        return csv_service.get_completed_diagnoses_summary()
    except Exception as e:
        print(f"Error fetching completed diagnoses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
