import os
import json
import joblib
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from models import SessionLocal, TreatmentFeedback, ClinicalOutcomeScore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'data', 'models')
Q_TABLE_PATH = os.path.join(MODELS_DIR, 'rl_q_table.pkl')

class RLRecommendationService:
    """
    Reinforcement Learning Pipeline using Epsilon-Greedy Contextual Bandits.
    Learns the best 'actions' (treatments/herbs) for a given 'state' (Cluster + Disease).
    """
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.2):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        # Q-Table structure: q_table[state][action] = q_value
        # state is a string "ClusterID_DiseaseName"
        # action is a string "HerbName" or "YogaPractice"
        self.q_table = {}
        self._load_model()

    def _load_model(self):
        if os.path.exists(Q_TABLE_PATH):
            try:
                self.q_table = joblib.load(Q_TABLE_PATH)
                print(f"✓ RL Q-Table loaded from {Q_TABLE_PATH}")
            except Exception as e:
                print(f"❌ Failed to load RL Q-Table: {e}")

    def _save_model(self):
        try:
            joblib.dump(self.q_table, Q_TABLE_PATH)
            print(f"✓ RL Q-Table saved to {Q_TABLE_PATH}")
        except Exception as e:
            print(f"❌ Failed to save RL Q-Table: {e}")

    def _get_state_key(self, cluster_id: int, disease: str) -> str:
        disease_clean = disease.strip().lower() if disease else "unknown"
        return f"{cluster_id}_{disease_clean}"

    def get_best_action(self, cluster_id: int, disease: str, available_actions: list = None) -> str:
        """
        Get the best learned action for a state, with epsilon exploration.
        """
        state = self._get_state_key(cluster_id, disease)
        
        # Explore
        if np.random.rand() < self.epsilon:
            if available_actions:
                return np.random.choice(available_actions)
            # If we don't know the exact actions to explore, we can pick a historical random action
            if self.q_table[state]:
                keys = list(self.q_table[state].keys())
                return np.random.choice(keys)
            return None
        
        # Exploit
        if state not in self.q_table or not self.q_table[state]:
            return None
            
        # Get action with max Q-value
        best_action = max(self.q_table[state], key=self.q_table[state].get)
        
        # If Q-value is too low or negative, prefer staying safe (no action)
        if self.q_table[state][best_action] <= 0:
            return None
            
        return best_action

    def retrain_from_feedback(self) -> dict:
        """
        Process un-processed TreatmentFeedback rows to update the Q-Table.
        """
        processed_count = 0
        with SessionLocal() as db:
            feedbacks = db.query(TreatmentFeedback).filter(TreatmentFeedback.is_retrained == False).all()
            
            for fb in feedbacks:
                try:
                    # Parse ML context
                    ml_context_str = fb.ml_context or "{}"
                    ml_context = json.loads(ml_context_str) if isinstance(ml_context_str, str) else ml_context_str
                    
                    cluster_id = ml_context.get("cluster_id")
                    disease = ml_context.get("disease")
                    
                    if cluster_id is None or not disease:
                        # Missing context, mark as trained anyway to prevent re-processing
                        fb.is_retrained = True
                        continue
                        
                    state = self._get_state_key(cluster_id, disease)
                    
                    # Parse Rating (Reward)
                    rating = fb.doctor_rating
                    if rating == "positive":
                        reward = 1.0
                    elif rating == "negative":
                        reward = -1.0
                    else:
                        reward = 0.0 # Neutral or missing
                        
                    if reward == 0:
                        fb.is_retrained = True
                        continue
                        
                    # Parse AI Plan
                    ai_plan_str = fb.ai_plan or "{}"
                    ai_plan = json.loads(ai_plan_str) if isinstance(ai_plan_str, str) else ai_plan_str
                    
                    # Ensure state exists in dict
                    if state not in self.q_table:
                        self.q_table[state] = {}

                    # We consider the prescribed herbs as the 'actions' taken in this state
                    herbs = ai_plan.get("herbs", [])
                    action_items = [h.get("name", "") if isinstance(h, dict) else str(h) for h in herbs]
                    action_items = [a for a in action_items if a]
                    
                    # Update Q-value Q(s,a) for each herb taken
                    # Q(s,a) = Q(s,a) + alpha * (reward - Q(s,a))
                    for action in action_items:
                        action_clean = action.strip().lower()
                        old_q = self.q_table[state].get(action_clean, 0.0)
                        new_q = old_q + self.learning_rate * (reward - old_q)
                        self.q_table[state][action_clean] = new_q

                    # Update Yoga actions as well
                    yoga = ai_plan.get("yoga", [])
                    yoga_actions = [y.get("practice", "") if isinstance(y, dict) else str(y) for y in yoga]
                    yoga_actions = [a for a in yoga_actions if a]
                    
                    for action in yoga_actions:
                        action_clean = f"yoga:{action.strip().lower()}"
                        old_q = self.q_table[state].get(action_clean, 0.0)
                        new_q = old_q + self.learning_rate * (reward - old_q)
                        self.q_table[state][action_clean] = new_q
                        
                    # Mark as processed
                    fb.is_retrained = True
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing feedback {fb.id} for RL: {e}")
                    
            if processed_count > 0:
                db.commit()
                self._save_model()
                
        return {"status": "success", "message": f"Processed {processed_count} feedback records for RL.", "processed": processed_count}

    def retrain_from_outcomes(self):
        """
        Process unprocessed automated clinical outcomes to update the Q-Table.
        Rewards are mathematical percentage vectors instead of subjective +/-1 ratings.
        """
        processed_count = 0
        with SessionLocal() as db:
            outcomes = db.query(ClinicalOutcomeScore).filter(ClinicalOutcomeScore.is_retrained == False).all()
            
            for oc in outcomes:
                try:
                    # Look up the AI Plan & ML Context from the corresponding TreatmentFeedback
                    # since feedback stores the cluster_id and the prescribed herbs list cleanly.
                    fb = db.query(TreatmentFeedback).filter(TreatmentFeedback.medical_record_id == oc.medical_record_id).first()
                    if not fb:
                        print(f"Skipping outcome {oc.id}: No corresponding feedback/prescription found.")
                        continue
                        
                    ml_context_str = fb.ml_context or "{}"
                    ml_context = json.loads(ml_context_str) if isinstance(ml_context_str, str) else ml_context_str
                    
                    cluster_id = ml_context.get("cluster_id")
                    if cluster_id is None:
                        continue
                        
                    state = self._get_state_key(cluster_id, oc.disease)
                    reward = float(oc.calculated_reward)

                    ai_plan_str = fb.ai_plan or "{}"
                    ai_plan = json.loads(ai_plan_str) if isinstance(ai_plan_str, str) else ai_plan_str
                    
                    if state not in self.q_table:
                        self.q_table[state] = {}

                    herbs = ai_plan.get("herbs", [])
                    action_items = [h.get("name", "") if isinstance(h, dict) else str(h) for h in herbs]
                    action_items = [a for a in action_items if a]
                    
                    for action in action_items:
                        action_clean = action.strip().lower()
                        old_q = self.q_table[state].get(action_clean, 0.0)
                        new_q = old_q + self.learning_rate * (reward - old_q)
                        self.q_table[state][action_clean] = new_q

                    yoga = ai_plan.get("yoga", [])
                    yoga_actions = [y.get("practice", "") if isinstance(y, dict) else str(y) for y in yoga]
                    yoga_actions = [a for a in yoga_actions if a]
                    
                    for action in yoga_actions:
                        action_clean = f"yoga:{action.strip().lower()}"
                        old_q = self.q_table[state].get(action_clean, 0.0)
                        new_q = old_q + self.learning_rate * (reward - old_q)
                        self.q_table[state][action_clean] = new_q
                        
                    oc.is_retrained = True
                    processed_count += 1
                except Exception as e:
                    print(f"Error processing clinical outcome {oc.id} for RL: {e}")
                    
            if processed_count > 0:
                db.commit()
                self._save_model()
                
        return {"status": "success", "message": f"Processed {processed_count} automated outcomes for RL.", "processed": processed_count}

# Singleton
rl_service = RLRecommendationService()
