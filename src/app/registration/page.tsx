"use client";

import { CopilotKit, useCopilotChat } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import "@copilotkit/react-ui/styles.css";
import { saveRegistration } from "../actions/saveRegistration";
import { Minus, Plus, ChevronDown, RefreshCw } from "lucide-react";
import { VoiceInputButton } from "@/components/VoiceInputButton";
import { LanguageSelector, INDIAN_LANGUAGES } from "@/components/LanguageSelector";
import { useRouter } from "next/navigation";


interface RegistrationData {
    contactInfo: {
        mobileNumber: string;
        address: string;
        city: string;
        state: string;
        pincode: string;
    };
    basicInfo: {
        firstName: string;
        lastName: string;
        gender: string;
        age: string; // Keeping as string for input, will parse
        maritalStatus: string;
        nationality: string;
    };
    otherInfo: {
        occupation: string;
        bloodGroup: string;
        idType: string;
        idNumber: string;
    };
    [key: string]: any;
}

const INITIAL_DATA: RegistrationData = {
    contactInfo: {
        mobileNumber: "",
        address: "",
        city: "",
        state: "",
        pincode: "",
    },
    basicInfo: {
        firstName: "",
        lastName: "",
        gender: "",
        age: "",
        maritalStatus: "",
        nationality: "Indian",
    },
    otherInfo: {
        occupation: "",
        bloodGroup: "",
        idType: "",
        idNumber: "",
    },
};

export default function RegistrationPage() {
    const [isChatOpen, setIsChatOpen] = useState(true);

    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="registration_agent">
            <CopilotSidebar
                instructions="You are an AI Assistant helping the user fill out the registration form."
                labels={{
                    title: "Registration Assistant",
                    initial: "Hello! I can help you fill out this form. Just tell me your details.",
                }}
                defaultOpen={true}
                clickOutsideToClose={false}
                onSetOpen={(open) => setIsChatOpen(open)}
            >
                <div className="flex-1 h-full min-h-screen overflow-y-auto bg-gradient-to-b from-background to-muted/20">
                    <div className="max-w-5xl mx-auto p-4 md:p-8">
                        <RegistrationForm isChatOpen={isChatOpen} />
                    </div>
                </div>
            </CopilotSidebar>
        </CopilotKit>
    );
}

