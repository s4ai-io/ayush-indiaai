'use server';

export async function getPatient(id: string) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/patients/${id}`, {
            cache: 'no-store'
        });
        if (!response.ok) {
            return null;
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching patient:", error);
        return null;
    }
}
