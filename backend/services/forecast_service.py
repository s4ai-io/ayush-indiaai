"""
Forecast Service Wrapper — backed by real PostgreSQL data via DiseaseForecaster.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from disease_forecaster import DiseaseForecaster


class ForecastService:
    """Wrapper service for disease forecasting."""

    def __init__(self):
        self.forecaster: DiseaseForecaster = None
        self.initialized: bool = False

    def initialize(self) -> bool:
        """Initialize forecasting service — loads trend data from PostgreSQL and
        makes sure a trained forecast model is ready (loads the persisted .pkl
        if it's still fresh, otherwise trains once). Actual retraining after
        that happens on the daily schedule via retrain(), never per-request."""
        try:
            print("Initializing Forecast Service (PostgreSQL-backed)...")
            self.forecaster = DiseaseForecaster()
            self.forecaster.load_trend_data()
            self.forecaster.ensure_model_ready()
            self.initialized = True
            print("✓ Forecast Service initialized successfully!")
            return True
        except FileNotFoundError as e:
            # No medical records in DB yet — service will run in degraded mode
            print(f"⚠️  Forecast Service: {e} — service degraded until data is available.")
            self.initialized = False
            return False
        except Exception as e:
            print(f"❌ Forecast Service init error: {e}")
            self.initialized = False
            return False

    def retrain(self) -> None:
        """Reload trend data from PostgreSQL and retrain the forecast model.
        Expensive — intended to be called from a daily background job, not
        from a request handler."""
        if self.forecaster is None:
            self.forecaster = DiseaseForecaster()
        self.forecaster.load_trend_data()
        self.forecaster.train_model()
        self.initialized = True

    def get_forecast(self, disease: str = None, months: int = 3) -> dict:
        """Get N-month disease forecast using real DB data."""
        if not self.initialized:
            raise RuntimeError(
                "Forecast Service not initialized — no data in medical_records yet."
            )

        forecasts_df = self.forecaster.predict_future(n_months=months)

        if disease:
            forecasts_df = forecasts_df[
                forecasts_df["disease"].str.contains(disease, case=False, na=False)
            ]

        # Compute actual calendar month names from today
        import calendar as _cal
        now = datetime.now()
        def month_label(offset: int) -> str:
            m = (now.month - 1 + offset) % 12 + 1
            y = now.year + (now.month - 1 + offset) // 12
            return f"{_cal.month_abbr[m]} {y}"

        forecast_data = []
        for _, row in forecasts_df.iterrows():
            offset = int(row["future_month"])
            forecast_data.append({
                "month":             f"Month {offset}",
                "month_name":        month_label(offset),
                "disease":           str(row["disease"]) if "disease" in row.index else "",
                "predicted_cases":   round(float(row["predicted_cases"]), 1),
                "season":            str(row["season"]) if "season" in row.index else "",
                "ritu_sandhi":       bool(row["ritu_sandhi"]) if "ritu_sandhi" in row.index else False,
                "confidence_lower":  None,
                "confidence_upper":  None,
            })

        # Trend direction
        trend = "stable"
        if len(forecast_data) >= 2:
            first = forecast_data[0]["predicted_cases"]
            last  = forecast_data[-1]["predicted_cases"]
            if last > first * 1.1:
                trend = "increasing"
            elif last < first * 0.9:
                trend = "decreasing"

        # Risk level from average predicted cases
        avg = sum(d["predicted_cases"] for d in forecast_data) / len(forecast_data) if forecast_data else 0
        risk_level = "high" if avg > 100 else "moderate" if avg > 30 else "low"

        # Group by disease for frontend rendering
        by_disease: dict = {}
        for entry in forecast_data:
            dk = entry["disease"]
            if dk not in by_disease:
                by_disease[dk] = []
            by_disease[dk].append({
                "month_name":      entry["month_name"],
                "predicted_cases": entry["predicted_cases"],
                "season":          entry["season"],
                "ritu_sandhi":     entry["ritu_sandhi"],
            })

        return {
            "disease":         disease or "All Diseases",
            "forecast_months": months,
            "forecast_data":   forecast_data,
            "by_disease":      by_disease,
            "trend":           trend,
            "risk_level":      risk_level,
            "generated_at":    datetime.now().isoformat(),
        }

    def get_emerging_trends(self) -> dict:
        """Get emerging disease trends from real DB data."""
        if not self.initialized:
            raise RuntimeError("Forecast Service not initialized.")

        trends_df = self.forecaster.detect_emerging_trends()
        if trends_df.empty:
            return {"trends": [], "generated_at": datetime.now().isoformat()}

        trends = []
        for _, row in trends_df.head(10).iterrows():
            growth = float(row["growth_rate"])
            alert_level = (
                "critical" if growth > 50
                else "high"  if growth > 25
                else "medium" if growth > 10
                else "low"
            )
            risk_score = min(100, max(0, (growth + 50) / 1.5))
            trends.append({
                "disease":      row["disease"],
                "category":     row["category"],
                "current_cases": int(row["recent_avg_cases"]),
                "growth_rate":  growth,
                "risk_score":   round(risk_score, 1),
                "alert_level":  alert_level,
                "trend":        row["trend"],
                "window_start": row.get("window_start"),
                "window_end":   row.get("window_end"),
            })

        return {
            "trends":       trends,
            "generated_at": datetime.now().isoformat(),
        }

    def health_check(self) -> dict:
        return {"initialized": self.initialized, "data_loaded": self.initialized}


# Singleton
forecast_service = ForecastService()
