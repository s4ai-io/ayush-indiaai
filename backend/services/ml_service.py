"""
ML Service Wrapper for AYUSH Recommendation System
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from ayush_ml_pipeline import AYUSHRecommendationSystem


class MLService:
    """Wrapper service for ML recommendation system"""
    
    def __init__(self):
        self.system = None
        self.initialized = False
        
    def initialize(self):
        """Initialize and load ML models"""
        try:
            print("Initializing ML Service...")
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            
            self.system = AYUSHRecommendationSystem(
                models_dir=models_dir,
                data_dir=data_dir
            )
            
            # Try to load pre-trained models
            models_loaded = self.system.load_pretrained_models()
            
            if not models_loaded:
                print("⚠️  Pre-trained models not found. Service will use rule-based recommendations.")
                print("To use ML predictions, please train models first.")
            
            self.initialized = True
            print("✓ ML Service initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing ML Service: {e}")
            return False
    
    def get_recommendation(self, patient_data: dict) -> dict:
        """
        Get treatment recommendation for a patient
        
        Args:
            patient_data: Patient profile dict
            
        Returns:
            Treatment recommendation dict
        """
        if not self.initialized:
            raise RuntimeError("ML Service not initialized. Call initialize() first.")
        
        try:
            # Use API-friendly method
            recommendation = self.system.recommend_treatment_api(patient_data)
            return recommendation
            
        except Exception as e:
            raise ValueError(f"Error generating recommendation: {str(e)}")
    
    def health_check(self) -> dict:
        """Check service health"""
        return {
            "initialized": self.initialized,
            "models_loaded": self.system.models_loaded if self.system else False
        }


# Global instance
ml_service = MLService()
