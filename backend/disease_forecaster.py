"""
Disease Forecaster — PostgreSQL-backed.
Replaces the synthetic public_health_trends.csv with real medical_records data.
Builds time-series features per disease, trains RandomForest, forecasts future months.
"""
import os
import time
import calendar
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from collections import defaultdict
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

from models import SessionLocal, Patient, MedicalRecord
from utils.episode_dedup import dedupe_repeat_diagnoses

# Trained model is expensive to (re)build (RandomForest over the full trend
# history) so it's persisted here and reused across requests instead of being
# retrained on every /api/forecast call — see ensure_model_ready().
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_BASE_DIR, "data", "models")
os.makedirs(_MODELS_DIR, exist_ok=True)
MODEL_PATH = os.path.join(_MODELS_DIR, "disease_forecaster_rf.pkl")
MODEL_MAX_AGE_SECONDS = 24 * 60 * 60  # retrain at most once a day


# Gregorian month → Ayurvedic Ritu (season)
_RITU_MAP = {
    1: "Shishira", 2: "Shishira",
    3: "Vasanta",  4: "Vasanta",
    5: "Grishma",  6: "Grishma",
    7: "Varsha",   8: "Varsha",
    9: "Sharad",   10: "Sharad",
    11: "Hemanta", 12: "Hemanta",
}

# Ritu Sandhi months (transition — highest risk)
_SANDHI_MONTHS = {3, 5, 7, 9, 11, 1}


def _load_trends_from_db() -> pd.DataFrame:
    """
    Query real medical_records + patients and return a monthly trend DataFrame
    equivalent to the old public_health_trends.csv schema.

    Returns columns:
        month, disease, disease_category, season, cases_reported, avg_severity
    """
    with SessionLocal() as db:
        rows = (
            db.query(
                MedicalRecord.visit_date,
                MedicalRecord.diagnosis,
                MedicalRecord.severity,
                Patient.city,
                Patient.state,
                MedicalRecord.patient_id,
            )
            .join(Patient, Patient.id == MedicalRecord.patient_id)
            .filter(
                MedicalRecord.visit_date != None,
                MedicalRecord.diagnosis != None,
                MedicalRecord.diagnosis != "",
            )
            .all()
        )

    if not rows:
        return pd.DataFrame()

    # Collapse tight-together repeat/follow-up visits (same patient, same
    # diagnosis, within 14 days) into one episode so a single patient's
    # follow-up doesn't inflate a month's case count or the forecast/
    # emerging-trends growth rate — see utils/episode_dedup.py.
    rows = dedupe_repeat_diagnoses(rows, patient_idx=5, diagnosis_idx=1, date_idx=0, gap_days=14)

    records = []
    for visit_date, diagnosis, severity, city, state, _patient_id in rows:
        if not visit_date or not diagnosis:
            continue
        d = visit_date.date() if hasattr(visit_date, "date") else visit_date
        month_str = d.strftime("%Y-%m")
        month_num = d.month

        # Parse severity (stored as string "1"-"10", "Mild"/"Moderate"/"Severe")
        sev = 5.0
        if severity:
            sv = str(severity).strip().lower()
            if sv == "mild":
                sev = 3.0
            elif sv == "moderate":
                sev = 6.0
            elif sv == "severe":
                sev = 9.0
            else:
                try:
                    sev = float(sv)
                except ValueError:
                    sev = 5.0

        records.append({
            "month":            month_str,
            "month_num":        month_num,
            "disease":          diagnosis.strip(),
            "disease_category": "Ayurvedic",   # can be enriched later
            "season":           _RITU_MAP.get(month_num, "Shishira"),
            "ritu_sandhi":      int(month_num in _SANDHI_MONTHS),
            "avg_severity":     sev,
            "city":             (city or "Unknown").strip(),
            "state":            (state or "Unknown").strip(),
        })

    df = pd.DataFrame(records)

    # Monthly aggregation: cases_reported = count of records per month × disease
    monthly = (
        df.groupby(["month", "disease", "disease_category", "season", "ritu_sandhi"])
        .agg(
            cases_reported=("avg_severity", "count"),
            avg_severity=("avg_severity", "mean"),
        )
        .reset_index()
    )
    return monthly.sort_values(["disease", "month"])


