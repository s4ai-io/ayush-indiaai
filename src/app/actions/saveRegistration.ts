'use server';

import fs from 'fs/promises';
import path from 'path';
import { generateAbhaId } from '@/lib/mockAbdmService';

const DATA_FILE_PATH = path.join(process.cwd(), 'data', 'registrations.json');

interface RegistrationData {
    basicInfo?: {
        abhaId?: string;
        [key: string]: unknown;
    };
    [key: string]: unknown;
}

export async function saveRegistration(data: RegistrationData) {
    try {
        // Ensure the data directory exists
        const dataDir = path.dirname(DATA_FILE_PATH);
        try {
            await fs.access(dataDir);
        } catch {
            await fs.mkdir(dataDir, { recursive: true });
        }

        // Mock ABDM Integration: Generate ABHA ID if not provided
        if (data.basicInfo && !data.basicInfo.abhaId) {
            data.basicInfo.abhaId = generateAbhaId();
        }

        let registrations: any[] = [];
        try {
            const fileContent = await fs.readFile(DATA_FILE_PATH, 'utf-8');
            registrations = JSON.parse(fileContent);
        } catch {
            // File doesn't exist or is empty, start with empty array
        }

        registrations.push({
            ...data,
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
        });

        await fs.writeFile(DATA_FILE_PATH, JSON.stringify(registrations, null, 2));
        return { success: true, message: 'Registration saved successfully!' };
    } catch (error: unknown) {
        console.error('Error saving registration:', error);
        return { success: false, message: 'Failed to save registration.' };
    }
}
