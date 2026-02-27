'use server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function getRegistrations(status?: 'pending' | 'completed') {
    try {
        const url = status
            ? `${API_URL}/api/patients?status=${status}`
            : `${API_URL}/api/patients`;
        const response = await fetch(url, {
            cache: 'no-store'
        });
        if (!response.ok) {
            throw new Error(`Failed to fetch patients: ${response.statusText}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching registrations:", error);
        return [];
    }
}
