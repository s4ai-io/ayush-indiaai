'use server';

import type { PatientRegistrationData, ConsultationData } from '@/types/clinical';


const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';


/**
 * Saves a new patient registration.
 * This should hit the backend `/api/patients` to create a new patient row and return the generated ID.
 */
export async function savePatient(data: PatientRegistrationData) {
    try {


        console.log("Saving new patient to backend:", `${API_URL}/api/patients`);

        const response = await fetch(`${API_URL}/api/patients`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend API Error (savePatient):', errorText);
            throw new Error(`Backend API Error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        // Mock return format - assuming the API returns the created patient ID.
        // Adapt depending on actual schema!
        return {
            success: true,
            message: 'Patient registered successfully.',
            patientId: result.id || Math.random().toString(36).substring(7)
        };

    } catch (error: unknown) {
        console.error('Error saving patient:', error);
        return { success: false, message: 'Failed to save patient. Please try again.' };
    }
}

/**
 * Saves a consultation (clinical assessment) for a specific patient.
 * This should hit a backend endpoint for adding medical records/consultations.
 */
export async function saveConsultation(patientId: string, data: ConsultationData) {
    try {
        console.log(`Saving consultation for patient ${patientId} to backend.`);

        // Ensure patientId is attached to the payload
        const payload = {
            ...data,
            patientId,
            timestamp: new Date().toISOString(),
        };

        // Note: Currently pointing to a hypothetical /api/consultations endpoint.
        // We will need to ensure the FastAPI backend actually supports this.
        const response = await fetch(`${API_URL}/api/consultations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend API Error (saveConsultation):', errorText);
            throw new Error(`Backend API Error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        return {
            success: true,
            message: 'Consultation saved successfully.',
            visitId: result.visitId || Math.random().toString(36).substring(7)
        };

    } catch (error: unknown) {
        console.error('Error saving consultation:', error);
        return {
            success: false,
            message: 'Failed to save consultation plan to the server.'
        };
    }
}
