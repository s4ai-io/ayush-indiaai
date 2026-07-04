"""
Gradient Boosting Regressor that replaces the 75/85 hardcoded improvement heuristic.

Training features:
  age, severity (1-10), comorbidity_count, symptom_count,
  dosha_match (prakriti==vikriti binary), season_num (month→Ritu 1-6), namc_code (target-encoded)

Target: doctor_rating proxy (Accurate→80, Needs Changes→40) until real outcome scores exist.
         If ClinicalOutcomeScore.percentage_change is available for a visit, it overrides.

Output: {"predicted_improvement": float, "confidence_interval": [low, high], "n_training_samples": int}
"""
import os, json, pickle, logging
from datetime import datetime
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'improvement_model.pkl')

MONTH_TO_RITU = {1:6, 2:6, 3:1, 4:1, 5:2, 6:2, 7:3, 8:3, 9:4, 10:4, 11:5, 12:5}


class ImprovementModelService:

    def __init__(self):
        self.model = None
        self.namc_means: dict = {}   # target-encoding map
        self.n_samples: int = 0
        self._load_or_train()

    # ── feature engineering ──────────────────────────────────────────────────

    @staticmethod
    def _count_items(text: Optional[str]) -> int:
        if not text:
            return 0
        return max(1, len([x for x in str(text).split(',') if x.strip()]))

    @staticmethod
    def _season(visit_date) -> int:
        if visit_date is None:
            return 3
        month = visit_date.month if hasattr(visit_date, 'month') else datetime.utcnow().month
        return MONTH_TO_RITU.get(month, 3)

    def _encode_namc(self, namc_code: str) -> float:
        return self.namc_means.get(namc_code, self.namc_means.get('__default__', 70.0))

    def _featurise(self, age, severity, comorbidities, symptoms, prakriti, vikriti, visit_date, namc_code) -> list:
        return [
            float(age or 35),
            float(severity or 5),
            self._count_items(comorbidities),
            self._count_items(symptoms),
            1.0 if (prakriti or '') == (vikriti or '') else 0.0,
            float(self._season(visit_date)),
            self._encode_namc(namc_code or ''),
        ]

    # ── training ─────────────────────────────────────────────────────────────

    def train(self, db=None):
        """Train on TreatmentFeedback rows. Falls back to synthetic data if DB unavailable."""
        from sklearn.ensemble import GradientBoostingRegressor

        X, y = [], []

        if db is not None:
            try:
                from models import TreatmentFeedback, MedicalRecord, Patient, ClinicalOutcomeScore
                rows = db.query(TreatmentFeedback).limit(20000).all()
                outcome_map = {}
                for oc in db.query(ClinicalOutcomeScore).filter(ClinicalOutcomeScore.followup_value.isnot(None)).all():
                    outcome_map[oc.medical_record_id] = oc.percentage_change

                namc_labels: dict = {}

                for fb in rows:
                    ctx = json.loads(fb.ml_context or '{}')
                    namc = ctx.get('namc_code', '')
                    label = outcome_map.get(fb.medical_record_id)
                    if label is None:
                        label = 80.0 if (fb.doctor_rating or '') == 'positive' else 40.0

                    rec = db.query(MedicalRecord).filter_by(id=fb.medical_record_id).first()
                    pat = db.query(Patient).filter_by(id=fb.patient_id).first() if fb.patient_id else None

                    feats = self._featurise(
                        age=getattr(pat, 'age', 35),
                        severity=ctx.get('severity', 5),
                        comorbidities=getattr(rec, 'comorbidities', '') if rec else '',
                        symptoms=getattr(rec, 'symptoms', '') if rec else '',
                        prakriti=ctx.get('prakriti', ''),
                        vikriti=ctx.get('vikriti', ''),
                        visit_date=getattr(rec, 'visit_date', None) if rec else None,
                        namc_code=namc,
                    )
                    X.append(feats)
                    y.append(float(label))
                    namc_labels.setdefault(namc, []).append(float(label))

                # Build target-encoding map
                self.namc_means = {k: float(np.mean(v)) for k, v in namc_labels.items()}
                self.namc_means['__default__'] = float(np.mean(y)) if y else 70.0

            except Exception as e:
                logger.warning(f"DB training failed ({e}), using synthetic fallback")
                X, y = [], []

        if len(X) < 50:
            X, y = self._synthetic_data()
            self.namc_means = {'__default__': 70.0}

        X = np.array(X)
        y = np.array(y)
        self.n_samples = len(y)

        gbm = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
        gbm.fit(X, y)
        self.model = gbm

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump({'model': gbm, 'namc_means': self.namc_means, 'n_samples': self.n_samples}, f)
        logger.info(f"Improvement model trained on {self.n_samples} samples")

    @staticmethod
    def _synthetic_data():
        """Minimal synthetic dataset for cold-start training."""
        rng = np.random.default_rng(42)
        n = 500
        ages        = rng.integers(20, 75, n).astype(float)
        severities  = rng.integers(1, 11, n).astype(float)
        como_counts = rng.integers(0, 4, n).astype(float)
        sym_counts  = rng.integers(1, 6, n).astype(float)
        dosha_match = rng.integers(0, 2, n).astype(float)
        seasons     = rng.integers(1, 7, n).astype(float)
        namc_enc    = rng.uniform(60, 85, n)
        # Simple linear relationship + noise
        y = (80 - 0.15*severities - 0.4*ages/10 + 5*dosha_match
             - 3*como_counts + rng.normal(0, 8, n))
        y = np.clip(y, 20, 98)
        X = np.column_stack([ages, severities, como_counts, sym_counts, dosha_match, seasons, namc_enc])
        return X.tolist(), y.tolist()

    # ── inference ─────────────────────────────────────────────────────────────

    def predict(self, age, severity, comorbidities, symptoms, prakriti, vikriti, visit_date=None, namc_code='') -> dict:
        if self.model is None:
            return {"predicted_improvement": 75.0, "confidence_interval": [65.0, 85.0], "n_training_samples": 0}

        feats = self._featurise(age, severity, comorbidities, symptoms, prakriti, vikriti, visit_date, namc_code)
        X = np.array([feats])
        pred = float(self.model.predict(X)[0])
        pred = round(max(20.0, min(98.0, pred)), 1)

        # Bootstrap-style CI using individual tree predictions
        try:
            tree_preds = np.array([t.predict(X)[0] for t in self.model.estimators_.flatten()])
            lo = round(float(np.percentile(tree_preds, 10)), 1)
            hi = round(float(np.percentile(tree_preds, 90)), 1)
            lo = max(20.0, min(pred, lo))
            hi = min(98.0, max(pred, hi))
        except Exception:
            lo, hi = round(pred - 8.0, 1), round(pred + 8.0, 1)

        return {
            "predicted_improvement": pred,
            "confidence_interval": [lo, hi],
            "n_training_samples": self.n_samples,
        }

    # ── load or train ─────────────────────────────────────────────────────────

    def _load_or_train(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    saved = pickle.load(f)
                self.model     = saved['model']
                self.namc_means = saved.get('namc_means', {'__default__': 70.0})
                self.n_samples  = saved.get('n_samples', 0)
                logger.info(f"Improvement model loaded ({self.n_samples} training samples)")
                return
            except Exception as e:
                logger.warning(f"Could not load improvement model: {e}")
        # Train on synthetic data at startup (no DB at init time)
        self.train(db=None)
