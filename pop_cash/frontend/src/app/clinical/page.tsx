"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { useState } from "react";
import "@copilotkit/react-ui/styles.css";

// Interface must match Backend Model
interface EHRDraft {
    demographics: {
        name?: string;
        age?: string | number;
        gender?: string;
        contact?: string;
        uhid?: string;
    };
    presenting_complaints: { symptom: string; duration?: string; severity?: string; notes?: string }[];
    clinical_findings: { observation: string; category?: string }[];
    diagnosis: { condition: string; icd_code?: string; ayush_terminology?: string; confidence?: number }[];
    prakriti: { primary_dosha?: string; secondary_dosha?: string; assessment_notes?: string };
    comorbidities: string[];
    therapies: { medicine: string; dosage?: string; duration?: string; anupana?: string }[];
    lifestyle_advice: string[];
    follow_up?: string;
}

const INITIAL_DRAFT: EHRDraft = {
    demographics: {},
    presenting_complaints: [],
    clinical_findings: [],
    diagnosis: [],
    prakriti: {},
    comorbidities: [],
    therapies: [],
    lifestyle_advice: [],
    follow_up: "",
};

export default function ClinicalPage() {
    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="clinical_agent">
            <ClinicalContent />
        </CopilotKit>
    );
}

function ClinicalContent() {
    const [ehrDraft, setEhrDraft] = useState<EHRDraft>(INITIAL_DRAFT);

    // Make the EHR Draft readable by the Copilot
    useCopilotReadable({
        description: "The current state of the Electronic Health Record draft.",
        value: ehrDraft,
    });

    // Action to update the EHR Draft
    useCopilotAction({
        name: "update_ehr_draft",
        description: "Update the EHR draft with new clinical information.",
        parameters: [
            {
                name: "demographics", type: "object", attributes: [
                    { name: "name", type: "string" },
                    { name: "age", type: "string" }, // Allow string or number
                    { name: "gender", type: "string" },
                    { name: "contact", type: "string" },
                    { name: "uhid", type: "string" }
                ]
            },
            {
                name: "presenting_complaints", type: "object[]", attributes: [
                    { name: "symptom", type: "string" },
                    { name: "duration", type: "string" },
                    { name: "severity", type: "string" }
                ]
            },
            {
                name: "clinical_findings", type: "object[]", attributes: [
                    { name: "observation", type: "string" },
                    { name: "category", type: "string" }
                ]
            },
            {
                name: "diagnosis", type: "object[]", attributes: [
                    { name: "condition", type: "string" },
                    { name: "confidence", type: "number" }
                ]
            },
            {
                name: "prakriti", type: "object", attributes: [
                    { name: "primary_dosha", type: "string" },
                    { name: "secondary_dosha", type: "string" }
                ]
            },
            {
                name: "therapies", type: "object[]", attributes: [
                    { name: "medicine", type: "string" },
                    { name: "dosage", type: "string" },
                    { name: "duration", type: "string" },
                    { name: "anupana", type: "string" }
                ]
            },
            { name: "lifestyle_advice", type: "string[]" },
            { name: "follow_up", type: "string" }
        ],
        handler: async (args: Partial<EHRDraft>) => {
            console.log("Updating EHR Draft with:", args);
            setEhrDraft((prev: EHRDraft) => {
                const newDraft = { ...prev };
                if (args.demographics) newDraft.demographics = { ...prev.demographics, ...args.demographics };

                // For lists, we append new items to existing ones
                if (args.presenting_complaints) newDraft.presenting_complaints = [...prev.presenting_complaints, ...args.presenting_complaints];
                if (args.clinical_findings) newDraft.clinical_findings = [...prev.clinical_findings, ...args.clinical_findings];
                if (args.diagnosis) newDraft.diagnosis = [...prev.diagnosis, ...args.diagnosis];
                if (args.prakriti) newDraft.prakriti = { ...prev.prakriti, ...args.prakriti };
                if (args.therapies) newDraft.therapies = [...prev.therapies, ...args.therapies];
                if (args.lifestyle_advice) newDraft.lifestyle_advice = [...prev.lifestyle_advice, ...args.lifestyle_advice];

                if (args.follow_up) newDraft.follow_up = args.follow_up;

                return newDraft;
            });
            return "EHR Draft updated on screen.";
        },
    });

    return (
        <div className="flex h-screen bg-gray-50 relative">
            {/* Left Panel: Live EHR Draft View */}
            <div className="w-2/3 p-8 overflow-y-auto relative z-10 bg-gray-50">
                <h1 className="text-2xl font-bold mb-6 text-gray-800">Live EHR Draft</h1>

                <div className="space-y-6">
                    {/* Demographics */}
                    <Section title="Demographics">
                        <div className="grid grid-cols-2 gap-4">
                            <Field label="Name" value={ehrDraft.demographics.name} />
                            <Field label="Age" value={ehrDraft.demographics.age} />
                            <Field label="Gender" value={ehrDraft.demographics.gender} />
                            <Field label="Contact" value={ehrDraft.demographics.contact} />
                        </div>
                    </Section>

                    {/* Presenting Complaints */}
                    <Section title="Presenting Complaints">
                        {ehrDraft.presenting_complaints.map((c, i) => (
                            <div key={i} className="bg-gray-100 p-2 rounded mb-2">
                                <strong>{c.symptom}</strong> ({c.duration}) - {c.severity}
                            </div>
                        ))}
                        {ehrDraft.presenting_complaints.length === 0 && <span className="text-gray-400">No complaints recorded</span>}
                    </Section>

                    {/* Diagnosis & Prakriti */}
                    <div className="grid grid-cols-2 gap-6">
                        <Section title="Prakriti Assessment">
                            <Field label="Primary" value={ehrDraft.prakriti.primary_dosha} />
                            <Field label="Secondary" value={ehrDraft.prakriti.secondary_dosha} />
                        </Section>
                        <Section title="Diagnosis">
                            {ehrDraft.diagnosis.map((d, i) => (
                                <div key={i} className="mb-1">
                                    • {d.condition} <span className="text-xs text-blue-600">({d.confidence ? `${(d.confidence * 100).toFixed(0)}%` : 'N/A'})</span>
                                </div>
                            ))}
                        </Section>
                    </div>

                    {/* Therapies */}
                    <Section title="Therapies / Medication">
                        <table className="min-w-full text-sm">
                            <thead>
                                <tr className="text-left text-gray-500">
                                    <th>Medicine</th>
                                    <th>Dosage</th>
                                    <th>Duration</th>
                                    <th>Anupana</th>
                                </tr>
                            </thead>
                            <tbody>
                                {ehrDraft.therapies.map((t, i) => (
                                    <tr key={i} className="border-t">
                                        <td className="py-1">{t.medicine}</td>
                                        <td className="py-1">{t.dosage}</td>
                                        <td className="py-1">{t.duration}</td>
                                        <td className="py-1">{t.anupana}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {ehrDraft.therapies.length === 0 && <span className="text-gray-400">No therapies prescribed</span>}
                    </Section>

                    {/* Lifestyle & Follow-up */}
                    <div className="grid grid-cols-2 gap-6">
                        <Section title="Lifestyle Advice">
                            <ul className="list-disc pl-5">
                                {ehrDraft.lifestyle_advice.map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ul>
                        </Section>
                        <Section title="Follow Up">
                            <p>{ehrDraft.follow_up || "Not specified"}</p>
                        </Section>
                    </div>

                </div>
            </div>

            {/* Right Panel: Copilot Sidebar (Chat) */}
            <div className="w-1/3 border-l border-gray-200 bg-white relative z-30 flex flex-col">
                <CopilotSidebar
                    instructions="You are an AI Clinical Copilot. Assist the doctor in documenting the patient visit."
                    labels={{
                        title: "Clinical Copilot (AGUI)",
                        initial: "Hello Doctor. I'm ready to document the consultation.",
                    }}
                    defaultOpen={true}
                    clickOutsideToClose={false}
                />
            </div>
        </div>
    );
}

// UI Helper Components
function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{title}</h2>
            <div>{children}</div>
        </div>
    )
}

function Field({ label, value }: { label: string; value?: string | number }) {
    return (
        <div>
            <span className="text-xs text-gray-400 block">{label}</span>
            <span className="font-medium text-gray-800">{value || "-"}</span>
        </div>
    )
}
