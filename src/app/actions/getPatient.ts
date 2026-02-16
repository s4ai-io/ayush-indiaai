'use server';

import fs from 'fs/promises';
import path from 'path';

const DATA_FILE_PATH = path.join(process.cwd(), 'data', 'registrations.json');

export async function getPatient(id: string) {
    try {
        await fs.access(DATA_FILE_PATH);
        const fileContent = await fs.readFile(DATA_FILE_PATH, 'utf-8');
        const data = JSON.parse(fileContent);
        return data.find((p: { id: string }) => p.id === id) || null;
    } catch (error) {
        console.error("Error reading patient:", error);
        return null;
    }
}
