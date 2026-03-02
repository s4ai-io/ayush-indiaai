"""
Disease Name Lookup — Sanskrit Devanāgarī names for all diseases tracked in the system.

Sources:
  - NAMC (National Ayurveda Morbidity Code) Codified_Ayurvedic_disease.csv
  - Manual additions for diseases not present in NAMC (verified Āyurvedic terms)

Each entry: { "devanagari": "...", "iast": "...", "english": "...", "hindi": "..." }
"""

# ── Full lookup keyed by the stored DB diagnosis string ─────────────────────
# DB diseases are stored as "English (Transliteration)" or plain "English"

DISEASE_NAMES: dict[str, dict] = {

    # ── Auto-matched from NAMC CSV ──────────────────────────────────────────
    "Acidity (Amlapitta)": {
        "devanagari": "अम्लपित्तम्",
        "iast":       "amlapittam",
        "english":    "Acidity",
        "hindi":      "अम्लपित्त",
    },
    "Amenorrhoea disorder (TM2)": {
        "devanagari": "अरजस्का",
        "iast":       "arajaskā",
        "english":    "Amenorrhoea",
        "hindi":      "रजोरोध",
    },
    "Anxiety (Chittodvega)": {
        "devanagari": "चित्तोद्वेगः",
        "iast":       "cittodvegaḥ",
        "english":    "Anxiety",
        "hindi":      "चिंता",
    },
    "Asthma (Tamaka Shwasa)": {
        "devanagari": "तमकश्वासः",
        "iast":       "tamakaśvāsaḥ",
        "english":    "Asthma",
        "hindi":      "दमा",
    },
    "Constipation (Vibandha)": {
        "devanagari": "विबन्धः",
        "iast":       "vibandhaḥ",
        "english":    "Constipation",
        "hindi":      "कब्ज़",
    },
    "Cough": {
        "devanagari": "कासः",
        "iast":       "kāsaḥ",
        "english":    "Cough",
        "hindi":      "खांसी",
    },
    "Cough (Kasa)": {
        "devanagari": "कासः",
        "iast":       "kāsaḥ",
        "english":    "Cough",
        "hindi":      "खांसी",
    },
    "Diabetes (Madhumeha)": {
        "devanagari": "मधुमेहः",
        "iast":       "madhumehaḥ",
        "english":    "Diabetes",
        "hindi":      "मधुमेह",
    },
    "Diarrhea (Atisara)": {
        "devanagari": "अतिसारः",
        "iast":       "atisāraḥ",
        "english":    "Diarrhea",
        "hindi":      "अतिसार",
    },
    "Eye Disorder (Netra Roga)": {
        "devanagari": "नेत्ररोगः",
        "iast":       "netarogaḥ",
        "english":    "Eye Disorder",
        "hindi":      "नेत्र रोग",
    },
    "Fever (Jwara)": {
        "devanagari": "ज्वरः",
        "iast":       "jvaraḥ",
        "english":    "Fever",
        "hindi":      "बुखार",
    },
    "Heat Stroke (Ushna Jwar)": {
        "devanagari": "उष्णज्वरः",
        "iast":       "uṣṇajvaraḥ",
        "english":    "Heat Stroke",
        "hindi":      "लू",
    },
    "Indigestion (Ajirna)": {
        "devanagari": "अजीर्णम्",
        "iast":       "ajīrṇam",
        "english":    "Indigestion",
        "hindi":      "अपच",
    },
    "Insomnia (Anidra)": {
        "devanagari": "अनिद्रा",
        "iast":       "anidrā",
        "english":    "Insomnia",
        "hindi":      "अनिद्रा",
    },
    "Lethargy (Tandra)": {
        "devanagari": "तन्द्रा",
        "iast":       "tandrā",
        "english":    "Lethargy",
        "hindi":      "तन्द्रा",
    },
    "lethargy (due only to kaphadōṣa)": {
        "devanagari": "तन्द्रा (कफदोषज)",
        "iast":       "tandrā (kaphadōṣaja)",
        "english":    "Lethargy (Kapha)",
        "hindi":      "तन्द्रा",
    },
    "Malaria (Vishama Jwara)": {
        "devanagari": "विषमज्वरः",
        "iast":       "viṣamajvaraḥ",
        "english":    "Malaria",
        "hindi":      "मलेरिया",
    },
    "Migraine (Ardhavabhedaka)": {
        "devanagari": "अर्धावभेदकः",
        "iast":       "ardhāvabhedakaḥ",
        "english":    "Migraine",
        "hindi":      "अर्धशीशी",
    },
    "Obesity (Sthoulya)": {
        "devanagari": "स्थूलत्वम्",
        "iast":       "sthūlatvam",
        "english":    "Obesity",
        "hindi":      "मोटापा",
    },
    "Rhinitis (Pratishyaya)": {
        "devanagari": "प्रतिश्यायः",
        "iast":       "pratiśyāyaḥ",
        "english":    "Rhinitis",
        "hindi":      "नज़ला",
    },
    "Skin Disorder (Kushtha)": {
        "devanagari": "कुष्ठम्",
        "iast":       "kuṣṭham",
        "english":    "Skin Disorder",
        "hindi":      "त्वचा रोग",
    },
    "Skin Rash (Kushtha)": {
        "devanagari": "शीतपित्तम्",
        "iast":       "śītapittam",
        "english":    "Skin Rash",
        "hindi":      "त्वचा विस्फोट",
    },

    # ── Manual additions (authentic Āyurvedic terms, not in NAMC CSV) ───────
    "Dengue (Dandashthaka Jwara)": {
        "devanagari": "दण्डाष्टकज्वरः",
        "iast":       "daṇḍāṣṭakajvaraḥ",
        "english":    "Dengue",
        "hindi":      "डेंगू ज्वर",
    },
    "Allergy (Sheetapitta)": {
        "devanagari": "शीतपित्तम्",
        "iast":       "śītapittam",
        "english":    "Allergy",
        "hindi":      "एलर्जी",
    },
    "Bronchitis (Kasa)": {
        "devanagari": "श्वासनलीकासः",
        "iast":       "śvāsanadīkāsaḥ",
        "english":    "Bronchitis",
        "hindi":      "श्वासनली शोथ",
    },
    "Common Cold": {
        "devanagari": "प्रतिश्यायः",
        "iast":       "pratiśyāyaḥ",
        "english":    "Common Cold",
        "hindi":      "सर्दी-जुकाम",
    },
    "Dehydration (Trishna)": {
        "devanagari": "तृष्णारोगः",
        "iast":       "tṛṣṇārogaḥ",
        "english":    "Dehydration",
        "hindi":      "निर्जलीकरण",
    },
    "Hemorrhoids (Arsha)": {
        "devanagari": "अर्शः",
        "iast":       "arśaḥ",
        "english":    "Hemorrhoids",
        "hindi":      "बवासीर",
    },
    "Joint Pain (Amavata)": {
        "devanagari": "आमवातः",
        "iast":       "āmavātaḥ",
        "english":    "Joint Pain",
        "hindi":      "आमवात",
    },
    "Skin Infection (Kushtha)": {
        "devanagari": "त्वक्संक्रमणम्",
        "iast":       "tvaksaṃkramaṇam",
        "english":    "Skin Infection",
        "hindi":      "त्वचा संक्रमण",
    },
    "Urinary Disorder (Mutraghata)": {
        "devanagari": "मूत्राघातः",
        "iast":       "mūtrāghātaḥ",
        "english":    "Urinary Disorder",
        "hindi":      "मूत्राघात",
    },
}


def get_devanagari(diagnosis: str) -> str:
    """Return Devanāgarī name for a diagnosis string. Falls back to the input."""
    entry = DISEASE_NAMES.get(diagnosis)
    if entry:
        return entry["devanagari"]
    # Try stripping trailing whitespace / casing variations
    for k, v in DISEASE_NAMES.items():
        if k.strip().lower() == diagnosis.strip().lower():
            return v["devanagari"]
    return diagnosis  # fallback: return as-is


def get_full_name(diagnosis: str) -> dict:
    """Return the complete name record for a diagnosis string."""
    return DISEASE_NAMES.get(diagnosis, {
        "devanagari": diagnosis,
        "iast":       diagnosis,
        "english":    diagnosis,
        "hindi":      diagnosis,
    })


def enrich_with_devanagari(records: list[dict], field: str = "disease") -> list[dict]:
    """
    Add 'devanagari', 'iast', 'hindi' keys to each record in a list.
    'field' is the key in each dict that holds the diagnosis string.
    """
    for r in records:
        raw = r.get(field, "")
        entry = get_full_name(raw)
        r["devanagari"] = entry["devanagari"]
        r["iast"]       = entry["iast"]
        r["hindi"]      = entry["hindi"]
    return records
