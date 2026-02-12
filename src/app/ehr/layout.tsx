
"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function EHRLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="ehr_agent">
            <CopilotSidebar
                defaultOpen={true}
                instructions="You are an expert AYUSH medical assistant. Help the doctor create an EHR by asking for patient details, symptoms, and suggesting diagnoses based on Ayurveda/AYUSH principles."
                labels={{
                    title: "AYUSH Copilot",
                    initial: "How can I help you with this patient record?",
                }}
            >
                <div className="min-h-screen bg-gray-50 dark:bg-zinc-900">
                    <header className="bg-white dark:bg-zinc-800 shadow-sm border-b border-gray-200 dark:border-zinc-700">
                        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
                            <h1 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                                AYUSH - Smart EHR
                            </h1>
                        </div>
                    </header>
                    <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                        {children}
                    </main>
                </div>
            </CopilotSidebar>
        </CopilotKit>
    );
}
