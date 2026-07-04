"""
disease_pool.py
────────────────
Shared disease catalogue for the v2 synthetic data generator
(generate_historical_data_v2.py / seed_weekly_surge_data_v2.py).

Two tiers, matching how a real OPD diagnosis-frequency table actually looks:

  SEASONAL_DISEASES  — ~20 acute/infectious conditions whose real-world
  incidence genuinely tracks the Ayurvedic Ritu calendar (dengue in monsoon,
  respiratory illness in winter, heat illness in summer). Unchanged from the
  original generator — this is real epidemiology, not just a detector
  convenience, so it's kept as the "common, seasonal" layer.

  CHRONIC_DISEASES — ~90 additional diagnoses that a real Ayurvedic OPD sees
  year-round at a roughly flat background rate (musculoskeletal, dermatological,
  endocrine, cardiovascular, neuro/psych, ENT, gynaecological/urological,
  infectious, and a handful of rare/referral-only conditions), each tagged with
  a rough real-world frequency tier (common / uncommon / rare) so the sampled
  mix has a realistic long tail instead of every diagnosis appearing equally
  often.

  Source: names, dosha, symptoms and yoga/herb suggestions are adapted from the
  National Ayurveda Morbidity Codes dataset already in this repo
  (data/Codified_Ayurvedic_disease.csv), filtered to conditions plausible in an
  Indian outpatient Ayurveda clinic (exotic/non-endemic entries in the raw NAMC
  set — e.g. Buruli ulcer, tularemia, river blindness, ciguatera poisoning —
  were dropped), cleaned to a simplified anglicized-Sanskrit label matching the
  existing house style (e.g. "Osteoarthritis (Sandhivata)"), and supplemented
  with a few very common Indian OPD conditions the raw NAMC extract didn't
  surface well (hypertension, vitiligo, infertility, typhoid, UTI). Herb/yoga
  fields that were "None specific" in the source were filled with a
  dosha-appropriate default rather than left empty.
"""
from __future__ import annotations

import random

