import pandas as pd
import numpy as np
import joblib
import json
import os
import sys
import pickle
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'backend', 'models')

# Ensure models dir exists
os.makedirs(MODELS_DIR, exist_ok=True)

def normalize_prakriti(val):
    val = str(val).strip()
    if "Vata" in val and "Pitta" in val: return "Vata-Pitta"
    if "Vata" in val and "Kapha" in val: return "Vata-Kapha"
    if "Pitta" in val and "Kapha" in val: return "Pitta-Kapha"
    if "Vata" in val: return "Vata"
    if "Pitta" in val: return "Pitta"
    if "Kapha" in val: return "Kapha"
    return "Tridosha"

def parse_age(val):
    try:
        val = str(val).lower().replace(' years', '').replace('all ages', '35')
        if '-' in val:
            low, high = map(int, val.split('-'))
            return (low + high) / 2
        return float(val)
    except:
        return 35.0

def parse_severity(val):
    # Handle Numeric
    try:
        if isinstance(val, (int, float)): return float(val)
        if str(val).isdigit(): return float(val)
    except: pass
    
    # Handle Base Dataset Labels
    severity_map = {
        'Mild': 1, 'Mild to Moderate': 3, 'Moderate': 5, 
        'Moderate to High': 7, 'Moderate to Severe': 7,
        'High': 8, 'Severe': 10
    }
    return severity_map.get(str(val), 5)

def load_and_augment_data():
    print("🔄 Loading Base Dataset...")
    base_df = pd.read_csv(os.path.join(DATA_DIR, 'AyurGenixAI_Dataset.csv'))
    
    # Ensure consistent columns
    # Base cols: Disease, Age Group, Gender, Constitution/Prakriti, Symptom Severity, Ayurvedic Herbs, etc.
    
    feedback_path = os.path.join(DATA_DIR, 'treatment_feedback.csv')
    if os.path.exists(feedback_path):
        print("📥 Feedback data found. Augmenting dataset...")
        try:
            feedback_df = pd.read_csv(feedback_path)
            positive_feedback = feedback_df[feedback_df['rating'] == 'positive']
            
            new_rows = []
            for _, row in positive_feedback.iterrows():
                try:
                    context = json.loads(row['context_json'])
                    plan = json.loads(row['treatment_plan_json'])
                    
                    herbs_str = ", ".join([h['name'] for h in plan.get('herbs', [])])
                    yoga_str = ", ".join([y['practice'] for y in plan.get('yoga', [])])
                    diet_str = ", ".join(plan.get('diet', []))
                    
                    # Map to Base Schema
                    new_row = {
                        'Disease': context.get('disease', 'Unknown'),
                        'Age Group': str(context.get('age', 35)), # Pass as string to match base
                        'Gender': context.get('gender', 'Male'),
                        'Constitution/Prakriti': context.get('prakriti', 'Vata'),
                        'Symptom Severity': context.get('severity', 5), # Pass raw int, check parse_severity
                        'Ayurvedic Herbs': herbs_str,
                        'Yoga & Physical Therapy': yoga_str,
                        'Dietary Habits': diet_str
                    }
                    
                    # Weighting (Duplicate rows to enforce learning)
                    for _ in range(3): # 3x Weight
                        new_rows.append(new_row)
                    
                except Exception as e:
                    print(f"Skipping malformed feedback row: {e}")
            
            if new_rows:
                augmented_df = pd.DataFrame(new_rows)
                combined_df = pd.concat([base_df, augmented_df], ignore_index=True)
                print(f"✅ Added {len(new_rows)} weighted records from doctor feedback.")
                return combined_df
            else:
                return base_df
                
        except Exception as e:
            print(f"⚠️  Error processing feedback: {e}")
            return base_df
    else:
        print("ℹ️  No feedback file found. Retraining on base data only.")
        return base_df

def train_models(df):
    print("\n🚀 Starting Model Training...")
    
    encoders = {}
    
    # Preprocessing
    df['Prakriti_Clean'] = df['Constitution/Prakriti'].apply(normalize_prakriti)
    df['Age_Num'] = df['Age Group'].apply(parse_age)
    df['Severity_Num'] = df['Symptom Severity'].apply(parse_severity)
    
    # Encode Categorical Features
    categorical_cols = ['Disease', 'Gender', 'Prakriti_Clean']
    for col in categorical_cols:
        le = LabelEncoder()
        df[f'{col}_Encoded'] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
    
    # Features
    X = df[['Disease_Encoded', 'Prakriti_Clean_Encoded', 'Severity_Num', 'Age_Num', 'Gender_Encoded']]
    
    # Check for NaNs
    if X.isnull().values.any():
        print("⚠️  Warning: X contains NaNs. Filling with mean/mode.")
        X = X.fillna(0)
    
    # 1. Train K-Means
    print("Training K-Means Clustering...")
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(X)
    
    # 2. Train Random Forest
    print("Training Random Forest Classifiers...")
    
    # Herbs
    rf_herbs = RandomForestClassifier(n_estimators=100, random_state=42)
    le_herbs = LabelEncoder()
    y_herbs = le_herbs.fit_transform(df['Ayurvedic Herbs'].astype(str))
    rf_herbs.fit(X, y_herbs)
    encoders['Herbs'] = le_herbs
    
    # Yoga
    rf_yoga = RandomForestClassifier(n_estimators=100, random_state=42)
    le_yoga = LabelEncoder()
    y_yoga = le_yoga.fit_transform(df['Yoga & Physical Therapy'].astype(str))
    rf_yoga.fit(X, y_yoga)
    encoders['Yoga'] = le_yoga
    
    # Diet
    rf_diet = RandomForestClassifier(n_estimators=100, random_state=42)
    le_diet = LabelEncoder()
    y_diet = le_diet.fit_transform(df['Dietary Habits'].astype(str))
    rf_diet.fit(X, y_diet)
    encoders['Diet'] = le_diet
    
    # Save
    print("💾 Saving Models...")
    with open(os.path.join(MODELS_DIR, 'ayurgenix_kmeans.pkl'), 'wb') as f:
        pickle.dump(kmeans, f)
    with open(os.path.join(MODELS_DIR, 'ayurgenix_rf_herbs.pkl'), 'wb') as f:
        pickle.dump(rf_herbs, f)
    with open(os.path.join(MODELS_DIR, 'ayurgenix_rf_yoga.pkl'), 'wb') as f:
        pickle.dump(rf_yoga, f)
    with open(os.path.join(MODELS_DIR, 'ayurgenix_rf_diet.pkl'), 'wb') as f:
        pickle.dump(rf_diet, f)
    with open(os.path.join(MODELS_DIR, 'ayurgenix_encoders.pkl'), 'wb') as f:
        pickle.dump(encoders, f)
        
    print("🎉 Retraining Complete! Models updated and saved.")

if __name__ == "__main__":
    df = load_and_augment_data()
    train_models(df)
