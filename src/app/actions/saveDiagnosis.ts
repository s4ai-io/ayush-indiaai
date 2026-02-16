'use server';

import fs from 'fs/promises';
import path from 'path';

const DATA_FILE_PATH = path.join(process.cwd(), 'data', 'registrations.json');

interface PrescriptionItem {
    medicine: string;
    dosage: string;
    frequency: string;
    duration: string;
}

interface DiagnosisRecord {
    symptoms: string;
    diagnosis: string;
    notes: string;
    prescription: PrescriptionItem[];
    timestamp: string;
}

export async function saveDiagnosis(patientId: string, diagnosisData: Omit<DiagnosisRecord, 'timestamp'>) {
    try {
        const fileContent = await fs.readFile(DATA_FILE_PATH, 'utf-8');
        const registrations = JSON.parse(fileContent);

        const patientIndex = registrations.findIndex((p: { id: string }) => p.id === patientId);

        if (patientIndex === -1) {
            return { success: false, message: 'Patient not found' };
        }

        // Initialize medicalRecords array if it doesn't exist
        if (!registrations[patientIndex].medicalRecords) {
            registrations[patientIndex].medicalRecords = [];
        }

        const newRecord: DiagnosisRecord = {
            ...diagnosisData,
            timestamp: new Date().toISOString()
        };

        registrations[patientIndex].medicalRecords.push(newRecord);

        await fs.writeFile(DATA_FILE_PATH, JSON.stringify(registrations, null, 2));
        return { success: true, message: 'Diagnosis saved successfully!' };
    } catch (error) {
        console.error("Error saving diagnosis:", error);
        return { success: false, message: 'Failed to save diagnosis.' };
    }
}
