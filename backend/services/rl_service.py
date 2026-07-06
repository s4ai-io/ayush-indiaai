import os
import json
import pickle
import joblib
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from models import SessionLocal, TreatmentFeedback, ClinicalOutcomeScore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'data', 'models')
Q_TABLE_PATH = os.path.join(MODELS_DIR, 'rl_q_table.pkl')
DEMO_Q_TABLE_PATH = os.path.join(MODELS_DIR, 'demo_q_table.pkl')

class RLRecommendationService:
    """
    Reinforcement Learning Pipeline using Epsilon-Greedy Contextual Bandits.
    Learns the best 'actions' (treatments/herbs) for a given 'state' (NAMC Code + Prakriti + Vikriti).
    """
    def __init__(self, learning_rate=0.1, discount_factor=0.9, epsilon=0.2):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table_path = Q_TABLE_PATH
        # Q-Table structure: q_table[state][action] = q_value
        # state is a string "namc_code_prakriti_vikriti"
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

    def _save_q_table(self):
        with open(self.q_table_path, 'wb') as f:
            pickle.dump(self.q_table, f)

    def _get_state_key(self, namc_code: str, prakriti: str, vikriti: str) -> str:
        return f"{namc_code}_{prakriti}_{vikriti}"

    def get_best_action(self, cluster_id: int, disease: str, available_actions: list = None) -> str:
        """
        Get the best learned action for a state, with epsilon exploration.
        Kept for backward compatibility — uses old key format.
        """
        disease_clean = disease.strip().lower() if disease else "unknown"
        state = f"{cluster_id}_{disease_clean}"

        # Explore
        if np.random.rand() < self.epsilon:
            if available_actions:
                return np.random.choice(available_actions)
            if self.q_table.get(state):
                keys = list(self.q_table[state].keys())
                return np.random.choice(keys)
            return None

        # Exploit
        if state not in self.q_table or not self.q_table[state]:
            return None

        best_action = max(self.q_table[state], key=self.q_table[state].get)

        if self.q_table[state][best_action] <= 0:
            return None

        return best_action

    def get_best_actions_by_namc(self, namc_code: str, prakriti: str, vikriti: str,
                                  demo_mode: bool = False) -> list:
        """
        Return all learned herb/yoga actions with positive Q-values for a state,
        sorted by Q-value descending.  Uses new namc+prakriti+vikriti state key.

        Returns: [{"name": str, "q_value": float, "is_learned": True}, ...]
        """
        state = self._get_state_key(namc_code, prakriti, vikriti)
        q_table = self._load_demo_q_table() if demo_mode else self.q_table
        state_q = q_table.get(state, {})

        actions = [
            {"name": k, "q_value": v, "is_learned": True}
            for k, v in state_q.items()
            if v > 0 and not k.startswith("yoga:") and not k.startswith("diet:") and not k.startswith("lifestyle:")
        ]
        actions.sort(key=lambda x: x["q_value"], reverse=True)
        return actions

    def get_learned_prefixed_actions(self, namc_code: str, prakriti: str, vikriti: str,
                                     prefix: str, demo_mode: bool = False) -> list:
        """
        All positive-Q actions for one prefixed category ("yoga:", "diet:", "lifestyle:"),
        returned as (name_without_prefix, q_value) tuples sorted by Q-value descending.
        """
        state = self._get_state_key(namc_code, prakriti, vikriti)
        q_table = self._load_demo_q_table() if demo_mode else self.q_table
        state_q = q_table.get(state, {})
        return sorted(
            [(k[len(prefix):], v) for k, v in state_q.items() if k.startswith(prefix) and v > 0],
            key=lambda x: -x[1],
        )

    # Plan categories: (plan_key, item_field_for_dicts, q_table_key_prefix)
    # Herbs are stored unprefixed (backward compatible with existing Q-tables and
    # historical added_herbs/removed_herbs rows); other categories are prefixed
    # and lowercased, matching their Q-table key format.
    PLAN_CATEGORIES = [
        ("herbs", "name", ""),
        ("yoga", "practice", "yoga:"),
        ("diet", None, "diet:"),
        ("lifestyle", None, "lifestyle:"),
    ]

    @classmethod
    def _plan_item_names(cls, plan: dict, plan_key: str, item_field: str) -> list:
        names = []
        for it in (plan or {}).get(plan_key, []) or []:
            name = it.get(item_field, "") if isinstance(it, dict) else str(it)
            name = (name or "").strip()
            if name:
                names.append(name)
        return names

    @staticmethod
    def _canonical_key(name: str, prefix: str) -> str:
        return f"{prefix}{name.strip().lower()}" if prefix else name.strip()

    @classmethod
    def compute_plan_diff(cls, original_plan: dict, final_plan: dict) -> tuple:
        """
        Diff every plan category between the original AI plan and the doctor's final plan.
        Returns (added, removed) as canonical Q-table action keys, so the category of
        each entry survives storage in the flat added_herbs/removed_herbs columns.
        """
        added, removed = [], []
        for plan_key, item_field, prefix in cls.PLAN_CATEGORIES:
            orig = [cls._canonical_key(n, prefix)
                    for n in cls._plan_item_names(original_plan, plan_key, item_field or "name")]
            fin = [cls._canonical_key(n, prefix)
                   for n in cls._plan_item_names(final_plan, plan_key, item_field or "name")]
            added += [n for n in fin if n not in orig]
            removed += [n for n in orig if n not in fin]
        return added, removed

    @classmethod
    def _plan_action_keys(cls, final_plan: dict, removed_actions: list) -> list:
        """Canonical action keys for every item in the final plan, plus removed actions."""
        keys = []
        for plan_key, item_field, prefix in cls.PLAN_CATEGORIES:
            for name in cls._plan_item_names(final_plan, plan_key, item_field or "name"):
                keys.append(cls._canonical_key(name, prefix))
        keys += [k for k in (removed_actions or []) if k]
        return list(dict.fromkeys(filter(None, keys)))

    @staticmethod
    def _compute_herb_reward(herb_name: str, added_herbs: list, removed_herbs: list, doctor_rating: str) -> float:
        is_added   = herb_name in (added_herbs or [])
        is_removed = herb_name in (removed_herbs or [])
        rating     = (doctor_rating or "").strip().lower()

        if is_added:
            if rating == "positive":  return 1.5
            if rating == "":          return 0.7
            return 0.3   # negative rating

        if is_removed:
            if rating == "negative":  return -1.0
            if rating == "positive":  return -0.8
            return -0.5  # no rating

        # herb was kept
        if rating == "positive":  return 1.0
        if rating == "":          return 0.3   # implicit acceptance
        return 0.2  # negative rating, herb kept

    def retrain_from_feedback(self) -> dict:
        """
        Process un-processed TreatmentFeedback rows to update the Q-Table.
        Uses namc_code from ml_context if available, falls back to old cluster_id+disease key.
        """
        processed_count = 0
        with SessionLocal() as db:
            feedbacks = db.query(TreatmentFeedback).filter(
                TreatmentFeedback.is_retrained == False,
            ).all()

            for fb in feedbacks:
                try:
                    ml_context_str = fb.ml_context or "{}"
                    ctx = json.loads(ml_context_str) if isinstance(ml_context_str, str) else ml_context_str

                    namc_code = ctx.get("namc_code")
                    prakriti  = ctx.get("prakriti", "")
                    vikriti   = ctx.get("vikriti", "")

                    if namc_code:
                        state = self._get_state_key(namc_code, prakriti, vikriti)
                    else:
                        # Fall back to old key format for historical rows not yet backfilled
                        cluster_id = ctx.get("cluster_id")
                        disease    = ctx.get("disease", "")
                        if cluster_id is None and not disease:
                            fb.is_retrained = True
                            continue
                        disease_clean = disease.strip().lower() if disease else "unknown"
                        state = f"{cluster_id}_{disease_clean}"

                    added_herbs   = json.loads(fb.added_herbs or "[]")
                    removed_herbs = json.loads(fb.removed_herbs or "[]")
                    final_plan    = json.loads(fb.final_plan or fb.ai_plan or "{}")
                    doctor_rating = fb.doctor_rating or ""

                    if state not in self.q_table:
                        self.q_table[state] = {}

                    # Diff-aware update for every plan category (herbs, yoga, diet,
                    # lifestyle) plus removed actions absent from the final plan.
                    # added/removed lists hold canonical keys, so membership checks
                    # and Q-table keys line up per category.
                    for key in self._plan_action_keys(final_plan, removed_herbs):
                        reward = self._compute_herb_reward(key, added_herbs, removed_herbs, doctor_rating)
                        old_q  = self.q_table[state].get(key, 0.0)
                        self.q_table[state][key] = old_q + self.learning_rate * (reward - old_q)

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
        Uses namc_code from ml_context if available, falls back to old cluster_id+disease key.
        """
        processed_count = 0
        with SessionLocal() as db:
            outcomes = db.query(ClinicalOutcomeScore).filter(ClinicalOutcomeScore.is_retrained == False).all()

            for oc in outcomes:
                try:
                    fb = db.query(TreatmentFeedback).filter(TreatmentFeedback.medical_record_id == oc.medical_record_id).first()
                    if not fb:
                        print(f"Skipping outcome {oc.id}: No corresponding feedback/prescription found.")
                        continue

                    ml_context_str = fb.ml_context or "{}"
                    ctx = json.loads(ml_context_str) if isinstance(ml_context_str, str) else ml_context_str

                    namc_code = ctx.get("namc_code")
                    prakriti  = ctx.get("prakriti", "")
                    vikriti   = ctx.get("vikriti", "")

                    if namc_code:
                        state = self._get_state_key(namc_code, prakriti, vikriti)
                    else:
                        cluster_id = ctx.get("cluster_id")
                        if cluster_id is None:
                            continue
                        state = f"{cluster_id}_{oc.disease}"

                    reward = float(oc.calculated_reward)

                    ai_plan_str = fb.final_plan or fb.ai_plan or "{}"
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

    def retrain_instant(self, feedback_id: str, db, demo_mode: bool = False) -> dict:
        """Single-row Q-update. Returns {herb_name: new_q_value} for frontend animation."""
        fb = db.query(TreatmentFeedback).filter(TreatmentFeedback.id == feedback_id).first()
        if not fb:
            return {}

        ctx = json.loads(fb.ml_context or "{}")
        namc_code = ctx.get("namc_code", "UNKNOWN")
        prakriti  = ctx.get("prakriti", "")
        vikriti   = ctx.get("vikriti", "")
        state = self._get_state_key(namc_code, prakriti, vikriti)

        final_plan    = json.loads(fb.final_plan or fb.ai_plan or "{}")
        added_herbs   = json.loads(fb.added_herbs or "[]")
        removed_herbs = json.loads(fb.removed_herbs or "[]")
        doctor_rating = fb.doctor_rating or ""

        # Always update the real Q-table
        if state not in self.q_table:
            self.q_table[state] = {}

        updated = {}

        # Diff-aware update for every plan category (herbs, yoga, diet, lifestyle)
        # plus removed actions absent from the final plan — same reward table as
        # the batch retrain, so instant and standard modes stay consistent.
        for key in self._plan_action_keys(final_plan, removed_herbs):
            reward = self._compute_herb_reward(key, added_herbs, removed_herbs, doctor_rating)
            old_q = self.q_table[state].get(key, 0.0)
            new_q = old_q + self.learning_rate * (reward - old_q)
            self.q_table[state][key] = new_q
            updated[key] = round(new_q, 4)

        self._save_q_table()

        # Also mirror to demo Q-table so the chart reflects it immediately
        if demo_mode:
            demo_q = self._load_demo_q_table()
            if state not in demo_q:
                demo_q[state] = {}
            demo_q[state].update(self.q_table[state])
            self._save_demo_q_table(demo_q)

        fb.is_retrained = True
        db.commit()
        return {"state_key": state, "updated_q_values": updated}

    def _load_demo_q_table(self) -> dict:
        if os.path.exists(DEMO_Q_TABLE_PATH):
            with open(DEMO_Q_TABLE_PATH, 'rb') as f:
                return pickle.load(f)
        # If no demo table exists yet, copy from production
        import copy
        return copy.deepcopy(self.q_table)

    def _save_demo_q_table(self, q_table: dict):
        with open(DEMO_Q_TABLE_PATH, 'wb') as f:
            pickle.dump(q_table, f)

    def reset_demo_q_table(self):
        """Copy production q_table → demo_q_table. Clears all demo-session learnings."""
        import copy
        demo = copy.deepcopy(self.q_table)
        self._save_demo_q_table(demo)
        return {"status": "reset", "base_q_states": len(demo)}


# Singleton
rl_service = RLRecommendationService()
