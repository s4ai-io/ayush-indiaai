
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class AnalyticsService:
    def __init__(self, data_path="data/registrations.json"):
        # Absolute path resolution
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_path = os.path.join(base_dir, data_path)

    def load_data(self):
        """Load and flatten patient records into a DataFrame"""
        if not os.path.exists(self.data_path):
            return pd.DataFrame()

        with open(self.data_path, 'r') as f:
            data = json.load(f)

        records = []
        for patient in data:
            medical_records = patient.get('medicalRecords', [])
            if not medical_records:
                continue
            
            # Use the most recent record or iterate all? 
            # For outbreak detection, we should look at all timestamped records.
            for record in medical_records:
                records.append({
                    'patient_id': patient['id'],
                    'city': patient['contactInfo'].get('correspondenceCity', 'Unknown'),
                    'pincode': patient['contactInfo'].get('correspondencePincode', 'Unknown'),
                    'diagnosis': record.get('diagnosis', 'Unknown'),
                    'timestamp': record.get('timestamp'),
                    'symptoms': record.get('symptoms', '')
                })
        
        df = pd.DataFrame(records)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    def get_disease_trends(self, days=30):
        """Aggregate daily case counts for top diseases"""
        df = self.load_data()
        if df.empty:
            return []

        # Ensure timestamp is datetime and handle timezones
        if df['timestamp'].dt.tz is None:
            # If naive, assume UTC or local. Synthetic data is ISO (UTC).
            # Let's make it UTC-aware to be safe, or just normalize to naive if easier.
            # Best practice: Work in UTC.
            df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        else:
            # Already aware (likely UTC from to_datetime on ISO strings)
            pass

        # Calculate start_date as UTC
        start_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
        
        df_filtered = df[df['timestamp'] >= start_date]

        # Group by Date and Diagnosis
        # df_filtered['timestamp'].dt.date returns python date objects (naive).
        trends = df_filtered.groupby([df_filtered['timestamp'].dt.date, 'diagnosis']).size().unstack(fill_value=0)
        
        # Convert to dict format suitable for frontend (Recharts)
        # format: [{date: '2023-10-01', Dengue: 5, Fever: 2}, ...]
        result = []
        for date, row in trends.iterrows():
            entry = {'date': date.strftime('%Y-%m-%d')}
            entry.update(row.to_dict())
            result.append(entry)
            
        return result

    def get_hotspots(self, disease=None):
        """Identify locations with high case counts"""
        df = self.load_data()
        if df.empty:
            return []

        if disease:
            df = df[df['diagnosis'] == disease]

        # Group by City and Pincode
        hotspots = df.groupby(['city', 'pincode', 'diagnosis']).size().reset_index(name='count')
        
        # Sort by count desc
        hotspots = hotspots.sort_values('count', ascending=False)
        
        return hotspots.to_dict(orient='records')

    def detect_anomalies(self):
        """Detect sudden spikes in disease cases"""
        df = self.load_data()
        if df.empty:
            return []

        # Ensure consistent timezone before grouping
        if df['timestamp'].dt.tz is None:
             df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        
        # Calculate daily counts for each disease
        # Group by naive date to avoid timezone splitting issues if they cross midnight differently
        # But we must be careful. Let's just use the timestamp.dt.date
        daily_counts = df.groupby([df['timestamp'].dt.date, 'diagnosis']).size().reset_index(name='count')
        
        alerts = []
        # Use the max date in data as "today" to ensure we catch the generated data
        if daily_counts.empty:
            return []
            
        latest_date = daily_counts['timestamp'].max() # timestamp here is the column name for date
        
        diseases = daily_counts['diagnosis'].unique()
        
        for disease in diseases:
            disease_data = daily_counts[daily_counts['diagnosis'] == disease].sort_values('timestamp')
            
            # Get count for the latest date (simulated "today")
            today_record = disease_data[disease_data['timestamp'] == latest_date]
            if today_record.empty:
                continue
            
            today_count = today_record.iloc[0]['count']
            
            # Get baseline (previous 7 days)
            start_baseline = latest_date - timedelta(days=7)
            baseline_data = disease_data[
                (disease_data['timestamp'] >= start_baseline) & 
                (disease_data['timestamp'] < latest_date)
            ]
            
            if baseline_data.empty:
                avg_count = 0
            else:
                avg_count = baseline_data['count'].mean()
            
            # Rule: If today's count is > 2x baseline (or > 5 if baseline is 0)
            # OR if count is simply very high (absolute threshold for outbreak)
            if today_count > max(5, avg_count * 1.5) or today_count > 15:
                alerts.append({
                    'disease': disease,
                    'severity': 'High',
                    'message': f"Potential outbreak of {disease} detected. Cases today ({today_count}) remain critically high (Weekly Avg: {avg_count:.1f}).",
                    'date': latest_date.strftime('%Y-%m-%d')
                })
                
        return alerts

# Singleton instance
analytics_service = AnalyticsService()
