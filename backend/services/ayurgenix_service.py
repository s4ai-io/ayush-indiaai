"""
AyurGenix Treatment Recommendation Service

Uses AyurGenixAI_Dataset.csv (447 diseases × 34 columns) to provide
disease-specific Ayurvedic treatment recommendations.

3-Tier Matching Strategy:
  Tier 1: Exact disease name lookup
  Tier 2: Fuzzy disease name match (difflib)
  Tier 3: TF-IDF + cosine similarity on symptoms
  Fallback: Dosha-based generic recommendations
"""
import os
import re
import difflib
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

    # ------------------------------------------------------------------
    # Core Recommendation Logic
    # ------------------------------------------------------------------

    def get_recommendation(self, patient_data: dict) -> dict:
        """
        Generate treatment recommendation using 3-tier matching.

        Args:
            patient_data: {
                'disease': str (optional),
                'symptoms': str (optional),
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
        prakriti = patient_data.get('prakriti', 'Vata')
        vikriti = patient_data.get('vikriti', 'Vata')
        severity = patient_data.get('severity', 5)
        age = patient_data.get('age', 30)
        gender = patient_data.get('gender', 'Male')
        bmi = patient_data.get('bmi', 25.0)

        # --- 3-Tier Matching ---
        matched_row = None
        match_method = "fallback"
        match_confidence = 0.0
        source_disease = None

        # Tier 1: Exact disease name lookup
        if disease_input:
            matched_row, match_confidence = self._exact_lookup(disease_input)
            if matched_row is not None:
                match_method = "exact"
                source_disease = matched_row['Disease']

        # Tier 2: Fuzzy disease name match
        if matched_row is None and disease_input:
            matched_row, match_confidence = self._fuzzy_match(disease_input)
            if matched_row is not None:
                match_method = "fuzzy"
                source_disease = matched_row['Disease']

        # Tier 3: TF-IDF symptom similarity
        if matched_row is None and symptoms_input:
            matched_row, match_confidence = self._symptom_match(symptoms_input)
            if matched_row is not None:
                match_method = "symptom_similarity"
                source_disease = matched_row['Disease']

        # Build response
        if matched_row is not None:
            response = self._build_dataset_response(
                matched_row, match_method, match_confidence,
                source_disease, vikriti, prakriti, severity, age, bmi
            )
        else:
            response = self._build_fallback_response(
                vikriti, prakriti, severity, disease_input, bmi
            )

        return response

    # ------------------------------------------------------------------
    # Tier 1: Exact Lookup
    # ------------------------------------------------------------------

    def _exact_lookup(self, disease: str):
        """Find exact match in dataset (case-insensitive)."""
        disease_lower = disease.strip().lower()
        matches = self.df[self.df['Disease_Clean'] == disease_lower]

        if len(matches) > 0:
            return matches.iloc[0], 1.0
        return None, 0.0

    # ------------------------------------------------------------------
    # Tier 2: Fuzzy Match
    # ------------------------------------------------------------------

    def _fuzzy_match(self, disease: str, cutoff: float = 0.65):
        """Find closest disease name using difflib."""
        disease_lower = disease.strip().lower()
        close_matches = difflib.get_close_matches(
            disease_lower, self.disease_names, n=1, cutoff=cutoff
        )

        if close_matches:
            best_match = close_matches[0]
            confidence = difflib.SequenceMatcher(
                None, disease_lower, best_match
            ).ratio()
            matched_row = self.df[self.df['Disease_Clean'] == best_match].iloc[0]
            return matched_row, round(confidence, 2)

        return None, 0.0

    # ------------------------------------------------------------------
    # Tier 3: Symptom Similarity (TF-IDF)
    # ------------------------------------------------------------------

    def _symptom_match(self, symptoms: str, threshold: float = 0.1):
        """Find closest disease by symptom similarity using TF-IDF."""
        query_vec = self.tfidf_vectorizer.transform([symptoms])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        if best_score >= threshold:
            return self.df.iloc[best_idx], round(float(best_score), 2)

        return None, 0.0

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

    def _build_fallback_response(self, vikriti, prakriti, severity, disease_input, bmi) -> dict:
        """Build dosha-based fallback when no disease matches."""

        herbs = self._dosha_herbs(vikriti)
        yoga = self._dosha_yoga(vikriti)
        diet = self._dosha_diet(vikriti, bmi)
        lifestyle = self._dosha_lifestyle(vikriti, severity)

        predicted_improvement = self._calculate_improvement(severity, prakriti, vikriti)
        recommended_duration_weeks = 8 if severity <= 5 else 12

        explainability = []
        if disease_input:
            explainability.append(f"No match found for '{disease_input}' in 447-disease database.")
        explainability.append(f"Using dosha-based recommendations for {vikriti} imbalance.")
        if vikriti != prakriti:
            explainability.append(f"Herbs target {vikriti} dosha imbalance (prakriti is {prakriti}).")
        explainability.append(f"Predicted {predicted_improvement}% improvement based on severity + dosha profile.")

        return {
            "herbs": herbs,
            "yoga": yoga,
            "diet": diet,
            "lifestyle": lifestyle,
            "formulation": None,
            "prevention": [],
            "prognosis": None,
            "complications": [],
            "medical_intervention": None,
            "doshas_affected": vikriti,
            "source_disease": None,
            "match_confidence": 0.0,
            "match_method": "fallback",
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
                f"Exact match: {source_disease} found in 447-disease Ayurvedic database."
            )
        elif match_method == "fuzzy":
            explainability.append(
                f"Fuzzy match: Input matched to '{source_disease}' ({match_confidence*100:.0f}% similarity)."
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
    # Dosha-Based Fallback Recommendations
    # ------------------------------------------------------------------

    def _dosha_herbs(self, vikriti) -> list:
        """Fallback herb recommendations based on dosha."""
        herb_db = {
            'Vata': [
                {'name': 'Ashwagandha', 'dosage': '500mg twice daily', 'benefits': 'Reduces anxiety, improves sleep'},
                {'name': 'Brahmi', 'dosage': '300mg daily', 'benefits': 'Enhances memory, reduces stress'},
                {'name': 'Shatavari', 'dosage': '500mg twice daily', 'benefits': 'Balances hormones, improves digestion'}
            ],
            'Pitta': [
                {'name': 'Amla', 'dosage': '1000mg daily', 'benefits': 'Cooling effect, rich in Vitamin C'},
                {'name': 'Licorice', 'dosage': '400mg twice daily', 'benefits': 'Soothes inflammation'},
                {'name': 'Neem', 'dosage': '500mg daily', 'benefits': 'Purifies blood, improves skin health'}
            ],
            'Kapha': [
                {'name': 'Triphala', 'dosage': '1000mg before bed', 'benefits': 'Detoxifies body, aids weight management'},
                {'name': 'Guggul', 'dosage': '500mg twice daily', 'benefits': 'Supports metabolism'},
                {'name': 'Ginger', 'dosage': 'Fresh ginger tea 2-3x daily', 'benefits': 'Improves digestion'}
            ]
        }
        base = vikriti.split('-')[0]
        return herb_db.get(base, herb_db['Vata'])

    def _dosha_yoga(self, vikriti) -> list:
        """Fallback yoga recommendations based on dosha."""
        yoga_db = {
            'Vata': [
                {'practice': 'Surya Namaskar', 'duration': '10 rounds daily', 'benefits': 'Grounds energy'},
                {'practice': 'Anulom Vilom', 'duration': '15 minutes', 'benefits': 'Balances nervous system'},
                {'practice': 'Shavasana', 'duration': '10 minutes', 'benefits': 'Deep relaxation'}
            ],
            'Pitta': [
                {'practice': 'Sheetali Pranayama', 'duration': '10 minutes', 'benefits': 'Cooling breath'},
                {'practice': 'Moon Salutation', 'duration': '5 rounds', 'benefits': 'Calming effect'},
                {'practice': 'Meditation', 'duration': '20 minutes daily', 'benefits': 'Mental clarity'}
            ],
            'Kapha': [
                {'practice': 'Kapalbhati', 'duration': '5 minutes', 'benefits': 'Energizes, aids weight loss'},
                {'practice': 'Surya Namaskar', 'duration': '12 rounds vigorously', 'benefits': 'Increases metabolism'},
                {'practice': 'Bhujangasana', 'duration': '5 repetitions', 'benefits': 'Opens chest, stimulates digestion'}
            ]
        }
        base = vikriti.split('-')[0]
        return yoga_db.get(base, yoga_db['Vata'])

    def _dosha_diet(self, vikriti, bmi) -> list:
        """Fallback diet recommendations based on dosha."""
        diet_db = {
            'Vata': ["Favor warm, cooked foods", "Include healthy fats (ghee, olive oil)", "Eat sweet fruits", "Avoid cold, raw foods", "Regular meal times"],
            'Pitta': ["Favor cooling foods (cucumber, coconut)", "Include sweet and bitter tastes", "Avoid spicy, oily foods", "Reduce caffeine", "Eat more salads"],
            'Kapha': ["Favor light, dry, warm foods", "Include pungent tastes (ginger, turmeric)", "Reduce dairy and sugar", "Eat more vegetables", "Smaller portions"]
        }
        base = vikriti.split('-')[0]
        guidelines = diet_db.get(base, diet_db['Vata'])
        if bmi and bmi > 28:
            guidelines.append("Focus on portion control and avoid late-night eating")
        return guidelines

    def _dosha_lifestyle(self, vikriti, severity) -> list:
        """Fallback lifestyle recommendations based on dosha."""
        lifestyle_db = {
            'Vata': ["Maintain regular daily routine", "Practice oil massage (Abhyanga)", "Ensure 7-8 hours of sleep", "Reduce screen time before bed"],
            'Pitta': ["Avoid overworking, take breaks", "Practice cooling activities", "Avoid direct sun during peak hours", "Spend time in nature"],
            'Kapha': ["Wake up early for morning walk", "Vigorous exercise 5-6 days/week", "Avoid day sleep", "Seek variety and new experiences"]
        }
        base = vikriti.split('-')[0]
        recs = lifestyle_db.get(base, lifestyle_db['Vata'])
        if severity > 7:
            recs.insert(0, "Consult AYUSH practitioner weekly for monitoring")
        return recs

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
