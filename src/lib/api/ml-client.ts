/**
 * ML API Client for AYUSH Application
 * Provides type-safe access to the Python ML backend
 */

// ============================================================================
// Type Definitions
// ============================================================================

export interface HerbRecommendation {
    name: string;
    dosage: string;
    benefits: string;
}

export interface YogaRecommendation {
    practice: string;
    duration: string;
    benefits: string;
}

export interface PatientProfile {
    age: number;
    gender: 'Male' | 'Female';
    prakriti: string;
    vikriti: string;
    disease: string;
    symptoms?: string;
    medical_history?: string; // Comorbidity
    severity: number; // 1-10
    bmi?: number;
}

export interface TreatmentRecommendation {
    herbs: HerbRecommendation[];
    yoga: YogaRecommendation[];
    diet: string[];
    lifestyle: string[];
    predicted_improvement?: number;
    recommended_duration_weeks?: number;
}

export interface ForecastDataPoint {
    month: string;
    predicted_cases: number;
    confidence_lower?: number;
    confidence_upper?: number;
}

export interface ForecastResponse {
    disease: string;
    forecast_months: number;
    forecast_data: ForecastDataPoint[];
    trend: 'increasing' | 'decreasing' | 'stable';
    risk_level: 'low' | 'moderate' | 'high';
}

export interface EmergingTrend {
    disease: string;
    category: string;
    current_cases: number;
    growth_rate: number;
    risk_score: number;
    alert_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface TrendsResponse {
    trends: EmergingTrend[];
    generated_at: string;
}

export interface HealthCheckResponse {
    status: string;
    models_loaded: boolean;
    version: string;
}

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Error Handling
// ============================================================================

export class MLAPIError extends Error {
    constructor(
        message: string,
        public statusCode?: number,
        public details?: unknown
    ) {
        super(message);
        this.name = 'MLAPIError';
    }
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new MLAPIError(
            errorData.detail || `API request failed with status ${response.status}`,
            response.status,
            errorData
        );
    }
    return response.json();
}

// ============================================================================
// API Client Functions
// ============================================================================

/**
 * Get ML-powered treatment recommendation for a patient
 */
export async function getMLRecommendation(
    profile: PatientProfile
): Promise<TreatmentRecommendation> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/ml/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(profile),
        });

        return handleResponse<TreatmentRecommendation>(response);
    } catch (error) {
        if (error instanceof MLAPIError) {
            throw error;
        }
        throw new MLAPIError(
            'Failed to get ML recommendation. Please check your connection and try again.',
            undefined,
            error
        );
    }
}

/**
 * Get disease forecast for next N months
 */
export async function getDiseaseForecast(
    disease?: string,
    months: number = 3
): Promise<ForecastResponse> {
    try {
        const params = new URLSearchParams();
        if (disease) params.append('disease', disease);
        params.append('months', months.toString());

        const response = await fetch(
            `${API_BASE_URL}/api/ml/forecast?${params.toString()}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );

        return handleResponse<ForecastResponse>(response);
    } catch (error) {
        if (error instanceof MLAPIError) {
            throw error;
        }
        throw new MLAPIError(
            'Failed to get disease forecast. Please try again.',
            undefined,
            error
        );
    }
}

/**
 * Get emerging disease trends
 */
export async function getEmergingTrends(): Promise<TrendsResponse> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/ml/trends`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        return handleResponse<TrendsResponse>(response);
    } catch (error) {
        if (error instanceof MLAPIError) {
            throw error;
        }
        throw new MLAPIError(
            'Failed to get emerging trends. Please try again.',
            undefined,
            error
        );
    }
}

/**
 * Check ML API health status
 */
export async function checkMLHealth(): Promise<HealthCheckResponse> {
    try {
        const response = await fetch(`${API_BASE_URL}/api/ml/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        return handleResponse<HealthCheckResponse>(response);
    } catch (error) {
        if (error instanceof MLAPIError) {
            throw error;
        }
        throw new MLAPIError(
            'Failed to check ML service health.',
            undefined,
            error
        );
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Validate patient profile before sending to API
 */
export function validatePatientProfile(profile: PatientProfile): string[] {
    const errors: string[] = [];

    if (!profile.disease || profile.disease.trim().length === 0) {
        errors.push('Disease name is required');
    }

    if (profile.age < 0 || profile.age > 120) {
        errors.push('Age must be between 0 and 120');
    }

    if (profile.severity < 1 || profile.severity > 10) {
        errors.push('Severity must be between 1 and 10');
    }

    if (profile.bmi && (profile.bmi < 10 || profile.bmi > 50)) {
        errors.push('BMI must be between 10 and 50');
    }

    if (!['Male', 'Female'].includes(profile.gender)) {
        errors.push('Gender must be Male or Female');
    }

    const validDoshas = [
        'Vata',
        'Pitta',
        'Kapha',
        'Vata-Pitta',
        'Pitta-Kapha',
        'Vata-Kapha',
        'Tridosha',
    ];

    if (!validDoshas.includes(profile.prakriti)) {
        errors.push('Invalid Prakriti value');
    }

    if (!validDoshas.includes(profile.vikriti)) {
        errors.push('Invalid Vikriti value');
    }

    return errors;
}