# ─── Tier 1: seasonal / acute — unchanged from generate_historical_data.py ────
SEASONAL_DISEASES: dict[int, list] = {
    1: [
        ("Cough (Kasa)",          "Kapha",  "Moderate",  "Kapha",     "Sitopaladi Churna, Tulsi",     "Pranayama, Bhujangasana"),
        ("Bronchitis (Kasa)",     "Kapha",  "Moderate",  "Kapha",     "Vasaka, Pippali",              "Anulom Vilom, Kapalbhati"),
        ("Joint Pain (Amavata)",  "Vata",   "Moderate",  "Vata",      "Ashwagandha, Guggulu",         "Pawanmuktasana, Trikonasana"),
        ("Common Cold",           "Kapha",  "Mild",      "Kapha",     "Tulsi, Ginger",                "Pranayama"),
        ("Asthma (Tamaka Shwasa)","Kapha",  "Severe",    "Kapha",     "Vasaka, Kantakari",            "Anulom Vilom"),
        ("Constipation (Vibandha)","Vata",  "Mild",      "Vata",      "Triphala, Isabgol",            "Pawanmuktasana"),
    ],
    2: [
        ("Cough (Kasa)",          "Kapha",  "Moderate",  "Kapha",     "Sitopaladi Churna, Tulsi",     "Pranayama, Bhujangasana"),
        ("Asthma (Tamaka Shwasa)","Kapha",  "Severe",    "Kapha",     "Vasaka, Kantakari",            "Anulom Vilom"),
        ("Joint Pain (Amavata)",  "Vata",   "Moderate",  "Vata",      "Ashwagandha, Guggulu",         "Pawanmuktasana"),
        ("Rhinitis (Pratishyaya)","Kapha",  "Mild",      "Kapha",     "Shadabindu Taila",             "Jal Neti"),
        ("Constipation (Vibandha)","Vata",  "Mild",      "Vata",      "Triphala, Isabgol",            "Pawanmuktasana"),
        ("Anxiety (Chittodvega)", "Vata",   "Moderate",  "Vata",      "Brahmi, Ashwagandha",          "Yoga Nidra, Shavasana"),
    ],
    3: [
        ("Allergy (Sheetapitta)", "Kapha",  "Mild",      "Kapha",     "Haridra Khanda, Neem",         "Bhastrika"),
        ("Rhinitis (Pratishyaya)","Kapha",  "Mild",      "Kapha",     "Shadabindu Taila",             "Jal Neti"),
        ("Skin Disorder (Kushtha)","Pitta", "Moderate",  "Pitta",     "Neem, Manjistha",              "Viparita Karani"),
        ("Fever (Jwara)",         "Pitta",  "Moderate",  "Pitta-Kapha","Sudarshan Churna, Tulsi",     "Shavasana"),
        ("Indigestion (Ajirna)",  "Kapha",  "Mild",      "Kapha",     "Trikatu, Ginger",              "Vajrasana post meals"),
        ("Lethargy (Tandra)",     "Kapha",  "Mild",      "Kapha",     "Trikatu, Brahmi",              "Surya Namaskar"),
    ],
    4: [
        ("Allergy (Sheetapitta)", "Kapha",  "Mild",      "Kapha",     "Haridra Khanda, Neem",         "Bhastrika"),
        ("Skin Disorder (Kushtha)","Pitta", "Moderate",  "Pitta",     "Neem, Manjistha",              "Viparita Karani"),
        ("Fever (Jwara)",         "Pitta",  "Moderate",  "Pitta",     "Sudarshan Churna, Tulsi",      "Shavasana"),
        ("Acidity (Amlapitta)",   "Pitta",  "Mild",      "Pitta",     "Shatavari, Licorice",          "Vajrasana, Setu Bandha"),
        ("Hemorrhoids (Arsha)",   "Vata",   "Moderate",  "Vata-Pitta","Arshakuthar Ras, Triphala",    "Mula Bandha"),
        ("Migraine (Ardhavabhedaka)","Pitta","Moderate", "Pitta",     "Brahmi, Sarpagandha",          "Sheetali Pranayama"),
    ],
    5: [
        ("Heat Stroke (Ushna Jwar)","Pitta","Severe",    "Pitta",     "Chandan, Ushira",              "Sheetali Pranayama"),
        ("Acidity (Amlapitta)",   "Pitta",  "Moderate",  "Pitta",     "Shatavari, Licorice",          "Vajrasana, Setu Bandha"),
        ("Skin Rash (Kushtha)",   "Pitta",  "Mild",      "Pitta",     "Neem, Chandan, Haridra",       "Sheetali"),
        ("Dehydration (Trishna)", "Pitta",  "Moderate",  "Pitta",     "Ushira, Chandan",              "Sheetali Pranayama"),
        ("Migraine (Ardhavabhedaka)","Pitta","Moderate", "Pitta",     "Brahmi, Sarpagandha",          "Sheetali Pranayama"),
        ("Urinary Disorder (Mutraghata)","Pitta","Moderate","Pitta",  "Gokshura, Punarnava",          "Baddha Konasana"),
    ],
    6: [
        ("Heat Stroke (Ushna Jwar)","Pitta","Severe",    "Pitta",     "Chandan, Ushira",              "Sheetali Pranayama"),
        ("Acidity (Amlapitta)",   "Pitta",  "Moderate",  "Pitta",     "Shatavari, Licorice",          "Vajrasana"),
        ("Fever (Jwara)",         "Pitta",  "Moderate",  "Pitta",     "Sudarshan Churna, Tulsi",      "Shavasana"),
        ("Skin Rash (Kushtha)",   "Pitta",  "Mild",      "Pitta",     "Neem, Chandan",                "Sheetali"),
        ("Diarrhea (Atisara)",    "Pitta",  "Moderate",  "Pitta",     "Bilva, Kutaj",                 "Pawanmuktasana"),
        ("Insomnia (Anidra)",     "Vata",   "Mild",      "Vata-Pitta","Brahmi, Jatamansi",            "Yoga Nidra"),
    ],
    7: [
        ("Fever (Jwara)",         "Pitta",  "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Diarrhea (Atisara)",    "Pitta",  "Moderate",  "Pitta",     "Bilva, Kutaj",                 "Pawanmuktasana"),
        ("Malaria (Vishama Jwara)","Pitta", "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Indigestion (Ajirna)",  "Vata",   "Moderate",  "Vata",      "Trikatu, Ginger",              "Vajrasana"),
        ("Joint Pain (Amavata)",  "Vata",   "Moderate",  "Vata",      "Ashwagandha, Guggulu",         "Pawanmuktasana"),
        ("Skin Infection (Kushtha)","Kapha","Moderate",  "Kapha",     "Neem, Haridra",                "Viparita Karani"),
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
    ],
    8: [
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
        ("Fever (Jwara)",         "Pitta",  "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Diarrhea (Atisara)",    "Pitta",  "Moderate",  "Pitta",     "Bilva, Kutaj",                 "Pawanmuktasana"),
        ("Malaria (Vishama Jwara)","Pitta", "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Indigestion (Ajirna)",  "Vata",   "Mild",      "Vata",      "Trikatu, Ginger",              "Vajrasana"),
    ],
    9: [
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Shavasana"),
        ("Eye Disorder (Netra Roga)","Pitta","Mild",     "Pitta",     "Triphala, Shatavari",          "Trataka"),
        ("Acidity (Amlapitta)",   "Pitta",  "Moderate",  "Pitta",     "Shatavari, Licorice",          "Vajrasana"),
        ("Fever (Jwara)",         "Pitta",  "Moderate",  "Pitta",     "Sudarshan Churna, Tulsi",      "Shavasana"),
        ("Skin Disorder (Kushtha)","Pitta", "Moderate",  "Pitta",     "Neem, Manjistha",              "Viparita Karani"),
        ("Diarrhea (Atisara)",    "Pitta",  "Mild",      "Pitta",     "Bilva, Kutaj",                 "Pawanmuktasana"),
    ],
    10: [
        ("Diabetes (Madhumeha)",  "Kapha",  "Moderate",  "Kapha",     "Gurmar, Karela, Vijaysar",     "Mandukasana, Yoga Nidra"),
        ("Obesity (Sthoulya)",    "Kapha",  "Moderate",  "Kapha",     "Triphala, Guggulu",            "Surya Namaskar"),
        ("Eye Disorder (Netra Roga)","Pitta","Mild",     "Pitta",     "Triphala, Shatavari",          "Trataka"),
        ("Anxiety (Chittodvega)", "Vata",   "Moderate",  "Vata",      "Brahmi, Ashwagandha",          "Yoga Nidra"),
        ("Acidity (Amlapitta)",   "Pitta",  "Mild",      "Pitta",     "Shatavari, Licorice",          "Vajrasana"),
        ("Migraine (Ardhavabhedaka)","Vata","Moderate",  "Vata",      "Brahmi, Sarpagandha",          "Sheetali Pranayama"),
    ],
    11: [
        ("Bronchitis (Kasa)",     "Kapha",  "Moderate",  "Kapha",     "Vasaka, Pippali, Tulsi",       "Kapalbhati"),
        ("Cough (Kasa)",          "Kapha",  "Mild",      "Kapha",     "Sitopaladi Churna, Tulsi",     "Pranayama"),
        ("Diabetes (Madhumeha)",  "Kapha",  "Moderate",  "Kapha",     "Gurmar, Karela",               "Mandukasana"),
        ("Obesity (Sthoulya)",    "Kapha",  "Moderate",  "Kapha",     "Triphala, Guggulu",            "Surya Namaskar"),
        ("Constipation (Vibandha)","Vata",  "Mild",      "Vata",      "Triphala, Isabgol",            "Pawanmuktasana"),
        ("Anxiety (Chittodvega)", "Vata",   "Moderate",  "Vata",      "Brahmi, Ashwagandha",          "Yoga Nidra, Shavasana"),
    ],
    12: [
        ("Cough (Kasa)",          "Kapha",  "Moderate",  "Kapha",     "Sitopaladi Churna, Tulsi",     "Pranayama"),
        ("Asthma (Tamaka Shwasa)","Kapha",  "Severe",    "Kapha",     "Vasaka, Kantakari",            "Anulom Vilom"),
        ("Joint Pain (Amavata)",  "Vata",   "Moderate",  "Vata",      "Ashwagandha, Guggulu",         "Pawanmuktasana"),
        ("Rhinitis (Pratishyaya)","Kapha",  "Mild",      "Kapha",     "Shadabindu Taila",             "Jal Neti"),
        ("Constipation (Vibandha)","Vata",  "Mild",      "Vata",      "Triphala, Isabgol",            "Pawanmuktasana"),
        ("Diabetes (Madhumeha)",  "Kapha",  "Moderate",  "Kapha",     "Gurmar, Karela",               "Mandukasana"),
    ],
}

