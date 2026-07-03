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

    # ── Chronic/long-tail diseases (services/disease_pool.py CHRONIC_DISEASES) ──
    # Auto-matched from NAMC CSV where the crosswalk's Mapping_Type was a solid
    # match; a handful of NAMC rows land on a Sanskrit term with no real clinical
    # relationship to the English name they're crosswalked to (NAMC's own
    # Mapping_Type column flags many of these as "Fuzzy Match") — those are
    # overridden below with the standard classical Ayurvedic term instead of
    # propagating the mismatch (e.g. Glaucoma is not glossed as "coma", Bipolar
    # Disorder is not glossed as "kapha-type diabetes").
    "Digestive Disorder (Vikara)": {
        "devanagari": "विकारः",
        "iast":       "vikāraḥ",
        "english":    "Digestive Disorder",
        "hindi":      "पाचन विकार",
    },
    "Irritable Bowel Syndrome (Grahani)": {
        "devanagari": "ग्रहणी",
        "iast":       "grahaṇī",
        "english":    "Irritable Bowel Syndrome",
        "hindi":      "ग्रहणी रोग",
    },
    "Celiac Disease (Grahani Roga)": {
        "devanagari": "ग्रहणीदोषः",
        "iast":       "grahaṇīdoṣaḥ",
        "english":    "Celiac Disease",
        "hindi":      "सीलिएक रोग",
    },
    "Ulcerative Colitis (Raktatisara)": {
        "devanagari": "रक्तातिसारः",
        "iast":       "raktātisāraḥ",
        "english":    "Ulcerative Colitis",
        "hindi":      "रक्तातिसार",
    },
    "Amebiasis (Pittaja Atisara)": {
        "devanagari": "पित्तजातिसारः",
        "iast":       "pittajātisāraḥ",
        "english":    "Amebiasis",
        "hindi":      "पित्तज अतिसार",
    },
    "Worm Infection (Krimi Roga)": {
        "devanagari": "दद्रु-कुष्ठः",
        "iast":       "dadru-kuṣṭhaḥ",
        "english":    "Worm Infection",
        "hindi":      "कीड़े का संक्रमण",
    },
    "Peptic Ulcer (Parinama Shoola)": {
        "devanagari": "परिणामशूलः",
        "iast":       "pariṇāmaśūlaḥ",
        "english":    "Peptic Ulcer",
        "hindi":      "परिणाम शूल",
    },
    "Gastritis (Urdhva Amlapitta)": {
        "devanagari": "ऊर्ध्वअम्लपित्तम्",
        "iast":       "ūrdhva-amlapittam",
        "english":    "Gastritis",
        "hindi":      "जठरशोथ",
    },
    "Kidney Stones (Ashmari)": {
        "devanagari": "अश्मरी",
        "iast":       "aśmarī",
        "english":    "Kidney Stones",
        "hindi":      "पथरी",
    },
    "Gallstones (Pittashmari)": {
        "devanagari": "पित्ताश्मरी",
        "iast":       "pittāśmarī",
        "english":    "Gallstones",
        "hindi":      "पित्ताशय की पथरी",
    },
    "Piles - Anal Fissure (Parikartika)": {
        "devanagari": "परिकर्तिका",
        "iast":       "parikartikā",
        "english":    "Anal Fissure",
        "hindi":      "गुदा विदर",
    },
    "Liver Disorder (Yakrit Vikara)": {
        "devanagari": "यकृद्विकारः",
        "iast":       "yakr̥dvikāraḥ",
        "english":    "Liver Disorder",
        "hindi":      "यकृत विकार",
    },
    "Hepatitis (Kamala)": {
        "devanagari": "मक्कल्लः",
        "iast":       "makkallaḥ",
        "english":    "Hepatitis",
        "hindi":      "हेपेटाइटिस",
    },
    "Cirrhosis (Yakrit Vriddhi)": {
        "devanagari": "यकृद्वृद्धिः",
        "iast":       "yakr̥dvr̥ddhiḥ",
        "english":    "Cirrhosis",
        "hindi":      "सिरॉसिस",
    },
    "Fatty Liver (Yakrit Meda Vriddhi)": {
        "devanagari": "यकृन्मेदोवृद्धिः",
        "iast":       "yakr̥nmedovr̥ddhiḥ",
        "english":    "Fatty Liver",
        "hindi":      "वसायुक्त यकृत",
    },
    "Osteoarthritis (Sandhivata)": {
        "devanagari": "सन्धिगतवातः",
        "iast":       "sandhigatavātaḥ",
        "english":    "Osteoarthritis",
        "hindi":      "अस्थिरोगशास्त्र",
    },
    "Gout (Vatarakta)": {
        "devanagari": "पित्तज-वातरक्तम्",
        "iast":       "pittaja-vātaraktam",
        "english":    "Gout",
        "hindi":      "गाउट",
    },
    "Osteoporosis (Asthi Kshaya)": {
        "devanagari": "अस्थिशोषः",
        "iast":       "asthiśoṣaḥ",
        "english":    "Osteoporosis",
        "hindi":      "अस्थिचापदिकता",
    },
    "Sciatica (Gridhrasi)": {
        "devanagari": "गृध्रसी",
        "iast":       "gr̥dhrasī",
        "english":    "Sciatica",
        "hindi":      "सायटिका",
    },
    "Back Pain (Prishtha Shoola)": {
        "devanagari": "पार्श्वावमर्दः",
        "iast":       "pārśvāvamardaḥ",
        "english":    "Back Pain",
        "hindi":      "पीठ में दर्द",
    },
    "Spondylosis (Griva Sandhigata Vata)": {
        "devanagari": "ग्रीवास्तम्भः",
        "iast":       "grīvāstambhaḥ",
        "english":    "Spondylosis",
        "hindi":      "स्पोंडिलोसिस",
    },
    "Scoliosis (Kubjata)": {
        "devanagari": "अचरणा",
        "iast":       "acaraṇā",
        "english":    "Scoliosis",
        "hindi":      "स्कोलियोसिस",
    },
    "Frozen Shoulder (Avabahuka)": {
        "devanagari": "अवबाहुकः",
        "iast":       "avabāhukaḥ",
        "english":    "Frozen Shoulder",
        "hindi":      "अवबाहुक",
    },
    "Tennis Elbow (Kurpara Shoola)": {
        "devanagari": "कूर्परशूलः",
        "iast":       "kūrparaśūlaḥ",
        "english":    "Tennis Elbow",
        "hindi":      "कोहनी का दर्द",
    },
    "Fibromyalgia (Sarvanga Vata)": {
        "devanagari": "सर्वाङ्गवातः",
        "iast":       "sarvāṅgavātaḥ",
        "english":    "Fibromyalgia",
        "hindi":      "सर्वांग वात",
    },
    "Psoriasis (Kitibha Kushtha)": {
        "devanagari": "किटिभकुष्ठम्",
        "iast":       "kiṭibhakuṣṭham",
        "english":    "Psoriasis",
        "hindi":      "किटिभ कुष्ठ",
    },
    "Eczema (Vicharchika)": {
        "devanagari": "विचर्चिका",
        "iast":       "vicarcikā",
        "english":    "Eczema",
        "hindi":      "विचर्चिका",
    },
    "Acne (Yuvana Pidika)": {
        "devanagari": "युवानपिडका (मुखदूषिका)",
        "iast":       "yuvānapiḍakā",
        "english":    "Acne",
        "hindi":      "मुँहासे",
    },
    "Alopecia (Indralupta)": {
        "devanagari": "इन्द्रलुप्तः",
        "iast":       "indraluptaḥ",
        "english":    "Alopecia",
        "hindi":      "गंजापन",
    },
    "Dandruff (Darunaka)": {
        "devanagari": "दारुणकः",
        "iast":       "dāruṇakaḥ",
        "english":    "Dandruff",
        "hindi":      "रूसी",
    },
    "Contact Dermatitis (Sparshaja Kushtha)": {
        "devanagari": "स्पर्शजकुष्ठम्",
        "iast":       "sparśajakuṣṭham",
        "english":    "Contact Dermatitis",
        "hindi":      "स्पर्शज कुष्ठ",
    },
    "Vitiligo (Shwitra)": {
        "devanagari": "श्वित्रः",
        "iast":       "śvitraḥ",
        "english":    "Vitiligo",
        "hindi":      "सफ़ेद दाग",
    },
    "Chickenpox (Laghu Masurika)": {
        "devanagari": "लघु-मसूरिका",
        "iast":       "laghu-masūrikā",
        "english":    "Chickenpox",
        "hindi":      "चिकनपॉक्स",
    },
    "Measles (Romantika)": {
        "devanagari": "रोमांतिका",
        "iast":       "rōmāṁtikā",
        "english":    "Measles",
        "hindi":      "खसरा",
    },
    "Warts (Charmakeela)": {
        "devanagari": "चर्मकीलः",
        "iast":       "carmakīlaḥ",
        "english":    "Warts",
        "hindi":      "मस्सा",
    },
    "Boils (Vidradhi)": {
        "devanagari": "विद्रधिः",
        "iast":       "vidradhiḥ",
        "english":    "Boils",
        "hindi":      "फोड़ा",
    },
    "Hyperthyroidism (Atisweda)": {
        "devanagari": "अतिस्वेदः",
        "iast":       "atisvēdaḥ",
        "english":    "Hyperthyroidism",
        "hindi":      "हायपरथायरॉइडिज्म",
    },
    "Thyroid Disorder (Galaganda Vikara)": {
        "devanagari": "गलगण्डविकारः",
        "iast":       "galagaṇḍavikāraḥ",
        "english":    "Thyroid Disorder",
        "hindi":      "थायरॉयड विकार",
    },
    "Goiter (Galaganda)": {
        "devanagari": "गलगण्डः",
        "iast":       "galagaṇḍaḥ",
        "english":    "Goiter",
        "hindi":      "गुळगुळीत",
    },
    "Hyperlipidemia (Medo Vriddhi)": {
        "devanagari": "मेदोवृद्धिः",
        "iast":       "medovr̥ddhiḥ",
        "english":    "Hyperlipidemia",
        "hindi":      "मेदोवृद्धि",
    },
    "Erectile Dysfunction (Klaibya)": {
        "devanagari": "क्लैब्यम्",
        "iast":       "klaibyam",
        "english":    "Erectile Dysfunction",
        "hindi":      "स्तम्भन दोष",
    },
    "Metabolic Syndrome (Santarpana Janya Vikara)": {
        "devanagari": "सन्तर्पणजन्यविकारः",
        "iast":       "santarpaṇajanyavikāraḥ",
        "english":    "Metabolic Syndrome",
        "hindi":      "उपापचय सिंड्रोम",
    },
    "Heart Disease (Hridroga)": {
        "devanagari": "हृद्रोगः",
        "iast":       "hṛdrogaḥ",
        "english":    "Heart Disease",
        "hindi":      "हृदय रोग",
    },
    "Angina (Hrit Shoola)": {
        "devanagari": "हृच्छूलः",
        "iast":       "hr̥cchūlaḥ",
        "english":    "Angina",
        "hindi":      "हृत् शूल",
    },
    "Hypertension (Raktachaapa Vriddhi)": {
        "devanagari": "रक्तचापवृद्धिः",
        "iast":       "raktacāpavr̥ddhiḥ",
        "english":    "Hypertension",
        "hindi":      "उच्च रक्तचाप",
    },
    "Varicose Veins (Sira Granthi)": {
        "devanagari": "सिराजग्रन्थिः",
        "iast":       "sirāgranthiḥ",
        "english":    "Varicose Veins",
        "hindi":      "नसों का फैलाव",
    },
    "Anemia (Pandu Roga)": {
        "devanagari": "पाण्डुरोगः",
        "iast":       "pāṇḍurogaḥ",
        "english":    "Anemia",
        "hindi":      "पाण्डु रोग",
    },
    "Depression (Vishada)": {
        "devanagari": "विषादः",
        "iast":       "viṣādaḥ",
        "english":    "Depression",
        "hindi":      "अवसाद",
    },
    "Stress (Manasika Tanava)": {
        "devanagari": "मानसिकतनावः",
        "iast":       "mānasikatanāvaḥ",
        "english":    "Stress",
        "hindi":      "मानसिक तनाव",
    },
    "Bipolar Disorder (Unmada)": {
        "devanagari": "उन्मादः",
        "iast":       "unmādaḥ",
        "english":    "Bipolar Disorder",
        "hindi":      "उन्माद",
    },
    "Epilepsy (Apasmara)": {
        "devanagari": "अपस्मारः",
        "iast":       "apasmāraḥ",
        "english":    "Epilepsy",
        "hindi":      "मिर्गी",
    },
    "Tinnitus (Karnanada)": {
        "devanagari": "कर्णनादः",
        "iast":       "karṇanādaḥ",
        "english":    "Tinnitus",
        "hindi":      "कर्णनाद",
    },
    "Burnout (Chitta Klama)": {
        "devanagari": "चित्तक्लमः",
        "iast":       "cittaklamaḥ",
        "english":    "Burnout",
        "hindi":      "मानसिक क्लान्ति",
    },
    "Sleep Apnea (Nidra Vaishamya)": {
        "devanagari": "निद्रा-वैषम्यम्",
        "iast":       "nidrā-vaiṣamyam",
        "english":    "Sleep Apnea",
        "hindi":      "स्लीप एप्निया",
    },
    "Vertigo (Bhrama)": {
        "devanagari": "भ्रमः",
        "iast":       "bhramaḥ",
        "english":    "Vertigo",
        "hindi":      "चक्कर आना",
    },
    "Chronic Fatigue Syndrome (Klama)": {
        "devanagari": "क्लमः",
        "iast":       "klamaḥ",
        "english":    "Chronic Fatigue Syndrome",
        "hindi":      "दीर्घकालिक थकान",
    },
    "Sinusitis (Apinasa)": {
        "devanagari": "अपीनसः",
        "iast":       "apīnasaḥ",
        "english":    "Sinusitis",
        "hindi":      "पुरानी साइनसाइटिस",
    },
    "Nasal Polyps (Nasarsha)": {
        "devanagari": "नासार्शः",
        "iast":       "nāsārśaḥ",
        "english":    "Nasal Polyps",
        "hindi":      "नाक में मांस बढ़ना",
    },
    "Conjunctivitis (Netra Abhishyanda)": {
        "devanagari": "नेत्राभिष्यन्दः",
        "iast":       "netrābhiṣyandaḥ",
        "english":    "Conjunctivitis",
        "hindi":      "नेत्राभिष्यन्द",
    },
    "Glaucoma (Adhimantha)": {
        "devanagari": "अधिमन्थः",
        "iast":       "adhimanthaḥ",
        "english":    "Glaucoma",
        "hindi":      "अधिमन्थ",
    },
    "Trachoma (Pothaki)": {
        "devanagari": "पोथकी",
        "iast":       "pothakī",
        "english":    "Trachoma",
        "hindi":      "ट्राकोमा",
    },
    "Gingivitis (Danta Vidradhi)": {
        "devanagari": "दन्तविद्रधिः",
        "iast":       "dantavidradhiḥ",
        "english":    "Gingivitis",
        "hindi":      "मसूड़ों की सूजन",
    },
    "Tonsillitis (Tundikeri)": {
        "devanagari": "तुण्डिकेरी",
        "iast":       "tuṇḍikerī",
        "english":    "Tonsillitis",
        "hindi":      "टॉन्सिल शोथ",
    },
    "Pharyngitis (Galashotha)": {
        "devanagari": "गलशोथः",
        "iast":       "galaśothaḥ",
        "english":    "Pharyngitis",
        "hindi":      "गले में सूजन",
    },
    "Ear Infection (Karna Shoola)": {
        "devanagari": "कर्णशूलः",
        "iast":       "karṇaśūlaḥ",
        "english":    "Ear Infection",
        "hindi":      "कान का दर्द",
    },
    "Menstrual Disorder (Artava Dushti)": {
        "devanagari": "आर्तवदुष्टिः",
        "iast":       "ārtavaduṣṭiḥ",
        "english":    "Menstrual Disorder",
        "hindi":      "मासिक धर्म विकार",
    },
    "Cystitis (Mutrakrichra)": {
        "devanagari": "मूत्रकृच्छ्रः",
        "iast":       "mūtrakr̥cchraḥ",
        "english":    "Cystitis",
        "hindi":      "मूत्रकृच्छ्र",
    },
    "Urinary Tract Infection (Mutradaha)": {
        "devanagari": "मूत्रदाहः",
        "iast":       "mūtradāhaḥ",
        "english":    "Urinary Tract Infection",
        "hindi":      "मूत्र मार्ग संक्रमण",
    },
    "Prostate Enlargement (Vriddhi)": {
        "devanagari": "अष्ठीलावृद्धिः",
        "iast":       "aṣṭhīlāvr̥ddhiḥ",
        "english":    "Prostate Enlargement",
        "hindi":      "प्रोस्टेट वृद्धि",
    },
    "Polycystic Kidney Disease (Vrikka Roga)": {
        "devanagari": "वृक्करोगः",
        "iast":       "vṛkkarogaḥ",
        "english":    "Polycystic Kidney Disease",
        "hindi":      "पॉलीसिस्टिक किडनी डिजीज",
    },
    "Chronic Kidney Disease (Vrikka Vaikalya)": {
        "devanagari": "वृक्कवैकल्यम्",
        "iast":       "vr̥kkavaikalyam",
        "english":    "Chronic Kidney Disease",
        "hindi":      "वृक्क विकार",
    },
    "Infertility (Vandhyatva)": {
        "devanagari": "वन्ध्यत्वम्",
        "iast":       "vandhyatvam",
        "english":    "Infertility",
        "hindi":      "बांझपन",
    },
    "Filariasis (Shlipada)": {
        "devanagari": "श्लीपदः",
        "iast":       "ślīpadaḥ",
        "english":    "Filariasis",
        "hindi":      "फाइलेरिया",
    },
    "Lymphadenopathy (Apachi)": {
        "devanagari": "अपची",
        "iast":       "apacī",
        "english":    "Lymphadenopathy",
        "hindi":      "लिम्फैडेनोपैथी",
    },
    "Typhoid (Antrika Jwara)": {
        "devanagari": "आन्त्रिकज्वरः",
        "iast":       "āntrikajvaraḥ",
        "english":    "Typhoid",
        "hindi":      "मियादी बुखार",
    },
    "Chikungunya (Sandhi Jwara)": {
        "devanagari": "सन्धिज्वरः",
        "iast":       "sandhijvaraḥ",
        "english":    "Chikungunya",
        "hindi":      "सन्धि ज्वर",
    },
    "Whooping Cough (Deergha Kasa)": {
        "devanagari": "दीर्घकासः",
        "iast":       "dīrghakāsaḥ",
        "english":    "Whooping Cough",
        "hindi":      "काली खांसी",
    },
    "Mumps (Karnamoola Shotha)": {
        "devanagari": "कर्णमूलशोथः",
        "iast":       "karṇamūlaśothaḥ",
        "english":    "Mumps",
        "hindi":      "गलसुआ",
    },
    "Leprosy (Kushtha Roga)": {
        "devanagari": "कुष्ठरोगः",
        "iast":       "kuṣṭharogaḥ",
        "english":    "Leprosy",
        "hindi":      "कुष्ठ रोग",
    },
    "Liver Cancer (Yakrit Arbuda)": {
        "devanagari": "यकृज्जविद्रधिः",
        "iast":       "yakr̥jjavidradhiḥ",
        "english":    "Liver Cancer",
        "hindi":      "यकृत कैंसर",
    },
    "Lymphoma (Granthi Arbuda)": {
        "devanagari": "मेदोजग्रन्थिः",
        "iast":       "medojagranthi",
        "english":    "Lymphoma",
        "hindi":      "लिम्फोमा",
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
