import sys
import os
# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from ayush_ml_pipeline import AYUSHRecommendationSystem

print("Initializing system...")
ayush_system = AYUSHRecommendationSystem()

print("Loading data...")
try:
    ayush_system.load_pretrained_models()
except Exception as e:
    print(f"Error loading models: {e}")

print("Testing Recommendation API...")
patient_data = {
    "age": 35,
    "gender": "Male",
    "prakriti": "Vata-Pitta",
    "vikriti": "Vata",
    "disease": "Hypertension", # Using a known disease from dataset
    "severity": 7,
    "bmi": 24.5
}

try:
    result = ayush_system.recommend_treatment_api(patient_data)
    print("\nResult:")
    print(result)
except Exception as e:
    print(f"Error during inference: {e}")
    import traceback
    traceback.print_exc()
