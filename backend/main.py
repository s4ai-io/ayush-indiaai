"""
FastAPI Backend for AYUSH ML Pipeline
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional
import asyncio
import uvicorn
import os
import time
import re
import json
import csv
import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from config import (
    ASR_REQUEST_TIMEOUT, TRANSLATE_REQUEST_TIMEOUT, GEMMA_REQUEST_TIMEOUT,
    DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT,
    DEFAULT_ALLOWED_ORIGINS,
)
from utils.run_logger import RunLogger, VOICE_DIR
from utils import phi4_prompts, gemma4_prompts

from utils.validators import (
    PatientProfile,
    TreatmentRecommendation,
    TreatmentFeedback,
    PrescriptionRequest,
    ForecastResponse,
    TrendsResponse,
    HealthCheckResponse
)
from services.ISHAAyush_service import ISHAAyush_service
from services.hybrid_service import hybrid_service
from services.patient_clustering_service import clustering_service
from services.rl_service import rl_service
from services.forecast_service import forecast_service
from services.csv_service import csv_service

FORECAST_RETRAIN_INTERVAL_SECONDS = 24 * 60 * 60  # daily


async def _forecast_retrain_loop():
    """Background job: retrain the disease-forecast RandomForest once a day
    and persist it, so /api/forecast never trains on the request path.
    Runs the (blocking, CPU-bound) training in a worker thread to avoid
    stalling the event loop."""
    while True:
        await asyncio.sleep(FORECAST_RETRAIN_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(forecast_service.retrain)
            print("✓ Forecast model retrained on schedule")
        except Exception as e:
            print(f"⚠️  Scheduled forecast retrain failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    print("\n" + "="*60)
    print("Starting AYUSH ML Backend API")
    print("="*60)

    # Initialize ISHAAyush Treatment Service
    ISHAAyush_service.initialize()

    # Initialize Forecast Service (loads a cached model if fresh, else trains once)
    forecast_service.initialize()
    retrain_task = asyncio.create_task(_forecast_retrain_loop())

    print("\n✓ Backend API ready!")
    print("="*60 + "\n")

    yield

    # Cleanup on shutdown
    retrain_task.cancel()
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
    # No wildcard: browsers reject `*` with credentials, and cookie auth
    # requires allow_credentials=True. Extra origins go in ALLOWED_ORIGINS.
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Added after CORS so CORS wraps it (Starlette applies middleware in reverse
# add-order) and 401/403 responses still carry CORS headers.
from security import RBACMiddleware
app.add_middleware(RBACMiddleware)


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
    ISHAAyush_health = ISHAAyush_service.health_check()
    
    return {
        "status": "healthy" if ISHAAyush_health["initialized"] else "degraded",
        "models_loaded": ISHAAyush_health["dataset_loaded"],
        "storage": "csv",
        "version": "3.0.0"
    }


@app.get("/api/diseases", tags=["Treatment Recommendations"])
async def get_disease_list(q: str = None):
    """
    Get list of all disease names from the ISHAAyush dataset.
    
    Args:
        q: Optional search query to filter disease names
        
    Returns:
        List of disease name strings
    """
    diseases = ISHAAyush_service.get_disease_list()
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
    suggestions = ISHAAyush_service.get_suggestions(q, limit=limit)
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


@app.post("/api/recommend", tags=["Treatment Recommendations"])
async def get_recommendation(patient: PatientProfile):
    """
    Get personalized AYUSH treatment recommendation using Hybrid Engine (Clustering + RL + Codified Data).

    Args:
        patient: Patient profile with disease, symptoms, prakriti, vikriti, severity, age, gender

    Returns:
        Treatment plan with herbs, yoga, diet, lifestyle, formulation, prevention, prognosis.
        Also includes `original_ai_plan` key mirroring the full recommendation for frontend tracking.
    """
    try:
        patient_data = patient.model_dump()
        recommendation = hybrid_service.get_recommendation(patient_data)
        # Mirror the recommendation as original_ai_plan so the frontend can store
        # the unmodified AI plan and later send it back with any doctor edits.
        if isinstance(recommendation, dict):
            recommendation["original_ai_plan"] = {k: v for k, v in recommendation.items() if k != "original_ai_plan"}
        else:
            # Pydantic model — convert to dict and add the key
            rec_dict = recommendation.model_dump() if hasattr(recommendation, "model_dump") else dict(recommendation)
            rec_dict["original_ai_plan"] = {k: v for k, v in rec_dict.items() if k != "original_ai_plan"}
            return rec_dict
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
    Manually trigger the non-RL-reward parts of the retraining pipeline:
    1. Retrain Patient Clustering (K-Means) on all historical AHIMS data.

    Does NOT call retrain_from_feedback(): production Q-values are only ever moved
    by a confirmed follow-up outcome via POST /api/visits/{visit_id}/outcome, never
    by the doctor's initial rating at prescribe time.

    Does NOT call retrain_from_outcomes(): that batch/backfill path would mark
    ClinicalOutcomeScore rows as is_retrained=True before the follow-up outcome
    endpoint has a chance to close them with real vitals + doctor judgment.
    retrain_from_outcomes() is intentionally kept out of the auto-trigger to avoid
    racing with the live apply_followup_outcome path.
    """
    try:
        cluster_res = clustering_service.retrain_clusters()

        return {
            "status": "success",
            "clustering": cluster_res,
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
                    "confidence_lower": entry.get("confidence_lower"),
                    "confidence_upper": entry.get("confidence_upper"),
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

@app.get("/api/analytics/case-details", tags=["Public Health Analytics"])
async def get_case_details(
    disease: str,
    cities: str = None,
    start_date: str = None,
    end_date: str = None,
    days: int = None,
    limit: int = 100,
):
    """
    Case-level drill-down behind a signal (alert, emerging threat, hotspot, or
    cluster) — the patient visits that actually produced the aggregate number.
    `cities` is a comma-separated list. `days` is a relative window (clusters);
    `start_date`/`end_date` is an explicit window (alerts/emerging threats);
    omit both for an all-time lookup (hotspots).
    """
    try:
        city_list = [c.strip() for c in cities.split(",")] if cities else None
        cases, total_count = analytics_service.get_case_details(
            disease=disease, cities=city_list, start_date=start_date,
            end_date=end_date, days=days, limit=limit,
        )
        entry = get_full_name(disease)
        return {
            "cases": cases,
            "total_count": total_count,
            "disease": disease,
            "devanagari": entry["devanagari"],
            "iast": entry["iast"],
            "hindi": entry["hindi"],
            "english": entry["english"],
        }
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
async def get_dashboard_summary(days: Optional[int] = None):
    """Get overall analytics dashboard summary, optionally scoped to the last `days` days"""
    try:
        summary = analytics_service.get_dashboard_summary(days=days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from services.spatial_service import spatial_service

@app.get("/api/analytics/weekly-alerts", response_model=list[AlertResponse], tags=["Public Health Analytics"])
async def get_weekly_alerts():
    """
    Weekly rolling Z-score anomaly detection.
    Detects disease surges 3–4 weeks earlier than the monthly detector.
    Uses a 6-week recent window vs 20-week baseline window.
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
            cluster["hindi"]      = entry["hindi"]
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




@app.get("/api/analytics/model-info", tags=["Public Health Analytics"])
async def get_analytics_model_info():
    """
    Returns metadata, parameters, and live stats for all 4 analytics models:
    DBSCAN Spatial Clustering, Z-Score+CUSUM Anomaly Detection,
    GNN Graph Diffusion, and Disease Forecaster (RandomForest).
    """
    result: dict = {}

    # ── DBSCAN ────────────────────────────────────────────────────────────────
    try:
        cluster_summary = spatial_service.get_cluster_summary(days=90)
        result["dbscan"] = {
            "name": "DBSCAN Spatial Clustering",
            "type": "Unsupervised Geospatial Clustering",
            "algorithm": "Density-Based Spatial Clustering of Applications with Noise",
            "params": {
                "eps_km": cluster_summary.get("eps_km", 400),
                "min_samples": cluster_summary.get("min_samples", 2),
                "distance_metric": "Haversine (great-circle)",
                "max_cities_per_cluster": 6,
                "period_days": 90,
            },
            "stats": {
                "total_clusters": cluster_summary.get("total_clusters", 0),
                "total_hotspots": cluster_summary.get("total_hotspots", 0),
                "diseases_tracked": cluster_summary.get("diseases_tracked", 0),
            },
            "clusters": cluster_summary.get("clusters", [])[:12],
        }
    except Exception as e:
        result["dbscan"] = {"error": str(e), "name": "DBSCAN Spatial Clustering"}

    # ── Anomaly Detection ─────────────────────────────────────────────────────
    try:
        alerts = analytics_service.detect_anomalies()
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for a in alerts:
            s = a.get("severity", "Low")
            if s in severity_counts:
                severity_counts[s] += 1

        disease_scores = [
            {
                "disease": a["disease"],
                "z_score": a["z_score"],
                "severity": a["severity"],
                "cusum_value": a["cusum_value"],
                "triggered_by": a.get("triggered_by", ""),
                "pct_increase": a.get("pct_increase", 0),
                "surge_month": a.get("surge_month", ""),
            }
            for a in alerts[:15]
        ]

        result["anomaly"] = {
            "name": "Statistical Anomaly Detection",
            "type": "Z-Score + CUSUM Dual Detector",
            "algorithms": ["Monthly Z-Score (leave-one-out baseline)", "CUSUM (Cumulative Sum)"],
            "params": {
                "z_threshold": 2.0,
                "cusum_k_factor": 0.5,
                "min_recent_cases": 3,
                "baseline_window": "6 months",
                "severity_thresholds": {
                    "Low":      "Z ≥ 1.5  (< 6.7% probability under H0)",
                    "Medium":   "Z ≥ 2.0  (< 2.3%)",
                    "High":     "Z ≥ 2.5  (< 0.6%)",
                    "Critical": "Z ≥ 3.5  (< 0.02%)",
                },
            },
            "stats": {
                "total_alerts": len(alerts),
                "by_severity": severity_counts,
            },
            "disease_scores": disease_scores,
        }
    except Exception as e:
        result["anomaly"] = {"error": str(e), "name": "Statistical Anomaly Detection"}

    # ── GNN Diffusion ─────────────────────────────────────────────────────────
    try:
        graph_summary = gnn_service.get_spread_graph_summary()
        result["gnn"] = {
            "name": "Disease Spread Simulation",
            "type": "Graph Diffusion (Phase 1)",
            "phase_note": "Phase 2: PyTorch Geometric ST-GNN after 6+ months of live data",
            "params": {
                "transmission_rate": 0.25,
                "adjacency_threshold_km": 300,
                "forecast_days": 7,
                "edge_weight_formula": "1 − (distance_km / 300)",
                "distance_metric": "Haversine",
            },
            "stats": {
                "graph_nodes": graph_summary.get("nodes", 0),
                "graph_edges": graph_summary.get("edges", 0),
                "top_hubs": graph_summary.get("top_hubs", []),
            },
        }
    except Exception as e:
        result["gnn"] = {"error": str(e), "name": "Disease Spread Simulation"}

    # ── Disease Forecaster ────────────────────────────────────────────────────
    try:
        fc = forecast_service.forecaster
        trained = fc is not None and fc.forecast_model is not None

        feature_cols = [
            "disease_enc", "category_enc", "season_enc",
            "month_num", "ritu_sandhi",
            "cases_lag1", "cases_lag2", "cases_lag3",
            "avg_severity",
        ]

        importances = []
        if trained and hasattr(fc.forecast_model, "feature_importances_"):
            imp = fc.forecast_model.feature_importances_
            importances = [
                {"feature": name, "importance": round(float(v), 4)}
                for name, v in sorted(zip(feature_cols, imp), key=lambda x: -x[1])
            ]

        diseases_count = 0
        training_samples = 0
        months_of_data = 0
        if trained and fc.last_data is not None:
            diseases_count = len(fc.last_data)
        if trained and fc.trends is not None and not fc.trends.empty:
            training_samples = int(len(fc.trends))
            if "month" in fc.trends.columns:
                months_of_data = int(fc.trends["month"].nunique())

        from disease_forecaster import MODEL_PATH
        model_age_hours = None
        if os.path.exists(MODEL_PATH):
            age_secs = time.time() - os.path.getmtime(MODEL_PATH)
            model_age_hours = round(age_secs / 3600, 1)

        result["forecaster"] = {
            "name": "Disease Forecaster",
            "type": "Random Forest Regressor",
            "params": {
                "n_estimators": 200,
                "max_depth": 10,
                "random_state": 42,
                "n_jobs": -1,
                "retrain_interval": "24 hours",
                "forecast_horizon": "3 months",
                "feature_count": len(feature_cols),
                "features": feature_cols,
            },
            "ritu_map": {
                "Shishira": {"months": "Jan–Feb", "label": "Winter", "emoji": "❄️"},
                "Vasanta":  {"months": "Mar–Apr", "label": "Spring", "emoji": "🌸"},
                "Grishma":  {"months": "May–Jun", "label": "Summer", "emoji": "☀️"},
                "Varsha":   {"months": "Jul–Aug", "label": "Monsoon", "emoji": "🌧️"},
                "Sharad":   {"months": "Sep–Oct", "label": "Autumn", "emoji": "🍂"},
                "Hemanta":  {"months": "Nov–Dec", "label": "Pre-winter", "emoji": "🌾"},
            },
            "sandhi_months": [1, 3, 5, 7, 9, 11],
            "stats": {
                "trained": trained,
                "diseases_tracked": diseases_count,
                "training_samples": training_samples,
                "months_of_data": months_of_data,
                "model_age_hours": model_age_hours,
            },
            "feature_importance": importances,
        }
    except Exception as e:
        result["forecaster"] = {"error": str(e), "name": "Disease Forecaster"}

    result["generated_at"] = datetime.datetime.utcnow().isoformat()
    return result


from services.registration_agent import registration_agent_router
from services.treatment_agent import treatment_agent_router
from services.admin_router import admin_router
from services.auth_router import auth_router
from services.staff_router import staff_router

app.include_router(registration_agent_router, prefix="/api/copilot/registration", tags=["Copilot Agent"])
app.include_router(treatment_agent_router, prefix="/api/copilot/treatment", tags=["Copilot Agent"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(staff_router, prefix="/api/staff", tags=["Staff"])

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


_VITALS_FIELDS = ("bpm", "sugar_level", "spo2", "temperature", "systolic_bp", "diastolic_bp")


def _extract_vitals(record: dict) -> dict:
    return {field: record.get(field) for field in _VITALS_FIELDS}


def _split_prescription_text(text: str | None) -> list[str]:
    """Split a comma/period-separated free-text field (legacy prescription format) into list items."""
    if not text:
        return []
    return [p.strip() for p in re.split(r"[,.]", text) if p.strip()]


def _extract_previous_treatment_plan(visit_id: str, raw_prescription: str) -> dict | None:
    """Best-effort reconstruction of a visit's prescribed plan, for follow-up auto-load.

    Real doctor-saved prescriptions store the full structured plan under prescription["ai_plan"].
    Older/synthetic records instead carry plain-text herbs/yoga/diet on the linked AyushTreatment
    row (no "ai_plan" wrapper) — fall back to that so follow-ups on that data still get something
    editable, rather than silently showing a blank panel.
    """
    if raw_prescription and raw_prescription != "{}":
        try:
            parsed = json.loads(raw_prescription)
            plan = parsed.get("ai_plan") if isinstance(parsed, dict) else None
            if isinstance(plan, dict) and plan:
                return plan
        except Exception:
            pass  # malformed JSON — fall through to the AyushTreatment lookup below

    from models import SessionLocal, AyushTreatment
    with SessionLocal() as db:
        treatment = db.query(AyushTreatment).filter(AyushTreatment.medical_record_id == visit_id).first()

    if not treatment:
        return None

    herbs = [{"name": h, "dosage": "", "benefits": ""} for h in _split_prescription_text(treatment.herbs_prescribed)]
    yoga = [{"practice": y, "duration": "", "benefits": ""} for y in _split_prescription_text(treatment.yoga_prescribed)]
    diet = _split_prescription_text(treatment.diet_plan)
    if not herbs and not yoga and not diet:
        return None
    return {"herbs": herbs, "yoga": yoga, "diet": diet, "lifestyle": []}


def _build_previous_visit_summary(parent_visit_id: str | None) -> dict | None:
    """For a follow-up visit, load the prior visit's diagnosis + vitals + last prescribed plan."""
    if not parent_visit_id:
        return None
    parent = csv_service.get_medical_record_by_id(parent_visit_id)
    if not parent:
        return None

    previous_plan = _extract_previous_treatment_plan(parent_visit_id, parent.get("prescription", ""))

    return {
        "visitId": parent_visit_id,
        "visitDate": parent.get("visit_date"),
        "diagnosis": parent.get("diagnosis", ""),
        "symptoms": parent.get("symptoms", ""),
        "vitals": _extract_vitals(parent),
        "treatmentPlan": previous_plan,
    }


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

        parent_visit_id = record.get("parent_visit_id")
        previous_visit = _build_previous_visit_summary(parent_visit_id)

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
            "comorbidities": record.get("comorbidities", ""),
            "parentVisitId": parent_visit_id,
            "vitals": _extract_vitals(record),
            "previousVisit": previous_visit,
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
                "parentVisitId": record.get("parent_visit_id"),
                "vitals": _extract_vitals(record),
            },
            "previousVisit": _build_previous_visit_summary(record.get("parent_visit_id")),
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
    Get patients, optionally filtered by status.

    Query params:
      - status=pending   → doctor's queue: visits awaiting a prescription
                           (first-time or follow-up) + never-consulted patients
      - status=completed → visits already prescribed
      - (none)           → all patients
    """
    try:
        if status == "pending":
            patients = csv_service.get_pending_visit_queue()
        elif status == "completed":
            patients = csv_service.get_completed_diagnoses_summary()
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


@app.get("/api/patients/{patient_id}/conditions", tags=["Patient Management"])
async def get_patient_conditions(patient_id: str):
    """
    Distinct past diagnoses for a patient (diagnosis name + visit id/date only) —
    deliberately excludes symptoms/notes/prescription/vitals. Powers the
    New-vs-Follow-up picker for ANY role, including receptionists, who are not
    otherwise allowed to view a patient's full clinical history.
    """
    try:
        return csv_service.get_patient_conditions(patient_id)
    except Exception as e:
        print(f"Error fetching patient conditions: {e}")
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


@app.post("/api/gemma4-turn", tags=["Voice Pipeline"])
async def gemma4_turn(
    audio: Optional[UploadFile] = File(None),
    flow: str = Form("registration"),
    conversation_history: Optional[str] = Form(None),
    user_text_prompt: Optional[str] = Form(None),
):
    """
    Configurable alternative to /api/transcribe + /api/translate: forwards
    the turn straight to the Modal Gemma-4-12B voice service, which
    understands audio natively (chunking internally for recordings over
    Gemma's ~30s per-clip cap) and also accepts plain typed text, returning
    an acknowledgement + structured JSON extraction in one hop, instead of
    the two-hop ASR + IndicTrans2 pipeline. This is a separate flow from
    Cloud (STT+Phi-4) — it does not touch the AG-UI/Phi-4 workflow at all.

    Every call is logged via RunLogger (step "gemma4_turn") so a bad
    extraction can be replayed later: the raw audio is saved to VOICE_DIR
    and the exact history/prompt sent to Modal plus its raw pre-parse
    output are recorded alongside the parsed result.
    """
    modal_gemma_url = os.getenv("MODAL_GEMMA_URL")
    if not modal_gemma_url:
        raise HTTPException(status_code=500, detail="MODAL_GEMMA_URL not configured in backend .env")

    if audio is None and not user_text_prompt:
        raise HTTPException(status_code=400, detail="Provide audio, user_text_prompt, or both")

    disease_str = _approved_disease_prompt_list() if flow == "treatment" else None
    system_prompt = gemma4_prompts.get_system_prompt(flow, disease_list=disease_str)

    rl = RunLogger()
    voice_path = None
    audio_bytes = None
    if audio is not None:
        audio_bytes = await audio.read()
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:23].replace(":", "-")
        ext = (audio.filename or "audio.webm").rsplit(".", 1)[-1]
        voice_path = os.path.join(VOICE_DIR, f"{ts}_{rl.run_id}.{ext}")
        with open(voice_path, "wb") as f:
            f.write(audio_bytes)
        rl.set_voice_file(voice_path)

    gemma_input = {
        "flow": flow,
        "system_prompt": system_prompt,
        "voice_file": voice_path,
        "user_text_prompt": user_text_prompt,
        "conversation_history": json.loads(conversation_history) if conversation_history else [],
        "modal_gemma_url": modal_gemma_url,
    }

    try:
        async with httpx.AsyncClient(timeout=GEMMA_REQUEST_TIMEOUT) as client:
            form_data = {"system_prompt": system_prompt}
            if conversation_history:
                form_data["conversation_history"] = conversation_history
            if user_text_prompt:
                form_data["user_text_prompt"] = user_text_prompt
            files = {}
            if audio_bytes is not None:
                files["file"] = (audio.filename or "audio.wav", audio_bytes, audio.content_type or "audio/wav")
            resp = await client.post(modal_gemma_url, data=form_data, files=files or None)

        if resp.status_code != 200:
            rl.update_step(
                "gemma4_turn",
                input=gemma_input,
                output=None,
                error=f"Modal Gemma-4 error {resp.status_code}: {resp.text[:500]}",
            )
            rl.finalize()
            raise HTTPException(status_code=resp.status_code, detail=f"Modal Gemma-4 error: {resp.text[:300]}")

        data = resp.json()
        data["extracted"] = _normalize_extracted_treatment_disease(flow, data.get("extracted"))
        if flow == "treatment" and isinstance(data.get("extracted"), dict):
            data["disease_match"] = {
                "raw": data["extracted"].get("disease_raw"),
                "matched": data["extracted"].get("disease"),
            }
        rl.update_step("gemma4_turn", input=gemma_input, output=data, error=None)
        rl.finalize()
        return data

    except httpx.TimeoutException:
        rl.update_step("gemma4_turn", input=gemma_input, output=None, error="Modal Gemma-4 request timed out")
        rl.finalize()
        raise HTTPException(status_code=504, detail="Modal Gemma-4 request timed out")
    except HTTPException:
        raise
    except Exception as exc:
        rl.update_step("gemma4_turn", input=gemma_input, output=None, error=str(exc))
        rl.finalize()
        raise HTTPException(status_code=500, detail=f"Gemma-4 turn failed: {exc}")


def _parse_structured_reply(full_text: str):
    """Pulls a fenced ```json block out of the model's reply and parses it.
    Tolerates a missing or malformed block — falls back to (text, None).
    Mirrors backend/modal_script/modal_gemma4_12b.py's parse_structured_reply
    so both turn endpoints share the same extraction contract."""
    match = re.search(r"```json\s*([\s\S]*?)\s*```", full_text, re.IGNORECASE)
    if not match:
        return full_text.strip(), None

    reply = (full_text[: match.start()] + full_text[match.end():]).strip()
    try:
        parsed = json.loads(match.group(1))
        return (reply, parsed) if isinstance(parsed, dict) else (reply, None)
    except json.JSONDecodeError:
        return reply, None


def _approved_disease_prompt_list() -> str:
    diseases = ISHAAyush_service.get_disease_list()
    return "\n".join(f"- {name}" for name in diseases)


def _normalize_extracted_treatment_disease(flow: str | None, extracted):
    if flow != "treatment" or not isinstance(extracted, dict) or "disease" not in extracted:
        return extracted

    raw_disease = extracted.get("disease")
    if raw_disease is None:
        return extracted

    raw_text = str(raw_disease).strip()
    if not raw_text:
        extracted["disease"] = None
        return extracted

    matched = ISHAAyush_service.match_disease(raw_text, threshold=85)
    print(f"[disease_match] raw='{raw_text}' → matched='{matched}'")
    extracted["disease"] = matched
    extracted["disease_raw"] = raw_text
    return extracted


@app.post("/api/phi4-turn", tags=["Voice Pipeline"])
async def phi4_turn(
    flow: str = Form("registration"),
    conversation_history: Optional[str] = Form(None),
    user_text_prompt: str = Form(...),
):
    """
    Text-turn endpoint for the Phi-4 (vLLM-hosted) assistant — same
    request/response contract as /api/gemma4-turn (one acknowledgement
    sentence + a fenced ```json extraction block), so the frontend's
    GemmaVoiceChatPanel can drive either model interchangeably. Phi-4 has
    no native audio understanding, so callers must transcribe first (the
    panel's mic button already does this via /api/transcribe when Phi-4
    is selected).
    """
    from llama_index.core.llms import ChatMessage, MessageRole
    from utils.llm_config import get_llm

    history = []
    if conversation_history:
        try:
            history = json.loads(conversation_history)
        except json.JSONDecodeError:
            history = []

    disease_list = ISHAAyush_service.get_disease_list() if flow == "treatment" else None
    system_prompt = phi4_prompts.get_system_prompt(flow, disease_list=disease_list)
    messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]
    for turn in history:
        role = MessageRole.ASSISTANT if turn.get("role") == "assistant" else MessageRole.USER
        content = turn.get("content", "")
        if content:
            messages.append(ChatMessage(role=role, content=content))
    messages.append(ChatMessage(role=MessageRole.USER, content=user_text_prompt))

    try:
        llm = get_llm()
        response = await llm.achat(messages)
        full_text = response.message.content or ""
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Phi-4 turn failed: {exc}")

    reply, extracted = _parse_structured_reply(full_text)
    extracted = _normalize_extracted_treatment_disease(flow, extracted)
    return {
        "reply": reply,
        "extracted": extracted,
        "tokens_generated": 0,
        "chunks_processed": 0,
        "audio_duration_seconds": 0.0,
    }


# ── AI Treatment Engine Revamp Endpoints ──────────────────────────────────────

from fastapi import Body
from pydantic import BaseModel as PydanticBase

@app.post("/api/ml/demo-submit", tags=["ML"])
async def demo_submit(
    disease: str = Body(..., embed=True),
    namc_code: str = Body("", embed=True),
    state_key: str = Body("", embed=True),
    prakriti: str = Body("Vata", embed=True),
    vikriti: str = Body("Vata", embed=True),
    original_plan: dict = Body({}, embed=True),
    final_plan: dict = Body({}, embed=True),
    rating: Optional[str] = Body(None, embed=True),
    demo_session: bool = Body(True, embed=True),
):
    """
    Save a demo prescription feedback row without requiring a real patient record.
    Returns feedback_id for use with retrain-instant.
    """
    import uuid, json as _json
    from models import SessionLocal, TreatmentFeedback as TFModel

    # Diff every plan category (herbs, yoga, diet, lifestyle) as canonical action keys
    added_herbs, removed_herbs = rl_service.compute_plan_diff(original_plan, final_plan)

    # Normalize UI rating labels to the stored positive/negative convention
    # used by the reward table (matches the doctor prescribe flow)
    rating_map = {"accurate": "positive", "needs changes": "negative"}
    rating = rating_map.get((rating or "").strip().lower(), rating)

    feedback_id = str(uuid.uuid4())
    with SessionLocal() as db:
        fb = TFModel(
            id=feedback_id,
            patient_id="demo-patient",
            medical_record_id="demo-record",
            doctor_rating=rating or "",
            ml_context=_json.dumps({
                "namc_code": namc_code,
                "prakriti":  prakriti,
                "vikriti":   vikriti,
                "disease":   disease,
            }),
            ai_plan=_json.dumps(original_plan),
            original_ai_plan=_json.dumps(original_plan),
            final_plan=_json.dumps(final_plan),
            added_herbs=_json.dumps(added_herbs),
            removed_herbs=_json.dumps(removed_herbs),
            demo_session=demo_session,
            is_retrained=False,
        )
        db.add(fb)
        db.commit()

    return {
        "feedback_id": feedback_id,
        "added_herbs": added_herbs,
        "removed_herbs": removed_herbs,
        "status": "saved",
    }


@app.post("/api/ml/retrain-instant", tags=["ML"])
async def retrain_instant(
    feedback_id: str = Body(..., embed=True),
    demo_session: bool = Body(False, embed=True),
    background_tasks: BackgroundTasks = None,
):
    """
    Perform a single-row Q-update for the given feedback row.
    Returns updated Q-values per herb for frontend animation.
    """
    from models import SessionLocal
    with SessionLocal() as db:
        result = rl_service.retrain_instant(feedback_id, db, demo_mode=demo_session)
    return result


@app.post("/api/ml/demo-reset", tags=["ML"])
async def demo_reset():
    """Reset the demo Q-table by copying from the production Q-table."""
    return rl_service.reset_demo_q_table()


@app.get("/api/model/q-table-state", tags=["Model"])
async def get_q_table_state(
    namc_code: Optional[str] = None,
    prakriti: Optional[str] = None,
    vikriti: Optional[str] = None,
    demo_session: bool = False,
):
    """
    Inspect the current Q-table state.
    If namc_code + prakriti + vikriti are provided, returns actions for that state.
    Otherwise returns a summary of all states.
    """
    # Always use real Q-table — demo writes directly into it
    q_table = rl_service.q_table

    if namc_code and prakriti is not None and vikriti is not None:
        state_key = rl_service._get_state_key(namc_code, prakriti, vikriti)
        actions = q_table.get(state_key, {})
        return {
            "state_key": state_key,
            "actions": [
                {"name": k, "q_value": round(v, 4), "is_learned": v > 0}
                for k, v in sorted(actions.items(), key=lambda x: -x[1])
            ],
            "total_prescriptions": len(actions),
        }
    elif namc_code:
        # Return all states and actions matching this namc_code prefix
        # (skip legacy/malformed keys that don't encode a valid prakriti_vikriti pair)
        states_list = []
        for sk, actions in q_table.items():
            if sk.startswith(f"{namc_code}_"):
                parts = sk.rsplit("_", 2)
                if len(parts) != 3 or not _DOSHA_RE.match(parts[1]) or not _DOSHA_RE.match(parts[2]):
                    continue
                p = parts[1]
                v = parts[2]
                states_list.append({
                    "state_key": sk,
                    "prakriti": p,
                    "vikriti": v,
                    "actions": [
                        {"name": k, "q_value": round(val, 4), "is_learned": val > 0}
                        for k, val in sorted(actions.items(), key=lambda x: -x[1])
                    ]
                })
        return {
            "namc_code": namc_code,
            "states": sorted(states_list, key=lambda x: x["state_key"])
        }
    else:
        return {
            "states": [
                {"state_key": sk, "n_actions": len(acts), "max_q": round(max(acts.values(), default=0), 4)}
                for sk, acts in q_table.items()
            ],
            "total_states": len(q_table),
        }


_DOSHA_RE = re.compile(r"^(vata|pitta|kapha)(-(vata|pitta|kapha))?$", re.IGNORECASE)

# Lazily built NAMC_CODE → display name lookup from the codified CSV
_namc_name_cache: dict | None = None

def _get_namc_names() -> dict:
    global _namc_name_cache
    if _namc_name_cache is not None:
        return _namc_name_cache
    _namc_name_cache = {}
    if ISHAAyush_service.df is not None:
        for _, row in ISHAAyush_service.df.iterrows():
            code = str(row.get("NAMC_CODE", "")).strip()
            if code:
                name = str(row.get("Name English", "") or row.get("NAMC_term", "")).strip()
                if code not in _namc_name_cache:
                    _namc_name_cache[code] = name or code
    return _namc_name_cache


@app.get("/api/model/learning-coverage", tags=["Model"])
async def get_learning_coverage():
    """
    Report which diseases have RL learning data (Q-table entries),
    with per-category breakdowns (herbs, yoga, diet, lifestyle).
    """
    q_table = rl_service.q_table
    namc_names = _get_namc_names()

    # Count unique NAMC codes in the catalog
    total_catalog = len(namc_names) if namc_names else 0

    # Group Q-table entries by NAMC code
    disease_map: dict = {}   # namc_code → aggregated info
    legacy_states = 0

    for state_key, actions in q_table.items():
        parts = state_key.rsplit("_", 2)
        if len(parts) != 3 or not _DOSHA_RE.match(parts[1]) or not _DOSHA_RE.match(parts[2]):
            legacy_states += 1
            continue

        namc_code = parts[0]
        entry = disease_map.setdefault(namc_code, {
            "namc_code": namc_code,
            "name": namc_names.get(namc_code, namc_code),
            "n_states": 0,
            "n_actions": 0,
            "n_learned": 0,
            "herbs_learned": 0,
            "yoga_learned": 0,
            "diet_learned": 0,
            "lifestyle_learned": 0,
            "max_q": 0.0,
            "top_learned": [],
        })
        entry["n_states"] += 1
        entry["n_actions"] += len(actions)

        for name, q_val in actions.items():
            if q_val > 0:
                entry["n_learned"] += 1
                if q_val > entry["max_q"]:
                    entry["max_q"] = q_val
                # Categorise
                if name.startswith("yoga:"):
                    entry["yoga_learned"] += 1
                elif name.startswith("diet:"):
                    entry["diet_learned"] += 1
                elif name.startswith("lifestyle:"):
                    entry["lifestyle_learned"] += 1
                else:
                    entry["herbs_learned"] += 1
                entry["top_learned"].append({"name": name, "q_value": round(q_val, 4)})

    # Finalise per-disease entries
    diseases = []
    learned_count = learning_count = 0
    total_learned_actions = 0

    for entry in disease_map.values():
        entry["max_q"] = round(entry["max_q"], 4)
        entry["status"] = "learned" if entry["n_learned"] > 0 else "learning"
        # Keep top 5 by Q-value
        entry["top_learned"] = sorted(entry["top_learned"], key=lambda x: -x["q_value"])[:5]
        if entry["status"] == "learned":
            learned_count += 1
        else:
            learning_count += 1
        total_learned_actions += entry["n_learned"]
        diseases.append(entry)

    # Sort: learned first (by n_learned desc), then learning (by n_states desc)
    diseases.sort(key=lambda d: (-1 if d["status"] == "learned" else 0, -d["n_learned"], -d["n_states"]))

    return {
        "summary": {
            "total_catalog": total_catalog,
            "diseases_with_data": len(diseases),
            "learned": learned_count,
            "learning": learning_count,
            "total_learned_actions": total_learned_actions,
            "total_states": len(q_table),
            "legacy_states": legacy_states,
        },
        "diseases": diseases,
    }

@app.get("/api/model/state-history/{state_key}", tags=["Model"])
async def get_state_history(state_key: str):
    """Replay Q-value history for a state from TreatmentFeedback rows."""
    from models import SessionLocal, TreatmentFeedback
    import json as _json
    import math

    with SessionLocal() as db:
        rows = db.query(TreatmentFeedback).filter(
            TreatmentFeedback.ml_context.contains(state_key.split("_")[0])
        ).order_by(TreatmentFeedback.created_at).all()

    events = []
    running_q = {}  # simulate Q-table replay

    for i, fb in enumerate(rows):
        try:
            ctx = _json.loads(fb.ml_context or "{}")
            namc = ctx.get("namc_code", "")
            prak = ctx.get("prakriti", "")
            vikr = ctx.get("vikriti", "")
            sk   = f"{namc}_{prak}_{vikr}"
            if sk != state_key:
                continue

            final_plan    = _json.loads(fb.final_plan or fb.ai_plan or "{}")
            added_herbs   = _json.loads(fb.added_herbs or "[]")
            removed_herbs = _json.loads(fb.removed_herbs or "[]")
            doctor_rating = fb.doctor_rating or ""

            all_herbs = list(set(
                [h.get("name", "") if isinstance(h, dict) else str(h) for h in final_plan.get("herbs", [])]
                + removed_herbs
            ))

            q_updates = {}
            for herb in filter(None, all_herbs):
                reward  = rl_service._compute_herb_reward(herb, added_herbs, removed_herbs, doctor_rating)
                old_q   = running_q.get(herb, 0.0)
                new_q   = old_q + 0.1 * (reward - old_q)
                running_q[herb] = new_q
                q_updates[herb] = {"before": round(old_q, 4), "after": round(new_q, 4), "reward": round(reward, 2)}

            events.append({
                "visit_number":   len(events) + 1,
                "date":           fb.created_at.isoformat() if fb.created_at else None,
                "original_herbs": _json.loads(fb.original_ai_plan or "{}").get("herbs", []) if fb.original_ai_plan else [],
                "added_herbs":    added_herbs,
                "removed_herbs":  removed_herbs,
                "doctor_rating":  doctor_rating,
                "q_updates":      q_updates,
            })
        except Exception:
            continue

    return {"state_key": state_key, "events": events}


class OutcomeRequest(PydanticBase):
    medical_record_id: str
    followup_value: float
    adherence: Optional[str] = None
    notes: Optional[str] = None


_VITAL_DIRECTION = {
    "HbA1c (%)": False,
    "Systolic BP (mmHg)": False,
    "BMI (kg/m²)": False,
    "PEFR (L/min)": True,
    "Symptom Severity (1-10)": False,
}
_VITAL_NORMALISER = {
    "HbA1c (%)": 10.0,
    "Systolic BP (mmHg)": 15.0,
    "BMI (kg/m²)": 10.0,
    "PEFR (L/min)": 20.0,
    "Symptom Severity (1-10)": 30.0,
}


@app.post("/api/outcomes", tags=["Outcomes"])
async def save_outcome(req: OutcomeRequest, background_tasks: BackgroundTasks):
    """
    Record a clinical follow-up outcome value for a visit and compute the RL reward.
    Triggers background RL retraining from outcomes after saving.
    """
    from models import SessionLocal, ClinicalOutcomeScore
    with SessionLocal() as db:
        cos = db.query(ClinicalOutcomeScore).filter(
            ClinicalOutcomeScore.medical_record_id == req.medical_record_id
        ).first()
        if not cos:
            raise HTTPException(status_code=404, detail="No pending outcome for this visit")

        cos.followup_value   = req.followup_value
        higher_is_better     = _VITAL_DIRECTION.get(cos.target_vital, False)
        normaliser           = _VITAL_NORMALISER.get(cos.target_vital, 30.0)

        if cos.baseline_value is not None:
            if higher_is_better:
                pct = ((req.followup_value - cos.baseline_value) / max(cos.baseline_value, 0.001)) * 100
            else:
                pct = ((cos.baseline_value - req.followup_value) / max(cos.baseline_value, 0.001)) * 100
        else:
            pct = 0.0

        cos.percentage_change = round(pct, 2)
        cos.calculated_reward = round(min(1.0, max(0.0, pct / normaliser)), 4)
        cos.is_retrained      = False
        db.commit()
        outcome_id            = cos.id
        calculated_reward     = cos.calculated_reward

    background_tasks.add_task(rl_service.retrain_from_outcomes)
    return {
        "outcome_id":        outcome_id,
        "percentage_change": pct,
        "calculated_reward": calculated_reward,
    }


class FollowupOutcomeRequest(PydanticBase):
    doctor_reported_outcome: str  # "improved" | "no_change" | "worsened"


def _resolve_vital_reading(record, target_vital: str):
    """
    Read the value on a MedicalRecord matching target_vital. No PEFR or BMI column
    exists in the live vitals form, so those (and the generic Symptom Severity
    bucket) fall back to the `severity` field the doctor fills on every visit.
    """
    if target_vital == "HbA1c (%)":
        return record.sugar_level
    if target_vital == "Systolic BP (mmHg)":
        return record.systolic_bp
    try:
        return float(record.severity) if record.severity not in (None, "") else None
    except (TypeError, ValueError):
        return None


@app.post("/api/visits/{visit_id}/outcome", tags=["Outcomes"])
async def save_followup_outcome(visit_id: str, req: FollowupOutcomeRequest):
    """
    Close out the PARENT visit's pending outcome using this follow-up visit's just-saved
    vitals plus the doctor's explicit judgment of whether the previous plan worked. This
    (together with the isolated Live Demo tab) is the only path that moves a production
    Q-value — reward always comes from a confirmed follow-up outcome, never from the
    doctor's rating at prescribe time. Call this after POST /api/prescribe has saved this
    follow-up visit's vitals.
    """
    from models import SessionLocal, MedicalRecord, ClinicalOutcomeScore

    if req.doctor_reported_outcome not in ("improved", "no_change", "worsened"):
        raise HTTPException(status_code=400, detail="doctor_reported_outcome must be improved, no_change, or worsened")

    with SessionLocal() as db:
        visit = db.query(MedicalRecord).filter(MedicalRecord.id == visit_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail="Visit not found")
        if not visit.parent_visit_id:
            raise HTTPException(status_code=400, detail="This visit has no parent visit to close an outcome for")

        parent = db.query(MedicalRecord).filter(MedicalRecord.id == visit.parent_visit_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent visit not found")

        outcome = db.query(ClinicalOutcomeScore).filter(
            ClinicalOutcomeScore.medical_record_id == visit.parent_visit_id,
            ClinicalOutcomeScore.is_retrained == False,
        ).first()
        if not outcome:
            raise HTTPException(status_code=404, detail="No pending outcome for the parent visit")

        target_vital = outcome.target_vital or "Symptom Severity (1-10)"
        baseline = _resolve_vital_reading(parent, target_vital)
        followup = _resolve_vital_reading(visit, target_vital)

        if baseline is None or followup is None or baseline == 0:
            pct = 0.0
        else:
            higher_is_better = _VITAL_DIRECTION.get(target_vital, False)
            if higher_is_better:
                pct = ((followup - baseline) / abs(baseline)) * 100
            else:
                pct = ((baseline - followup) / abs(baseline)) * 100

        normaliser = _VITAL_NORMALISER.get(target_vital, 30.0)
        signed = min(1.0, max(-1.0, pct / normaliser))

        outcome.baseline_value = baseline
        outcome.followup_value = followup
        outcome.percentage_change = round(pct, 2)
        outcome.doctor_reported_outcome = req.doctor_reported_outcome
        # Pre-blend signed vitals signal, stored for audit; the actual Q-update reward
        # (blended with the doctor's dropdown) is computed in apply_followup_outcome.
        outcome.calculated_reward = round(signed, 4)
        db.commit()
        parent_visit_id = visit.parent_visit_id

    result = rl_service.apply_followup_outcome(parent_visit_id, req.doctor_reported_outcome, signed)
    return {"status": "success", "percentage_change": pct, "signed": signed, **result}


# ── End of Revamp Endpoints ────────────────────────────────────────────────────

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
