/**
 * Shared clinical domain types for the Ayush AI application.
 *
 * Import from this file whenever you need types related to patients,
 * visits, consultations, or clinical assessments.
 */

// ── Patient Registration ────────────────────────────────────────────────────

export interface BasicInfo {
    abhaId?: string;
    firstName: string;
    middleName?: string;
    lastName: string;
    age: string;
    gender: 'Male' | 'Female' | 'Transgender' | 'Other' | 'Prefer not to say' | '';
    bloodGroup?: string;
    maritalStatus: string;
    height?: number; // cm
    weight?: number; // kg
    occupation?: string;
}

export interface ContactInfo {
    mobile: string;
    email?: string;
    address?: string;
    taluka?: string;
    district?: string;
    city?: string;
    state?: string;
    pincode?: string;
}

export interface OtherInfo {
    occupation?: string;
    bloodGroup?: string;
    idType?: string;
    idNumber?: string;
    emergencyContactName?: string;
    emergencyContactRelation?: string;
    emergencyContactNumber?: string;
    currentMedication?: string;
    pastSurgeries?: string;
    familyMedicalHistory?: string;
    allergies?: string;
    habits?: {
        smoking?: boolean;
        alcohol?: boolean;
    };
    preferredLanguage?: string;
    insuranceProvider?: string;
    insurancePolicyNumber?: string;
}

export interface PatientRegistrationData {
    id?: string; // Optional for creation, returned by backend
    basicInfo: BasicInfo;
    contactInfo: ContactInfo;
    otherInfo: OtherInfo;
}

// ── Patient Records (API responses, snake_case from backend) ────────────────

/** Full patient record as returned by GET /api/patients/:id */
export interface PatientRecord {
    id: string;
    first_name: string;
    last_name: string;
    gender: string;
    age: number;
    marital_status: string;
    mobile: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    blood_group: string;
    occupation: string;
    id_type: string;
    id_number: string;
    created_at: string;
    diagnosis_done: boolean;
}

/** Lightweight patient entry as used in the patients directory listing */
export interface PatientDirectoryItem {
    id: string;
    first_name: string;
    last_name: string;
    mobile: string;
    gender: string;
    age: number;
    city: string;
    visited: boolean;
}

// ── Visits & Clinical Assessment ────────────────────────────────────────────

export interface ClinicalAssessment {
    symptoms: string;
    diagnosis: string;
    prakriti?: string;
    vikriti?: string;
    severity?: number;
    comorbidities?: string;
    notes: string;
}

export interface ConsultationData {
    visitId?: string;
    patientId: string;
    assessment: ClinicalAssessment;
    timestamp?: string; // Automatically generated on save
}

/** Patient demographics embedded inside a visit response */
export interface VisitPatient {
    id: string;
    firstName: string;
    lastName: string;
    gender: string;
    age: string;
    mobile: string;
}

/** Full visit context used by the treatment page */
export interface VisitContext {
    patientId: string;
    patientName: string;
    patientMobile: string;
    symptoms: string;
    diagnosis: string;
    doctorNotes: string;
    prakriti: string;
    vikriti: string;
    severity: string;
    comorbidities: string;
    patient?: VisitPatient;
}

/** Complete visit details as returned by GET /api/visits/:id */
export interface VisitDetails {
    patient: {
        id: string;
        firstName: string;
        lastName: string;
        gender: string;
        age: string;
        maritalStatus: string;
        mobile: string;
        address: string;
        city: string;
        state: string;
        pincode: string;
        bloodGroup: string;
        occupation: string;
        idType: string;
        idNumber: string;
    };
    visit: {
        id: string;
        visitDate: string;
        symptoms: string;
        diagnosis: string;
        prakriti: string;
        vikriti: string;
        severity: string;
        comorbidities: string;
        notes: string;
        prescription: Record<string, unknown>;
    };
    treatment: {
        herbs: string;
        yoga: string;
        diet: string;
        durationWeeks: string;
        predictedImprovement: string;
        outcome: string;
    };
    feedback: {
        rating: string;
        comments: string;
    };
}

// ── Diagnoses ───────────────────────────────────────────────────────────────

/** Summary of a completed diagnosis (used in doctor dashboard completed tab) */
export interface CompletedDiagnosis {
    record_id: string;
    patient_id: string;
    patient_name: string;
    patient_age: number;
    patient_gender: string;
    patient_city: string;
    patient_mobile: string;
    diagnosis: string;
    symptoms: string;
    visit_date: string;
}

/** Detailed diagnosis record for a specific patient */
export interface DiagnosisDetail {
    id: string;
    diagnosis: string;
    symptoms: string;
    notes: string;
    prescription: unknown;
    visit_date: string;
    herbs: string;
    yoga: string;
    diet: string;
    duration_weeks: number;
    improvement: number;
    outcome: string;
}

// ── Treatment Plan ──────────────────────────────────────────────────────────

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

/** Full AI-generated treatment plan returned by /api/recommend */
export interface TreatmentPlan {
    herbs: HerbRecommendation[];
    yoga: YogaRecommendation[];
    diet: string[];
    lifestyle: string[];
    formulation?: string;
    prevention: string[];
    prognosis?: string;
    complications: string[];
    medical_intervention?: string;
    doshas_affected?: string;
    source_disease?: string;
    predicted_improvement: number;
    recommended_duration_weeks: number;
    explainability: string[];
    namc_code?: string;
    namc_term?: string;
    namc_term_devanagari?: string;
    no_match_found?: boolean;
    message?: string;
}
