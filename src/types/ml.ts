/**
 * ML / forecasting types for the Ayush AI application.
 *
 * Import from this file whenever you need types specific to ML model
 * inputs/outputs that are not already in clinical.ts.
 */

/** Input payload sent to /api/recommend */
export interface PatientProfile {
    age: number;
    gender: 'Male' | 'Female';
    prakriti: string;
    vikriti: string;
    disease: string;
    symptoms?: string;
    medical_history?: string; // Comorbidity
    severity: number; // 1–10
    bmi?: number;
}

/** A single data point in a disease forecast series */
export interface ForecastDataPoint {
    month: string;
    predicted_cases: number;
    confidence_lower?: number;
    confidence_upper?: number;
}

/** Response shape for GET /api/forecast */
export interface ForecastResponse {
    disease: string;
    forecast_months: number;
    forecast_data: ForecastDataPoint[];
    trend: 'increasing' | 'decreasing' | 'stable';
    risk_level: 'low' | 'moderate' | 'high';
}

/** A single emerging disease trend entry */
export interface EmergingTrend {
    disease: string;
    category: string;
    current_cases: number;
    growth_rate: number;
    risk_score: number;
    alert_level: 'low' | 'medium' | 'high' | 'critical';
}

/** Response shape for GET /api/trends */
export interface TrendsResponse {
    trends: EmergingTrend[];
    generated_at: string;
}

/** Health check response */
export interface HealthCheckResponse {
    status: string;
    models_loaded: boolean;
    version: string;
}