SEASONAL_SYMPTOMS: dict[str, str] = {
    "Cough (Kasa)":         "Persistent cough, throat irritation, breathlessness",
    "Asthma (Tamaka Shwasa)":"Wheezing, breathlessness, chest tightness, cough at night",
    "Joint Pain (Amavata)": "Morning stiffness, swelling in joints, pain on movement",
    "Dengue (Dandashthaka Jwara)":"High fever, severe headache, rash, retro-orbital pain, myalgia",
    "Fever (Jwara)":        "High temperature, chills, body ache, fatigue, sweating",
    "Acidity (Amlapitta)":  "Heartburn, sour belching, nausea, upper abdominal discomfort",
    "Skin Disorder (Kushtha)":"Itching, rash, discoloration, scaling of skin",
    "Diarrhea (Atisara)":   "Loose watery stools, abdominal cramps, dehydration",
    "Diabetes (Madhumeha)": "Excessive thirst, frequent urination, fatigue, blurred vision",
    "Obesity (Sthoulya)":   "Excess weight, lethargy, breathlessness on exertion",
    "Anxiety (Chittodvega)":"Restlessness, palpitations, sleeplessness, excessive worry",
    "Constipation (Vibandha)":"Infrequent stools, hard stools, bloating, discomfort",
    "Allergy (Sheetapitta)":"Urticaria, itching, redness, runny nose, sneezing",
    "Migraine (Ardhavabhedaka)":"One-sided throbbing headache, nausea, photophobia",
    "Bronchitis (Kasa)":    "Productive cough, mucus, chest congestion, low-grade fever",
    "Rhinitis (Pratishyaya)":"Runny nose, blocked nose, sneezing, post-nasal drip",
    "Heat Stroke (Ushna Jwar)":"High body temperature, dizziness, fainting, no sweating",
    "Malaria (Vishama Jwara)":"Cyclical fever with chills, headache, vomiting, sweating",
    "Indigestion (Ajirna)": "Bloating, heaviness, loss of appetite, belching",
    "Lethargy (Tandra)":    "Excessive sleepiness, fatigue, dullness, low enthusiasm",
    "Hemorrhoids (Arsha)":  "Pain during bowel movement, bleeding, swelling near anus",
    "Skin Rash (Kushtha)":  "Redness, itching, inflamed patches on skin",
    "Dehydration (Trishna)":"Excessive thirst, dry mouth, dizziness, fatigue",
    "Urinary Disorder (Mutraghata)":"Painful or difficult urination, lower abdomen discomfort",
    "Eye Disorder (Netra Roga)":"Eye irritation, redness, blurred vision, discharge",
    "Insomnia (Anidra)":    "Difficulty falling or staying asleep, daytime fatigue",
    "Skin Infection (Kushtha)":"Redness, pus, swelling, localized pain",
}

