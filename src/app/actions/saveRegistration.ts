'use server';

import fs from 'fs/promises';
import path from 'path';

const DATA_FILE_PATH = path.join(process.cwd(), 'data', 'registrations.json');

export async function saveRegistration(data: any) {
    try {
        // Ensure the data directory exists
        const dataDir = path.dirname(DATA_FILE_PATH);
        try {
            await fs.access(dataDir);
        } catch {
            await fs.mkdir(dataDir, { recursive: true });
        }

        let registrations = [];
        try {
            const fileContent = await fs.readFile(DATA_FILE_PATH, 'utf-8');
            registrations = JSON.parse(fileContent);
        } catch (error) {
            // File doesn't exist or is empty, start with empty array
        }

        registrations.push({
            ...data,
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
        });

        await fs.writeFile(DATA_FILE_PATH, JSON.stringify(registrations, null, 2));
        return { success: true, message: 'Registration saved successfully!' };
    } catch (error) {
        console.error('Error saving registration:', error);
        return { success: false, message: 'Failed to save registration.' };
    }
}
