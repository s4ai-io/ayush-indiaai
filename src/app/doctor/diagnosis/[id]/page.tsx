'use client';

import { useEffect, useState, use } from 'react';
import { getPatient } from '@/app/actions/getPatient';
import { saveDiagnosis } from '@/app/actions/saveDiagnosis';
import { VoiceInputButton } from '@/components/VoiceInputButton';
import { LanguageSelector } from '@/components/LanguageSelector';
import { CopilotKit, useCopilotChat, useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import "@copilotkit/react-ui/styles.css";
import { User, Activity, FileText, Pill, Save } from 'lucide-react';

interface Patient {
    id: string;
    basicInfo: {
        firstName: string;
        lastName: string;
        gender: string;
        dateOfBirth: string;
        abhaId: string;
    };
    contactInfo: {
        mobileNumber: string;
    };
}

interface PrescriptionItem {
    medicine: string;
    dosage: string;
    frequency: string;
    duration: string;
}

interface DiagnosisData {
    symptoms: string;
    diagnosis: string;
    prescription: PrescriptionItem[];
    notes: string;
}

function DiagnosisForm({ patient }: { patient: Patient }) {
    const [selectedLanguage, setSelectedLanguage] = useState("en-US");
    const [isListening, setIsListening] = useState(false);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    // Diagnosis State
    const [diagnosisData, setDiagnosisData] = useState<DiagnosisData>({
        symptoms: '',
        diagnosis: '',
        prescription: [],
        notes: ''
    });

    const { appendMessage } = useCopilotChat();

    useCopilotReadable({
        description: "Current patient details and diagnosis form state.",
        value: { patient, diagnosisData },
    });

    useCopilotAction({
        name: "update_diagnosis",
        description: "Update the diagnosis, symptoms, or prescription based on doctor's voice notes.",
        parameters: [
            { name: "symptoms", type: "string" },
            { name: "diagnosis", type: "string" },
            { name: "notes", type: "string" },
            {
                name: "prescription",
                type: "object[]",
                attributes: [
                    { name: "medicine", type: "string" },
                    { name: "dosage", type: "string" },
                    { name: "frequency", type: "string" },
                    { name: "duration", type: "string" },
                ]
            }
        ],
        handler: async (args: Partial<DiagnosisData>) => {
            setDiagnosisData((prev) => ({
                ...prev,
                ...args,
                prescription: args.prescription ? [...prev.prescription, ...args.prescription] : prev.prescription
            }));
            return "Diagnosis updated.";
        }
    });

    const handleVoiceTranscript = async (transcript: string) => {
        setVoiceError(null);
        await appendMessage(
            new TextMessage({
                role: MessageRole.User,
                content: transcript
            })
        );
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const result = await saveDiagnosis(patient.id, diagnosisData);
            if (result.success) {
                alert("Diagnosis saved successfully!");
                // Optionally redirect to dashboard
                // window.location.href = '/doctor'; 
            } else {
                alert("Failed to save diagnosis: " + result.message);
            }
        } catch (error) {
            console.error(error);
            alert("An error occurred while saving.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 p-8 pb-32">
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Patient Header */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex justify-between items-start">
                    <div className="flex gap-4">
                        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-2xl">
                            {patient.basicInfo.firstName[0]}{patient.basicInfo.lastName[0]}
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-slate-900">{patient.basicInfo.firstName} {patient.basicInfo.lastName}</h1>
                            <div className="text-slate-500 flex gap-3 text-sm mt-1">
                                <span>{patient.basicInfo.gender}</span>
                                <span>•</span>
                                <span>{new Date().getFullYear() - new Date(patient.basicInfo.dateOfBirth).getFullYear()} Years</span>
                                <span>•</span>
                                <span className="font-mono bg-slate-100 px-1 rounded">{patient.basicInfo.abhaId}</span>
                            </div>
                            <div className="flex items-center gap-2 mt-2 text-sm text-slate-600">
                                <User className="w-4 h-4" />
                                {patient.contactInfo.mobileNumber}
                            </div>
                        </div>
                    </div>
                    <div className="text-right">
                        <span className="inline-flex items-center gap-1 bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium">
                            <Activity className="w-4 h-4" />
                            Active Visit
                        </span>
                    </div>
                </div>

                {/* Diagnosis Section */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
                    <div className="flex justify-between items-center border-b border-slate-100 pb-4">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            <FileText className="w-5 h-5 text-blue-600" />
                            Clinical Notes
                        </h2>
                        <div className="flex items-center gap-2">
                            {/* Language Selector moved to bottom right */}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Symptoms</label>
                            <textarea
                                className="w-full p-3 border border-slate-200 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Patient reported symptoms..."
                                value={diagnosisData.symptoms}
                                onChange={(e) => setDiagnosisData({ ...diagnosisData, symptoms: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Diagnosis</label>
                            <textarea
                                className="w-full p-3 border border-slate-200 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 outline-none"
                                placeholder="Clinical diagnosis..."
                                value={diagnosisData.diagnosis}
                                onChange={(e) => setDiagnosisData({ ...diagnosisData, diagnosis: e.target.value })}
                            />
                        </div>
                    </div>
                </div>

                {/* Prescription Section */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 space-y-4">
                    <div className="flex justify-between items-center border-b border-slate-100 pb-4">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            <Pill className="w-5 h-5 text-purple-600" />
                            Prescription
                        </h2>
                    </div>

                    {diagnosisData.prescription.length === 0 ? (
                        <div className="text-center py-8 text-slate-400 border border-dashed border-slate-200 rounded-lg">
                            No medicines added yet. Speak to add.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th className="p-3 font-medium text-slate-600">Medicine</th>
                                        <th className="p-3 font-medium text-slate-600">Dosage</th>
                                        <th className="p-3 font-medium text-slate-600">Frequency</th>
                                        <th className="p-3 font-medium text-slate-600">Duration</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {diagnosisData.prescription.map((item, idx) => (
                                        <tr key={idx}>
                                            <td className="p-3 font-medium text-slate-900">{item.medicine}</td>
                                            <td className="p-3 text-slate-600">{item.dosage}</td>
                                            <td className="p-3 text-slate-600">{item.frequency}</td>
                                            <td className="p-3 text-slate-600">{item.duration}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* Save Actions */}
                <div className="flex justify-end gap-4">
                    <button
                        className="px-6 py-2 border border-slate-300 rounded-lg text-slate-700 font-medium hover:bg-slate-50"
                        disabled={saving}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-6 py-2 bg-[#00A9B4] hover:bg-[#008f99] text-white rounded-lg font-medium shadow-sm transition-colors disabled:opacity-50"
                    >
                        <Save className="w-4 h-4" />
                        {saving ? "Saving..." : "Finalize & Save Record"}
                    </button>
                </div>
            </div>

            {/* Voice Input Floating Button Overlay */}
            <div className="fixed bottom-24 right-6 z-[1000] flex flex-col items-end gap-2">
                {isListening && (
                    <div className="bg-black/75 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm animate-pulse">
                        Listening ({selectedLanguage})...
                    </div>
                )}
                {voiceError && (
                    <div className="bg-red-500 text-white text-xs px-2 py-1 rounded shadow-lg max-w-[200px]">
                        {voiceError}
                    </div>
                )}
                <div className="flex items-center gap-3">
                    <LanguageSelector
                        selectedLanguage={selectedLanguage}
                        onLanguageChange={setSelectedLanguage}
                    />
                    <VoiceInputButton
                        onTranscript={handleVoiceTranscript}
                        onError={(err) => setVoiceError(err)}
                        onStateChange={setIsListening}
                        language={selectedLanguage}
                    />
                </div>
            </div>
        </div>
    );
}

export default function DiagnosisPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [patient, setPatient] = useState<Patient | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPatient = async () => {
            const data = await getPatient(id);
            setPatient(data);
            setLoading(false);
        };
        fetchPatient();
    }, [id]);

    if (loading) return <div className="p-8 text-center text-slate-500">Loading patient details...</div>;
    if (!patient) return <div className="p-8 text-center text-red-500">Patient not found.</div>;

    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="doctor_agent">
            <CopilotSidebar
                instructions="You are a medical scribe. Help the doctor document the diagnosis and prescription."
                defaultOpen={true}
                clickOutsideToClose={false}
                labels={{
                    title: "Medical Scribe",
                    initial: "Ready to record diagnosis. Please speak.",
                }}
            >
                <DiagnosisForm patient={patient} />
            </CopilotSidebar>
        </CopilotKit>
    );
}
