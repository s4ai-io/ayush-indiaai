"""
AYUSH Health System - Complete Demo
====================================
This script demonstrates the entire pipeline:
1. Generate synthetic dataset
2. Train ML models
3. Get personalized recommendations
4. Forecast disease trends
"""

from ayush_data_generator import AYUSHDataGenerator
from ayush_ml_pipeline import AYUSHRecommendationSystem
from disease_forecaster import DiseaseForecaster

def print_header(title):
    """Print a styled section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")

def main():
    print_header("INTELLIGENT AYUSH HEALTH SYSTEM - COMPLETE DEMO")
    
    # ========================================================================
    # STEP 1: Generate Dataset
    # ========================================================================
    print_header("STEP 1: GENERATING SYNTHETIC DATASET")
    
    generator = AYUSHDataGenerator(n_patients=500)
    datasets = generator.generate_complete_dataset()
    
    # Save datasets
    datasets['patients'].to_csv('/home/claude/patients.csv', index=False)
    datasets['health_records'].to_csv('/home/claude/health_records.csv', index=False)
    datasets['treatments'].to_csv('/home/claude/treatments.csv', index=False)
    datasets['public_health_trends'].to_csv('/home/claude/public_health_trends.csv', index=False)
    
    print("\n✓ Dataset saved to CSV files")
    
    # ========================================================================
    # STEP 2: Train ML Models
    # ========================================================================
    print_header("STEP 2: TRAINING MACHINE LEARNING MODELS")
    
    ayush_system = AYUSHRecommendationSystem()
    ayush_system.load_data()
    ayush_system.prepare_features()
    
    # Train models
    ayush_system.train_outcome_classifier()
    ayush_system.train_improvement_predictor()
    
    # Save models
    ayush_system.save_models()
    
    # ========================================================================
    # STEP 3: Generate System Report
    # ========================================================================
    print_header("STEP 3: SYSTEM STATISTICS & ANALYSIS")
    
    ayush_system.generate_report()
    
    # ========================================================================
    # STEP 4: Personalized Recommendations
    # ========================================================================
    print_header("STEP 4: PERSONALIZED TREATMENT RECOMMENDATIONS")
    
    # Example patients with different profiles
    test_patients = [
        {
            'name': 'Patient A - Young Adult with Anxiety',
            'profile': {
                'age': 28,
                'gender': 'Female',
                'prakriti': 'Vata-Pitta',
                'vikriti': 'Vata',
                'disease': 'Anxiety',
                'severity': 7,
                'bmi': 22.0
            }
        },
        {
            'name': 'Patient B - Middle-aged with Diabetes',
            'profile': {
                'age': 52,
                'gender': 'Male',
                'prakriti': 'Kapha',
                'vikriti': 'Kapha',
                'disease': 'Diabetes',
                'severity': 6,
                'bmi': 29.5
            }
        },
        {
            'name': 'Patient C - Senior with Arthritis',
            'profile': {
                'age': 65,
                'gender': 'Female',
                'prakriti': 'Vata',
                'vikriti': 'Vata',
                'disease': 'Arthritis',
                'severity': 8,
                'bmi': 24.0
            }
        }
    ]
    
    for patient in test_patients:
        print("\n" + "-"*70)
        print(f"  {patient['name']}")
        print("-"*70)
        recommendations = ayush_system.recommend_treatment(patient['profile'])
    
    # ========================================================================
    # STEP 5: Disease Forecasting
    # ========================================================================
    print_header("STEP 5: PUBLIC HEALTH RISK FORECASTING")
    
    forecaster = DiseaseForecaster()
    forecaster.load_trend_data()
    
    # Detect emerging trends
    print("\n[5.1] Emerging Disease Trends")
    print("-"*70)
    emerging_trends = forecaster.detect_emerging_trends()
    
    # Seasonal analysis
    print("\n[5.2] Seasonal Disease Patterns")
    print("-"*70)
    seasonal_patterns = forecaster.seasonal_analysis()
    
    # Forecast future
    print("\n[5.3] 3-Month Disease Forecast")
    print("-"*70)
    forecasts = forecaster.forecast_next_months(n_months=3)
    
    # Risk assessment
    print("\n[5.4] Public Health Risk Assessment")
    print("-"*70)
    risk_assessment = forecaster.risk_assessment()
    
    # Generate alerts
    print("\n[5.5] Active Health Alerts")
    print("-"*70)
    alerts = forecaster.generate_alerts()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_header("DEMO COMPLETE - SUMMARY")
    
    print("✅ Successfully Completed:")
    print("  1. Generated synthetic AYUSH dataset (500 patients)")
    print("  2. Trained ML models for treatment prediction")
    print("  3. Generated personalized recommendations for 3 patients")
    print("  4. Forecasted disease trends for next 3 months")
    print("  5. Identified emerging health threats")
    print()
    print("📁 Generated Files:")
    print("  • patients.csv")
    print("  • health_records.csv")
    print("  • treatments.csv")
    print("  • public_health_trends.csv")
    print("  • outcome_model.pkl")
    print("  • improvement_model.pkl")
    print("  • scaler.pkl")
    print("  • label_encoders.pkl")
    print()
    print("🎯 Key Capabilities Demonstrated:")
    print("  ✓ Dosha-based personalized treatment recommendations")
    print("  ✓ Herbal medicine prescription with dosages")
    print("  ✓ Yoga and lifestyle modification suggestions")
    print("  ✓ Disease trend detection and forecasting")
    print("  ✓ Public health risk assessment")
    print("  ✓ Seasonal disease pattern analysis")
    print()
    print("💡 Next Steps:")
    print("  • Validate with real AYUSH clinic data")
    print("  • Develop web/mobile interface")
    print("  • Integrate with electronic health records")
    print("  • Deploy as clinical decision support system")
    print()
    print("="*70)
    print("Thank you for exploring the Intelligent AYUSH Health System!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
