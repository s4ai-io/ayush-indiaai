import os
import sys
import uuid
import random
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))

from models import SessionLocal, AyushTreatment, ClinicalOutcomeScore

def generate_mock_outcomes(num_records=10):
    with SessionLocal() as db:
        # Get random recent treatments
        treatments = db.query(AyushTreatment).all()
        if not treatments:
            print("No treatments found to generate mock outcomes.")
            return

        sampled_treatments = random.sample(treatments, min(num_records, len(treatments)))
        
        added_count = 0
        for t in sampled_treatments:
            # Check if an outcome already exists for this medical record
            existing = db.query(ClinicalOutcomeScore).filter(ClinicalOutcomeScore.medical_record_id == t.medical_record_id).first()
            if existing:
                continue

            disease = (t.disease or "Unknown").title()
            
            # Simulated mappings per disease
            if "Asthma" in disease or "Shwasa" in disease or "Cough" in disease or "Kasa" in disease:
                target_vital = "PEFR (L/min)"
                baseline = random.uniform(250, 350)
                # simulate 10% to 30% improvement
                followup = baseline * random.uniform(1.10, 1.30)
                # Reward correlates to % change positively
                pct_change = ((followup - baseline) / baseline) * 100
                reward = min(1.0, float(pct_change) / 20.0)  # max +1.0 for >20% improvement
            elif "Diabetes" in disease or "Madhumeha" in disease:
                target_vital = "HbA1c (%)"
                baseline = random.uniform(7.5, 9.5)
                # simulate dropping by 0.5 to 1.5
                followup = max(5.0, baseline - random.uniform(0.5, 1.5))
                # drop is good
                pct_change = ((baseline - followup) / baseline) * 100
                reward = min(1.0, float(pct_change) / 10.0) 
            else:
                target_vital = "Symptom Severity (1-10)"
                baseline = random.uniform(6.0, 9.0)
                followup = max(1.0, baseline - random.uniform(2.0, 5.0))
                # drop is good
                pct_change = ((baseline - followup) / baseline) * 100
                reward = min(1.0, float(pct_change) / 30.0)

            # Let's introduce intentional noise so the RL learns varying success
            reward = reward * random.uniform(0.8, 1.2)
            # Clip between -1 and 1
            reward = max(-1.0, min(1.0, reward))

            outcome = ClinicalOutcomeScore(
                id=str(uuid.uuid4()),
                patient_id=t.patient_id,
                medical_record_id=t.medical_record_id,
                disease=disease,
                target_vital=target_vital,
                baseline_value=round(baseline, 2),
                followup_value=round(followup, 2),
                percentage_change=round(pct_change, 2),
                calculated_reward=round(reward, 3),
                is_retrained=False,
                created_at=datetime.utcnow()
            )
            
            db.add(outcome)
            added_count += 1
            
            print(f"Generated Outcome -> Patient: {t.patient_id[:8]}, Disease: {disease}, Vital: {target_vital}, Change: {pct_change:.1f}%, Reward: {reward:.3f}")

        db.commit()
        print(f"\\nSuccessfully inserted {added_count} mock clinical outcome records!")

if __name__ == "__main__":
    generate_mock_outcomes(5)
