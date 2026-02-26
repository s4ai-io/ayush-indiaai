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
