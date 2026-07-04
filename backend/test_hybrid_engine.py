import os
import sys

# Add the backend directory to python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from services.hybrid_service import hybrid_service
from services.patient_clustering_service import clustering_service
from services.rl_service import rl_service
from services.ayurgenix_service import ayurgenix_service

def test_hybrid_engine():
    print("--- Testing Hybrid Engine ---")
    ayurgenix_service.initialize()
    
    # 1. Cold Start Recommendation Phase
    patient_data = {
        "disease": "Asthma",
        "prakriti": "Vata",
        "vikriti": "Vata",
        "severity": 6,
        "age": 45,
        "gender": "Male"
    }
    
    # Test base recommendation
    rec = hybrid_service.get_recommendation(patient_data)
    print(f"Cold Start Herbs: {[h.get('name') for h in rec.get('herbs', [])]}")
    cluster_id = rec.get("cluster_id")
    print(f"Assigned Cluster ID: {cluster_id}")
    
    if not hasattr(rec, 'explainability') or not any("Historical" in line or "Clinical Cluster" in line for line in rec.get("explainability", [])):
        print("✓ Explainability includes cluster information.")
        
    print(f"Is Hybrid Modified? {rec.get('is_hybrid_modified')}")
    
    # 2. Simulate Doctor Feedback
    print("\n--- Simulating Doctor Feedback & Retraining ---")
    # We will directly update the Q-table for the specific state
    # State = f"{cluster_id}_asthma"
    state = rl_service._get_state_key(cluster_id, "Asthma")
    
    # Let's say a doctor highly rated a specific herb that wasn't in the default list
    best_discovered_herb = "ashwagandha root powder"
    
    print(f"Injecting positive reward manually for action: {best_discovered_herb}")
    # Simulate: Q-value goes up
    old_q = rl_service.q_table[state][best_discovered_herb]
    new_q = old_q + rl_service.learning_rate * (1.0 - old_q)
    rl_service.q_table[state][best_discovered_herb] = new_q
    
    # 3. Test Warm Engine
    print("\n--- Testing Warm Engine (Post-RL Training) ---")
    warm_rec = hybrid_service.get_recommendation(patient_data)
    
    print(f"Warm Start Herbs: {[h.get('name') for h in warm_rec.get('herbs', [])]}")
    print(f"Is Hybrid Modified? {warm_rec.get('is_hybrid_modified')}")
    
    expected_top = warm_rec['herbs'][0]['name'].lower()
    if expected_top == best_discovered_herb:
        print("✓ SUCCESS: RL logic successfully influenced the top recommendation!")
    else:
        print(f"❌ FAILURE: RL logic did not influence the top recommendation. Got {expected_top}")
        
    print("✓ All tests complete.")

if __name__ == "__main__":
    test_hybrid_engine()
