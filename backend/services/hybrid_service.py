from services.ISHAAyush_service import ISHAAyush_service
from services.clustering_service import clustering_service
from services.rl_service import rl_service
import copy

class HybridRecommendationEngine:
    """
    Orchestrates the hybrid recommendation process:
    1. Base Content Matching (Rules mapping Disease + Prakriti)
    2. Patient Clustering
    3. Reinforcement Learning (Bandits overlay)
    """
    def __init__(self):
        pass

    def get_recommendation(self, patient_data: dict) -> dict:
        """
        Produce a full hybrid recommendation dict.
        """
        # 1. Base Strategy: Codified Rules execution
        # Get the standard Ayurvedic recommendations
        base_recommendation = ISHAAyush_service.get_recommendation(patient_data)
        
        # If no match in the rule base, return early
        if base_recommendation.get("no_match_found"):
            return base_recommendation

        # Work on a copy to modify
        hybrid_rec = copy.deepcopy(base_recommendation)
        
        # 2. Extract Cluster
        try:
            cluster_id = clustering_service.get_cluster(patient_data)
            hybrid_rec["cluster_id"] = cluster_id
        except Exception as e:
            print(f"Clustering error: {e}")
            cluster_id = 0
            hybrid_rec["cluster_id"] = cluster_id

        # 3. Consult RL Pipeline
        disease = patient_data.get('disease', '')
        best_learned_action = None
        best_learned_yoga = None
        
        try:
            # We don't restrict to available actions because the base might be lacking 
            # and the RL learned a totally new herb for this cluster.
            best_learned_action = rl_service.get_best_action(cluster_id, disease)
            
            # (Optional) we can also extract yoga actions explicitly
            if best_learned_action and best_learned_action.startswith("yoga:"):
                best_learned_yoga = best_learned_action.replace("yoga:", "")
                best_learned_action = None
        except Exception as e:
            print(f"RL Pipeline error: {e}")

        # 4. Hybrid Merging (Cold-start handling is implicit: if no best_action, stick to base)
        explainability = hybrid_rec.get("explainability", [])
        
        # Add clustered insight
        explainability.insert(0, f"Patient grouped into Clinical Cluster {cluster_id} based on historical outcomes.")

        modified = False

        if best_learned_action:
            # Check if it's already in the base
            existing_herbs = [h.get("name", "").lower() for h in hybrid_rec.get("herbs", [])]
            if best_learned_action not in existing_herbs:
                hybrid_rec["herbs"].insert(0, {
                    "name": best_learned_action.title(),
                    "dosage": "As per physician",
                    "benefits": f"AI Discovered: Highly effective for Cluster {cluster_id} with {disease}."
                })
                explainability.append(f"Added {best_learned_action.title()} based on positive clinician feedback for similar patients.")
                modified = True
                
        if best_learned_yoga:
            existing_yoga = [y.get("practice", "").lower() for y in hybrid_rec.get("yoga", [])]
            if best_learned_yoga not in existing_yoga:
                hybrid_rec["yoga"].insert(0, {
                    "practice": best_learned_yoga.title(),
                    "duration": "20 mins daily",
                    "benefits": f"AI Discovered: Highly effective for Cluster {cluster_id}."
                })
                explainability.append(f"Recommended {best_learned_yoga.title()} based on positive clinician feedback.")
                modified = True

        hybrid_rec["explainability"] = explainability
        hybrid_rec["is_hybrid_modified"] = modified
        
        return hybrid_rec

# Singleton
hybrid_service = HybridRecommendationEngine()