# ─── Tier 2: chronic / non-seasonal long tail ────────────────────────────────
# Fields: (name, dosha, prakriti, severity_profile, herbs, yoga, symptoms, weight_tier)
# weight_tier: "common" | "uncommon" | "rare" — coarse real-world OPD frequency,
# not month-dependent (sampled flat across all 12 months).
SEVERITY_PROFILES: dict[str, dict[str, int]] = {
    "mild_heavy":   {"Mild": 60, "Moderate": 30, "Severe": 10},
    "balanced":     {"Mild": 30, "Moderate": 45, "Severe": 25},
    "severe_heavy": {"Mild": 10, "Moderate": 35, "Severe": 55},
}

TIER_WEIGHTS: dict[str, int] = {"common": 10, "uncommon": 4, "rare": 1}

CHRONIC_DISEASES: list[tuple[str, str, str, str, str, str, str, str]] = [
    # (name, dosha, prakriti, severity_profile, herbs, yoga, symptoms, tier)

    # ── Digestive ──
    ("Digestive Disorder (Vikara)",        "Pitta-Vata", "Pitta",  "balanced",   "Triphala, Ginger",              "Vajrasana, Pranayama",        "Bloating, nausea, indigestion, discomfort after eating", "common"),
    ("Irritable Bowel Syndrome (Grahani)",  "Vata",      "Vata",   "balanced",   "Bilva, Kutaja, Triphala",       "Pawanmuktasana",               "Abdominal cramps, bloating, alternating diarrhea and constipation", "common"),
    ("Celiac Disease (Grahani Roga)",       "Vata-Pitta","Vata",   "balanced",   "Kutki, Triphala",               "Vajrasana",                    "Bloating, chronic diarrhea, weight loss", "uncommon"),
    ("Ulcerative Colitis (Raktatisara)",    "Vata-Pitta","Pitta",  "severe_heavy","Kutaja, Bilva, Musta",         "Pawanmuktasana",               "Abdominal pain, diarrhea, blood in stool", "uncommon"),
    ("Amebiasis (Pittaja Atisara)",         "Pitta-Kapha","Pitta", "balanced",   "Kutki, Triphala",               "Vajrasana",                    "Abdominal pain, diarrhea, fever", "uncommon"),
    ("Worm Infection (Krimi Roga)",         "Vata",      "Vata",   "mild_heavy", "Vidanga, Palasha, Triphala",    "Pawanmuktasana",               "Abdominal pain, diarrhea, weight loss, bloating", "common"),
    ("Peptic Ulcer (Parinama Shoola)",      "Pitta",     "Pitta",  "balanced",   "Yashtimadhu, Shatavari",        "Vajrasana",                    "Burning stomach pain, bloating, nausea", "common"),
    ("Gastritis (Urdhva Amlapitta)",        "Pitta",     "Pitta",  "mild_heavy", "Yashtimadhu, Amla",             "Vajrasana",                    "Stomach pain, bloating, nausea after meals", "common"),
    ("Kidney Stones (Ashmari)",             "Vata-Kapha","Kapha",  "severe_heavy","Gokshura, Punarnava, Pashanabheda","Baddha Konasana",           "Severe flank pain, blood in urine, nausea", "uncommon"),
    ("Gallstones (Pittashmari)",            "Pitta-Kapha","Pitta", "balanced",   "Punarnava, Kalmegh",            "Vajrasana",                    "Abdominal pain, nausea, bloating after fatty food", "rare"),
    ("Piles - Anal Fissure (Parikartika)",  "Vata",      "Vata",   "balanced",   "Triphala, Nagakesara",          "Pawanmuktasana",               "Pain during bowel movement, bleeding", "uncommon"),

    # ── Liver / hepatic ──
    ("Liver Disorder (Yakrit Vikara)",      "Pitta-Kapha","Pitta", "balanced",   "Amla, Turmeric, Guduchi",       "Dhanurasana",                  "Fatigue, loss of appetite, yellowing of the skin", "uncommon"),
    ("Hepatitis (Kamala)",                  "Pitta",     "Pitta",  "severe_heavy","Bhumi Amla, Turmeric, Kutki",  "Dhanurasana",                  "Yellowing of skin, fatigue, loss of appetite", "uncommon"),
    ("Cirrhosis (Yakrit Vriddhi)",          "Pitta",     "Pitta",  "severe_heavy","Bhumi Amla, Kutki",            "Gentle walking",               "Jaundice, fatigue, abdominal pain", "rare"),
    ("Fatty Liver (Yakrit Meda Vriddhi)",   "Kapha-Pitta","Kapha", "mild_heavy", "Bhumi Amla, Guduchi, Triphala", "Surya Namaskar",               "Fatigue, mild abdominal discomfort", "common"),

    # ── Musculoskeletal ──
    ("Osteoarthritis (Sandhivata)",         "Vata-Kapha","Vata",   "balanced",   "Turmeric, Ashwagandha, Guggulu","Trikonasana",                  "Joint pain, swelling, stiffness", "common"),
    ("Gout (Vatarakta)",                    "Vata-Pitta","Pitta",  "balanced",   "Guduchi, Triphala",             "Gentle stretching",            "Joint pain, swelling, redness in the big toe", "uncommon"),
    ("Osteoporosis (Asthi Kshaya)",         "Vata",      "Vata",   "balanced",   "Ashwagandha, Guggulu, Shatavari","Tadasana",                    "Fragile bones, fractures, height loss", "uncommon"),
    ("Sciatica (Gridhrasi)",                "Vata",      "Vata",   "balanced",   "Nirgundi, Guggulu",             "Pawanmuktasana",               "Lower back pain, pain radiating down the leg", "common"),
    ("Back Pain (Prishtha Shoola)",         "Vata",      "Vata",   "mild_heavy", "Guggulu, Ashwagandha",          "Bhujangasana",                 "Muscle stiffness, difficulty moving", "common"),
    ("Spondylosis (Griva Sandhigata Vata)", "Vata",      "Vata",   "balanced",   "Nirgundi, Ashwagandha",         "Neck stretches",               "Neck or back pain, stiffness, muscle weakness", "uncommon"),
    ("Scoliosis (Kubjata)",                 "Vata",      "Vata",   "balanced",   "Ashwagandha, Guggulu",          "Spine-flexibility yoga",       "Uneven shoulders, back pain, difficulty standing straight", "rare"),
    ("Frozen Shoulder (Avabahuka)",         "Vata",      "Vata",   "balanced",   "Nirgundi, Guggulu",             "Shoulder rotations",           "Shoulder stiffness, restricted movement, pain", "uncommon"),
    ("Tennis Elbow (Kurpara Shoola)",       "Vata",      "Vata",   "mild_heavy", "Nirgundi, Guggulu",             "Gentle stretching",            "Elbow pain, weak grip", "uncommon"),
    ("Fibromyalgia (Sarvanga Vata)",        "Vata",      "Vata",   "severe_heavy","Ashwagandha, Guggulu",         "Gentle stretching",            "Widespread muscle pain, fatigue, tenderness", "rare"),

    # ── Dermatological ──
    ("Psoriasis (Kitibha Kushtha)",         "Pitta",     "Pitta",  "balanced",   "Neem, Turmeric, Manjistha",     "Sheetali Pranayama",           "Red, inflamed skin, scales, itching", "uncommon"),
    ("Eczema (Vicharchika)",                "Pitta",     "Pitta",  "mild_heavy", "Neem, Aloe Vera, Turmeric",     "Sheetali Pranayama",           "Itchy skin, red rashes, inflammation", "common"),
    ("Acne (Yuvana Pidika)",                "Pitta-Kapha","Pitta", "mild_heavy", "Neem, Turmeric, Manjistha",     "Kapalbhati",                   "Pimples, blackheads, oily skin", "common"),
    ("Alopecia (Indralupta)",               "Pitta",     "Pitta",  "mild_heavy", "Bhringraj, Amla, Neem",         "Head massage",                 "Hair loss, thinning of scalp", "common"),
    ("Dandruff (Darunaka)",                 "Kapha-Pitta","Kapha", "mild_heavy", "Neem, Aloe Vera, Bhringraj",    "Scalp massage",                "Scalp itchiness, flaking", "common"),
    ("Contact Dermatitis (Sparshaja Kushtha)","Pitta",    "Pitta",  "mild_heavy", "Aloe Vera, Neem, Chandan",      "Sheetali Pranayama",           "Redness, itching, swelling", "uncommon"),
    ("Vitiligo (Shwitra)",                  "Pitta-Vata","Pitta",  "balanced",   "Bakuchi, Neem, Manjistha",      "Sheetali Pranayama",           "White patches on the skin", "uncommon"),
    ("Chickenpox (Laghu Masurika)",         "Pitta",     "Pitta",  "balanced",   "Neem, Tulsi, Guduchi",          "Rest",                         "Itchy rashes, fever, tiredness", "uncommon"),
    ("Measles (Romantika)",                 "Pitta",     "Pitta",  "balanced",   "Tulsi, Guduchi, Neem",          "Rest",                         "Fever, cough, runny nose, red eyes, skin rash", "uncommon"),
    ("Warts (Charmakeela)",                 "Kapha",     "Kapha",  "mild_heavy", "Thuja, Neem",                   "Gentle skin care, avoid scratching",                "Small rough skin growths", "common"),
    ("Boils (Vidradhi)",                    "Pitta-Kapha","Pitta", "mild_heavy", "Neem, Turmeric, Manjistha",     "Sheetali Pranayama",           "Painful red lumps, pus formation", "common"),

    # ── Endocrine / metabolic ──
    ("Hyperthyroidism (Atisweda)",          "Pitta",     "Pitta",  "balanced",   "Ashwagandha, Shatavari, Brahmi","Sheetali Pranayama",           "Weight loss, anxiety, tremors, rapid heartbeat", "uncommon"),
    ("Thyroid Disorder (Galaganda Vikara)", "Vata-Pitta","Vata",   "balanced",   "Ashwagandha, Guggulu, Kanchanar","Sarvangasana",                "Fatigue, weight changes, mood swings, hair loss", "common"),
    ("Goiter (Galaganda)",                  "Vata-Pitta","Kapha",  "balanced",   "Kanchanar Guggulu",             "Sarvangasana",                 "Swelling in the neck, difficulty swallowing", "uncommon"),
    ("Hyperlipidemia (Medo Vriddhi)",       "Kapha",     "Kapha",  "mild_heavy", "Guggulu, Arjuna, Triphala",     "Surya Namaskar",               "Elevated cholesterol, fatigue, chest heaviness", "common"),
    ("Erectile Dysfunction (Klaibya)",      "Vata",      "Vata",   "balanced",   "Ashwagandha, Shatavari, Kapikacchu","Mula Bandha",              "Difficulty achieving or maintaining an erection", "uncommon"),
    ("Metabolic Syndrome (Santarpana Janya Vikara)","Kapha","Kapha","mild_heavy","Triphala, Guggulu",            "Surya Namaskar",               "Weight gain, fatigue, high blood sugar and cholesterol", "common"),

    # ── Cardiovascular ──
    ("Heart Disease (Hridroga)",            "Vata-Pitta","Vata",   "severe_heavy","Arjuna, Brahmi, Guggulu",     "Gentle Pranayama",             "Chest pain, fatigue, shortness of breath", "common"),
    ("Angina (Hrit Shoola)",                "Vata-Kapha","Vata",   "severe_heavy","Arjuna, Guggulu",              "Gentle breathing",             "Chest pain, shortness of breath, dizziness", "uncommon"),
    ("Hypertension (Raktachaapa Vriddhi)",  "Pitta",     "Pitta",  "balanced",   "Arjuna, Sarpagandha, Ashwagandha","Shavasana, Anulom Vilom",    "Headache, dizziness, chest discomfort", "common"),
    ("Varicose Veins (Sira Granthi)",       "Vata",      "Vata",   "mild_heavy", "Guggulu, Triphala",             "Viparita Karani",              "Swollen, twisted veins, pain, heaviness in legs", "uncommon"),
    ("Anemia (Pandu Roga)",                 "Pitta",     "Pitta",  "balanced",   "Punarnava, Loha Bhasma, Amla",  "Surya Namaskar",               "Fatigue, pale skin, shortness of breath", "common"),

    # ── Neuro / psychiatric ──
    ("Depression (Vishada)",                "Vata-Pitta","Vata",   "balanced",   "Ashwagandha, Brahmi, Jatamansi","Yoga Nidra",                   "Sadness, loss of interest, fatigue", "common"),
    ("Stress (Manasika Tanava)",            "Vata",      "Vata",   "mild_heavy", "Ashwagandha, Brahmi",           "Shavasana",                    "Anxiety, fatigue, headaches, irritability", "common"),
    ("Bipolar Disorder (Unmada)",           "Vata-Pitta","Vata",   "severe_heavy","Ashwagandha, Brahmi, Jatamansi","Yoga Nidra",                  "Mood swings, depressive and manic episodes", "rare"),
    ("Epilepsy (Apasmara)",                 "Vata",      "Vata",   "severe_heavy","Brahmi, Ashwagandha",          "Shavasana, mindfulness",       "Seizures, confusion, loss of consciousness", "uncommon"),
    ("Tinnitus (Karnanada)",                "Vata",      "Vata",   "mild_heavy", "Brahmi, Ashwagandha",           "Bhramari Pranayama",           "Ringing in the ears, hearing loss, ear fullness", "uncommon"),
    ("Burnout (Chitta Klama)",              "Vata-Pitta","Vata",   "mild_heavy", "Ashwagandha, Brahmi, Jatamansi","Yoga Nidra",                   "Fatigue, irritability, trouble sleeping, anxiety", "common"),
    ("Sleep Apnea (Nidra Vaishamya)",       "Vata-Kapha","Kapha",  "balanced",   "Ashwagandha, Brahmi",           "Bhramari Pranayama",           "Loud snoring, choking during sleep, daytime fatigue", "uncommon"),
    ("Vertigo (Bhrama)",                    "Vata-Pitta","Vata",   "mild_heavy", "Brahmi, Ashwagandha",           "Shavasana",                    "Dizziness, spinning sensation, nausea", "common"),
    ("Chronic Fatigue Syndrome (Klama)",    "Vata-Kapha","Vata",   "balanced",   "Ashwagandha, Shatavari",        "Yoga Nidra",                   "Persistent fatigue, weakness, poor concentration", "uncommon"),

    # ── ENT / eye ──
    ("Sinusitis (Apinasa)",                 "Vata-Kapha","Kapha",  "mild_heavy", "Sitopaladi Churna, Tulsi",      "Jal Neti",                     "Nasal congestion, facial pain, headaches", "common"),
    ("Nasal Polyps (Nasarsha)",             "Vata",      "Kapha",  "balanced",   "Sitopaladi Churna",             "Jal Neti",                     "Nasal congestion, loss of smell, sinus pressure", "rare"),
    ("Conjunctivitis (Netra Abhishyanda)",  "Pitta",     "Pitta",  "mild_heavy", "Triphala eye wash, Rose water", "Netra Vyayama",                "Red eyes, itchy eyes, eye discharge", "common"),
    ("Glaucoma (Adhimantha)",               "Pitta",     "Pitta",  "severe_heavy","Triphala, Shatavari",         "Trataka",                       "Blurred vision, eye pain, headache", "rare"),
    ("Trachoma (Pothaki)",                  "Pitta",     "Pitta",  "balanced",   "Triphala eye wash",             "Netra Vyayama",                "Eye irritation, swelling, blurred vision", "rare"),
    ("Gingivitis (Danta Vidradhi)",         "Pitta",     "Pitta",  "mild_heavy", "Triphala, Clove oil",           "Oil pulling",                   "Red, swollen gums, bleeding while brushing", "common"),
    ("Tonsillitis (Tundikeri)",             "Kapha-Pitta","Kapha", "mild_heavy", "Sitopaladi Churna, Yashtimadhu","Jal Neti",                     "Sore throat, difficulty swallowing, fever", "common"),
    ("Pharyngitis (Galashotha)",            "Kapha",     "Kapha",  "mild_heavy", "Tulsi, Yashtimadhu",            "Bhramari Pranayama",           "Sore throat, dry cough, hoarseness", "common"),
    ("Ear Infection (Karna Shoola)",        "Kapha-Vata","Kapha",  "mild_heavy", "Tulsi, Neem oil drops",         "Rest",                         "Ear pain, discharge, mild fever", "common"),

    # ── Gynaecological / urological ──
    ("Menstrual Disorder (Artava Dushti)",  "Vata-Pitta","Vata",   "balanced",   "Ashwagandha, Shatavari",        "Baddha Konasana",              "Irregular periods, heavy bleeding, cramps", "common"),
    ("Cystitis (Mutrakrichra)",             "Vata",      "Vata",   "mild_heavy", "Gokshura, Punarnava",           "Baddha Konasana",              "Painful urination, frequent urge to urinate", "common"),
    ("Urinary Tract Infection (Mutradaha)", "Pitta",     "Pitta",  "mild_heavy", "Gokshura, Chandan, Punarnava",  "Baddha Konasana",              "Burning urination, frequent urge, lower abdomen pain", "common"),
    ("Prostate Enlargement (Vriddhi)",      "Vata",      "Vata",   "balanced",   "Gokshura, Varuna",              "Baddha Konasana",              "Frequent urination, difficulty urinating, weak stream", "uncommon"),
    ("Polycystic Kidney Disease (Vrikka Roga)","Vata-Pitta","Vata","severe_heavy","Punarnava, Gokshura",         "Gentle stretching",             "Abdominal pain, high blood pressure, kidney enlargement", "rare"),
    ("Chronic Kidney Disease (Vrikka Vaikalya)","Vata-Pitta","Vata","severe_heavy","Punarnava, Gokshura",        "Gentle walking",                "Fatigue, swelling, reduced urination", "uncommon"),
    ("Infertility (Vandhyatva)",            "Vata-Pitta","Vata",   "balanced",   "Shatavari, Ashwagandha",        "Baddha Konasana",              "Difficulty conceiving, irregular cycles", "uncommon"),

    # ── Infectious / general ──
    ("Filariasis (Shlipada)",               "Kapha-Pitta","Kapha", "severe_heavy","Guduchi, Punarnava",           "Leg elevation",                 "Swelling, fever, lymph node enlargement", "rare"),
    ("Lymphadenopathy (Apachi)",            "Pitta",     "Pitta",  "balanced",   "Guduchi, Manjistha",            "Gentle movement",              "Swollen lymph nodes, fever, night sweats", "uncommon"),
    ("Typhoid (Antrika Jwara)",             "Pitta",     "Pitta",  "severe_heavy","Guduchi, Sudarshan Churna",    "Rest, Shavasana",               "Prolonged fever, weakness, abdominal pain", "common"),
    ("Chikungunya (Sandhi Jwara)",          "Vata-Pitta","Pitta",  "severe_heavy","Guduchi, Papaya leaf",         "Rest",                          "Joint pain, fever, rash", "uncommon"),
    ("Whooping Cough (Deergha Kasa)",       "Kapha",     "Kapha",  "balanced",   "Vasaka, Tulsi",                 "Rest",                          "Severe coughing fits, whooping sound, vomiting after cough", "uncommon"),
    ("Mumps (Karnamoola Shotha)",           "Kapha",     "Kapha",  "balanced",   "Guduchi, Tulsi",                "Rest",                          "Swollen salivary glands, fever, jaw pain", "uncommon"),
    ("Leprosy (Kushtha Roga)",              "Pitta-Vata","Pitta",  "severe_heavy","Amla, Guduchi, Neem",         "None specific (medical referral)",                 "Skin lesions, nerve damage, muscle weakness", "rare"),

    # ── Rare / referral-only (very low weight, present for realism only) ──
    ("Liver Cancer (Yakrit Arbuda)",        "Pitta",     "Pitta",  "severe_heavy","Guduchi (supportive)",        "Gentle breathing",              "Abdominal pain, weight loss, jaundice", "rare"),
    ("Lymphoma (Granthi Arbuda)",           "Pitta-Vata","Pitta",  "severe_heavy","Ashwagandha (supportive)",     "Gentle breathing",              "Swollen lymph nodes, fever, night sweats, weight loss", "rare"),
]


