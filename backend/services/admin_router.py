import json
import os
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from services.ayurgenix_service import ayurgenix_service

admin_router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'src', 'data')

@admin_router.get("/evaluate", tags=["Admin"])
async def evaluate_accuracy():
    """
    Reads ground truth JSON, runs it against the AyurGenix service,
    and returns accuracy metrics.
    """
    try:
        ground_truth_path = os.path.join(DATA_DIR, 'ground_truth.json')
        
        if not os.path.exists(ground_truth_path):
            raise HTTPException(status_code=404, detail="ground_truth.json not found")

        with open(ground_truth_path, 'r', encoding='utf-8') as f:
            ground_truth_data = json.load(f)

        if not isinstance(ground_truth_data, list):
            raise HTTPException(status_code=400, detail="Invalid ground_truth.json format. Expected a list.")

        total_cases = len(ground_truth_data)
        correct_predictions = 0
        results = []

        import pandas as pd
        csv_path = os.path.join(os.path.dirname(BASE_DIR), 'backend', 'data', 'medical_records.csv')
        df_medical = pd.DataFrame()
        if os.path.exists(csv_path):
            df_medical = pd.read_csv(csv_path)

        for item in ground_truth_data:
            expected_disease = item.get("Disease", "")
            symptoms_list = item.get("Symptoms", [])
            symptoms_str = ", ".join(symptoms_list) if isinstance(symptoms_list, list) else str(symptoms_list)

            predicted_disease = "Unknown (No match for symptoms in records)"
            match_confidence = 0.0
            is_match = False
            error_msg = None

            try:
                # 1. Match against medical_records.csv by symptoms (using fuzzy matching)
                matched_row = pd.DataFrame()
                if not df_medical.empty and 'symptoms' in df_medical.columns:
                    import difflib
                    
                    df_medical['symptoms'] = df_medical['symptoms'].fillna('')
                    
                    best_match_idx = -1
                    best_ratio = 0.0
                    
                    for idx, row in df_medical.iterrows():
                        record_symptoms = str(row['symptoms'])
                        ratio = difflib.SequenceMatcher(None, symptoms_str.lower(), record_symptoms.lower()).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match_idx = idx
                            
                    # Threshold for a match (can be adjusted)
                    if best_ratio > 0.6 and best_match_idx != -1:
                        matched_row = df_medical.iloc[[best_match_idx]]

                if not matched_row.empty:
                    # 2. Extract diagnosis as predicted_disease
                    predicted_disease = str(matched_row.iloc[0]['diagnosis'])
                    match_confidence = best_ratio # Use similarity ratio as confidence
                    
                    expected_clean = expected_disease.lower().strip()
                    predicted_clean = predicted_disease.lower().strip()
                    
                    import re
                    # Extract words > 3 chars
                    expected_words = {w for w in re.findall(r'\w+', expected_clean) if len(w) > 3}
                    predicted_words = {w for w in re.findall(r'\w+', predicted_clean) if len(w) > 3}
                    
                    # Exact match, substring match, OR word intersection
                    if (expected_clean == predicted_clean or 
                        predicted_clean in expected_clean or 
                        expected_clean in predicted_clean or 
                        bool(expected_words.intersection(predicted_words))):
                        is_match = True
                        correct_predictions += 1
                else:
                    error_msg = f"No matching symptoms found in medical_records.csv"
                    
            except Exception as e:
                error_msg = str(e)

            results.append({
                "expected": expected_disease,
                "predicted": predicted_disease,
                "is_match": is_match,
                "confidence": match_confidence,
                "symptoms_used": symptoms_str,
                "error": error_msg
            })

        accuracy = (correct_predictions / total_cases * 100) if total_cases > 0 else 0.0

        return {
            "summary": {
                "total": total_cases,
                "correct": correct_predictions,
                "accuracy": round(accuracy, 2)
            },
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in evaluate_accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
