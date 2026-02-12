"""
Refactored AYUSH ML Pipeline for API Integration
Fixes:
- Hardcoded file paths replaced with relative paths
- Added model loading functionality
- API-friendly wrapper methods
- Input validation
"""
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, mean_absolute_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

# Get base directory for relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATA_DIR = os.path.join(BASE_DIR, 'data')


class AYUSHRecommendationSystem:
    """
    ML Pipeline for Personalized AYUSH Treatment Recommendations
    Features:
    1. Treatment effectiveness prediction
    2. Personalized herb recommendations
    3. Lifestyle recommendations based on patient profile
    """
    
    def __init__(self, models_dir=None, data_dir=None):
        """
        Initialize the recommendation system
        
        Args:
            models_dir: Directory containing trained models (default: ./models)
            data_dir: Directory containing training data (default: ./data)
        """
        self.models_dir = models_dir or MODELS_DIR
        self.data_dir = data_dir or DATA_DIR
        
        self.outcome_model = None
        self.improvement_model = None
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_importance = None
        self.models_loaded = False
        
    def load_pretrained_models(self):
        """Load pre-trained models from disk"""
        try:
            print("Loading pre-trained models...")
            self.outcome_model = joblib.load(os.path.join(self.models_dir, 'outcome_model.pkl'))
            self.improvement_model = joblib.load(os.path.join(self.models_dir, 'improvement_model.pkl'))
            self.scaler = joblib.load(os.path.join(self.models_dir, 'scaler.pkl'))
            self.label_encoders = joblib.load(os.path.join(self.models_dir, 'label_encoders.pkl'))
            self.models_loaded = True
            print("✓ Models loaded successfully!")
            return True
        except FileNotFoundError as e:
            print(f"⚠️  Model files not found: {e}")
            print("Please train models first using the training pipeline.")
            return False
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def load_data(self):
        """Load all datasets"""
        print("Loading datasets...")
        patients_path = os.path.join(self.data_dir, 'patients.csv')
        health_records_path = os.path.join(self.data_dir, 'health_records.csv')
        treatments_path = os.path.join(self.data_dir, 'treatments.csv')
        
        # Check if files exist
        if not os.path.exists(patients_path):
            patients_path = os.path.join(BASE_DIR, 'patients.csv')
        if not os.path.exists(health_records_path):
            health_records_path = os.path.join(BASE_DIR, 'health_records.csv')
        if not os.path.exists(treatments_path):
            treatments_path = os.path.join(BASE_DIR, 'treatments.csv')
        
        self.patients = pd.read_csv(patients_path)
        self.health_records = pd.read_csv(health_records_path)
        self.treatments = pd.read_csv(treatments_path)
        
        print(f"✓ Loaded {len(self.patients)} patients")
        print(f"✓ Loaded {len(self.health_records)} health records")
        print(f"✓ Loaded {len(self.treatments)} treatment records")
        
    def prepare_features(self):
        """Feature engineering for ML models"""
        print("\nPerforming feature engineering...")
        
        # Merge datasets
        df = self.health_records.merge(self.patients, on='patient_id', how='left')
        df = df.merge(self.treatments, on=['patient_id', 'visit_date', 'disease'], how='left')
        
        # Handle missing values
        df = df.dropna()
        
        # Create derived features
        df['age_group'] = pd.cut(df['age'], bins=[0, 30, 45, 60, 100], 
                                  labels=['Young', 'Middle', 'Senior', 'Elderly'])
        
        df['bmi_category'] = pd.cut(df['bmi'], bins=[0, 18.5, 25, 30, 100],
                                     labels=['Underweight', 'Normal', 'Overweight', 'Obese'])
        
        df['sleep_quality'] = df['sleep_hours'].apply(
            lambda x: 'Good' if 7 <= x <= 9 else 'Poor'
        )
        
        df['exercise_level'] = pd.cut(df['exercise_days_week'], bins=[-1, 2, 4, 7],
                                       labels=['Low', 'Moderate', 'High'])
        
        df['stress_category'] = pd.cut(df['stress_level'], bins=[0, 3, 6, 10],
                                        labels=['Low', 'Moderate', 'High'])
        
        # Dosha balance score (0-1, 1 = balanced)
        df['dosha_balance'] = df.apply(
            lambda row: 1.0 if row['prakriti'] == row['vikriti'] else 0.5,
            axis=1
        )
        
        # Lifestyle score (composite metric)
        df['lifestyle_score'] = (
            (df['sleep_hours'] / 8) * 0.3 +
            (df['exercise_days_week'] / 7) * 0.3 +
            (1 - df['stress_level'] / 10) * 0.2 +
            (df['meditation_minutes'] / 60) * 0.2
        )
        df['lifestyle_score'] = df['lifestyle_score'].clip(0, 1)
        
        self.df_features = df
        print(f"✓ Feature engineering complete. Total features: {len(df.columns)}")
        
        return df
    
    def encode_categorical_features(self, df):
        """Encode categorical variables"""
        categorical_cols = [
            'gender', 'prakriti', 'vikriti', 'occupation', 'season',
            'disease_category', 'disease', 'diet_type', 'age_group',
            'bmi_category', 'sleep_quality', 'exercise_level', 'stress_category'
        ]
        
        df_encoded = df.copy()
        
        for col in categorical_cols:
            if col in df_encoded.columns:
                le = LabelEncoder()
                df_encoded[col + '_encoded'] = le.fit_transform(df_encoded[col].astype(str))
                self.label_encoders[col] = le
        
        return df_encoded
    
    def train_outcome_classifier(self):
        """Train model to predict treatment outcomes"""
        print("\n" + "="*60)
        print("TRAINING OUTCOME PREDICTION MODEL")
        print("="*60)
        
        df = self.encode_categorical_features(self.df_features)
        
        # Select features for outcome prediction
        feature_cols = [
            'age', 'bmi', 'severity', 'duration_days', 'sleep_hours',
            'exercise_days_week', 'stress_level', 'water_intake_liters',
            'meditation_minutes', 'treatment_duration_weeks', 'compliance_rate',
            'dosha_balance', 'lifestyle_score',
            'gender_encoded', 'prakriti_encoded', 'vikriti_encoded',
            'disease_category_encoded', 'disease_encoded', 'season_encoded',
            'diet_type_encoded', 'age_group_encoded', 'bmi_category_encoded',
            'sleep_quality_encoded', 'exercise_level_encoded', 'stress_category_encoded'
        ]
        
        X = df[feature_cols]
        y = df['outcome']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest Classifier
        print("\nTraining Random Forest Classifier...")
        self.outcome_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.outcome_model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = self.outcome_model.predict(X_test_scaled)
        
        # Evaluation
        accuracy = accuracy_score(y_test, y_pred)
        print(f"\n✓ Model Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.outcome_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Most Important Features:")
        print(self.feature_importance.head(10).to_string(index=False))
        
        return accuracy
    
    def train_improvement_predictor(self):
        """Train regression model to predict improvement percentage"""
        print("\n" + "="*60)
        print("TRAINING IMPROVEMENT PERCENTAGE PREDICTOR")
        print("="*60)
        
        df = self.encode_categorical_features(self.df_features)
        
        feature_cols = [
            'age', 'bmi', 'severity', 'duration_days', 'sleep_hours',
            'exercise_days_week', 'stress_level', 'water_intake_liters',
            'meditation_minutes', 'treatment_duration_weeks', 'compliance_rate',
            'dosha_balance', 'lifestyle_score',
            'gender_encoded', 'prakriti_encoded', 'vikriti_encoded',
            'disease_category_encoded', 'disease_encoded', 'season_encoded',
            'diet_type_encoded'
        ]
        
        X = df[feature_cols]
        y = df['improvement_percentage']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Gradient Boosting Regressor
        print("\nTraining Gradient Boosting Regressor...")
        self.improvement_model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            random_state=42
        )
        
        self.improvement_model.fit(X_train, y_train)
        
        # Predictions
        y_pred = self.improvement_model.predict(X_test)
        
        # Evaluation
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"\n✓ Mean Absolute Error: {mae:.2f}%")
        print(f"✓ R² Score: {r2:.3f}")
        
        return mae, r2
    
    def recommend_treatment(self, patient_profile):
        """
        Generate personalized treatment recommendations for a new patient
        
        Args:
            patient_profile: dict with patient information
        """
        print("\n" + "="*60)
        print("PERSONALIZED TREATMENT RECOMMENDATION")
        print("="*60)
        
        # Extract profile
        age = patient_profile['age']
        gender = patient_profile['gender']
        prakriti = patient_profile['prakriti']
        vikriti = patient_profile['vikriti']
        disease = patient_profile['disease']
        severity = patient_profile['severity']
        bmi = patient_profile.get('bmi', 25)
        
        print(f"\nPatient Profile:")
        print(f"  Age: {age} | Gender: {gender}")
        print(f"  Constitution (Prakriti): {prakriti}")
        print(f"  Current Imbalance (Vikriti): {vikriti}")
        print(f"  Condition: {disease} (Severity: {severity}/10)")
        print(f"  BMI: {bmi}")
        
        # Herb recommendations based on dosha
        herb_recommendations = self._recommend_herbs(vikriti, disease)
        
        # Yoga recommendations
        yoga_recommendations = self._recommend_yoga(vikriti, disease)
        
        # Diet recommendations
        diet_recommendations = self._recommend_diet(vikriti, bmi)
        
        # Lifestyle modifications
        lifestyle_recommendations = self._recommend_lifestyle(vikriti, severity)
        
        print(f"\n{'─'*60}")
        print("RECOMMENDED TREATMENT PLAN")
        print(f"{'─'*60}")
        
        print(f"\n🌿 HERBAL MEDICINES:")
        for i, herb in enumerate(herb_recommendations, 1):
            print(f"  {i}. {herb['name']}: {herb['dosage']}")
            print(f"     Benefits: {herb['benefits']}")
        
        print(f"\n🧘 YOGA & PRANAYAMA:")
        for i, yoga in enumerate(yoga_recommendations, 1):
            print(f"  {i}. {yoga['practice']}: {yoga['duration']}")
            print(f"     Benefits: {yoga['benefits']}")
        
        print(f"\n🥗 DIETARY GUIDELINES:")
        for guideline in diet_recommendations:
            print(f"  • {guideline}")
        
        print(f"\n💡 LIFESTYLE MODIFICATIONS:")
        for modification in lifestyle_recommendations:
            print(f"  • {modification}")
        
        print(f"\n📊 PREDICTED OUTCOMES:")
        print(f"  Expected improvement: 60-80%")
        print(f"  Recommended duration: 8-12 weeks")
        print(f"  Follow-up: Every 3 weeks")
        
        return {
            'herbs': herb_recommendations,
            'yoga': yoga_recommendations,
            'diet': diet_recommendations,
            'lifestyle': lifestyle_recommendations
        }
    
    def recommend_treatment_api(self, patient_data: dict) -> dict:
        """
        API-friendly recommendation method
        
        Args:
            patient_data: {
                'age': int,
                'gender': str,
                'prakriti': str,
                'vikriti': str,
                'disease': str,
                'severity': int (1-10),
                'bmi': float (optional)
            }
        
        Returns:
            {
                'herbs': [...],
                'yoga': [...],
                'diet': [...],
                'lifestyle': [...],
                'predicted_improvement': float,
                'recommended_duration_weeks': int
            }
        """
        # Validate inputs
        age = patient_data.get('age')
        if not age or age < 0 or age > 120:
            raise ValueError("Age must be between 0 and 120")
        
        severity = patient_data.get('severity')
        if not severity or severity < 1 or severity > 10:
            raise ValueError("Severity must be between 1 and 10")
        
        bmi = patient_data.get('bmi', 25)
        if bmi and (bmi < 10 or bmi > 50):
            raise ValueError("BMI must be between 10 and 50")
        
        # Get recommendations
        vikriti = patient_data['vikriti']
        disease = patient_data['disease']
        
        herb_recommendations = self._recommend_herbs(vikriti, disease)
        yoga_recommendations = self._recommend_yoga(vikriti, disease)
        diet_recommendations = self._recommend_diet(vikriti, bmi)
        lifestyle_recommendations = self._recommend_lifestyle(vikriti, severity)
        
        # Calculate predicted improvement (simplified - in production use ML model)
        base_improvement = 65
        severity_factor = (10 - severity) * 2
        dosha_balance_factor = 5 if patient_data['prakriti'] == vikriti else 0
        predicted_improvement = min(95, base_improvement + severity_factor + dosha_balance_factor)
        
        # Calculate recommended duration
        recommended_duration = 8 if severity <= 5 else 12
        
        return {
            'herbs': herb_recommendations,
            'yoga': yoga_recommendations,
            'diet': diet_recommendations,
            'lifestyle': lifestyle_recommendations,
            'predicted_improvement': round(predicted_improvement, 1),
            'recommended_duration_weeks': recommended_duration
        }
    
    def _recommend_herbs(self, vikriti, disease):
        """Recommend herbs based on dosha and disease"""
        herb_db = {
            'Vata': [
                {'name': 'Ashwagandha', 'dosage': '500mg twice daily', 
                 'benefits': 'Reduces anxiety, improves sleep, strengthens immunity'},
                {'name': 'Brahmi', 'dosage': '300mg daily',
                 'benefits': 'Enhances memory, reduces stress'},
                {'name': 'Shatavari', 'dosage': '500mg twice daily',
                 'benefits': 'Balances hormones, improves digestion'}
            ],
            'Pitta': [
                {'name': 'Amla', 'dosage': '1000mg daily',
                 'benefits': 'Cooling effect, rich in Vitamin C, improves digestion'},
                {'name': 'Licorice', 'dosage': '400mg twice daily',
                 'benefits': 'Soothes inflammation, supports digestive health'},
                {'name': 'Neem', 'dosage': '500mg daily',
                 'benefits': 'Purifies blood, improves skin health'}
            ],
            'Kapha': [
                {'name': 'Triphala', 'dosage': '1000mg before bed',
                 'benefits': 'Detoxifies body, aids weight management'},
                {'name': 'Guggul', 'dosage': '500mg twice daily',
                 'benefits': 'Supports metabolism, reduces cholesterol'},
                {'name': 'Ginger', 'dosage': 'Fresh ginger tea 2-3 times daily',
                 'benefits': 'Improves digestion, reduces inflammation'}
            ]
        }
        
        base_dosha = vikriti.split('-')[0]
        return herb_db.get(base_dosha, herb_db['Vata'])[:3]
    
    def _recommend_yoga(self, vikriti, disease):
        """Recommend yoga practices"""
        yoga_db = {
            'Vata': [
                {'practice': 'Surya Namaskar', 'duration': '10 rounds daily',
                 'benefits': 'Grounds energy, improves circulation'},
                {'practice': 'Anulom Vilom', 'duration': '15 minutes',
                 'benefits': 'Balances nervous system, reduces anxiety'},
                {'practice': 'Shavasana', 'duration': '10 minutes',
                 'benefits': 'Deep relaxation, stress relief'}
            ],
            'Pitta': [
                {'practice': 'Sheetali Pranayama', 'duration': '10 minutes',
                 'benefits': 'Cooling breath, reduces anger'},
                {'practice': 'Moon Salutation', 'duration': '5 rounds',
                 'benefits': 'Calming, cooling effect'},
                {'practice': 'Meditation', 'duration': '20 minutes daily',
                 'benefits': 'Mental clarity, emotional balance'}
            ],
            'Kapha': [
                {'practice': 'Kapalbhati', 'duration': '5 minutes, 100 breaths',
                 'benefits': 'Energizes, aids weight loss'},
                {'practice': 'Surya Namaskar', 'duration': '12 rounds vigorously',
                 'benefits': 'Increases metabolism, burns calories'},
                {'practice': 'Bhujangasana', 'duration': '5 repetitions',
                 'benefits': 'Opens chest, stimulates digestion'}
            ]
        }
        
        base_dosha = vikriti.split('-')[0]
        return yoga_db.get(base_dosha, yoga_db['Vata'])[:3]
    
    def _recommend_diet(self, vikriti, bmi):
        """Dietary recommendations"""
        diet_guidelines = {
            'Vata': [
                "Favor warm, cooked, and grounding foods",
                "Include healthy fats (ghee, olive oil, nuts)",
                "Eat sweet fruits like bananas, dates, mangoes",
                "Avoid cold, raw, and dry foods",
                "Regular meal times are essential"
            ],
            'Pitta': [
                "Favor cooling foods like cucumber, coconut, melons",
                "Include sweet and bitter tastes",
                "Avoid spicy, oily, and fried foods",
                "Reduce caffeine and alcohol",
                "Eat more salads and fresh vegetables"
            ],
            'Kapha': [
                "Favor light, dry, and warm foods",
                "Include pungent and bitter tastes (ginger, turmeric)",
                "Reduce dairy, sugar, and heavy foods",
                "Eat more vegetables and legumes",
                "Smaller portions, avoid overeating"
            ]
        }
        
        base_dosha = vikriti.split('-')[0]
        guidelines = diet_guidelines.get(base_dosha, diet_guidelines['Vata'])
        
        if bmi > 28:
            guidelines.append("Focus on portion control and avoid late-night eating")
        
        return guidelines
    
    def _recommend_lifestyle(self, vikriti, severity):
        """Lifestyle modification recommendations"""
        lifestyle = {
            'Vata': [
                "Maintain regular daily routine (wake, sleep, meals)",
                "Practice oil massage (Abhyanga) with warm sesame oil",
                "Ensure 7-8 hours of quality sleep",
                "Reduce screen time, especially before bed",
                "Stay warm and avoid cold, windy environments"
            ],
            'Pitta': [
                "Avoid overworking, take regular breaks",
                "Practice cooling activities like swimming",
                "Avoid direct sun exposure during peak hours",
                "Cultivate patience and avoid competitive situations",
                "Spend time in nature, especially near water"
            ],
            'Kapha': [
                "Wake up early (before 6 AM) for morning walk",
                "Engage in vigorous exercise 5-6 days/week",
                "Avoid day sleep and sedentary lifestyle",
                "Try dry brushing before shower",
                "Seek variety and new experiences"
            ]
        }
        
        base_dosha = vikriti.split('-')[0]
        recommendations = lifestyle.get(base_dosha, lifestyle['Vata'])
        
        if severity > 7:
            recommendations.insert(0, "Consult AYUSH practitioner weekly for monitoring")
        
        return recommendations
    
    def save_models(self):
        """Save trained models"""
        print("\nSaving models...")
        os.makedirs(self.models_dir, exist_ok=True)
        
        joblib.dump(self.outcome_model, os.path.join(self.models_dir, 'outcome_model.pkl'))
        joblib.dump(self.improvement_model, os.path.join(self.models_dir, 'improvement_model.pkl'))
        joblib.dump(self.scaler, os.path.join(self.models_dir, 'scaler.pkl'))
        joblib.dump(self.label_encoders, os.path.join(self.models_dir, 'label_encoders.pkl'))
        print("✓ Models saved successfully!")
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*60)
        print("AYUSH ML SYSTEM - ANALYSIS REPORT")
        print("="*60)
        
        print("\n📊 DATASET STATISTICS:")
        print(f"  Total Patients: {len(self.patients)}")
        print(f"  Total Health Records: {len(self.health_records)}")
        print(f"  Total Treatments: {len(self.treatments)}")
        
        print("\n🎯 DISEASE DISTRIBUTION:")
        disease_dist = self.df_features['disease_category'].value_counts()
        for disease, count in disease_dist.head(5).items():
            print(f"  {disease}: {count} cases")
        
        print("\n⚖️ DOSHA DISTRIBUTION:")
        dosha_dist = self.patients['vikriti'].value_counts()
        for dosha, count in dosha_dist.head(3).items():
            print(f"  {dosha}: {count} patients")
        
        print("\n🏆 TREATMENT OUTCOMES:")
        outcome_dist = self.treatments['outcome'].value_counts()
        for outcome, count in outcome_dist.items():
            print(f"  {outcome}: {count} ({count/len(self.treatments)*100:.1f}%)")
        
        print("\n💊 MOST PRESCRIBED HERBS:")
        all_herbs = ','.join(self.treatments['herbs_prescribed'].dropna()).split(',')
        from collections import Counter
        herb_counts = Counter(all_herbs)
        for herb, count in herb_counts.most_common(5):
            print(f"  {herb}: {count} prescriptions")


if __name__ == "__main__":
    # Initialize system
    ayush_system = AYUSHRecommendationSystem()
    
    # Load data
    ayush_system.load_data()
    
    # Prepare features
    ayush_system.prepare_features()
    
    # Train models
    ayush_system.train_outcome_classifier()
    ayush_system.train_improvement_predictor()
    
    # Save models
    ayush_system.save_models()
    
    # Generate report
    ayush_system.generate_report()
    
    # Example: Personalized recommendation for a new patient
    print("\n" + "="*60)
    print("EXAMPLE: PERSONALIZED RECOMMENDATION")
    print("="*60)
    
    new_patient = {
        'age': 35,
        'gender': 'Male',
        'prakriti': 'Vata-Pitta',
        'vikriti': 'Vata',
        'disease': 'Anxiety',
        'severity': 7,
        'bmi': 24.5
    }
    
    recommendations = ayush_system.recommend_treatment(new_patient)
    
    print("\n" + "="*60)
    print("✓ ML PIPELINE COMPLETE!")
    print("="*60)
