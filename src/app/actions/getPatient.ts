'use server';

import { BACKEND_URL, authHeaders } from '@/lib/server/backend';

export async function getPatient(id: string) {
    try {
        const response = await fetch(`${BACKEND_URL}/api/patients/${id}`, {
            cache: 'no-store',
            headers: await authHeaders(),
        });
        if (!response.ok) {
            return null;
        }
        const p = await response.json();

        // Transform flat snake_case API shape → nested camelCase shape expected by DiagnosisForm
        return {
            id: p.id,
            basicInfo: {
                firstName: p.first_name || p.firstName || '',
                lastName: p.last_name || p.lastName || '',
                gender: p.gender || '',
                dateOfBirth: p.date_of_birth || p.dateOfBirth || '',
                abhaId: p.abha_id || p.abhaId || p.id_number || '',
            },
            contactInfo: {
                mobileNumber: p.mobile || p.mobileNumber || '',
            },
        };
    } catch (error) {
        console.error("Error fetching patient:", error);
        return null;
    }
}
