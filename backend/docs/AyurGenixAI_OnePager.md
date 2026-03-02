# ISHAAyush AI — One-Page Summary

**AYUSH India AI | Ministry of AYUSH PoC | February 2026**

---

## What It Does

ISHAAyush AI is a **treatment recommendation engine** that generates personalised Ayurvedic treatment plans for doctors. Given a patient's disease, symptoms, and dosha profile, it returns herb prescriptions, yoga therapy, dietary guidelines, prognosis, and complications — all sourced from a curated **446-disease medical dataset** with full explainability.

## How It Works — 4-Tier Matching

```
Patient Input → Tier 1: Exact Disease Lookup (100% confidence)
             → Tier 2: Fuzzy Name Match — difflib SequenceMatcher (65-99%)
             → Tier 3: Symptom Matching — TF-IDF + Cosine Similarity (10-99%)
             → Tier 4: Dosha-Based Fallback — Prakriti/Vikriti rules (0%)
```

| Tier | Algorithm | When Used | Example |
|------|-----------|-----------|---------|
| **1. Exact** | String equality | Doctor types known disease | "Diabetes" → Diabetes (100%) |
| **2. Fuzzy** | Ratcliff/Obershelp | Typos or partial names | "Diabtes" → Diabetes (86%) |
| **3. TF-IDF** | Cosine similarity on symptom vectors | No disease name, only symptoms | "excessive thirst, frequent urination" → Diabetes (72%) |
| **4. Fallback** | Dosha-specific herb/yoga/diet rules | Nothing matches | Kapha imbalance → Triphala, Kapalbhati |

## Key Design Decisions

| Decision | Alternative Considered | Why We Chose This |
|---|---|---|
| **Retrieval-based** (not generative AI) | GPT-4 / LLM | Zero hallucination risk — every herb comes from verified dataset. Critical for patient safety. |
| **TF-IDF** (not BERT/transformers) | Medical BERT embeddings | 446 docs → TF-IDF is optimal. BERT adds 1.5GB RAM for marginal gain at this scale. |
| **difflib** (not Levenshtein) | python-Levenshtein, FuzzyWuzzy | Zero dependencies (Python stdlib). Fast enough for 446 entries. |
| **In-memory** (not database queries) | PostgreSQL full-text search | Sub-50ms inference. Dataset fits in ~15MB RAM. |

## Dataset

**`ISHAAyushAI_Dataset.csv`** — 446 diseases × 34 columns covering: symptoms, herbs, formulations, yoga, diet, lifestyle, doshas, prognosis, complications, prevention, and medical intervention. Includes Hindi and Marathi disease names.

## Output (13 Fields)

| Category | Fields |
|---|---|
| **Treatment** | Herbs (with dosage), Yoga practices, Diet, Lifestyle, Formulation |
| **Clinical** | Prevention, Prognosis, Complications, Medical Intervention |
| **AI Metadata** | Match method, Confidence %, Source disease, Predicted improvement, Explainability |

## Performance

| Metric | Value |
|---|---|
| Startup | ~200ms |
| Inference | < 50ms |
| Memory | ~15 MB |
| TF-IDF Features | 1,523 (unigrams + bigrams) |
| External API calls | None (fully offline) |

## Tech Stack

**Python 3.11** · **FastAPI** · **Pandas** · **scikit-learn** (TfidfVectorizer, cosine_similarity) · **NumPy** · **difflib** (stdlib)

## Architecture

```
Next.js Frontend ──POST──▶ FastAPI /api/ml/recommend ──▶ ISHAAyushService (in-memory)
                  ◀─JSON──                              ◀── ISHAAyushAI_Dataset.csv
```

---

*Full technical report: [ISHAAyushAI_Model_Report.md](./ISHAAyushAI_Model_Report.md)*
