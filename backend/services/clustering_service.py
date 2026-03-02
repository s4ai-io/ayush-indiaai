import os
import joblib
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session
from models import SessionLocal, Patient, MedicalRecord
from sqlalchemy import desc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'data', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, 'patient_cluster_model.pkl')

class PatientClusteringService:
    """
    Service for clustering patients based on historical AHIMS outcomes.
    Groups patients based on:
    - Demographics (Age, Gender)
    - Clinical profile (Prakriti, Vikriti)
    - Disease
    - Severity
    """
    def __init__(self, n_clusters=10):
        self.n_clusters = n_clusters
        self.pipeline = self._build_pipeline()
        self.is_fitted = False
        self._load_model()

    def _build_pipeline(self) -> Pipeline:
        numeric_features = ['age', 'severity_numeric']
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())
        ])

        categorical_features = ['gender', 'prakriti', 'vikriti', 'disease']
        categorical_transformer = Pipeline(steps=[
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ])

        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', KMeans(n_clusters=self.n_clusters, random_state=42, n_init='auto'))
        ])
        return pipeline

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.pipeline = joblib.load(MODEL_PATH)
                self.is_fitted = True
                print(f"✓ Patient Clustering Model loaded from {MODEL_PATH}")
            except Exception as e:
                print(f"❌ Failed to load Patient Clustering Model: {e}")

    def _save_model(self):
        try:
            joblib.dump(self.pipeline, MODEL_PATH)
            print(f"✓ Patient Clustering Model saved to {MODEL_PATH}")
        except Exception as e:
            print(f"❌ Failed to save Patient Clustering Model: {e}")

    def retrain_clusters(self) -> dict:
        """
        Fetch all historical patient data and retrain the KMeans clustering model.
        Returns the number of patients clustered and the status.
        """
        data = []
        with SessionLocal() as db:
            # Join MedicalRecord with Patient
            records = db.query(MedicalRecord, Patient).join(
                Patient, MedicalRecord.patient_id == Patient.id
            ).all()

            if not records:
                return {"status": "skipped", "message": "No historical data found"}

            for r, p in records:
                # Basic parsing
                severity_val = 5
                try:
                    severity_val = int(r.severity) if r.severity else 5
                except ValueError:
                    pass
                
                age_val = 30
                try:
                    age_val = int(p.age) if p.age else 30
                except ValueError:
                    pass

                data.append({
                    "patient_id": r.patient_id,
                    "record_id": r.id,
                    "age": age_val,
                    "gender": p.gender or "Unknown",
                    "prakriti": r.prakriti or "Unknown",
                    "vikriti": r.vikriti or "Unknown",
                    "disease": r.diagnosis or "Unknown",
                    "severity_numeric": severity_val
                })

        if len(data) < self.n_clusters:
            return {"status": "skipped", "message": f"Need at least {self.n_clusters} records to cluster, found {len(data)}"}

        df = pd.DataFrame(data)
        
        # Fit pipeline
        self.pipeline.fit(df)
        self.is_fitted = True
        
        # Save model
        self._save_model()
        
        return {"status": "success", "message": f"Clustering model retrained on {len(data)} historical records.", "samples": len(data)}

    def get_cluster(self, patient_profile: dict) -> int:
        """
        Assign a patient profile to a cluster.
        If the model isn't fitted, returns a default cluster 0.
        """
        if not self.is_fitted:
            return 0  # Cold start cluster
            
        severity_val = 5
        try:
            severity_val = int(patient_profile.get("severity", 5))
        except ValueError:
            pass
            
        age_val = 30
        try:
            age_val = int(patient_profile.get("age", 30))
        except ValueError:
            pass

        df = pd.DataFrame([{
            "age": age_val,
            "gender": patient_profile.get("gender", "Unknown"),
            "prakriti": patient_profile.get("prakriti", "Unknown"),
            "vikriti": patient_profile.get("vikriti", "Unknown"),
            "disease": patient_profile.get("disease", "Unknown"),
            "severity_numeric": severity_val
        }])
        
        cluster_id = self.pipeline.predict(df)[0]
        return int(cluster_id)

# Singleton
clustering_service = PatientClusteringService()
