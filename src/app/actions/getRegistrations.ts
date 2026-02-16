'use server';

import fs from 'fs/promises';
import path from 'path';

const DATA_FILE_PATH = path.join(process.cwd(), 'data', 'registrations.json');

export async function getRegistrations() {
    try {
        await fs.access(DATA_FILE_PATH);
        const fileContent = await fs.readFile(DATA_FILE_PATH, 'utf-8');
        const data = JSON.parse(fileContent);
        // Sort by timestamp descending
        return data.sort((a: { timestamp: string }, b: { timestamp: string }) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    } catch (error) {
        console.error("Error reading registrations:", error);
        return [];
    }
}
