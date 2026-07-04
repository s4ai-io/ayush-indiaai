from services.ISHAAyush_service import ISHAAyush_service
from services.patient_clustering_service import clustering_service
from services.rl_service import rl_service
import copy
import logging
import os

logger = logging.getLogger(__name__)

class HybridRecommendationEngine:
    """
    Orchestrates the hybrid recommendation process:
    1. Base Content Matching (Rules mapping Disease + Prakriti)
    2. Patient Clustering
    3. Reinforcement Learning (Bandits overlay)
    4. LLM Narration (Step 8, opt-in via ENABLE_LLM_NARRATION env var)
    """
    def __init__(self):
        pass

    def _generate_narration(self, herbs: list, yoga: list, disease: str, namc_code: str, prakriti: str, vikriti: str):
        """
        Call the Modal Gemma narration endpoint (sync via httpx) to generate a
        2-3 sentence clinical explanation of the finalised treatment plan.
        Returns None if the env var is unset, the endpoint is unreachable, or
        sentence-transformers/httpx are not installed.
        """
        modal_url = os.getenv("MODAL_GEMMA_URL")
        if not modal_url:
            return None

        herb_names = [h.get("name", "") if isinstance(h, dict) else str(h) for h in herbs]
        yoga_names = [y.get("practice", "") if isinstance(y, dict) else str(y) for y in yoga]

        user_prompt = (
            f"Disease: {disease} (NAMC: {namc_code})\n"
            f"Patient constitution — Prakriti: {prakriti}, Vikriti: {vikriti}\n"
            f"Prescribed herbs: {', '.join(filter(None, herb_names))}\n"
            f"Prescribed yoga: {', '.join(filter(None, yoga_names))}\n\n"
            "Explain why these specific herbs and practices were chosen for this patient's dosha profile."
        )

        try:
            import httpx
            resp = httpx.post(
                modal_url,
                data={"flow": "narration", "user_text_prompt": user_prompt},
                timeout=45.0,
            )
            if resp.status_code == 200:
                return resp.json().get("reply", "").strip() or None
        except Exception as e:
            logger.warning(f"LLM narration failed: {e}")
        return None

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
        
        # 2. Extract Cluster (analytics only — not used for RL state key)
        try:
            cluster_id = clustering_service.get_cluster(patient_data)
            hybrid_rec["cluster_id"] = cluster_id
        except Exception as e:
            print(f"Clustering error: {e}")
            cluster_id = 0
            hybrid_rec["cluster_id"] = cluster_id

        # 3. Consult RL Pipeline using new namc+prakriti+vikriti state key
        disease  = patient_data.get('disease', '')
        prakriti = patient_data.get('prakriti', '')
        vikriti  = patient_data.get('vikriti', '')
        namc_code = hybrid_rec.get("namc_code", "")

        # Build stable state key and expose it for the frontend
        state_key = rl_service._get_state_key(namc_code, prakriti, vikriti) if namc_code else None
        hybrid_rec["state_key"] = state_key

        learned_actions = []
        learned_yoga_actions = []

        try:
            learned_actions = rl_service.get_best_actions_by_namc(namc_code, prakriti, vikriti)
            # All positive-Q yoga actions sorted by Q-value
            yoga_q_table = rl_service.q_table.get(state_key or "", {})
            learned_yoga_actions = sorted(
                [(k.replace("yoga:", ""), v) for k, v in yoga_q_table.items()
                 if k.startswith("yoga:") and v > 0],
                key=lambda x: -x[1]
            )
        except Exception as e:
            print(f"RL Pipeline error: {e}")

        # 4. Hybrid Merging
        explainability = hybrid_rec.get("explainability", [])
        explainability.insert(0, f"Patient grouped into Clinical Cluster {cluster_id} based on historical outcomes.")

        modified = False

        # Add ALL learned herbs not already in base recommendation
        existing_herbs = {h.get("name", "").lower() for h in hybrid_rec.get("herbs", [])}
        for la in learned_actions:
            name = la["name"]
            if name.startswith("yoga:"):
                continue
            if name.lower() not in existing_herbs:
                hybrid_rec["herbs"].append({
                    "name": name.title(),
                    "dosage": "As per physician",
                    "benefits": f"AI Discovered: Recommended based on positive clinician feedback for {disease}.",
                    "ai_learned": True,
                })
                existing_herbs.add(name.lower())
                explainability.append(f"Added {name.title()} based on positive clinician feedback for similar patients.")
                modified = True

        existing_yoga = {y.get("practice", "").lower() for y in hybrid_rec.get("yoga", [])}
        for practice, _ in learned_yoga_actions:
            if practice.lower() not in existing_yoga:
                hybrid_rec["yoga"].append({
                    "practice": practice.title(),
                    "duration": "20 mins daily",
                    "benefits": f"AI Discovered: Recommended based on positive clinician feedback for {disease}.",
                    "ai_learned": True,
                })
                existing_yoga.add(practice.lower())
                explainability.append(f"Recommended {practice.title()} based on positive clinician feedback.")
                modified = True

        hybrid_rec["explainability"] = explainability
        hybrid_rec["is_hybrid_modified"] = modified

        # Step 8 — LLM Narration (opt-in via ENABLE_LLM_NARRATION=true)
        explanation_text = None
        enable_narration = os.getenv("ENABLE_LLM_NARRATION", "false").lower() == "true"
        if enable_narration:
            try:
                explanation_text = self._generate_narration(
                    herbs=hybrid_rec.get("herbs", []),
                    yoga=hybrid_rec.get("yoga", []),
                    disease=disease,
                    namc_code=hybrid_rec.get("namc_code", ""),
                    prakriti=patient_data.get("prakriti", ""),
                    vikriti=patient_data.get("vikriti", ""),
                )
            except Exception as e:
                logger.warning(f"Narration step error: {e}")

        # Fallback: join existing explainability strings
        if not explanation_text:
            explanation_text = " ".join(hybrid_rec.get("explainability", []))

        hybrid_rec["explanation_text"] = explanation_text

        # Expose original AI plan for frontend to send back on prescribe
        # (at this point the plan is unedited — this IS the original)
        import copy as _copy
        hybrid_rec["original_ai_plan"] = _copy.deepcopy({
            k: hybrid_rec[k]
            for k in ("herbs", "yoga", "diet", "lifestyle", "namc_code", "state_key")
            if k in hybrid_rec
        })

        return hybrid_rec

# Singleton
hybrid_service = HybridRecommendationEngine()
