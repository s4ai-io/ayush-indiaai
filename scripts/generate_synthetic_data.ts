
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Simulation Configuration
const TOTAL_PATIENTS = 300;
const OUTBREAK_DISEASE = "Dengue";
const OUTBREAK_CITY = "New Delhi";
const OUTBREAK_PINCODES = ["110001", "110002", "110003", "110004"];
const START_DATE = new Date();
START_DATE.setDate(START_DATE.getDate() - 30); // Last 30 days

const OTHER_DISEASES = ["Common Cold", "Fever", "Hypertension", "Diabetes", "Gastritis"];
const OTHER_CITIES = ["Mumbai", "Bangalore", "Chennai", "Kolkata"];

// Helper Data
const FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Diya", "Saanvi", "Anaya", "Aadhya", "Pari", "Anvi", "Myra", "Riya", "Aarya", "Kyra"];
const LAST_NAMES = ["Sharma", "Verma", "Gupta", "Malhotra", "Bhatia", "Saxena", "Mehta", "Chopra", "Singh", "Das", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Kumar", "Mishra", "Yadav", "Joshi", "Jain"];

const DATA_FILE_PATH = path.join(process.cwd(), 'data', 'registrations.json');

// Interface matching the app's structure
interface RegistrationData {
    id: string;
    timestamp: string;
    basicInfo: {
        firstName: string;
        lastName: string;
        gender: string;
        dateOfBirth: string;
        abhaId: string;
        [key: string]: any;
    };
    contactInfo: {
        mobileNumber: string;
        correspondenceCity: string;
        correspondencePincode: string;
        [key: string]: any;
    };
    medicalRecords: {
        symptoms: string;
        diagnosis: string;
        notes: string;
        prescription: any[];
        timestamp: string;
    }[];
    [key: string]: any;
}

function getRandomElement<T>(arr: T[]): T {
    return arr[Math.floor(Math.random() * arr.length)];
}

function getRandomDate(start: Date, end: Date): string {
    return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime())).toISOString();
}

function generatePatient(index: number): RegistrationData {
    const isOutbreakCase = Math.random() < 0.7; // 70% chance of being part of the outbreak

    // Basic Info
    const firstName = getRandomElement(FIRST_NAMES);
    const lastName = getRandomElement(LAST_NAMES);
    const gender = Math.random() > 0.5 ? "Male" : "Female";
    const dobYear = 1970 + Math.floor(Math.random() * 40);
    const dateOfBirth = `${dobYear}-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`;
    const abhaId = `${Math.floor(Math.random() * 100)}-${Math.floor(Math.random() * 1000)}-${Math.floor(Math.random() * 1000)}-${Math.floor(Math.random() * 1000)}`;
    const mobileNumber = `9${Math.floor(Math.random() * 1000000000)}`;

    // Location
    let city, pincode;
    if (isOutbreakCase) {
        city = OUTBREAK_CITY;
        pincode = getRandomElement(OUTBREAK_PINCODES);
    } else {
        city = getRandomElement(OTHER_CITIES);
        pincode = `${Math.floor(100000 + Math.random() * 900000)}`;
    }

    // Diagnosis
    let diagnosis, symptoms, notes;
    let recordDate;

    if (isOutbreakCase) {
        diagnosis = OUTBREAK_DISEASE;
        symptoms = "High fever, severe headache, joint pain, rash";
        notes = "Patient presented with classic dengue symptoms. Platelet count monitoring advised.";

        // 80% chance for outbreak cases to be VERY recent (last 5 days) to trigger alert
        if (Math.random() < 0.8) {
            const fiveDaysAgo = new Date();
            fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);
            recordDate = getRandomDate(fiveDaysAgo, new Date());
        } else {
            recordDate = getRandomDate(START_DATE, new Date());
        }
    } else {
        diagnosis = getRandomElement(OTHER_DISEASES);
        symptoms = "General malaise, mild fever";
        notes = "Routine checkup.";
        recordDate = getRandomDate(START_DATE, new Date());
    }

    return {
        id: crypto.randomUUID(),
        timestamp: recordDate,
        basicInfo: {
            firstName,
            lastName,
            gender,
            dateOfBirth,
            abhaId,
            nationality: "Indian",
            insuranceProvider: "LIC"
        },
        contactInfo: {
            mobileNumber,
            emailId: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@example.com`,
            correspondenceCity: city,
            correspondencePincode: pincode,
            correspondenceState: "Delhi", // Simplified for outbreak
            correspondenceCountry: "India"
        },
        medicalRecords: [
            {
                symptoms,
                diagnosis,
                notes,
                prescription: [],
                timestamp: recordDate
            }
        ]
    };
}

function generateSyntheticData() {
    const patients: RegistrationData[] = [];
    console.log(`Generating ${TOTAL_PATIENTS} synthetic patient records...`);
    console.log(`Simulating ${OUTBREAK_DISEASE} outbreak in ${OUTBREAK_CITY}.`);

    for (let i = 0; i < TOTAL_PATIENTS; i++) {
        patients.push(generatePatient(i));
    }

    // Ensure directory exists
    const dir = path.dirname(DATA_FILE_PATH);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(DATA_FILE_PATH, JSON.stringify(patients, null, 2));
    console.log(`✅ Successfully saved ${patients.length} records to ${DATA_FILE_PATH}`);
}

generateSyntheticData();
