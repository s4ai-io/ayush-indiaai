"""
Intelligent AYUSH Health System
================================
AI-based system for:
1. Early detection of emerging disease trends
2. Public health risk forecasting
3. Personalized treatment and lifestyle recommendations

Author: Your Name
Date: 2024
"""

import sys
import pandas as pd
from ayush_data_generator import AYUSHDataGenerator
from ayush_ml_pipeline import AYUSHRecommendationSystem
from disease_forecaster import DiseaseForecaster

class AYUSHHealthSystem:
    """Main interface for the Intelligent AYUSH Health System"""
    
    def __init__(self):
        self.data_generator = None
        self.recommendation_system = None
        self.forecaster = None
        self.data_generated = False
        self.models_trained = False
        
    def display_banner(self):
        """Display system banner"""
        print("\n" + "="*70)
        print(" " * 15 + "INTELLIGENT AYUSH HEALTH SYSTEM")
        print(" " * 10 + "AI-Powered Personalized Healthcare & Risk Forecasting")
        print("="*70)
        
    def display_menu(self):
        """Display main menu"""
        print("\n" + "-"*70)
        print("MAIN MENU")
        print("-"*70)
        print("1. Generate Synthetic Dataset")
        print("2. Train ML Models (Outcome Prediction & Improvement Forecasting)")
        print("3. Personalized Treatment Recommendation (New Patient)")
        print("4. Public Health Risk Forecasting")
        print("5. Detect Emerging Disease Trends")
        print("6. View System Statistics & Reports")
        print("7. Exit")
        print("-"*70)
        
    def generate_dataset(self):
        """Generate synthetic AYUSH dataset"""
        print("\n" + "="*70)
        print("STEP 1: SYNTHETIC DATASET GENERATION")
        print("="*70)
        
        n_patients = input("\nEnter number of patients to generate (default: 1000): ").strip()
        n_patients = int(n_patients) if n_patients else 1000
        
        print(f"\nGenerating dataset with {n_patients} patients...")
        self.data_generator = AYUSHDataGenerator(n_patients=n_patients)
        datasets = self.data_generator.generate_complete_dataset()
        
        # Save datasets
        print("\nSaving datasets...")
        datasets['patients'].to_csv('/home/claude/patients.csv', index=False)
        datasets['health_records'].to_csv('/home/claude/health_records.csv', index=False)
        datasets['treatments'].to_csv('/home/claude/treatments.csv', index=False)
        datasets['public_health_trends'].to_csv('/home/claude/public_health_trends.csv', index=False)
        
        self.data_generated = True
        
        print("\n✓ Dataset generation complete!")
        print(f"  • Patients: {len(datasets['patients'])} records")
        print(f"  • Health Records: {len(datasets['health_records'])} visits")
        print(f"  • Treatments: {len(datasets['treatments'])} prescriptions")
        print(f"  • Public Health Trends: {len(datasets['public_health_trends'])} data points")
        
        input("\nPress Enter to continue...")
        
    def train_models(self):
        """Train ML models"""
        if not self.data_generated:
            print("\n⚠️ Please generate dataset first (Option 1)")
            input("\nPress Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("STEP 2: MACHINE LEARNING MODEL TRAINING")
        print("="*70)
        
        self.recommendation_system = AYUSHRecommendationSystem()
        
        # Load and prepare data
        self.recommendation_system.load_data()
        self.recommendation_system.prepare_features()
        
        # Train models
        print("\nTraining models... This may take a few moments...")
        self.recommendation_system.train_outcome_classifier()
        self.recommendation_system.train_improvement_predictor()
        
        # Save models
        self.recommendation_system.save_models()
        
        self.models_trained = True
        
        print("\n✓ All models trained and saved successfully!")
        input("\nPress Enter to continue...")
        
    def personalized_recommendation(self):
        """Get personalized treatment recommendation"""
        if not self.models_trained:
            print("\n⚠️ Please train models first (Option 2)")
            input("\nPress Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("STEP 3: PERSONALIZED TREATMENT RECOMMENDATION")
        print("="*70)
        
        print("\nEnter patient details:")
        print("-" * 70)
        
        try:
            age = int(input("Age: "))
            gender = input("Gender (Male/Female): ").strip()
            
            print("\nPrakriti (Natural Constitution) Options:")
            print("  Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha, Tridosha")
            prakriti = input("Prakriti: ").strip()
            
            print("\nVikriti (Current Imbalance) Options:")
            print("  Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha")
            vikriti = input("Vikriti: ").strip()
            
            print("\nCommon Conditions:")
            print("  Respiratory: Asthma, Bronchitis, Sinusitis, Allergic Rhinitis")
            print("  Digestive: IBS, Acidity, Constipation, Gastritis")
            print("  Metabolic: Diabetes, Obesity, Thyroid Disorder")
            print("  Mental: Anxiety, Depression, Insomnia, Stress, Migraine")
            print("  Musculoskeletal: Arthritis, Back Pain, Joint Pain")
            disease = input("Disease/Condition: ").strip()
            
            severity = int(input("Severity (1-10): "))
            bmi = float(input("BMI (optional, press Enter to skip): ") or "25")
            
            patient_profile = {
                'age': age,
                'gender': gender,
                'prakriti': prakriti,
                'vikriti': vikriti,
                'disease': disease,
                'severity': severity,
                'bmi': bmi
            }
            
            # Generate recommendations
            recommendations = self.recommendation_system.recommend_treatment(patient_profile)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please check your inputs and try again.")
        
        input("\nPress Enter to continue...")
        
    def forecast_risks(self):
        """Forecast public health risks"""
        if not self.data_generated:
            print("\n⚠️ Please generate dataset first (Option 1)")
            input("\nPress Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("STEP 4: PUBLIC HEALTH RISK FORECASTING")
        print("="*70)
        
        self.forecaster = DiseaseForecaster()
        self.forecaster.load_trend_data()
        
        # Seasonal analysis
        self.forecaster.seasonal_analysis()
        
        # Risk assessment
        self.forecaster.risk_assessment()
        
        # Forecast future months
        n_months = input("\nEnter number of months to forecast (default: 3): ").strip()
        n_months = int(n_months) if n_months else 3
        
        self.forecaster.forecast_next_months(n_months=n_months)
        
        # Generate alerts
        self.forecaster.generate_alerts()
        
        input("\nPress Enter to continue...")
        
    def detect_trends(self):
        """Detect emerging disease trends"""
        if not self.data_generated:
            print("\n⚠️ Please generate dataset first (Option 1)")
            input("\nPress Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("STEP 5: EMERGING DISEASE TREND DETECTION")
        print("="*70)
        
        if not self.forecaster:
            self.forecaster = DiseaseForecaster()
            self.forecaster.load_trend_data()
        
        trends = self.forecaster.detect_emerging_trends()
        
        print("\n📊 DETAILED TREND ANALYSIS:")
        print("-" * 70)
        print(trends.to_string(index=False))
        
        input("\nPress Enter to continue...")
        
    def view_statistics(self):
        """View system statistics and reports"""
        if not self.data_generated:
            print("\n⚠️ Please generate dataset first (Option 1)")
            input("\nPress Enter to continue...")
            return
        
        print("\n" + "="*70)
        print("SYSTEM STATISTICS & REPORTS")
        print("="*70)
        
        if self.recommendation_system:
            self.recommendation_system.generate_report()
        else:
            # Load data and generate basic stats
            patients = pd.read_csv('/home/claude/patients.csv')
            health_records = pd.read_csv('/home/claude/health_records.csv')
            treatments = pd.read_csv('/home/claude/treatments.csv')
            
            print("\n📊 DATASET OVERVIEW:")
            print(f"  Total Patients: {len(patients)}")
            print(f"  Total Health Records: {len(health_records)}")
            print(f"  Total Treatments: {len(treatments)}")
            
            print("\n👥 PATIENT DEMOGRAPHICS:")
            print(f"  Age Range: {patients['age'].min()}-{patients['age'].max()} years")
            print(f"  Gender Distribution:")
            gender_dist = patients['gender'].value_counts()
            for gender, count in gender_dist.items():
                print(f"    {gender}: {count} ({count/len(patients)*100:.1f}%)")
            
            print("\n⚖️ PRAKRITI DISTRIBUTION:")
            prakriti_dist = patients['prakriti'].value_counts()
            for prakriti, count in prakriti_dist.head(5).items():
                print(f"  {prakriti}: {count} ({count/len(patients)*100:.1f}%)")
            
            print("\n🏥 TREATMENT OUTCOMES:")
            outcome_dist = treatments['outcome'].value_counts()
            for outcome, count in outcome_dist.items():
                print(f"  {outcome}: {count} ({count/len(treatments)*100:.1f}%)")
        
        input("\nPress Enter to continue...")
        
    def run(self):
        """Main system loop"""
        self.display_banner()
        
        while True:
            self.display_menu()
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                self.generate_dataset()
            elif choice == '2':
                self.train_models()
            elif choice == '3':
                self.personalized_recommendation()
            elif choice == '4':
                self.forecast_risks()
            elif choice == '5':
                self.detect_trends()
            elif choice == '6':
                self.view_statistics()
            elif choice == '7':
                print("\n" + "="*70)
                print("Thank you for using the Intelligent AYUSH Health System!")
                print("Stay healthy with personalized AYUSH care.")
                print("="*70 + "\n")
                sys.exit(0)
            else:
                print("\n❌ Invalid choice. Please enter a number between 1 and 7.")
                input("\nPress Enter to continue...")


def main():
    """Entry point"""
    system = AYUSHHealthSystem()
    system.run()


if __name__ == "__main__":
    main()