function RegistrationForm({ isChatOpen }: { isChatOpen: boolean }) {
    const [formData, setFormData] = useState<RegistrationData>(INITIAL_DATA);
    const [status, setStatus] = useState<string | null>(null);
    const [isBasicInfoExpanded, setIsBasicInfoExpanded] = useState(true);
    const [isContactExpanded, setIsContactExpanded] = useState(true);
    const [isOtherInfoExpanded, setIsOtherInfoExpanded] = useState(true);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [isListening, setIsListening] = useState(false);
    const [selectedLanguage, setSelectedLanguage] = useState("en-IN");
    const [chatInputNode, setChatInputNode] = useState<Element | null>(null);
    const router = useRouter();

    useEffect(() => {
        if (!isChatOpen) {
            setChatInputNode(null);
            return;
        }

        const interval = setInterval(() => {
            const inputContainer = document.querySelector('.copilotKitInput');
            if (inputContainer) {
                (inputContainer as HTMLElement).style.position = 'relative';
                setChatInputNode(inputContainer);
                clearInterval(interval);
            }
        }, 100);

        return () => clearInterval(interval);
    }, [isChatOpen]);

    const { appendMessage, reset: resetChat } = useCopilotChat();

    const handleNewChat = () => {
        const confirmClearData = window.confirm("Do you want to clear the form data as well?\n\nClick 'OK' to clear the form and start fresh.\nClick 'Cancel' to keep the form data but start a new chat.");
        resetChat();
        if (confirmClearData) {
            setFormData(INITIAL_DATA);
        }
    };

    const handleVoiceTranscript = async (transcript: string) => {
        setVoiceError(null); // Clear error on new input

        // Auto-submit the transcript to Copilot
        await appendMessage(
            new TextMessage({
                role: MessageRole.User,
                content: transcript
            })
        );
    };

    useCopilotReadable({
        description: "The current state of the registration form.",
        value: formData,
    });

    useCopilotAction({
        name: "fill_registration_form",
        description: "Fill the registration form with user details.",
        parameters: [
            {
                name: "contactInfo",
                type: "object",
                attributes: [
                    { name: "mobileNumber", type: "string", description: "The mobile phone number" },
                    { name: "address", type: "string", description: "The correspondence or residential address" },
                    { name: "city", type: "string", description: "Must exactly match: New Delhi, Mumbai, Bangalore, Ahmedabad, Lucknow. Map 'Bengaluru' to 'Bangalore'" },
                    { name: "state", type: "string", description: "Must exactly match: Delhi, Maharashtra, Karnataka, Gujarat, Uttar Pradesh" },
                    { name: "pincode", type: "string", description: "The postal code or pincode" },
                ],
            },
            {
                name: "basicInfo",
                type: "object",
                attributes: [
                    { name: "firstName", type: "string" },
                    { name: "lastName", type: "string" },
                    { name: "gender", type: "string", description: "Male, Female, or Transgender" },
                    { name: "age", type: "string" },
                    { name: "maritalStatus", type: "string", description: "Must exactly match: Married, Unmarried, Divorcee, Widow (e.g., map 'Single' to 'Unmarried')" },
                    { name: "nationality", type: "string" },
                ],
            },
            {
                name: "otherInfo",
                type: "object",
                attributes: [
                    { name: "occupation", type: "string" },
                    { name: "bloodGroup", type: "string", description: "Must exactly match: A+, A-, B+, B-, O+, O-, AB+, AB-" },
                    { name: "idType", type: "string", description: "Must exactly match: Aadhar, PAN Card, Voter ID" },
                    { name: "idNumber", type: "string" },
                ],
            },
        ],
        handler: async (args: Partial<RegistrationData>) => {
            console.log("Fill registration form called with:", args);
            setStatus("Auto-filling form...");
            setFormData((prev) => {
                const newData = { ...prev };
                if (args.contactInfo) {
                    newData.contactInfo = { ...prev.contactInfo, ...args.contactInfo };
                    setIsContactExpanded(true);
                }
                if (args.basicInfo) {
                    newData.basicInfo = { ...prev.basicInfo, ...args.basicInfo };
                    setIsBasicInfoExpanded(true);
                }
                if (args.otherInfo) {
                    newData.otherInfo = { ...prev.otherInfo, ...args.otherInfo };
                    setIsOtherInfoExpanded(true);
                }
                return newData;
            });
            setTimeout(() => setStatus(null), 2000); // Clear status after 2 seconds
            return "Form updated.";
        },
    });

    const handleChange = (section: keyof RegistrationData, field: string, value: any) => {
        setFormData((prev) => {
            const newData = { ...prev };
            (newData[section] as any)[field] = value;
            return newData;
        });
    };

    const submitForm = async () => {
        setStatus("Saving...");
        const result = await saveRegistration(formData);
        setStatus(result.message);

        if (result.success) {
            // Optional: short delay to let them see the success message
            setTimeout(() => {
                router.push('/');
            }, 1500);
        }

        return result.message;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await submitForm();
    };

    useCopilotAction({
        name: "confirm_registration",
        description: "Confirm and submit the registration form.",
        parameters: [],
        handler: async () => {
            const result = await submitForm();
            return `Registration submitted.Status: ${result} `;
        },
    });

    return (
        <form onSubmit={handleSubmit} className="space-y-8 pb-32">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-foreground tracking-tight">Patient Registration</h1>
                <p className="text-muted-foreground mt-2">Enter patient details to register for Ayurvedic consultation.</p>
            </div>

            {/* Basic Info Section */}
            <Section title="Basic Info" isExpanded={isBasicInfoExpanded} onToggle={() => setIsBasicInfoExpanded(!isBasicInfoExpanded)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormInput label="First Name" required value={formData.basicInfo.firstName} onChange={(v: string) => handleChange("basicInfo", "firstName", v)} placeholder="First Name" />
                    <FormInput label="Last Name" value={formData.basicInfo.lastName} onChange={(v: string) => handleChange("basicInfo", "lastName", v)} placeholder="Last Name" />

                    <FormRadioGroup
                        label="Gender"
                        required
                        options={["Male", "Female", "Transgender"]}
                        value={formData.basicInfo.gender}
                        onChange={(v: string) => handleChange("basicInfo", "gender", v)}
                    />

                    <FormInput
                        label="Age"
                        required
                        type="number"
                        value={formData.basicInfo.age}
                        onChange={(v: string) => handleChange("basicInfo", "age", v)}
                        placeholder="Age in Years"
                    />

                    <FormRadioGroup
                        label="Marital Status"
                        required
                        options={["Married", "Unmarried", "Divorcee", "Widow"]}
                        value={formData.basicInfo.maritalStatus}
                        onChange={(v: string) => handleChange("basicInfo", "maritalStatus", v)}
                    />
                </div>
            </Section>

            {/* Contact Info Section */}
            <Section title="Contact Info" isExpanded={isContactExpanded} onToggle={() => setIsContactExpanded(!isContactExpanded)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormInput label="Mobile Number" required value={formData.contactInfo.mobileNumber} onChange={(v: string) => handleChange("contactInfo", "mobileNumber", v)} placeholder="10-digit Mobile Number" />

                    <div className="md:col-span-2">
                        <FormTextArea label="Address" value={formData.contactInfo.address} onChange={(v: string) => handleChange("contactInfo", "address", v)} placeholder="Complete Address (Street, Sector, Landmark)" />
                    </div>

                    <FormSelect label="State" required options={["Delhi", "Maharashtra", "Karnataka", "Gujarat", "Uttar Pradesh"]} value={formData.contactInfo.state} onChange={(v: string) => handleChange("contactInfo", "state", v)} />
                    <FormSelect label="City" required options={["New Delhi", "Mumbai", "Bangalore", "Ahmedabad", "Lucknow"]} value={formData.contactInfo.city} onChange={(v: string) => handleChange("contactInfo", "city", v)} />
                    <FormInput label="Pincode" value={formData.contactInfo.pincode} onChange={(v: string) => handleChange("contactInfo", "pincode", v)} placeholder="6-digit Pincode" />
                </div>
            </Section>

            {/* Other Info Section */}
            <Section title="Other Info" isExpanded={isOtherInfoExpanded} onToggle={() => setIsOtherInfoExpanded(!isOtherInfoExpanded)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormInput label="Occupation" value={formData.otherInfo.occupation} onChange={(v: string) => handleChange("otherInfo", "occupation", v)} placeholder="Current Occupation" />
                    <FormSelect label="Blood Group" options={["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]} value={formData.otherInfo.bloodGroup} onChange={(v: string) => handleChange("otherInfo", "bloodGroup", v)} />

                    <div className="grid grid-cols-2 gap-4 md:col-span-2">
                        <FormSelect label="ID Type" options={["Aadhar", "PAN Card", "Voter ID"]} value={formData.otherInfo.idType} onChange={(v: string) => handleChange("otherInfo", "idType", v)} />
                        <FormInput label="ID Number" value={formData.otherInfo.idNumber} onChange={(v: string) => handleChange("otherInfo", "idNumber", v)} placeholder="ID Number (e.g. 12-digit Aadhar)" />
                    </div>
                </div>
            </Section>

            <div className="flex flex-col md:flex-row items-center justify-between pt-4 sticky bottom-0 bg-background/90 backdrop-blur-md pb-6 border-t border-border mt-8 z-50 px-2 gap-4">
                {/* Left side: Status */}
                <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                    {status && (
                        <span className="text-primary font-medium bg-primary/10 px-4 py-2 rounded-full text-sm border border-primary/20">
                            {status}
                        </span>
                    )}
                </div>

                {/* Right side: Submit */}
                <div className="flex items-center gap-4 w-full md:w-auto justify-end">
                    <button
                        type="submit"
                        className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3 h-12 rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 font-bold tracking-wide uppercase text-sm w-full md:w-auto whitespace-nowrap"
                    >
                        Complete Registration
                    </button>
                </div>
            </div>

            {/* --- Chat Overlay Controls (Injected natively INSIDE the Copilot Text Input area) --- */}
            {chatInputNode && createPortal(
                <>
                    {/* Restart Chat Button: Above text box on the right side */}
                    <div className="absolute -top-12 right-0 z-[1000]">
                        <button
                            type="button"
                            onClick={handleNewChat}
                            className="flex items-center justify-center w-8 h-8 bg-background border border-border shadow-sm rounded-full text-muted-foreground hover:text-primary transition-all duration-200"
                            title="Restart Chat"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Language Selector: Inside text box, bottom left corner */}
                    <div className="absolute bottom-1.5 left-1 z-[1000] pointer-events-auto">
                        <LanguageSelector
                            selectedLanguage={selectedLanguage}
                            onLanguageChange={setSelectedLanguage}
                        />
                    </div>

                    {/* Voice Input: Inside text box, besides send button (right side) */}
                    <div className="absolute bottom-1.5 right-12 z-[1000] pointer-events-auto">
                        <VoiceInputButton
                            onTranscript={handleVoiceTranscript}
                            onError={(err) => setVoiceError(err)}
                            onStateChange={setIsListening}
                            language={selectedLanguage}
                            isActive={isChatOpen}
                        />
                        {isListening && (
                            <span className="absolute top-0 right-0 flex h-2 w-2 -mt-0.5 -mr-0.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-destructive"></span>
                            </span>
                        )}
                    </div>
                </>,
                chatInputNode
            )}

            {/* Voice Error Display */}
            {isChatOpen && voiceError && (
                <div className="fixed bottom-[130px] right-4 md:right-auto md:w-[350px] z-[1000] px-4 pointer-events-none flex justify-end">
                    <div className="bg-destructive/10 text-destructive px-3 py-1.5 rounded-lg border border-destructive/20 shadow-sm text-xs animate-in fade-in slide-in-from-bottom-4 pointer-events-auto">
                        {voiceError}
                    </div>
                </div>
            )}
        </form>
    );
}

// --- Reusable UI Components ---

function Section({ title, isExpanded, onToggle, children }: { title: string; isExpanded: boolean; onToggle: () => void; children: React.ReactNode }) {
    return (
        <div className="bg-card rounded-2xl shadow-sm border border-border overflow-hidden transition-shadow hover:shadow-md">
            <div
                className={`px-8 py-5 flex justify-between items-center cursor-pointer select-none transition-colors duration-200 ${isExpanded ? 'bg-card border-b border-border' : 'bg-muted/30 hover:bg-muted/50'} `}
                onClick={onToggle}
            >
                <div className="flex items-center gap-3">
                    <div className={`w-1 h-6 rounded-full ${isExpanded ? 'bg-primary' : 'bg-muted-foreground/30'} `}></div>
                    <h2 className={`font-bold uppercase tracking-wide text-sm ${isExpanded ? 'text-card-foreground' : 'text-muted-foreground'} `}>{title}</h2>
                </div>
                {isExpanded ? <Minus className="text-primary w-5 h-5" /> : <Plus className="text-muted-foreground w-5 h-5" />}
            </div>
            {isExpanded && <div className="p-8 animate-in fade-in slide-in-from-top-4 duration-300">{children}</div>}
        </div>
    );
}

function FormInput({ label, value, onChange, placeholder, type = "text", required, disabled, readOnly, className, helperText }: any) {
    return (
        <div className="flex flex-col gap-2 w-full">
            <label className="text-sm font-semibold text-foreground flex justify-between">
                <span>{label} {required && <span className="text-destructive">*</span>}</span>
            </label>
            <input
                type={type}
                placeholder={placeholder}
                className={`w-full h-12 px-4 border border-input rounded-lg focus:ring-2 focus:ring-ring border-input focus:border-ring outline-none transition-all text-foreground bg-background placeholder-muted-foreground shadow-sm ${className} ${disabled ? 'bg-muted text-muted-foreground' : ''} `}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                readOnly={readOnly}
            />
            {helperText && <p className="text-xs text-gray-500 ml-1">{helperText}</p>}
        </div>
    );
}

function FormTextArea({ label, value, onChange, placeholder, disabled }: any) {
    return (
        <div className="flex flex-col gap-2 w-full">
            <label className="text-sm font-semibold text-foreground">{label}</label>
            <textarea
                placeholder={placeholder}
                rows={3}
                className={`w-full p-4 border border-input rounded-lg focus:ring-2 focus:ring-ring border-input focus:border-ring outline-none transition-all text-foreground bg-background placeholder-muted-foreground shadow-sm resize-none ${disabled ? 'bg-muted text-muted-foreground' : ''} `}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
            />
        </div>
    );
}

function FormSelect({ label, value, onChange, options, required, disabled }: any) {
    return (
        <div className="flex flex-col gap-2 w-full relative">
            <label className="text-sm font-semibold text-foreground">{label} {required && <span className="text-destructive">*</span>}</label>
            <div className="relative">
                <select
                    className={`w-full h-12 px-4 border border-input rounded-lg focus:ring-2 focus:ring-ring border-input focus:border-ring outline-none transition-all text-foreground bg-background shadow-sm appearance-none cursor-pointer ${disabled ? 'bg-muted text-muted-foreground' : ''} `}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                >
                    <option value="">Select {label}</option>
                    {options.map((opt: string) => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                </select>
                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>
        </div>
    );
}

function FormRadioGroup({ label, value, onChange, options, required }: any) {
    return (
        <div className="flex flex-col gap-3 w-full">
            <label className="text-sm font-semibold text-foreground">{label} {required && <span className="text-destructive">*</span>}</label>
            <div className="flex flex-wrap gap-3">
                {options.map((opt: string) => (
                    <label
                        key={opt}
                        className={`
                            flex items-center gap-2 px-4 py-2.5 rounded-lg border cursor-pointer transition-all select-none text-sm font-medium
                            ${value === opt
                                ? 'bg-primary/5 border-primary text-primary shadow-sm ring-1 ring-primary'
                                : 'bg-background border-border text-muted-foreground hover:bg-muted/50 hover:border-border'
                            }
`}
                    >
                        <input
                            type="radio"
                            name={label} // simplistic unique name
                            value={opt}
                            checked={value === opt}
                            onChange={(e) => onChange(e.target.value)}
                            className="hidden" // hide default radio
                        />
                        {/* Custom radio indicator */}
                        <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${value === opt ? 'border-primary' : 'border-muted-foreground'} `}>
                            {value === opt && <div className="w-2 h-2 rounded-full bg-primary"></div>}
                        </div>
                        {opt}
                    </label>
                ))}
            </div>
        </div>
    );
}

function calculateAge(dob: string) {
    if (!dob) return "";
    const birthDate = new Date(dob);
    const today = new Date();
    let years = today.getFullYear() - birthDate.getFullYear();
    let months = today.getMonth() - birthDate.getMonth();
    let days = today.getDate() - birthDate.getDate();
    if (days < 0) {
        months--;
        days += new Date(today.getFullYear(), today.getMonth(), 0).getDate();
    }
    if (months < 0) {
        years--;
        months += 12;
    }
    return `${years} Years ${months} Months ${days} Days`;
}
