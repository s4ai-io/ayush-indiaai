import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# Indian cities for synthetic data
INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur',
    'Indore', 'Bhopal', 'Visakhapatnam', 'Patna', 'Vadodara', 'Ghaziabad'
]

class AYUSHDataGenerator:
    """Generate synthetic AYUSH health system dataset"""
    
    def __init__(self, n_patients=1000):
        self.n_patients = n_patients
        
        # AYUSH-specific configurations
        self.doshas = ['Vata', 'Pitta', 'Kapha', 'Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha']
        self.prakriti_types = ['Vata', 'Pitta', 'Kapha', 'Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha', 'Tridosha']
        
        self.diseases = {
            'Respiratory': ['Asthma', 'Bronchitis', 'Common Cold', 'Sinusitis', 'Allergic Rhinitis'],
            'Digestive': ['IBS', 'Acidity', 'Constipation', 'Gastritis', 'Indigestion'],
            'Metabolic': ['Diabetes', 'Obesity', 'Thyroid Disorder', 'High Cholesterol'],
            'Musculoskeletal': ['Arthritis', 'Back Pain', 'Joint Pain', 'Muscle Weakness'],
            'Mental': ['Anxiety', 'Depression', 'Insomnia', 'Stress', 'Migraine'],
            'Skin': ['Eczema', 'Psoriasis', 'Acne', 'Dermatitis'],
            'Lifestyle': ['Hypertension', 'Fatigue', 'Poor Immunity']
        }
        
        self.herbs = [
            'Ashwagandha', 'Tulsi', 'Turmeric', 'Ginger', 'Triphala',
            'Brahmi', 'Neem', 'Amla', 'Giloy', 'Shatavari',
            'Guggul', 'Arjuna', 'Moringa', 'Haritaki', 'Licorice'
        ]
        
        self.yoga_practices = [
            'Surya Namaskar', 'Pranayama', 'Anulom Vilom', 'Kapalbhati',
            'Bhujangasana', 'Shavasana', 'Meditation', 'Vajrasana',
            'Trikonasana', 'Paschimottanasana'
        ]
        
        self.diet_types = ['Vegetarian', 'Vegan', 'Sattvic', 'Mixed', 'Rajasic']
        self.seasons = ['Spring', 'Summer', 'Monsoon', 'Autumn', 'Winter', 'Late Winter']
        
    def generate_patient_demographics(self):
        """Generate patient demographic data"""
        patients = []
        
        for i in range(self.n_patients):
            age = np.random.randint(18, 80)
            gender = random.choice(['Male', 'Female'])
            
            # Prakriti distribution (natural constitution)
            prakriti = np.random.choice(self.prakriti_types, p=[0.15, 0.20, 0.15, 0.20, 0.15, 0.10, 0.05])
            
            # Current dosha imbalance (Vikriti)
            if prakriti in ['Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha']:
                vikriti = random.choice(prakriti.split('-') + [prakriti])
            else:
                vikriti = np.random.choice(self.doshas, p=[0.25, 0.25, 0.25, 0.10, 0.08, 0.07])
            
            patient = {
                'patient_id': f'P{i+1:05d}',
                'age': age,
                'gender': gender,
                'prakriti': prakriti,
                'vikriti': vikriti,
                'bmi': round(np.random.normal(25, 4), 1),
                'city': random.choice(INDIAN_CITIES),
                'occupation': random.choice(['Office Worker', 'Manual Labor', 'Student', 'Retired', 'Healthcare', 'Teacher'])
            }
            patients.append(patient)
        
        return pd.DataFrame(patients)
    
    def generate_health_records(self, patients_df):
        """Generate health records with diseases and symptoms"""
        records = []
        
        for _, patient in patients_df.iterrows():
            # Number of visits per patient (1-5)
            n_visits = np.random.randint(1, 6)
            
            for visit in range(n_visits):
                # Date of visit (last 2 years)
                visit_date = datetime.now() - timedelta(days=np.random.randint(1, 730))
                season = self._get_season(visit_date.month)
                
                # Disease category based on dosha imbalance
                disease_category = self._disease_for_dosha(patient['vikriti'])
                disease = random.choice(self.diseases[disease_category])
                
                # Severity (1-10)
                severity = np.random.randint(3, 10)
                
                # Duration of illness (days)
                duration = np.random.randint(7, 180)
                
                # Lifestyle factors
                sleep_hours = round(np.random.normal(6.5, 1.5), 1)
                exercise_days = np.random.randint(0, 8)
                stress_level = np.random.randint(1, 11)
                diet_type = random.choice(self.diet_types)
                
                record = {
                    'patient_id': patient['patient_id'],
                    'visit_date': visit_date,
                    'season': season,
                    'disease_category': disease_category,
                    'disease': disease,
                    'severity': severity,
                    'duration_days': duration,
                    'sleep_hours': max(3, min(10, sleep_hours)),
                    'exercise_days_week': exercise_days,
                    'stress_level': stress_level,
                    'diet_type': diet_type,
                    'water_intake_liters': round(np.random.uniform(1.5, 4), 1),
                    'meditation_minutes': np.random.randint(0, 60)
                }
                records.append(record)
        
        return pd.DataFrame(records)
    
    def generate_treatments(self, health_records_df, patients_df):
        """Generate treatment plans and outcomes"""
        treatments = []
        
        for _, record in health_records_df.iterrows():
            # Get patient info
            patient = patients_df[patients_df['patient_id'] == record['patient_id']].iloc[0]
            
            # Treatment components
            n_herbs = np.random.randint(2, 5)
            prescribed_herbs = random.sample(self.herbs, n_herbs)
            
            n_yoga = np.random.randint(1, 4)
            prescribed_yoga = random.sample(self.yoga_practices, n_yoga)
            
            # Dietary recommendations
            diet_recommendations = self._get_diet_for_dosha(patient['vikriti'])
            
            # Treatment duration (weeks)
            treatment_duration = np.random.randint(4, 16)
            
            # Compliance (adherence to treatment)
            compliance = round(np.random.beta(8, 2), 2)  # Most patients have good compliance
            
            # Outcome calculation (based on compliance, severity, etc.)
            base_improvement = compliance * 0.7
            severity_factor = (10 - record['severity']) / 10 * 0.2
            lifestyle_factor = (record['exercise_days_week'] / 7 + record['meditation_minutes'] / 60) * 0.1
            
            improvement = min(1.0, base_improvement + severity_factor + lifestyle_factor + np.random.normal(0, 0.1))
            improvement = max(0.1, improvement)
            
            outcome = 'Cured' if improvement > 0.8 else 'Significant Improvement' if improvement > 0.5 else 'Moderate Improvement' if improvement > 0.3 else 'Mild Improvement'
            
            treatment = {
                'patient_id': record['patient_id'],
                'visit_date': record['visit_date'],
                'disease': record['disease'],
                'herbs_prescribed': ','.join(prescribed_herbs),
                'yoga_prescribed': ','.join(prescribed_yoga),
                'diet_plan': diet_recommendations,
                'treatment_duration_weeks': treatment_duration,
                'compliance_rate': compliance,
                'improvement_percentage': round(improvement * 100, 1),
                'outcome': outcome,
                'follow_up_required': 'Yes' if improvement < 0.7 else 'No'
            }
            treatments.append(treatment)
        
        return pd.DataFrame(treatments)
    
    def generate_public_health_trends(self, n_months=24):
        """Generate public health trend data for disease forecasting"""
        trends = []
        start_date = datetime.now() - timedelta(days=30*n_months)
        
        for month in range(n_months):
            current_date = start_date + timedelta(days=30*month)
            season = self._get_season(current_date.month)
            
            for category, diseases in self.diseases.items():
                for disease in diseases:
                    # Seasonal variation
                    base_cases = np.random.randint(50, 500)
                    seasonal_factor = self._seasonal_factor(disease, season)
                    
                    cases = int(base_cases * seasonal_factor * np.random.uniform(0.8, 1.2))
                    
                    trend = {
                        'month': current_date.strftime('%Y-%m'),
                        'season': season,
                        'disease_category': category,
                        'disease': disease,
                        'cases_reported': cases,
                        'avg_severity': round(np.random.uniform(4, 8), 1),
                        'avg_age': round(np.random.uniform(30, 60), 1)
                    }
                    trends.append(trend)
        
        return pd.DataFrame(trends)
    
    def _disease_for_dosha(self, dosha):
        """Map dosha imbalance to disease categories"""
        dosha_disease_map = {
            'Vata': np.random.choice(['Musculoskeletal', 'Mental', 'Respiratory'], p=[0.4, 0.4, 0.2]),
            'Pitta': np.random.choice(['Digestive', 'Skin', 'Metabolic'], p=[0.4, 0.3, 0.3]),
            'Kapha': np.random.choice(['Respiratory', 'Metabolic', 'Lifestyle'], p=[0.4, 0.3, 0.3])
        }
        
        base_dosha = dosha.split('-')[0]
        return dosha_disease_map.get(base_dosha, random.choice(list(self.diseases.keys())))
    
    def _get_diet_for_dosha(self, dosha):
        """Dietary recommendations based on dosha"""
        diet_map = {
            'Vata': 'Warm, cooked foods; healthy fats; sweet fruits',
            'Pitta': 'Cooling foods; sweet & bitter tastes; avoid spicy',
            'Kapha': 'Light, dry foods; pungent tastes; reduce dairy'
        }
        base_dosha = dosha.split('-')[0]
        return diet_map.get(base_dosha, 'Balanced, seasonal foods')
    
    def _get_season(self, month):
        """Get season from month"""
        season_map = {
            1: 'Late Winter', 2: 'Late Winter', 3: 'Spring', 4: 'Spring',
            5: 'Summer', 6: 'Summer', 7: 'Monsoon', 8: 'Monsoon',
            9: 'Autumn', 10: 'Autumn', 11: 'Winter', 12: 'Winter'
        }
        return season_map[month]
    
    def _seasonal_factor(self, disease, season):
        """Seasonal variation in disease occurrence"""
        seasonal_diseases = {
            'Summer': {'Pitta': 1.5, 'Skin': 1.4},
            'Monsoon': {'Respiratory': 1.6, 'Digestive': 1.4},
            'Winter': {'Kapha': 1.5, 'Respiratory': 1.3}
        }
        
        for key_season, factors in seasonal_diseases.items():
            if key_season == season:
                for key, factor in factors.items():
                    if key in disease:
                        return factor
        return 1.0
    
    def generate_complete_dataset(self):
        """Generate complete AYUSH dataset"""
        print("Generating patient demographics...")
        patients = self.generate_patient_demographics()
        
        print("Generating health records...")
        health_records = self.generate_health_records(patients)
        
        print("Generating treatments and outcomes...")
        treatments = self.generate_treatments(health_records, patients)
        
        print("Generating public health trends...")
        trends = self.generate_public_health_trends()
        
        return {
            'patients': patients,
            'health_records': health_records,
            'treatments': treatments,
            'public_health_trends': trends
        }


if __name__ == "__main__":
    # Generate dataset
    generator = AYUSHDataGenerator(n_patients=1000)
    datasets = generator.generate_complete_dataset()
    
    # Save to CSV
    print("\nSaving datasets to CSV...")
    datasets['patients'].to_csv('/home/claude/patients.csv', index=False)
    datasets['health_records'].to_csv('/home/claude/health_records.csv', index=False)
    datasets['treatments'].to_csv('/home/claude/treatments.csv', index=False)
    datasets['public_health_trends'].to_csv('/home/claude/public_health_trends.csv', index=False)
    
    print("\n✓ Dataset generation complete!")
    print(f"  - Patients: {len(datasets['patients'])} records")
    print(f"  - Health Records: {len(datasets['health_records'])} records")
    print(f"  - Treatments: {len(datasets['treatments'])} records")
    print(f"  - Public Health Trends: {len(datasets['public_health_trends'])} records")