def sample_chronic_disease(rng: random.Random | None = None):
    """Weighted pick from CHRONIC_DISEASES, common diseases favored over rare ones."""
    r = rng or random
    weights = [TIER_WEIGHTS[entry[7]] for entry in CHRONIC_DISEASES]
    return r.choices(CHRONIC_DISEASES, weights=weights, k=1)[0]


def sample_severity(profile: str, rng: random.Random | None = None) -> str:
    r = rng or random
    dist = SEVERITY_PROFILES[profile]
    return r.choices(list(dist.keys()), weights=list(dist.values()), k=1)[0]


_DURATION_QUALIFIERS = [
    "for the past 2 days", "since last night", "for about a week",
    "intermittently", "worsening over the last few days",
    "mild and manageable", "gradually improving", "on and off for a few days",
]


def vary_symptoms(base: str, rng: random.Random | None = None) -> str:
    """
    Lightly perturb a disease's canonical symptom description so patients
    sharing a diagnosis don't all carry byte-identical symptoms text — real
    intake notes vary in which symptoms are mentioned, their order, and
    phrasing, even for the same underlying condition.
    """
    r = rng or random
    clauses = [c.strip() for c in base.split(",") if c.strip()]
    if len(clauses) >= 3 and r.random() < 0.35:
        drop_idx = r.randrange(len(clauses))
        clauses = clauses[:drop_idx] + clauses[drop_idx + 1:]
    if len(clauses) >= 2 and r.random() < 0.4:
        r.shuffle(clauses)
    text = ", ".join(clauses)
    if r.random() < 0.45:
        text = f"{text} ({r.choice(_DURATION_QUALIFIERS)})"
    return text
