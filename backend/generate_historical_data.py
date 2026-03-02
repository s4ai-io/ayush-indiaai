"""
generate_historical_data.py
----------------------------
Generates ~1 year of realistic Ayurvedic clinical data and inserts it into
the existing PostgreSQL tables (patients, medical_records, ayush_treatments,
treatment_feedbacks).

Seasonal disease surge patterns are baked in so that anomaly detection,
forecasting, and geospatial clustering have meaningful signals on day 1.

Run from backend/:
    ./venv/bin/python3.11 generate_historical_data.py
"""
import uuid
import random
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import SessionLocal, Patient, MedicalRecord, AyushTreatment, TreatmentFeedback, init_db

# ─── Seed for reproducibility ─────────────────────────────────────────────────
random.seed(42)

# ─── Indian Cities with state + rough patient volume weights ──────────────────
CITIES = [
    ("Mumbai",       "Maharashtra",   10),
    ("Delhi",        "Delhi",         10),
    ("Ahmedabad",    "Gujarat",        8),
    ("Pune",         "Maharashtra",    7),
    ("Bangalore",    "Karnataka",      7),
    ("Jaipur",       "Rajasthan",      7),
    ("Lucknow",      "Uttar Pradesh",  6),
    ("Chennai",      "Tamil Nadu",     6),
    ("Hyderabad",    "Telangana",      5),
    ("Surat",        "Gujarat",        5),
    ("Kolkata",      "West Bengal",    5),
    ("Indore",       "Madhya Pradesh", 4),
    ("Bhopal",       "Madhya Pradesh", 4),
    ("Nagpur",       "Maharashtra",    4),
    ("Patna",        "Bihar",          3),
    ("Varanasi",     "Uttar Pradesh",  3),
    ("Amritsar",     "Punjab",         3),
    ("Coimbatore",   "Tamil Nadu",     3),
    ("Nashik",       "Maharashtra",    2),
    ("Ranchi",       "Jharkhand",      2),
]
city_names   = [c[0] for c in CITIES]
city_states  = {c[0]: c[1] for c in CITIES}
city_weights = [c[2] for c in CITIES]

# ─── Prakriti distribution ────────────────────────────────────────────────────
PRAKRITI_OPTIONS = ["Vata", "Pitta", "Kapha", "Vata-Pitta", "Pitta-Kapha", "Vata-Kapha"]
PRAKRITI_WEIGHTS = [22, 20, 15, 18, 14, 11]

# ─── Ayurvedic Ritu (Season) Disease Map ──────────────────────────────────────
# Each entry: (disease_name, dosha, severity_range, typical_prakriti, herbs, yoga)
# Month → multiple weighted diseases — creates seasonal surge patterns

