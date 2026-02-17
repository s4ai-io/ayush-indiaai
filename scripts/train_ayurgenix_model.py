import pandas as pd
import numpy as np
import pickle
import os
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Configuration
DATA_PATH = os.path.join("data", "AyurGenixAI_Dataset.csv")
MODEL_DIR = os.path.join("backend", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def load_and_clean_data():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # 1. Normalize Prakriti
    # Map variations like "Vata-Prakriti" to "Vata"
    def normalize_prakriti(val):
        val = str(val).strip()
        if "Vata" in val and "Pitta" in val: return "Vata-Pitta"
        if "Vata" in val and "Kapha" in val: return "Vata-Kapha"
        if "Pitta" in val and "Kapha" in val: return "Pitta-Kapha"
        if "Vata" in val: return "Vata"
        if "Pitta" in val: return "Pitta"
        if "Kapha" in val: return "Kapha"
        return "Tridosha" # Fallback

    df['Prakriti_Clean'] = df['Constitution/Prakriti'].apply(normalize_prakriti)
    
    # 2. Handle Age Group
    # Convert "30-60 years" to approximate numeric mean for clustering
    def parse_age(val):
        try:
            val = str(val).lower().replace(' years', '').replace('all ages', '35')
            if '-' in val:
                low, high = map(int, val.split('-'))
                return (low + high) / 2
            return float(val)
        except:
            return 35.0 # Default

    df['Age_Num'] = df['Age Group'].apply(parse_age)
    
    # 3. Encode Severity
    severity_map = {
        'Mild': 1, 'Mild to Moderate': 3, 'Moderate': 5, 
        'Moderate to High': 7, 'Moderate to Severe': 7,
        'High': 8, 'Severe': 10
    }
    df['Severity_Num'] = df['Symptom Severity'].map(severity_map).fillna(5)

    return df

def train_models(df):
    encoders = {}
    
    # --- FEATURES FOR TRAINING ---
    # We need to encode categorical string inputs to numbers
    categorical_cols = ['Disease', 'Gender', 'Prakriti_Clean']
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[f'{col}_Encoded'] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        print(f"Encoded {col}: {len(le.classes_)} classes")

    # Features for Clustering & Classification
    # X = [Disease, Prakriti, Severity, Age, Gender]
    X = df[['Disease_Encoded', 'Prakriti_Clean_Encoded', 'Severity_Num', 'Age_Num', 'Gender_Encoded']]
    
    # --- 1. K-MEANS CLUSTERING ---
    print("\nTraining K-Means Clustering...")
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(X)
    print("K-Means trained. Cluster distribution:")
    print(df['Cluster'].value_counts())

    # --- 2. RANDOM FOREST (RECOMMENDATIONS) ---
    print("\nTraining Random Forest Classifiers...")
    
    # Target 1: Herbs
    rf_herbs = RandomForestClassifier(n_estimators=50, max_depth=20, random_state=42)
    le_herbs = LabelEncoder()
    y_herbs = le_herbs.fit_transform(df['Ayurvedic Herbs'].astype(str).fillna('Consult Physician'))
    rf_herbs.fit(X, y_herbs)
    encoders['Herbs'] = le_herbs
    print("RF Herbs trained.")

    # Target 2: Yoga
    rf_yoga = RandomForestClassifier(n_estimators=50, max_depth=20, random_state=42)
    le_yoga = LabelEncoder()
    y_yoga = le_yoga.fit_transform(df['Yoga & Physical Therapy'].astype(str).fillna('Yoga Nidra'))
    rf_yoga.fit(X, y_yoga)
    encoders['Yoga'] = le_yoga
    print("RF Yoga trained.")
    
    # Target 3: Diet
    rf_diet = RandomForestClassifier(n_estimators=50, max_depth=20, random_state=42)
    le_diet = LabelEncoder()
    y_diet = le_diet.fit_transform(df['Dietary Habits'].astype(str).fillna('Balanced Diet'))
    rf_diet.fit(X, y_diet)
    encoders['Diet'] = le_diet
    print("RF Diet trained.")

    # --- SAVING ARTIFACTS ---
    print("\nSaving models to backend/models/...")
    
    # Save Models
    with open(os.path.join(MODEL_DIR, 'ayurgenix_kmeans.pkl'), 'wb') as f:
        pickle.dump(kmeans, f)
    with open(os.path.join(MODEL_DIR, 'ayurgenix_rf_herbs.pkl'), 'wb') as f:
        pickle.dump(rf_herbs, f)
    with open(os.path.join(MODEL_DIR, 'ayurgenix_rf_yoga.pkl'), 'wb') as f:
        pickle.dump(rf_yoga, f)
    with open(os.path.join(MODEL_DIR, 'ayurgenix_rf_diet.pkl'), 'wb') as f:
        pickle.dump(rf_diet, f)
        
    # Save Encoders
    with open(os.path.join(MODEL_DIR, 'ayurgenix_encoders.pkl'), 'wb') as f:
        pickle.dump(encoders, f)
        
    print("✅ All models and encoders saved successfully.")

if __name__ == "__main__":
    try:
        df = load_and_clean_data()
        train_models(df)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
