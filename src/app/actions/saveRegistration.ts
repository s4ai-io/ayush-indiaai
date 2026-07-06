'use server';


import type { PatientRegistrationData } from '@/types/clinical';
import { BACKEND_URL, authHeaders } from '@/lib/server/backend';



export async function saveRegistration(data: PatientRegistrationData) {
    try {


        console.log("Saving registration to backend:", `${BACKEND_URL}/api/patients`);

        const response = await fetch(`${BACKEND_URL}/api/patients`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(await authHeaders()),
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backend API Error:', errorText);
            throw new Error(`Backend API Error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        return { success: true, message: 'Registration saved successfully to Database!' };

    } catch (error: unknown) {
        console.error('Error saving registration:', error);
        return { success: false, message: 'Failed to save registration. Please try again.' };
    }
}