SEASONAL_DISEASES: dict[int, list] = {
    # Shishira (Jan–Feb): Vata/Kapha disorders, respiratory, joint pain
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
    # Vasanta (Mar–Apr): Kapha liquefaction, allergies, skin
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
    # Grishma (May–Jun): Pitta surge, heat, dehydration, acidity
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
    # Varsha (Jul–Aug): Vata aggravation, infections, waterborne diseases — SURGE period
    7: [
        ("Fever (Jwara)",         "Pitta",  "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Diarrhea (Atisara)",    "Pitta",  "Moderate",  "Pitta",     "Bilva, Kutaj",                 "Pawanmuktasana"),
        ("Malaria (Vishama Jwara)","Pitta", "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Indigestion (Ajirna)",  "Vata",   "Moderate",  "Vata",      "Trikatu, Ginger",              "Vajrasana"),
        ("Joint Pain (Amavata)",  "Vata",   "Moderate",  "Vata",      "Ashwagandha, Guggulu",         "Pawanmuktasana"),
        ("Skin Infection (Kushtha)","Kapha","Moderate",  "Kapha",     "Neem, Haridra",                "Viparita Karani"),
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
    ],
    # *** DENGUE SURGE — July to September (intentional spike for anomaly detection) ***
    8: [
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
        ("Dengue (Dandashthaka Jwara)","Pitta","Severe", "Pitta",     "Papaya leaf, Guduchi",         "Bed rest, Shavasana"),
        ("Fever (Jwara)",         "Pitta",  "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Diarrhea (Atisara)",    "Pitta",  "Moderate",  "Pitta",     "Bilva, Kutaj",                 "Pawanmuktasana"),
        ("Malaria (Vishama Jwara)","Pitta", "Severe",    "Pitta",     "Sudarshan Churna, Guduchi",    "Shavasana"),
        ("Indigestion (Ajirna)",  "Vata",   "Mild",      "Vata",      "Trikatu, Ginger",              "Vajrasana"),
    ],
    # Sharad (Sep–Oct): Pitta aggravation, eye/skin disorders
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
    # Hemanta (Nov–Dec): Kapha/Vata, digestive, respiratory
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

SEVERITY_SCORES = {"Mild": "3", "Moderate": "6", "Severe": "9"}
OUTCOME_OPTIONS  = ["Improved", "Significantly Improved", "Stable", "Under Treatment", "Recovered"]
OUTCOME_WEIGHTS  = [35, 30, 15, 15, 5]

FIRST_NAMES_M = ["Amit", "Rajesh", "Vikram", "Suresh", "Pradeep", "Manoj", "Dinesh",
                  "Ramesh", "Anil", "Ajay", "Sanjay", "Rohit", "Nitin", "Kiran",
                  "Mahesh", "Deepak", "Vivek", "Ashok", "Pramod", "Girish", "Hemant",
                  "Naresh", "Santosh", "Vinod", "Ravi", "Sunil", "Arun", "Mohan"]

FIRST_NAMES_F = ["Priya", "Sunita", "Meera", "Kavita", "Rekha", "Asha", "Neha",
                  "Pooja", "Sonal", "Anjali", "Shweta", "Ritu", "Puja", "Anita",
                  "Geeta", "Lata", "Nisha", "Pallavi", "Archana", "Divya", "Manisha",
                  "Seema", "Usha", "Vandana", "Madhuri", "Jyoti", "Sarita"]

LAST_NAMES = ["Sharma", "Patel", "Gupta", "Kumar", "Singh", "Joshi", "Mehta",
               "Shah", "Yadav", "Mishra", "Tiwari", "Chauhan", "Verma", "Pandey",
               "Agarwal", "Nair", "Reddy", "Rao", "Iyer", "Pillai", "Desai",
               "Jain", "Srivastava", "Dubey", "Bhatt", "Pawar", "More", "Patil"]

OCCUPATIONS = ["Farmer", "Teacher", "Engineer", "Doctor", "Business", "Student",
                "Housewife", "Labourer", "Government Employee", "Shopkeeper",
                "Driver", "Clerk", "Retired", "Nurse"]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

DIET_MAP = {
    "Vata":       "Warm, oily foods. Avoid cold and dry. Sweet, sour, salty taste.",
    "Pitta":      "Cool, light foods. Avoid spicy and fermented. Sweet, bitter, astringent.",
    "Kapha":      "Light, dry, warm foods. Avoid heavy and oily. Pungent, bitter, astringent.",
    "Vata-Pitta": "Warm, moderately oily foods. Sweet, slightly sour.",
    "Pitta-Kapha":"Cool, light, non-oily foods. Bitter, astringent, sweet.",
    "Vata-Kapha": "Warm, light, slightly oily foods. Sour, pungent, bitter.",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _weighted_choice(options, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for opt, w in zip(options, weights):
        cumulative += w
        if r <= cumulative:
            return opt
    return options[-1]


def _random_date_in_month(year: int, month: int) -> datetime:
    """Return a random datetime within the given year/month."""
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    day  = random.randint(1, days_in_month)
    hour = random.randint(8, 18)
    minute = random.choice([0, 15, 30, 45])
    return datetime(year, month, day, hour, minute)


def _cases_for_month(month: int) -> int:
    """
    Return number of cases to generate for a given calendar month.
    Surge months (Jul–Sep for Dengue/Monsoon, Jan–Feb for Respiratory) get more cases.
    """
    surge_months = {7: 90, 8: 140, 9: 110,  # Dengue/Monsoon surge
                    1: 80, 2: 75,            # Respiratory surge
                    5: 70, 6: 65,            # Heat/Pitta surge
                    3: 55, 4: 55,            # Vasanta moderate
                    10: 50, 11: 60, 12: 65}  # Hemanta build-up
    return surge_months.get(month, 50)


def _pick_disease(month: int):
    """Return a random (disease, dosha, severity, prakriti, herbs, yoga) for the month."""
    options = SEASONAL_DISEASES.get(month, SEASONAL_DISEASES[1])
    return random.choice(options)


# ─── Main Generation ──────────────────────────────────────────────────────────

def generate_data(year: int = 2025, dry_run: bool = False) -> None:
    print("=" * 60)
    print("  Ayurveda Historical Data Generator")
    print(f"  Target year: {year}")
    print("=" * 60)

    init_db()
    session = SessionLocal()

    patients_created = 0
    records_created  = 0

    # ── Generate 800 unique patients ─────────────────────────────────────────
    print("\n[1/3] Generating patients...")
    patient_ids = []

    for i in range(800):
        gender = random.choice(["Male", "Female"])
        first  = random.choice(FIRST_NAMES_M if gender == "Male" else FIRST_NAMES_F)
        last   = random.choice(LAST_NAMES)
        city   = _weighted_choice(city_names, city_weights)
        state  = city_states[city]
        age    = random.choices(
            range(18, 80),
            weights=[
                max(1, 10 - abs(a - 35)) for a in range(18, 80)   # bell curve ~35
            ]
        )[0]

        pid = str(uuid.uuid4())
        p = Patient(
            id=pid,
            first_name=first,
            last_name=last,
            gender=gender,
            age=age,
            marital_status=random.choice(["Married", "Single", "Widowed"]),
            mobile=f"9{random.randint(100000000, 999999999)}",
            address=f"{random.randint(1, 999)}, {random.choice(['MG Road', 'Nehru Nagar', 'Gandhi Chowk', 'Ambedkar Marg', 'Shivaji Nagar'])}",
            city=city,
            state=state,
            pincode=str(random.randint(100000, 999999)),
            blood_group=random.choice(BLOOD_GROUPS),
            occupation=random.choice(OCCUPATIONS),
            id_type="Aadhaar",
            id_number=str(random.randint(100000000000, 999999999999)),
            diagnosis_done=True,
        )
        if not dry_run:
            session.add(p)
        patient_ids.append(pid)
        patients_created += 1

    if not dry_run:
        session.commit()
    print(f"  ✓ {patients_created} patients created")

    # ── Generate medical records month-by-month ───────────────────────────────
    print("\n[2/3] Generating medical records + treatments...")

    for month in range(1, 13):
        n_cases = _cases_for_month(month)
        ritu_map = {1:"Shishira",2:"Shishira",3:"Vasanta",4:"Vasanta",
                    5:"Grishma",6:"Grishma",7:"Varsha",8:"Varsha",
                    9:"Sharad",10:"Sharad",11:"Hemanta",12:"Hemanta"}
        season = ritu_map[month]

        for _ in range(n_cases):
            pid = random.choice(patient_ids)
            disease, dosha, severity_label, prakriti, herbs, yoga = _pick_disease(month)
            severity_score = SEVERITY_SCORES[severity_label]
            visit_dt = _random_date_in_month(year, month)
            diet = DIET_MAP.get(prakriti, DIET_MAP["Vata"])
            outcome = _weighted_choice(OUTCOME_OPTIONS, OUTCOME_WEIGHTS)

            # Duration proportional to severity
            dur_weeks = {"Mild": random.randint(1, 3), "Moderate": random.randint(3, 8),
                         "Severe": random.randint(6, 16)}[severity_label]

            # Symptoms (realistic for the disease)
            symptoms_map = {
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
            }
            symptoms = symptoms_map.get(disease, f"Symptoms related to {disease}")

            record_id = str(uuid.uuid4())
            mr = MedicalRecord(
                id=record_id,
                patient_id=pid,
                visit_date=visit_dt,
                diagnosis=disease,
                symptoms=symptoms,
                prakriti=prakriti,
                vikriti=dosha,
                severity=severity_score,
                comorbidities=random.choice(["None", "Hypertension", "Diabetes", "Obesity", "Stress", ""]),
                notes=f"Patient presents with {severity_label.lower()} {disease}. Season: {season}. Dosha predominant: {dosha}.",
                prescription="{}",
            )

            treatment_id = str(uuid.uuid4())
            at = AyushTreatment(
                id=treatment_id,
                patient_id=pid,
                medical_record_id=record_id,
                visit_date=visit_dt,
                disease=disease,
                herbs_prescribed=herbs,
                yoga_prescribed=yoga,
                diet_plan=diet,
                treatment_duration_weeks=str(dur_weeks),
                improvement_percentage=str(random.randint(40, 95)),
                outcome=outcome,
            )

            feedback_id = str(uuid.uuid4())
            rating = random.choice(["positive", "positive", "positive", "negative"])
            fb = TreatmentFeedback(
                id=feedback_id,
                patient_id=pid,
                medical_record_id=record_id,
                ai_plan="{}",
                ml_context=f'{{"disease":"{disease}","dosha":"{dosha}","prakriti":"{prakriti}","season":"{season}"}}',
                doctor_rating=rating,
                doctor_comments=random.choice([
                    "Patient responded well to treatment.",
                    "Good improvement noted after 2 weeks.",
                    "Requires follow-up after 1 month.",
                    "Minimal response, dosage adjusted.",
                    "Excellent recovery.",
                    "",
                ]),
                is_retrained=False,
            )

            if not dry_run:
                session.add(mr)
                session.add(at)
                session.add(fb)
            records_created += 1

        if not dry_run:
            session.commit()
        print(f"  Month {month:02d} ({season:10s}): {n_cases} records")

    session.close()

    print(f"\n[3/3] Summary")
    print(f"  Patients created  : {patients_created}")
    print(f"  Medical records   : {records_created}")
    print(f"  AYUSH treatments  : {records_created}")
    print(f"  Treatment feedbacks: {records_created}")
    print("\n✓ Historical data generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no data will be written to DB")
    generate_data(year=2025, dry_run=dry_run)
