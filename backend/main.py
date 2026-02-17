"""
FastAPI Backend for AYUSH ML Pipeline
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from utils.validators import (
    PatientProfile,
    TreatmentRecommendation,
    TreatmentFeedback,
    ForecastResponse,
    TrendsResponse,
    HealthCheckResponse
)
from services.ml_service import ml_service
from services.forecast_service import forecast_service
import csv
import os
import json


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    print("\n" + "="*60)
    print("Starting AYUSH ML Backend API")
    print("="*60)
    
    # Initialize ML Service
    ml_service.initialize()
    
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
    ml_health = ml_service.health_check()
    forecast_health = forecast_service.health_check()
    
    return {
        "status": "healthy" if ml_health["initialized"] else "degraded",
        "models_loaded": ml_health["models_loaded"],
        "version": "1.0.0"
    }


@app.post("/api/recommend", response_model=TreatmentRecommendation, tags=["ML Recommendations"])
async def get_recommendation(patient: PatientProfile):
    """
    Get personalized AYUSH treatment recommendation
    
    Args:
        patient: Patient profile with age, gender, prakriti, vikriti, disease, severity, and optional BMI
        
    Returns:
        Treatment recommendation with herbs, yoga, diet, lifestyle, and predictions
    """
    try:
        # Convert Pydantic model to dict
        patient_data = patient.model_dump()
        
        # Get recommendation from ML service
        recommendation = ml_service.get_recommendation(patient_data)
        
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
        # Use absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        feedback_file = os.path.join(base_dir, "data", "treatment_feedback.csv")
        file_exists = os.path.isfile(feedback_file)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        
        with open(feedback_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'patient_id', 'rating', 'feedback', 'treatment_plan_json', 'context_json'])
            
            writer.writerow([
                feedback.timestamp,
                feedback.patientId,
                feedback.rating,
                feedback.feedback,
                json.dumps(feedback.treatmentPlan),
                json.dumps(feedback.context)
            ])
            
        print(f"✓ Feedback saved for Patient {feedback.patientId}")
        return {"status": "success", "message": "Feedback recorded for continuous learning"}
        
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")


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
from services.ehr_agent import ehr_agent_router

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

@app.get("/api/analytics/trends", tags=["Public Health Analytics"])
async def get_disease_trends(days: int = 30):
    """Get disease trends over time"""
    try:
        trends = analytics_service.get_disease_trends(days=days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/hotspots", tags=["Public Health Analytics"])
async def get_disease_hotspots(disease: str = None):
    """Get location-based disease hotspots"""
    try:
        hotspots = analytics_service.get_hotspots(disease=disease)
        return hotspots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/alerts", tags=["Public Health Analytics"])
async def get_public_health_alerts():
    """Get active outbreak alerts"""
    try:
        # Detect anomalies dynamically
        alerts = analytics_service.detect_anomalies()
        return alerts
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
app.include_router(ehr_agent_router, prefix="/api/copilot/ehr", tags=["Copilot Agent"])

from services.registration_agent import registration_agent_router
app.include_router(registration_agent_router, prefix="/api/copilot/registration", tags=["Copilot Agent"])

from services.doctor_agent import doctor_agent_router
app.include_router(doctor_agent_router, prefix="/api/copilot/doctor", tags=["Copilot Agent"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
