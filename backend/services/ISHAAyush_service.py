"""
ISHAAyush Treatment Recommendation Service

Uses Codified_Ayurvedic_disease.csv to provide disease-specific Ayurvedic treatment recommendations based on standardized NAMC codes.

Matching Strategy:
  Semantic search (sentence-transformers) → direct substring search → TF-IDF fuzzy fallback.
"""
import os
import re
import logging
import pandas as pd
import numpy as np
import difflib
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Semantic embeddings cache path (Step 7)
EMBEDDINGS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'disease_embeddings.pkl')

class ISHAAyushService:
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
            print("Initializing ISHAAyush Service with Codified Data...")
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
            print(f"✓ ISHAAyush Service loaded: {len(self.df)} codified diseases")
            return True

        except Exception as e:
            print(f"❌ Error initializing ISHAAyush Service: {e}")
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
            raise RuntimeError("ISHAAyush Service not initialized. Call initialize() first.")

        disease_input = (patient_data.get('disease') or '').strip()

        # Validate: disease is required
        if not disease_input:
            raise ValueError("Disease name is required.")

        # --- Semantic Search (Step 7) ---
        matched_row = None
        match_confidence = 0.0
        match_alternatives = []
        match_requires_confirmation = False

        sem_results = self._semantic_search(disease_input)
        if sem_results:
            top_row, top_conf = sem_results[0]
            if top_conf >= 0.3:
                matched_row = top_row
                match_confidence = top_conf
                match_requires_confirmation = top_conf < 0.85
                # Build alternatives from positions 2 and 3
                for alt_row, alt_conf in sem_results[1:]:
                    match_alternatives.append({
                        "disease": self._safe_get(alt_row, 'Name English') or self._safe_get(alt_row, 'Disease'),
                        "namc_code": self._safe_get(alt_row, 'NAMC_CODE'),
                        "confidence": round(alt_conf, 3),
                    })

        # --- Direct Search Fallback ---
        if matched_row is None:
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

        # Log a warning instead of silently substituting prakriti/vikriti from CSV
        ds_doshas = self._safe_get(matched_row, 'Doshas')
        ds_prakriti = self._safe_get(matched_row, 'Constitution/Prakriti')

        if ds_doshas and ds_doshas != vikriti:
            logger.warning(
                f"CSV vikriti/doshas '{ds_doshas}' differs from submitted '{vikriti}' "
                f"for disease '{disease_input}' — using submitted value"
            )
        if ds_prakriti and ds_prakriti != prakriti:
            logger.warning(
                f"CSV prakriti '{ds_prakriti}' differs from submitted '{prakriti}' "
                f"for disease '{disease_input}' — using submitted value"
            )

        # Source disease display string
        source_disease = self._safe_get(matched_row, 'Name English') or self._safe_get(matched_row, 'Disease')

        # Resolve NAMC code for the improvement model
        namc_code = self._safe_get(matched_row, 'NAMC_CODE') or ''

        # Build response from matched disease row
        response = self._build_dataset_response(
            matched_row, source_disease, vikriti, prakriti, age,
            patient_data=patient_data, namc_code=namc_code,
        )

        # Inject NAMC data explicitly at the top level
        response["namc_code"] = namc_code
        response["namc_term"] = self._safe_get(matched_row, 'NAMC_term')
        response["namc_term_devanagari"] = self._safe_get(matched_row, 'NAMC_term_DEVANAGARI')

        # Semantic search metadata (Step 7)
        response["match_confidence"] = round(match_confidence, 3)
        response["match_alternatives"] = match_alternatives
        response["match_requires_confirmation"] = match_requires_confirmation

        return response




    # ------------------------------------------------------------------
    # Semantic Search (Step 7)
    # ------------------------------------------------------------------

    def _load_or_build_embeddings(self):
        """Pre-compute sentence embeddings for all disease names. Cached to disk."""
        import pickle, os
        if os.path.exists(EMBEDDINGS_PATH):
            try:
                with open(EMBEDDINGS_PATH, 'rb') as f:
                    data = pickle.load(f)
                return data['names'], data['embeddings']
            except Exception as e:
                logger.warning(f"Could not load embeddings cache: {e}")

        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            # Get all disease names from the loaded CSV dataframe (self.df)
            names = self.df['Name English'].fillna('').tolist()
            embeddings = model.encode(names, normalize_embeddings=True, show_progress_bar=False)
            os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
            with open(EMBEDDINGS_PATH, 'wb') as f:
                pickle.dump({'names': names, 'embeddings': embeddings}, f)
            return names, embeddings
        except ImportError:
            return None, None

    def _semantic_search(self, query: str):
        """Returns list of (row, confidence) sorted by descending confidence, max 3."""
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity
            import numpy as np

            if not hasattr(self, '_sem_names') or self._sem_names is None:
                self._sem_names, self._sem_embeddings = self._load_or_build_embeddings()

            if self._sem_names is None:
                return []

            if not hasattr(self, '_sem_model'):
                self._sem_model = SentenceTransformer('all-MiniLM-L6-v2')

            q_emb = self._sem_model.encode([query], normalize_embeddings=True)
            sims  = sk_cosine_similarity(q_emb, self._sem_embeddings)[0]
            top3  = sims.argsort()[-3:][::-1]
            return [(self.df.iloc[i], float(sims[i])) for i in top3 if float(sims[i]) > 0.3]
        except Exception as e:
            logger.debug(f"Semantic search unavailable: {e}")
            return []

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
        self, row, source_disease, vikriti, prakriti, age,
        patient_data: dict = None, namc_code: str = '',
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

        # Predicted improvement via GBM model (Step 6)
        pd_data = patient_data or {}
        improvement_result = _improvement_svc.predict(
            age=age,
            severity=pd_data.get("severity", 5),
            comorbidities=pd_data.get("comorbidities", ""),
            symptoms=pd_data.get("symptoms", ""),
            prakriti=prakriti,
            vikriti=vikriti,
            namc_code=namc_code,
        )
        predicted_improvement = improvement_result["predicted_improvement"]
        confidence_interval = improvement_result["confidence_interval"]
        improvement_model_samples = improvement_result["n_training_samples"]

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
            "confidence_interval": confidence_interval,
            "improvement_model_samples": improvement_model_samples,
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
                f"Recommendation sourced from ISHAAyush dataset ({age_group}, {gender_info})."
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
ISHAAyush_service = ISHAAyushService()

# Improvement model singleton (Step 6)
# Wrapped in try/except so sklearn import errors don't break the service
try:
    from services.improvement_model_service import ImprovementModelService
    _improvement_svc = ImprovementModelService()
except Exception as _imp_err:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"ImprovementModelService unavailable: {_imp_err}")

    class _FallbackImprovementSvc:
        def predict(self, **kwargs):
            prakriti = kwargs.get('prakriti', '')
            vikriti = kwargs.get('vikriti', '')
            val = 85.0 if prakriti == vikriti else 75.0
            return {"predicted_improvement": val, "confidence_interval": [val - 10.0, val + 5.0], "n_training_samples": 0}

    _improvement_svc = _FallbackImprovementSvc()