class DiseaseForecaster:
    """
    Public Health Risk Forecasting System — backed by real PostgreSQL data.
    """

    def __init__(self):
        self.trends: pd.DataFrame = pd.DataFrame()
        self.forecast_model = None
        self.label_encoders: dict = {}
        self.last_data: pd.DataFrame = None
        self.initialized = False

    def load_trend_data(self):
        """Load disease trend data from PostgreSQL medical_records."""
        print("Loading disease trend data from PostgreSQL...")
        self.trends = _load_trends_from_db()
        if self.trends.empty:
            raise FileNotFoundError(
                "No medical records found in PostgreSQL. "
                "Please ensure data has been migrated."
            )
        print(f"✓ Loaded {len(self.trends)} monthly disease records from DB "
              f"({self.trends['disease'].nunique()} diseases, "
              f"{self.trends['month'].nunique()} months)")
        self.initialized = True

    # ─── Emerging Trends ──────────────────────────────────────────────────────

    def detect_emerging_trends(self) -> pd.DataFrame:
        """Identify diseases with month-over-month rising case rates."""
        if self.trends.empty:
            return pd.DataFrame()

        trends_sorted = self.trends.sort_values(["disease", "month"])
        disease_trends = []

        for disease in self.trends["disease"].unique():
            disease_data = trends_sorted[trends_sorted["disease"] == disease].copy()
            if len(disease_data) < 2:
                continue
            disease_data["cases_prev"] = disease_data["cases_reported"].shift(1)
            disease_data["growth_rate"] = (
                (disease_data["cases_reported"] - disease_data["cases_prev"])
                / disease_data["cases_prev"].replace(0, 1) * 100
            )
            recent_growth = disease_data["growth_rate"].tail(3).mean()
            recent_cases  = disease_data["cases_reported"].tail(3).mean()
            recent_months = disease_data["month"].tail(3)

            disease_trends.append({
                "disease":         disease,
                "category":        disease_data["disease_category"].iloc[0],
                "recent_avg_cases": int(recent_cases),
                "growth_rate":     round(recent_growth, 2),
                "trend": (
                    "Rising" if recent_growth > 10
                    else "Stable" if recent_growth > -10
                    else "Declining"
                ),
                # Exact months behind recent_avg_cases/growth_rate, so the UI can
                # drill down into the actual case records instead of guessing a
                # window off today's date (the data's "recent" months aren't
                # necessarily anywhere near the real current date).
                "window_start": f"{recent_months.min()}-01",
                "window_end": (
                    f"{recent_months.max()}-"
                    f"{calendar.monthrange(*map(int, recent_months.max().split('-')))[1]:02d}"
                ),
            })

        if not disease_trends:
            return pd.DataFrame()
        return pd.DataFrame(disease_trends).sort_values("growth_rate", ascending=False)

    # ─── Seasonal Analysis ────────────────────────────────────────────────────

    def seasonal_analysis(self) -> pd.DataFrame:
        """Analyse disease prevalence per Ayurvedic Ritu season."""
        if self.trends.empty:
            return pd.DataFrame()
        return (
            self.trends.groupby(["season", "disease_category"])
            .agg(cases_reported=("cases_reported", "mean"),
                 avg_severity=("avg_severity", "mean"))
            .round(1)
        )

    # ─── Forecasting ──────────────────────────────────────────────────────────

    def _model_is_fresh(self) -> bool:
        if not os.path.exists(MODEL_PATH):
            return False
        age = time.time() - os.path.getmtime(MODEL_PATH)
        return age < MODEL_MAX_AGE_SECONDS

    def _save_model(self) -> None:
        joblib.dump({
            "model": self.forecast_model,
            "label_encoders": self.label_encoders,
            "last_data": self.last_data,
        }, MODEL_PATH)

    def _load_cached_model(self) -> bool:
        try:
            state = joblib.load(MODEL_PATH)
            self.forecast_model = state["model"]
            self.label_encoders = state["label_encoders"]
            self.last_data = state["last_data"]
            return True
        except Exception as e:
            print(f"⚠️  Failed to load cached forecast model: {e}")
            return False

    def ensure_model_ready(self, force: bool = False) -> None:
        """
        Make sure a trained model is available for inference.
        Loads the persisted .pkl if it's still fresh (< MODEL_MAX_AGE_SECONDS
        old); otherwise (re)trains. Call this from a daily background job —
        never from a request path, since training is the expensive part.
        """
        if not force and self._model_is_fresh() and self._load_cached_model():
            return
        self.train_model()

    def train_model(self) -> None:
        """Train the RandomForest on the currently loaded trend data and
        persist it to disk. Expensive — meant to run on a schedule, not
        per-request."""
        if self.trends.empty:
            raise ValueError("No trend data loaded. Call load_trend_data() first.")

        df = self.trends.copy()
        df["month_dt"]  = pd.to_datetime(df["month"])
        df["month_num"] = df["month_dt"].dt.month
        df["year"]      = df["month_dt"].dt.year

        # Lag features
        df = df.sort_values(["disease", "month"])
        df["cases_lag1"] = df.groupby("disease")["cases_reported"].shift(1)
        df["cases_lag2"] = df.groupby("disease")["cases_reported"].shift(2)
        df["cases_lag3"] = df.groupby("disease")["cases_reported"].shift(3)
        df = df.dropna(subset=["cases_lag1", "cases_lag2", "cases_lag3"])

        if df.empty:
            raise ValueError(
                "Not enough historical months to build lag features. "
                "Need at least 3 months of data per disease."
            )

        # Encode categoricals
        le_disease  = LabelEncoder()
        le_category = LabelEncoder()
        le_season   = LabelEncoder()

        df["disease_enc"]  = le_disease.fit_transform(df["disease"])
        df["category_enc"] = le_category.fit_transform(df["disease_category"])
        df["season_enc"]   = le_season.fit_transform(df["season"])

        self.label_encoders = {
            "disease": le_disease, "category": le_category, "season": le_season
        }

        feature_cols = [
            "disease_enc", "category_enc", "season_enc",
            "month_num", "ritu_sandhi",
            "cases_lag1", "cases_lag2", "cases_lag3",
            "avg_severity",
        ]

        X = df[feature_cols]
        y = df["cases_reported"]

        self.forecast_model = RandomForestRegressor(
            n_estimators=200, max_depth=10, random_state=42, n_jobs=-1
        )
        self.forecast_model.fit(X, y)
        self.last_data = df.groupby("disease").last()
        self._save_model()

    def predict_future(self, n_months: int = 3) -> pd.DataFrame:
        """Fast inference path — uses the cached/trained model, no training here."""
        if self.forecast_model is None or self.last_data is None:
            self.ensure_model_ready()
        return self._predict_future(n_months)

    def _predict_future(self, n_months: int) -> pd.DataFrame:
        """Generate future monthly predictions per disease."""
        last_data = self.last_data
        forecasts = []

        for disease in last_data.index:
            row = last_data.loc[disease]

            for month_ahead in range(1, n_months + 1):
                future_month = (int(row["month_num"]) + month_ahead - 1) % 12 + 1
                future_season = _RITU_MAP[future_month]
                ritu_sandhi   = int(future_month in _SANDHI_MONTHS)

                try:
                    season_enc = self.label_encoders["season"].transform([future_season])[0]
                except ValueError:
                    season_enc = 0

                features = np.array([[
                    row["disease_enc"],
                    row["category_enc"],
                    season_enc,
                    future_month,
                    ritu_sandhi,
                    row["cases_lag1"],
                    row["cases_lag2"],
                    row["cases_lag3"],
                    row["avg_severity"],
                ]])

                predicted = max(0, self.forecast_model.predict(features)[0])
                forecasts.append({
                    "disease":         disease,
                    "category":        self.label_encoders["category"].inverse_transform(
                                           [int(row["category_enc"])])[0],
                    "future_month":    month_ahead,
                    "month_num":       future_month,
                    "season":          future_season,
                    "ritu_sandhi":     ritu_sandhi,
                    "predicted_cases": predicted,
                })

        return pd.DataFrame(forecasts)

    # ─── Risk Assessment ──────────────────────────────────────────────────────

    def risk_assessment(self) -> pd.DataFrame:
        """Composite risk score per disease category from real data."""
        if self.trends.empty:
            return pd.DataFrame()

        risk = self.trends.groupby("disease_category").agg(
            cases_reported=("cases_reported", "sum"),
            avg_severity=("avg_severity", "mean"),
        )
        risk["cases_norm"] = risk["cases_reported"] / risk["cases_reported"].max()
        risk["risk_score"] = (risk["cases_norm"] * 0.6 + risk["avg_severity"] / 10 * 0.4) * 100
        return risk.sort_values("risk_score", ascending=False)

    # ─── Alerts ───────────────────────────────────────────────────────────────

    def generate_alerts(self) -> list:
        """Generate public-health alerts from real trend data."""
        if self.trends.empty:
            return []

        alerts = []
        for disease in self.trends["disease"].unique():
            d_data = self.trends[self.trends["disease"] == disease].sort_values("month")
            if len(d_data) < 3:
                continue
            recent_avg  = d_data["cases_reported"].tail(3).mean()
            overall_avg = d_data["cases_reported"].mean()
            if recent_avg > overall_avg * 1.5:
                alerts.append({
                    "type": "SPIKE",
                    "disease": disease,
                    "message": (
                        f"{disease} cases are "
                        f"{round((recent_avg/overall_avg - 1)*100)}% above historical average. "
                        f"Increase monitoring."
                    ),
                })

        # Seasonal (Ritu) alert
        current_ritu = _RITU_MAP[datetime.now().month]
        seasonal = (
            self.trends[self.trends["season"] == current_ritu]
            .groupby("disease")["cases_reported"]
            .mean()
            .sort_values(ascending=False)
        )
        for disease in seasonal.head(3).index:
            alerts.append({
                "type": "SEASONAL",
                "disease": disease,
                "message": (
                    f"Historical data shows elevated {disease} cases during "
                    f"{current_ritu} (current Ritu). Prepare accordingly."
                ),
            })

        return alerts
