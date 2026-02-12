"""
Forecast Service Wrapper for Disease Forecasting
"""
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from disease_forecaster import DiseaseForecaster


class ForecastService:
    """Wrapper service for disease forecasting"""
    
    def __init__(self):
        self.forecaster = None
        self.initialized = False
        
    def initialize(self):
        """Initialize forecasting service"""
        try:
            print("Initializing Forecast Service...")
            self.forecaster = DiseaseForecaster()
            
            # Try to load trend data
            try:
                self.forecaster.load_trend_data()
                self.initialized = True
                print("✓ Forecast Service initialized successfully!")
                return True
            except FileNotFoundError:
                print("⚠️  Trend data not found. Forecast service will have limited functionality.")
                self.initialized = False
                return False
                
        except Exception as e:
            print(f"❌ Error initializing Forecast Service: {e}")
            return False
    
    def get_forecast(self, disease: str = None, months: int = 3) -> dict:
        """
        Get disease forecast
        
        Args:
            disease: Specific disease to forecast (optional)
            months: Number of months to forecast
            
        Returns:
            Forecast data dict
        """
        if not self.initialized:
            raise RuntimeError("Forecast Service not initialized.")
        
        try:
            # Generate forecasts
            forecasts_df = self.forecaster.forecast_next_months(n_months=months)
            
            # Filter by disease if specified
            if disease:
                forecasts_df = forecasts_df[forecasts_df['disease'] == disease]
            
            # Convert to API response format
            forecast_data = []
            for _, row in forecasts_df.iterrows():
                forecast_data.append({
                    "month": f"Month {row['future_month']}",
                    "predicted_cases": float(row['predicted_cases']),
                    "confidence_lower": None,  # Can be added with confidence intervals
                    "confidence_upper": None
                })
            
            # Determine trend
            if len(forecast_data) >= 2:
                first_cases = forecast_data[0]['predicted_cases']
                last_cases = forecast_data[-1]['predicted_cases']
                if last_cases > first_cases * 1.1:
                    trend = "increasing"
                elif last_cases < first_cases * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            # Determine risk level
            avg_cases = sum(d['predicted_cases'] for d in forecast_data) / len(forecast_data) if forecast_data else 0
            if avg_cases > 100:
                risk_level = "high"
            elif avg_cases > 50:
                risk_level = "moderate"
            else:
                risk_level = "low"
            
            return {
                "disease": disease or "All Diseases",
                "forecast_months": months,
                "forecast_data": forecast_data,
                "trend": trend,
                "risk_level": risk_level
            }
            
        except Exception as e:
            raise ValueError(f"Error generating forecast: {str(e)}")
    
    def get_emerging_trends(self) -> dict:
        """Get emerging disease trends"""
        if not self.initialized:
            raise RuntimeError("Forecast Service not initialized.")
        
        try:
            trends_df = self.forecaster.detect_emerging_trends()
            
            trends = []
            for _, row in trends_df.head(10).iterrows():
                # Determine alert level
                growth_rate = row['growth_rate']
                if growth_rate > 50:
                    alert_level = "critical"
                elif growth_rate > 25:
                    alert_level = "high"
                elif growth_rate > 10:
                    alert_level = "medium"
                else:
                    alert_level = "low"
                
                # Calculate risk score (0-100)
                risk_score = min(100, max(0, (growth_rate + 50) / 1.5))
                
                trends.append({
                    "disease": row['disease'],
                    "category": row['category'],
                    "current_cases": int(row['recent_avg_cases']),
                    "growth_rate": float(row['growth_rate']),
                    "risk_score": round(risk_score, 1),
                    "alert_level": alert_level
                })
            
            return {
                "trends": trends,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise ValueError(f"Error getting emerging trends: {str(e)}")
    
    def health_check(self) -> dict:
        """Check service health"""
        return {
            "initialized": self.initialized,
            "data_loaded": self.initialized
        }


# Global instance
forecast_service = ForecastService()
