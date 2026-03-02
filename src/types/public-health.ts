/**
 * Shared public-health domain types for the Ayush AI application.
 *
 * Import from this file whenever you need types related to outbreak
 * monitoring, disease trends, hotspots, alerts, or predictions.
 */

/** A single data point in a disease trend time series */
export interface TrendData {
    date: string;
    [key: string]: number | string;
}

/** An active outbreak alert */
export interface AlertData {
    disease: string;
    severity: string;
    message: string;
    date: string;
}

/** A geographic disease hotspot */
export interface HotspotData {
    city: string;
    pincode: string;
    diagnosis: string;
    count: number;
}

/** A GNN-based disease spread prediction for a geographic area */
export interface PredictionData {
    pincode: string;
    predicted_cases: number;
    risk_level: string;
    day_offset: number;
}
