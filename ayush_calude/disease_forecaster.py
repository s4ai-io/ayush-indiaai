import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

class DiseaseForecaster:
    """
    Public Health Risk Forecasting System
    - Detects emerging disease trends
    - Forecasts future disease outbreaks
    - Identifies high-risk seasons and populations
    """
    
    def __init__(self):
        self.forecast_model = None
        self.label_encoders = {}
        
    def load_trend_data(self):
        """Load public health trend data"""
        print("Loading public health trend data...")
        self.trends = pd.read_csv('/home/claude/public_health_trends.csv')
        print(f"✓ Loaded {len(self.trends)} trend records")
        
    def detect_emerging_trends(self):
        """Identify diseases with increasing case rates"""
        print("\n" + "="*60)
        print("EMERGING DISEASE TREND DETECTION")
        print("="*60)
        
        # Calculate month-over-month growth
        trends_sorted = self.trends.sort_values(['disease', 'month'])
        
        disease_trends = []
        
        for disease in self.trends['disease'].unique():
            disease_data = trends_sorted[trends_sorted['disease'] == disease].copy()
            disease_data['cases_prev_month'] = disease_data['cases_reported'].shift(1)
            disease_data['growth_rate'] = (
                (disease_data['cases_reported'] - disease_data['cases_prev_month']) / 
                disease_data['cases_prev_month'] * 100
            )
            
            # Recent 3 months average growth
            recent_growth = disease_data['growth_rate'].tail(3).mean()
            recent_cases = disease_data['cases_reported'].tail(3).mean()
            
            disease_trends.append({
                'disease': disease,
                'category': disease_data['disease_category'].iloc[0],
                'recent_avg_cases': int(recent_cases),
                'growth_rate': round(recent_growth, 2),
                'trend': 'Rising' if recent_growth > 10 else 'Stable' if recent_growth > -10 else 'Declining'
            })
        
        trend_df = pd.DataFrame(disease_trends).sort_values('growth_rate', ascending=False)
        
        print("\n🚨 TOP 5 EMERGING DISEASE THREATS:")
        print("-" * 60)
        for idx, row in trend_df.head(5).iterrows():
            print(f"  {row['disease']} ({row['category']})")
            print(f"    Recent cases: {row['recent_avg_cases']}")
            print(f"    Growth rate: {row['growth_rate']:+.1f}%")
            print(f"    Trend: {row['trend']}")
            print()
        
        return trend_df
    
    def seasonal_analysis(self):
        """Analyze seasonal patterns in disease occurrence"""
        print("\n" + "="*60)
        print("SEASONAL DISEASE PATTERN ANALYSIS")
        print("="*60)
        
        seasonal_summary = self.trends.groupby(['season', 'disease_category']).agg({
            'cases_reported': 'mean',
            'avg_severity': 'mean'
        }).round(1)
        
        print("\n📅 Disease Prevalence by Season:")
        print("-" * 60)
        
        for season in ['Spring', 'Summer', 'Monsoon', 'Autumn', 'Winter', 'Late Winter']:
            if season in seasonal_summary.index.get_level_values(0):
                season_data = seasonal_summary.loc[season].sort_values('cases_reported', ascending=False)
                print(f"\n{season}:")
                for category, row in season_data.head(3).iterrows():
                    print(f"  • {category}: {row['cases_reported']:.0f} cases (severity: {row['avg_severity']:.1f}/10)")
        
        return seasonal_summary
    
    def forecast_next_months(self, n_months=3):
        """Forecast disease cases for next n months"""
        print("\n" + "="*60)
        print(f"FORECASTING DISEASE TRENDS ({n_months} months ahead)")
        print("="*60)
        
        # Prepare data for forecasting
        df = self.trends.copy()
        
        # Convert month to datetime
        df['month_dt'] = pd.to_datetime(df['month'])
        df['month_num'] = df['month_dt'].dt.month
        df['year'] = df['month_dt'].dt.year
        
        # Create lag features
        df = df.sort_values(['disease', 'month'])
        df['cases_lag1'] = df.groupby('disease')['cases_reported'].shift(1)
        df['cases_lag2'] = df.groupby('disease')['cases_reported'].shift(2)
        df['cases_lag3'] = df.groupby('disease')['cases_reported'].shift(3)
        
        # Drop NaN from lags
        df = df.dropna()
        
        # Encode categorical
        le_disease = LabelEncoder()
        le_category = LabelEncoder()
        le_season = LabelEncoder()
        
        df['disease_encoded'] = le_disease.fit_transform(df['disease'])
        df['category_encoded'] = le_category.fit_transform(df['disease_category'])
        df['season_encoded'] = le_season.fit_transform(df['season'])
        
        self.label_encoders = {
            'disease': le_disease,
            'category': le_category,
            'season': le_season
        }
        
        # Features and target
        feature_cols = [
            'disease_encoded', 'category_encoded', 'season_encoded',
            'month_num', 'cases_lag1', 'cases_lag2', 'cases_lag3', 'avg_severity'
        ]
        
        X = df[feature_cols]
        y = df['cases_reported']
        
        # Train model
        print("\nTraining forecast model...")
        self.forecast_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.forecast_model.fit(X, y)
        
        print("✓ Model trained successfully!")
        
        # Make predictions for next months
        forecasts = self._predict_future(df, n_months)
        
        print(f"\n🔮 FORECAST FOR NEXT {n_months} MONTHS:")
        print("-" * 60)
        
        # Show top forecasted diseases
        for month in range(1, n_months + 1):
            month_forecast = forecasts[forecasts['future_month'] == month].sort_values(
                'predicted_cases', ascending=False
            )
            
            print(f"\nMonth {month}:")
            for idx, row in month_forecast.head(5).iterrows():
                print(f"  • {row['disease']}: {int(row['predicted_cases'])} cases (expected)")
        
        return forecasts
    
    def _predict_future(self, df, n_months):
        """Generate future predictions"""
        last_data = df.groupby('disease').last()
        
        forecasts = []
        
        for disease in df['disease'].unique():
            disease_data = last_data.loc[disease]
            
            for month_ahead in range(1, n_months + 1):
                # Predict next month
                future_month_num = (disease_data['month_num'] + month_ahead) % 12
                if future_month_num == 0:
                    future_month_num = 12
                
                # Get season for month
                season_map = {
                    1: 'Late Winter', 2: 'Late Winter', 3: 'Spring', 4: 'Spring',
                    5: 'Summer', 6: 'Summer', 7: 'Monsoon', 8: 'Monsoon',
                    9: 'Autumn', 10: 'Autumn', 11: 'Winter', 12: 'Winter'
                }
                future_season = season_map[future_month_num]
                
                features = np.array([[
                    disease_data['disease_encoded'],
                    disease_data['category_encoded'],
                    self.label_encoders['season'].transform([future_season])[0],
                    future_month_num,
                    disease_data['cases_lag1'],
                    disease_data['cases_lag2'],
                    disease_data['cases_lag3'],
                    disease_data['avg_severity']
                ]])
                
                predicted_cases = self.forecast_model.predict(features)[0]
                
                forecasts.append({
                    'disease': disease,
                    'category': self.label_encoders['category'].inverse_transform(
                        [int(disease_data['category_encoded'])]
                    )[0],
                    'future_month': month_ahead,
                    'month_num': future_month_num,
                    'season': future_season,
                    'predicted_cases': max(0, predicted_cases)
                })
        
        return pd.DataFrame(forecasts)
    
    def risk_assessment(self):
        """Assess public health risks"""
        print("\n" + "="*60)
        print("PUBLIC HEALTH RISK ASSESSMENT")
        print("="*60)
        
        # Calculate risk scores
        risk_scores = self.trends.groupby('disease_category').agg({
            'cases_reported': 'sum',
            'avg_severity': 'mean'
        })
        
        # Normalize and calculate composite risk
        risk_scores['cases_normalized'] = (
            risk_scores['cases_reported'] / risk_scores['cases_reported'].max()
        )
        risk_scores['risk_score'] = (
            risk_scores['cases_normalized'] * 0.6 + 
            risk_scores['avg_severity'] / 10 * 0.4
        ) * 100
        
        risk_scores = risk_scores.sort_values('risk_score', ascending=False)
        
        print("\n⚠️ DISEASE CATEGORY RISK LEVELS:")
        print("-" * 60)
        for category, row in risk_scores.iterrows():
            risk_level = 'HIGH' if row['risk_score'] > 70 else 'MEDIUM' if row['risk_score'] > 40 else 'LOW'
            print(f"  {category:20s}: {row['risk_score']:5.1f} [{risk_level}]")
            print(f"    Total cases: {int(row['cases_reported']):,}")
            print(f"    Avg severity: {row['avg_severity']:.1f}/10")
            print()
        
        return risk_scores
    
    def generate_alerts(self):
        """Generate health alerts based on analysis"""
        print("\n" + "="*60)
        print("PUBLIC HEALTH ALERTS")
        print("="*60)
        
        alerts = []
        
        # Detect spikes
        for disease in self.trends['disease'].unique():
            disease_data = self.trends[self.trends['disease'] == disease].sort_values('month')
            
            if len(disease_data) >= 3:
                recent_avg = disease_data['cases_reported'].tail(3).mean()
                overall_avg = disease_data['cases_reported'].mean()
                
                if recent_avg > overall_avg * 1.5:
                    alerts.append({
                        'type': 'SPIKE',
                        'disease': disease,
                        'message': f"{disease} cases are 50% above normal. Increase monitoring."
                    })
        
        # Seasonal alerts
        current_month = pd.Timestamp.now().month
        season_map = {
            1: 'Late Winter', 2: 'Late Winter', 3: 'Spring', 4: 'Spring',
            5: 'Summer', 6: 'Summer', 7: 'Monsoon', 8: 'Monsoon',
            9: 'Autumn', 10: 'Autumn', 11: 'Winter', 12: 'Winter'
        }
        current_season = season_map[current_month]
        
        seasonal_diseases = self.trends[self.trends['season'] == current_season].groupby(
            'disease_category'
        )['cases_reported'].mean().sort_values(ascending=False)
        
        for category in seasonal_diseases.head(2).index:
            alerts.append({
                'type': 'SEASONAL',
                'disease': category,
                'message': f"Prepare for increased {category} diseases during {current_season}."
            })
        
        print(f"\n🔔 {len(alerts)} Active Alerts:")
        print("-" * 60)
        for i, alert in enumerate(alerts, 1):
            print(f"{i}. [{alert['type']}] {alert['disease']}")
            print(f"   {alert['message']}")
            print()
        
        return alerts


if __name__ == "__main__":
    # Initialize forecaster
    forecaster = DiseaseForecaster()
    
    # Load data
    forecaster.load_trend_data()
    
    # Run analyses
    emerging_trends = forecaster.detect_emerging_trends()
    seasonal_patterns = forecaster.seasonal_analysis()
    forecasts = forecaster.forecast_next_months(n_months=3)
    risk_assessment = forecaster.risk_assessment()
    alerts = forecaster.generate_alerts()
    
    print("\n" + "="*60)
    print("✓ DISEASE FORECASTING COMPLETE!")
    print("="*60)
