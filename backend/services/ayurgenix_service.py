"""
AyurGenix Treatment Recommendation Service

Uses AyurGenixAI_Dataset.csv (447 diseases × 34 columns) to provide
disease-specific Ayurvedic treatment recommendations.

2-Tier Matching Strategy:
  Tier 1: Exact disease name lookup
  Tier 2: TF-IDF + cosine similarity on symptoms
"""
import os
import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')


class AyurGenixService:
    """
    Treatment recommendation service powered by AyurGenixAI_Dataset.csv.
    """

    def __init__(self):
        self.df = None
        self.initialized = False
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.disease_names = []

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self):
        """Load dataset and build TF-IDF index on startup."""
        try:
            print("Initializing AyurGenix Service...")
            csv_path = os.path.join(DATA_DIR, 'AyurGenixAI_Dataset.csv')

            if not os.path.exists(csv_path):
                print(f"❌ Dataset not found at {csv_path}")
                return False

            # Load CSV
            self.df = pd.read_csv(csv_path, encoding='utf-8-sig')
            self.df.columns = self.df.columns.str.strip()

            # Clean disease names for lookup
            self.df['Disease_Clean'] = self.df['Disease'].str.strip().str.lower()
            self.disease_names = self.df['Disease_Clean'].tolist()

            # Build TF-IDF index on Symptoms column
            symptoms_corpus = self.df['Symptoms'].fillna('').tolist()
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=5000,
                ngram_range=(1, 2)
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(symptoms_corpus)

            self.initialized = True
            print(f"✓ AyurGenix Service loaded: {len(self.df)} diseases")
            print(f"✓ TF-IDF index built on symptoms ({self.tfidf_matrix.shape[1]} features)")
            return True

        except Exception as e:
            print(f"❌ Error initializing AyurGenix Service: {e}")
            return False

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    def health_check(self) -> dict:
        """Return service health status."""
        return {
            "initialized": self.initialized,
            "dataset_loaded": self.df is not None,
            "disease_count": len(self.df) if self.df is not None else 0
        }

    def get_disease_list(self) -> list:
        """Return all disease names from the dataset (original casing)."""
        if not self.initialized or self.df is None:
            return []
        return sorted(self.df['Disease'].str.strip().unique().tolist())

    # ------------------------------------------------------------------
    # Core Recommendation Logic
    # ------------------------------------------------------------------

    def get_recommendation(self, patient_data: dict) -> dict:
        """
        Generate treatment recommendation using 3-tier matching.

        Args:
            patient_data: {
                'disease': str ,
                'symptoms': str ,
                'medical_history': str (optional),
                'prakriti': str,
                'vikriti': str,
                'severity': int,
                'age': int,
                'gender': str,
                'bmi': float (optional)
            }

        Returns:
            Full treatment recommendation dict.
        """
        if not self.initialized:
            raise RuntimeError("AyurGenix Service not initialized. Call initialize() first.")

        disease_input = (patient_data.get('disease') or '').strip()
        symptoms_input = (patient_data.get('symptoms') or '').strip()
        medical_history_input = (patient_data.get('medical_history') or '').strip()

        # Validate: disease is required
        if not disease_input:
            raise ValueError("Disease name is required.")

        prakriti = patient_data.get('prakriti', 'Vata')
        vikriti = patient_data.get('vikriti', 'Vata')
        severity = patient_data.get('severity', 5)
        age = patient_data.get('age', 30)
        gender = patient_data.get('gender', 'Male')
        bmi = patient_data.get('bmi', 25.0)

        # --- 2-Tier Matching ---
        matched_row = None
        match_method = None
        match_confidence = 0.0
        source_disease = None

        # Tier 1: Exact disease name lookup with Scoring
        matched_row, match_confidence = self._exact_lookup(
            disease=disease_input,
            symptoms=symptoms_input,
            medical_history=medical_history_input,
            prakriti=prakriti,
            vikriti=vikriti,
            gender=gender,
            age=age
        )
        if matched_row is not None:
            match_method = "exact"
            source_disease = matched_row['Disease']

        # No match found
        if matched_row is None:
            raise ValueError(
                f"No matching disease found for '{disease_input}' with the given symptoms. "
                f"Please verify the disease name and symptoms and try again."
            )

        # Override clinical assessment with dataset values if available
        ds_doshas = self._safe_get(matched_row, 'Doshas')
        ds_prakriti = self._safe_get(matched_row, 'Constitution/Prakriti')
        
        if ds_doshas:
            vikriti = ds_doshas
        if ds_prakriti:
            prakriti = ds_prakriti

        # Build response from matched disease row
        response = self._build_dataset_response(
            matched_row, match_method, match_confidence,
            source_disease, vikriti, prakriti, severity, age, bmi
        )

        return response

    # ------------------------------------------------------------------
    # Tier 1: Exact Lookup (Scoring Algorithm)
    # ------------------------------------------------------------------

    def _exact_lookup(self, disease: str, symptoms: str = "", medical_history: str = "", 
                      prakriti: str = "", vikriti: str = "", gender: str = "", age: int = 30):
        """Find exact match in dataset and return best fit row based on scoring."""
        disease_lower = disease.strip().lower()
        matches = self.df[self.df['Disease_Clean'] == disease_lower]

        if len(matches) == 0:
            return None, 0.0
            
        if len(matches) == 1:
            return matches.iloc[0], 1.0

        best_score = -999.0
        best_row = None
        
        for idx, row in matches.iterrows():
            score = 0.0
            
            # 1. Symptom Similarity (Max +30)
            row_symptoms = str(row.get('Symptoms', ''))
            if symptoms and row_symptoms and row_symptoms != 'nan':
                try:
                    query_vec = self.tfidf_vectorizer.transform([symptoms])
                    row_vec = self.tfidf_vectorizer.transform([row_symptoms])
                    sim = cosine_similarity(query_vec, row_vec)[0][0]
                    score += (sim * 30.0)
                except Exception:
                    pass
                    
            # 2. Medical History (Comorbidity) (+20 or -20)
            patient_mh_lower = medical_history.lower()
            if patient_mh_lower:
                row_history = str(row.get('Medical History', '')).lower()
                row_risks = str(row.get('Risk Factors', '')).lower()
                
                # Boost if the row is meant for this comorbidity
                if any(word in row_history for word in patient_mh_lower.split()):
                    score += 10.0
                if any(word in row_risks for word in patient_mh_lower.split()):
                    score += 10.0
                    
                # Note: In a production system, explicit contraindications would be highly penalized here.
                    
            # 3. Dosha/Prakriti Alignment (+10)
            row_dosha = str(row.get('Doshas', '')).lower()
            row_prakriti = str(row.get('Constitution/Prakriti', '')).lower()
            
            if vikriti.lower() in row_dosha or vikriti.lower() in row_prakriti:
                score += 5.0
            if prakriti.lower() in row_dosha or prakriti.lower() in row_prakriti:
                score += 5.0
                
            # 4. Demographics Alignment (+10)
            row_gender = str(row.get('Gender', '')).lower()
            if row_gender != 'both genders' and row_gender != 'all genders' and row_gender != 'nan':
                if gender.lower() == row_gender:
                    score += 5.0
                else:
                    score -= 5.0 # Penalty for mismatch
                    
            if score > best_score:
                best_score = score
                best_row = row
                
        # Calculate a pseudo-confidence score between 0.3 and 1.0 based on how well it matched
        normalized_confidence = min(0.3 + (max(best_score, 0) / 100.0), 1.0)
        
        return best_row, round(normalized_confidence, 2)

    # ------------------------------------------------------------------
    # Response Builders
    # ------------------------------------------------------------------

    def _build_dataset_response(
        self, row, match_method, match_confidence,
        source_disease, vikriti, prakriti, severity, age, bmi
    ) -> dict:
        """Build response from a matched CSV row."""

        # Parse herbs
        herbs = self._parse_herbs(row)

        # Parse yoga
        yoga = self._parse_yoga(row)

        # Parse diet & lifestyle
        diet, lifestyle = self._parse_diet_lifestyle(row)

        # Parse other fields
        formulation = self._safe_get(row, 'Formulation')
        prevention = self._split_field(row, 'Prevention')
        prognosis = self._safe_get(row, 'Prognosis')
        complications = self._split_field(row, 'Complications')
        medical_intervention = self._safe_get(row, 'Medical Intervention')
        doshas_affected = self._safe_get(row, 'Doshas')

        # Predicted improvement
        predicted_improvement = self._calculate_improvement(severity, prakriti, vikriti)

        # Duration
        recommended_duration_weeks = self._parse_duration(row)

        # Explainability
        explainability = self._build_explainability(
            match_method, match_confidence, source_disease,
            vikriti, prakriti, severity, predicted_improvement,
            recommended_duration_weeks, row
        )

        return {
            "herbs": herbs,
            "yoga": yoga,
            "diet": diet,
            "lifestyle": lifestyle,
            "formulation": formulation,
            "prevention": prevention,
            "prognosis": prognosis,
            "complications": complications,
            "medical_intervention": medical_intervention,
            "doshas_affected": doshas_affected,
            "source_disease": source_disease,
            "match_confidence": match_confidence,
            "match_method": match_method,
            "predicted_improvement": predicted_improvement,
            "recommended_duration_weeks": recommended_duration_weeks,
            "explainability": explainability
        }



    # ------------------------------------------------------------------
    # CSV Field Parsers
    # ------------------------------------------------------------------

    def _parse_herbs(self, row) -> list:
        """Parse Ayurvedic Herbs + Formulation from CSV row."""
        herbs_text = self._safe_get(row, 'Ayurvedic Herbs')
        herbal_remedies = self._safe_get(row, 'Herbal/Alternative Remedies')
        formulation = self._safe_get(row, 'Formulation')

        herbs = []
        if herbs_text:
            for herb_name in herbs_text.split(','):
                herb_name = herb_name.strip()
                if herb_name:
                    herbs.append({
                        "name": herb_name,
                        "dosage": formulation if formulation else "As per physician",
                        "benefits": f"Recommended for {row.get('Disease', 'condition')}"
                    })

        # Add herbal remedies if different from herbs
        if herbal_remedies:
            existing_names = {h['name'].lower() for h in herbs}
            for remedy in herbal_remedies.split(','):
                remedy = remedy.strip()
                if remedy and remedy.lower() not in existing_names:
                    herbs.append({
                        "name": remedy,
                        "dosage": "As per physician",
                        "benefits": f"Traditional remedy for {row.get('Disease', 'condition')}"
                    })

        return herbs if herbs else [{"name": "Consult Ayurvedic Practitioner", "dosage": "N/A", "benefits": "Personalized assessment needed"}]

    def _parse_yoga(self, row) -> list:
        """Parse Yoga & Physical Therapy from CSV row."""
        yoga_text = self._safe_get(row, 'Yoga & Physical Therapy')
        yoga = []

        if yoga_text:
            for practice in yoga_text.split(','):
                practice = practice.strip()
                if practice:
                    yoga.append({
                        "practice": practice,
                        "duration": "20 mins daily",
                        "benefits": f"Therapeutic for {row.get('Disease', 'condition')}"
                    })

        return yoga if yoga else [{"practice": "Pranayama", "duration": "15 mins", "benefits": "General wellness"}]

    def _parse_diet_lifestyle(self, row) -> tuple:
        """Parse Diet and Lifestyle Recommendations from CSV row."""
        text = self._safe_get(row, 'Diet and Lifestyle Recommendations')

        if not text:
            return (["Eat balanced meals", "Stay hydrated"],
                    ["Maintain regular routine", "Get adequate sleep"])

        # Split by semicolons or periods
        parts = re.split(r'[;.]', text)
        parts = [p.strip() for p in parts if p.strip()]

        # Separate diet and lifestyle heuristically
        diet_keywords = ['eat', 'food', 'diet', 'avoid', 'consume', 'drink',
                         'sugar', 'salt', 'fruit', 'vegetable', 'meal', 'hydrat']
        lifestyle_keywords = ['exercise', 'yoga', 'sleep', 'meditat', 'walk',
                              'routine', 'stress', 'activ', 'rest']

        diet_items = []
        lifestyle_items = []

        for part in parts:
            part_lower = part.lower()
            is_diet = any(kw in part_lower for kw in diet_keywords)
            is_lifestyle = any(kw in part_lower for kw in lifestyle_keywords)

            if is_diet and not is_lifestyle:
                diet_items.append(part)
            elif is_lifestyle and not is_diet:
                lifestyle_items.append(part)
            else:
                # Default to diet if ambiguous
                diet_items.append(part)

        # Ensure we have at least one item in each
        if not diet_items:
            diet_items = ["Follow balanced Ayurvedic diet"]
        if not lifestyle_items:
            lifestyle_items = ["Maintain regular daily routine"]

        return diet_items, lifestyle_items

    def _parse_duration(self, row) -> int:
        """Parse Duration of Treatment into weeks."""
        duration_text = self._safe_get(row, 'Duration of Treatment')
        if not duration_text:
            return 8

        text_lower = duration_text.lower()

        # Handle common patterns
        if 'lifetime' in text_lower or 'chronic' in text_lower:
            return 12
        if 'week' in text_lower:
            nums = re.findall(r'\d+', duration_text)
            if nums:
                return max(int(nums[-1]), 1)  # Take the larger number
        if 'month' in text_lower:
            nums = re.findall(r'\d+', duration_text)
            if nums:
                return int(nums[-1]) * 4
        if 'day' in text_lower:
            nums = re.findall(r'\d+', duration_text)
            if nums:
                return max(int(nums[-1]) // 7, 1)

        return 8  # Default

    # ------------------------------------------------------------------
    # Explainability Builder
    # ------------------------------------------------------------------

    def _build_explainability(
        self, match_method, match_confidence, source_disease,
        vikriti, prakriti, severity, predicted_improvement,
        recommended_duration_weeks, row
    ) -> list:
        """Build human-readable explainability strings."""
        explainability = []

        # 1. Match info
        if match_method == "exact":
            explainability.append(
                f"Exact match: {source_disease} found in 446-disease Ayurvedic database."
            )

        elif match_method == "symptom_similarity":
            explainability.append(
                f"Symptom match: Symptoms most similar to {source_disease} ({match_confidence*100:.0f}% match)."
            )

        # 2. Dosha reasoning
        if vikriti != prakriti:
            explainability.append(
                f"Herbs target {vikriti} dosha imbalance (patient's prakriti is {prakriti})."
            )
        else:
            explainability.append(
                f"Doshas balanced ({prakriti}). Focus on maintenance therapy."
            )

        # 3. Severity reasoning
        if severity > 6:
            explainability.append(
                f"High severity ({severity}/10): Intensive treatment with {recommended_duration_weeks}-week plan."
            )

        # 4. Improvement prediction
        explainability.append(
            f"Predicted {predicted_improvement}% improvement based on severity + dosha profile."
        )

        # 5. Dataset evidence
        age_group = self._safe_get(row, 'Age Group')
        gender_info = self._safe_get(row, 'Gender')
        if age_group and gender_info:
            explainability.append(
                f"Recommendation sourced from AyurGenix dataset ({age_group}, {gender_info})."
            )

        return explainability

    # ------------------------------------------------------------------
    # Improvement Calculator
    # ------------------------------------------------------------------

    def _calculate_improvement(self, severity, prakriti, vikriti) -> float:
        """Calculate predicted improvement percentage."""
        base_improvement = 65
        severity_factor = (10 - severity) * 2
        dosha_balance_bonus = 5 if prakriti == vikriti else 0
        improvement = min(95, base_improvement + severity_factor + dosha_balance_bonus)
        return round(float(improvement), 1)



    # ------------------------------------------------------------------
    # Utility Helpers
    # ------------------------------------------------------------------

    def _safe_get(self, row, column: str) -> str:
        """Safely get a value from a pandas row, returns None for NaN."""
        val = row.get(column)
        if pd.isna(val) or val is None:
            return None
        return str(val).strip()

    def _split_field(self, row, column: str) -> list:
        """Split a comma-separated CSV field into a list."""
        text = self._safe_get(row, column)
        if not text:
            return []
        return [item.strip() for item in text.split(',') if item.strip()]


# Global singleton instance
ayurgenix_service = AyurGenixService()
