"""
AyurGenix Treatment Recommendation Service

Uses Codified_Ayurvedic_disease.csv to provide disease-specific Ayurvedic treatment recommendations based on standardized NAMC codes.

Matching Strategy:
  Direct substring search against normalized dataset columns.
"""
import os
import re
import pandas as pd
import numpy as np
import difflib
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class AyurGenixService:
    """
    Treatment recommendation service powered by Codified_Ayurvedic_disease.csv.
    """

    def __init__(self):
        self.df = None
        self.initialized = False
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3), lowercase=True)
        self.tfidf_matrix = None
        self.all_diseases = []

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self):
        """Load the codified dataset on startup."""
        try:
            print("Initializing AyurGenix Service with Codified Data...")
            csv_path = os.path.join(DATA_DIR, 'Codified_Ayurvedic_disease.csv')

            if not os.path.exists(csv_path):
                print(f"❌ Dataset not found at {csv_path}")
                return False

            # Load CSV
            self.df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # Clean column names (strip whitespace)
            self.df.columns = self.df.columns.str.strip()
            
            # Normalize Columns: Rename Ayur_X to X for backward compatibility in parsers
            rename_map = {col: col.replace('Ayur_', '') for col in self.df.columns if col.startswith('Ayur_')}
            self.df = self.df.rename(columns=rename_map)

            # Ensure NaN values in search columns are empty strings
            search_cols = ['Name English', 'NAMC_term', 'Disease']
            for col in search_cols:
                if col in self.df.columns:
                    self.df[col] = self.df[col].fillna('').astype(str)

            # Pre-compute lowercase versions for faster search
            self.df['search_english'] = self.df['Name English'].str.lower().str.strip()
            self.df['search_namc'] = self.df['NAMC_term'].str.lower().str.strip()
            self.df['search_disease'] = self.df['Disease'].str.lower().str.strip()

            # Initialize TF-IDF for fuzzy matching
            self.all_diseases = self.get_disease_list()
            if self.all_diseases:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.all_diseases)

            self.initialized = True
            print(f"✓ AyurGenix Service loaded: {len(self.df)} codified diseases")
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
        if self.df is None:
            return []
        
        # Prefer English name, fallback to Disease
        diseases = self.df['Name English'].tolist() + self.df['Disease'].tolist()
        # Filter out empty strings and return unique sorted list
        return sorted(list(set([d.strip() for d in diseases if d and isinstance(d, str) and d.strip()])))

    def get_suggestions(self, query: str, limit: int = 3) -> list:
        """
        Return fuzzy-matched suggestions for a disease name.
        Uses TF-IDF + Cosine Similarity for robust matching.
        """
        if not self.initialized or self.tfidf_matrix is None or not self.all_diseases:
            return []
        
        query_lower = query.strip().lower()
        if not query_lower:
            return []
            
        # Transform query and compute similarity
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top-N indices
        top_indices = similarities.argsort()[-limit:][::-1]
        
        # Filter by a small threshold to avoid completely irrelevant matches
        matches = []
        for idx in top_indices:
            if similarities[idx] > 0.1: # Threshold for basic relevance
                matches.append(self.all_diseases[idx])
        
        # Fallback to difflib if TF-IDF is too sparse or fails
        if not matches:
             matches = difflib.get_close_matches(query, self.all_diseases, n=limit, cutoff=0.3)
             
        return matches

    # ------------------------------------------------------------------
    # Core Recommendation Logic
    # ------------------------------------------------------------------

    def get_recommendation(self, patient_data: dict) -> dict:
        """
        Generate treatment recommendation using direct substring search.

        Args:
            patient_data: dict containing 'disease'

        Returns:
            Full treatment recommendation dict, or a no_match dict.
        """
        if not self.initialized:
            raise RuntimeError("AyurGenix Service not initialized. Call initialize() first.")

        disease_input = (patient_data.get('disease') or '').strip()

        # Validate: disease is required
        if not disease_input:
            raise ValueError("Disease name is required.")

        # --- Direct Search Matching ---
        matched_row = self._direct_search(disease_input)

        # No match found
        if matched_row is None:
             return {
                "no_match_found": True,
                "message": "No matches found with National Ayurveda Morbidity Codes."
            }

        # Match found - Extract info
        prakriti = patient_data.get('prakriti', 'Vata')
        vikriti = patient_data.get('vikriti', 'Vata')
        age = patient_data.get('age', 30)

        # Override clinical assessment with dataset values if available
        ds_doshas = self._safe_get(matched_row, 'Doshas')
        ds_prakriti = self._safe_get(matched_row, 'Constitution/Prakriti')
        
        if ds_doshas:
            vikriti = ds_doshas
        if ds_prakriti:
            prakriti = ds_prakriti

        # Source disease display string
        source_disease = self._safe_get(matched_row, 'Name English') or self._safe_get(matched_row, 'Disease')

        # Build response from matched disease row
        response = self._build_dataset_response(
            matched_row, source_disease, vikriti, prakriti, age
        )
        
        # Inject NAMC data explicitly at the top level
        response["namc_code"] = self._safe_get(matched_row, 'NAMC_CODE')
        response["namc_term"] = self._safe_get(matched_row, 'NAMC_term')
        response["namc_term_devanagari"] = self._safe_get(matched_row, 'NAMC_term_DEVANAGARI')

        return response




    # ------------------------------------------------------------------
    # Direct Search Algorithm
    # ------------------------------------------------------------------

    def _direct_search(self, query: str):
        """
        Find best matching row using simple substring search.
        Handles case insensitivity, whitespace, partial matches, and multiple matches.
        """
        query_lower = query.strip().lower()
        
        if not query_lower:
            return None

        # Find rows where the query is a substring of the target columns
        matches_english = self.df['search_english'].str.contains(query_lower, na=False, regex=False)
        matches_namc = self.df['search_namc'].str.contains(query_lower, na=False, regex=False)
        matches_disease = self.df['search_disease'].str.contains(query_lower, na=False, regex=False)
        
        # Combine masks (Logical OR)
        all_matches_mask = matches_english | matches_namc | matches_disease
        matched_df = self.df[all_matches_mask]

        if matched_df.empty:
            return None
        
        if len(matched_df) == 1:
            return matched_df.iloc[0]

        # Multiple matches: pick the one with the shortest string length in 'Name English'
        # This acts as a heuristic to pick the broader category (e.g., "Fever" instead of "Viral Fever")
        # Ensure we don't calculate length on empty strings if possible
        lens = matched_df['search_english'].str.len()
        # Replace 0 length with a very high number so it's not picked as the shortest
        lens = lens.replace(0, 99999)
        
        shortest_idx = lens.idxmin()
        return matched_df.loc[shortest_idx]

    # ------------------------------------------------------------------
    # Response Builders
    # ------------------------------------------------------------------

    def _build_dataset_response(
        self, row, source_disease, vikriti, prakriti, age
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
        predicted_improvement = self._calculate_improvement(prakriti, vikriti)

        # Duration
        recommended_duration_weeks = self._parse_duration(row)

        # Explainability
        explainability = self._build_explainability(
            source_disease,
            vikriti, prakriti, predicted_improvement,
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
                if herb_name and herb_name.lower() not in ["none specific", "none", "n/a", "-"]:
                    herbs.append({
                        "name": herb_name,
                        "dosage": "As per physician",
                        "benefits": f"Recommended for {row.get('Disease', 'condition')}"
                    })

        # Add herbal remedies if different from herbs
        if herbal_remedies:
            existing_names = {h['name'].lower() for h in herbs}
            for remedy in herbal_remedies.split(','):
                remedy = remedy.strip()
                if remedy and remedy.lower() not in existing_names and remedy.lower() not in ["none specific", "none", "n/a", "-"]:
                    herbs.append({
                        "name": remedy,
                        "dosage": "As per physician",
                        "benefits": f"Traditional remedy for {row.get('Disease', 'condition')}"
                    })

        return herbs

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

        return yoga

    def _parse_diet_lifestyle(self, row) -> tuple:
        """Parse Diet and Lifestyle Recommendations from CSV row."""
        text = self._safe_get(row, 'Diet and Lifestyle Recommendations')

        if not text:
            return ([], [])

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

        return diet_items, lifestyle_items

    def _parse_duration(self, row) -> int:
        """Parse Duration of Treatment into weeks."""
        duration_text = self._safe_get(row, 'Duration of Treatment')
        if not duration_text:
            return 1

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

        return 1  # Default

    # ------------------------------------------------------------------
    # Explainability Builder
    # ------------------------------------------------------------------

    def _build_explainability(
        self, source_disease,
        vikriti, prakriti, predicted_improvement,
        recommended_duration_weeks, row
    ) -> list:
        """Build human-readable explainability strings."""
        explainability = []

        # 1. Match info
        explainability.append(
            f"Mapped to National Ayurveda Morbidity Code for: {source_disease}."
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

        # 3. Removed severity reasoning
        
        # 4. Improvement prediction
        explainability.append(
            f"Predicted {predicted_improvement}% improvement based on dosha profile."
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

    def _calculate_improvement(self, prakriti, vikriti) -> float:
        """Calculate predicted improvement percentage."""
        base_improvement = 75
        dosha_balance_bonus = 10 if prakriti == vikriti else 0
        improvement = min(95, base_improvement + dosha_balance_bonus)
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
