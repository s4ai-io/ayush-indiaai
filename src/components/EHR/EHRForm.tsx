
"use client";

import { useState } from "react";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";

export default function EHRForm() {
    const [patientName, setPatientName] = useState("");
    const [age, setAge] = useState("");
    const [gender, setGender] = useState("");
    const [symptoms, setSymptoms] = useState("");
    const [diagnosis, setDiagnosis] = useState("");
    const [notes, setNotes] = useState("");

    // --- Make form state readable to the Copilot ---
    useCopilotReadable({
        description: "The current state of the EHR form",
        value: {
            patientName,
            age,
            gender,
            symptoms,
            diagnosis,
            notes,
        },
    });

    // --- Define action to update the form ---
    useCopilotAction({
        name: "update_ehr_form",
        description: "Update the EHR form fields with new information.",
        parameters: [
            { name: "patientName", type: "string", description: "Name of the patient", required: false },
            { name: "age", type: "string", description: "Age of the patient", required: false },
            { name: "gender", type: "string", description: "Gender of the patient", required: false },
            { name: "symptoms", type: "string", description: "Symptoms reported by patient", required: false },
            { name: "diagnosis", type: "string", description: "Diagnosis details", required: false },
            { name: "notes", type: "string", description: "Additional clinical notes", required: false },
        ],
        handler: async ({ patientName, age, gender, symptoms, diagnosis, notes }) => {
            if (patientName) setPatientName(patientName);
            if (age) setAge(age);
            if (gender) setGender(gender);
            if (symptoms) setSymptoms(symptoms);
            if (diagnosis) setDiagnosis(diagnosis);
            if (notes) setNotes((prev) => (prev ? prev + "\n" + notes : notes));
            return "Form updated successfully.";
        },
    });

    return (
        <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md dark:bg-zinc-800">
            <h2 className="text-2xl font-bold mb-6 text-gray-800 dark:text-white">New EHR Entry</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Patient Demographics */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Patient Details</h3>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
                        <input
                            type="text"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-zinc-700 dark:text-white p-2"
                            value={patientName}
                            onChange={(e) => setPatientName(e.target.value)}
                            placeholder="e.g. John Doe"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Age</label>
                            <input
                                type="number"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-zinc-700 dark:text-white p-2"
                                value={age}
                                onChange={(e) => setAge(e.target.value)}
                                placeholder="e.g. 45"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Gender</label>
                            <select
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-zinc-700 dark:text-white p-2"
                                value={gender}
                                onChange={(e) => setGender(e.target.value)}
                            >
                                <option value="">Select...</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Clinical Info */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Clinical Information</h3>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Symptoms</label>
                        <textarea
                            rows={3}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-zinc-700 dark:text-white p-2"
                            value={symptoms}
                            onChange={(e) => setSymptoms(e.target.value)}
                            placeholder="Describe patient symptoms..."
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Diagnosis</label>
                        <input
                            type="text"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-zinc-700 dark:text-white p-2"
                            value={diagnosis}
                            onChange={(e) => setDiagnosis(e.target.value)}
                            placeholder="Provisional diagnosis..."
                        />
                    </div>
                </div>
            </div>

            <div className="mt-6 space-y-4">
                <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Notes & Plan</h3>
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Doctor's Notes</label>
                    <textarea
                        rows={5}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-zinc-700 dark:text-white p-2"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Detailed observations and treatment plan..."
                    />
                </div>
            </div>

            <div className="mt-8 flex justify-end gap-4">
                <button className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors">
                    Reset
                </button>
                <button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-500/30">
                    Save Record
                </button>
            </div>
        </div>
    );
}
