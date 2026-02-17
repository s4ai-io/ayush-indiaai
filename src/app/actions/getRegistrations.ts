'use server';

export async function getRegistrations() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/patients', {
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
