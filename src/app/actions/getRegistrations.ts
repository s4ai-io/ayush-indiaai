'use server';

export async function getRegistrations(status?: 'pending' | 'completed') {
    try {
        const url = status
            ? `http://127.0.0.1:8000/api/patients?status=${status}`
            : 'http://127.0.0.1:8000/api/patients';
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
