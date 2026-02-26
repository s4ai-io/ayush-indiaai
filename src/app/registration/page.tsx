"use client";

import { CopilotKit, useCopilotChat } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import "@copilotkit/react-ui/styles.css";
import { saveRegistration } from "../actions/saveRegistration";
import {
    Minus, Plus, ChevronDown, RefreshCw,
    User, Phone, FileText, Stethoscope,
    CheckCircle2, AlertCircle, Loader2,
    MapPin, Briefcase, Droplets, CreditCard, X
} from "lucide-react";
import { VoiceInputButton } from "@/components/VoiceInputButton";
import { LanguageSelector } from "@/components/LanguageSelector";
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
        age: string;
        maritalStatus: string;
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
    contactInfo: { mobileNumber: "", address: "", city: "", state: "", pincode: "" },
    basicInfo: { firstName: "", lastName: "", gender: "", age: "", maritalStatus: "" },
    otherInfo: { occupation: "", bloodGroup: "", idType: "", idNumber: "" },
};

type StatusType = "info" | "error" | "success" | "loading";

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
                <div className="flex-1 h-full min-h-screen overflow-y-auto bg-gradient-to-br from-background via-muted/10 to-background">
                    <div className="max-w-4xl mx-auto px-4 py-6 md:px-8 md:py-10">
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
    const [statusType, setStatusType] = useState<StatusType>("info");
    const [isBasicInfoExpanded, setIsBasicInfoExpanded] = useState(true);
    const [isContactExpanded, setIsContactExpanded] = useState(true);
    const [isOtherInfoExpanded, setIsOtherInfoExpanded] = useState(true);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [isListening, setIsListening] = useState(false);
    const [selectedLanguage, setSelectedLanguage] = useState("hi-IN");
    const [chatInputNode, setChatInputNode] = useState<Element | null>(null);
    const [showNewChatConfirm, setShowNewChatConfirm] = useState(false);
    const router = useRouter();

    useEffect(() => {
        if (!isChatOpen) { setChatInputNode(null); return; }
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

    const handleNewChat = (clearForm: boolean) => {
        resetChat();
        if (clearForm) setFormData(INITIAL_DATA);
        setShowNewChatConfirm(false);
    };

    const handleVoiceTranscript = async (transcript: string) => {
        setVoiceError(null);
        await appendMessage(new TextMessage({ role: MessageRole.User, content: transcript }));
    };

    useCopilotReadable({ description: "The current state of the registration form.", value: formData });

    useCopilotAction({
        name: "fill_registration_form",
        description: "Fill the registration form with user details.",
        parameters: [
            {
                name: "contactInfo", type: "object",
                attributes: [
                    { name: "mobileNumber", type: "string", description: "10-digit mobile phone number. Extract ONLY digits, ignore spaces, hyphens, +91." },
                    { name: "address", type: "string", description: "Residential address" },
                    { name: "city", type: "string", description: "Must exactly match: New Delhi, Mumbai, Bangalore, Ahmedabad, Lucknow" },
                    { name: "state", type: "string", description: "Must exactly match: Delhi, Maharashtra, Karnataka, Gujarat, Uttar Pradesh" },
                    { name: "pincode", type: "string", description: "6-digit postal pincode" },
                ],
            },
            {
                name: "basicInfo", type: "object",
                attributes: [
                    { name: "firstName", type: "string" },
                    { name: "lastName", type: "string" },
                    { name: "gender", type: "string", description: "Male, Female, or Transgender" },
                    { name: "age", type: "string" },
                    { name: "maritalStatus", type: "string", description: "Must exactly match: Married, Unmarried, Divorcee, Widow" },
                ],
            },
            {
                name: "otherInfo", type: "object",
                attributes: [
                    { name: "occupation", type: "string" },
                    { name: "bloodGroup", type: "string", description: "Must exactly match: A+, A-, B+, B-, O+, O-, AB+, AB-" },
                    { name: "idType", type: "string", description: "Must exactly match: Aadhar, PAN Card, Voter ID" },
                    { name: "idNumber", type: "string" },
                ],
            },
        ],
        handler: async (args: Partial<RegistrationData>) => {
            setStatus("Auto-filling form…");
            setStatusType("loading");
            const updatedData = { ...formData };
            if (args.basicInfo) {
                updatedData.basicInfo = { ...updatedData.basicInfo, ...args.basicInfo };
                updatedData.basicInfo.age = String(Number(updatedData.basicInfo.age) || 0);
                setIsBasicInfoExpanded(true);
            }
            if (args.contactInfo) {
                let mobile = args.contactInfo.mobileNumber || "";
                if (mobile) {
                    mobile = mobile.replace(/\D/g, '');
                    if (mobile.length > 10) mobile = mobile.substring(mobile.length - 10);
                }
                args.contactInfo.mobileNumber = mobile;
                updatedData.contactInfo = { ...updatedData.contactInfo, ...args.contactInfo };
                setIsContactExpanded(true);
            }
            if (args.otherInfo) {
                updatedData.otherInfo = { ...updatedData.otherInfo, ...args.otherInfo };
                setIsOtherInfoExpanded(true);
            }
            setFormData(updatedData);
            setTimeout(() => setStatus(null), 2000);
            return "Registration form updated successfully.";
        },
    });

    const handleChange = (section: keyof RegistrationData, field: string, value: any) => {
        setFormData((prev) => {
            const newData = { ...prev };
            (newData[section] as any)[field] = value;
            return newData;
        });
    };

    const validateForm = (): string | null => {
        if (!formData.basicInfo.firstName.trim()) return "Please enter the patient's first name.";
        if (!formData.basicInfo.gender) return "Please select a gender.";
        if (!formData.basicInfo.maritalStatus) return "Please select a marital status.";
        if (Number(formData.basicInfo.age) <= 0 || Number(formData.basicInfo.age) > 120) return "Please enter a valid age (1–120).";
        if (!formData.contactInfo.state) return "Please select a state.";
        if (!formData.contactInfo.city) return "Please select a city.";
        const mobileRegex = /^[6-9]\d{9}$/;
        if (!mobileRegex.test(formData.contactInfo.mobileNumber)) return "Please enter a valid 10-digit Indian mobile number.";
        const pincodeRegex = /^[1-9][0-9]{5}$/;
        if (formData.contactInfo.pincode && !pincodeRegex.test(formData.contactInfo.pincode)) return "Please enter a valid 6-digit PIN code.";
        const idType = formData.otherInfo.idType;
        const idNumber = formData.otherInfo.idNumber.toUpperCase();
        if (idType && idNumber) {
            if (idType === "Aadhar" && !/^\d{12}$/.test(idNumber)) return "Please enter a valid 12-digit Aadhaar number.";
            if (idType === "PAN Card" && !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(idNumber)) return "Please enter a valid PAN number (e.g., ABCDE1234F).";
            if (idType === "Voter ID" && !/^[A-Z]{3}[0-9]{7}$/.test(idNumber)) return "Please enter a valid Voter ID (e.g., ABC1234567).";
        }
        return null;
    };

    const submitForm = async () => {
        setStatus("Saving registration…");
        setStatusType("loading");
        const dataToSave = { ...formData };
        const idType = dataToSave.otherInfo.idType;
        if (idType === "PAN Card" || idType === "Voter ID") {
            dataToSave.otherInfo = { ...dataToSave.otherInfo, idNumber: dataToSave.otherInfo.idNumber.toUpperCase() };
        }
        const result = await saveRegistration(dataToSave);
        setStatus(result.message);
        setStatusType(result.success ? "success" : "error");
        if (result.success) setTimeout(() => router.push('/'), 1500);
        return result.message;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const error = validateForm();
        if (error) { setStatus(error); setStatusType("error"); return; }
        await submitForm();
    };

    useCopilotAction({
        name: "confirm_registration",
        description: "Confirm and submit the registration form.",
        parameters: [],
        handler: async () => {
            const error = validateForm();
            if (error) { setStatus(error); setStatusType("error"); return `Validation failed: ${error}`; }
            const result = await submitForm();
            return `Registration submitted. Status: ${result}`;
        },
    });

    return (
        <form onSubmit={handleSubmit} className="space-y-5 pb-6">

            {/* ── Page Header ── */}
            <div className="mb-6">
                <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                        <Stethoscope className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-foreground tracking-tight leading-none">Patient Registration</h1>
                        <p className="text-sm text-muted-foreground mt-0.5">Fill in details below or use the AI assistant →</p>
                    </div>
                </div>
                {/* Step pills */}
                <div className="flex gap-2 flex-wrap">
                    {[
                        { label: "Basic Info", icon: User, filled: !!(formData.basicInfo.firstName && formData.basicInfo.gender) },
                        { label: "Contact", icon: Phone, filled: !!(formData.contactInfo.mobileNumber && formData.contactInfo.state) },
                        { label: "Other Info", icon: FileText, filled: false },
                    ].map(({ label, icon: Icon, filled }) => (
                        <div key={label} className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all ${filled ? 'bg-primary/10 border-primary/30 text-primary' : 'bg-muted/40 border-border text-muted-foreground'}`}>
                            <Icon className="w-3 h-3" />
                            {label}
                            {filled && <CheckCircle2 className="w-3 h-3" />}
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Basic Info ── */}
            <Section
                title="Basic Info"
                icon={<User className="w-4 h-4" />}
                isExpanded={isBasicInfoExpanded}
                onToggle={() => setIsBasicInfoExpanded(!isBasicInfoExpanded)}
            >
                {/* Name row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput
                        label="First Name" required
                        value={formData.basicInfo.firstName}
                        onChange={(v: string) => handleChange("basicInfo", "firstName", v)}
                        placeholder="e.g. Rahul"
                    />
                    <FormInput
                        label="Last Name"
                        value={formData.basicInfo.lastName}
                        onChange={(v: string) => handleChange("basicInfo", "lastName", v)}
                        placeholder="e.g. Sharma"
                    />
                </div>

                {/* Gender + Age */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-xs font-semibold text-foreground uppercase tracking-wide">
                            Gender <span className="text-destructive">*</span>
                        </label>
                        <div className="flex gap-2 flex-wrap">
                            {["Male", "Female", "Transgender"].map((opt) => (
                                <button
                                    key={opt}
                                    type="button"
                                    onClick={() => handleChange("basicInfo", "gender", opt)}
                                    className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all duration-150 ${formData.basicInfo.gender === opt
                                        ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                                        : 'bg-background border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                                        }`}
                                >
                                    {opt}
                                </button>
                            ))}
                        </div>
                    </div>
                    <FormInput
                        label="Age" required type="number"
                        value={formData.basicInfo.age}
                        onChange={(v: string) => handleChange("basicInfo", "age", v)}
                        placeholder="Years"
                    />
                </div>

                {/* Marital Status */}
                <div className="mt-4">
                    <label className="text-xs font-semibold text-foreground uppercase tracking-wide mb-2 block">
                        Marital Status <span className="text-destructive">*</span>
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {["Married", "Unmarried", "Divorcee", "Widow"].map((opt) => (
                            <button
                                key={opt}
                                type="button"
                                onClick={() => handleChange("basicInfo", "maritalStatus", opt)}
                                className={`py-2.5 px-3 rounded-lg border text-sm font-medium transition-all duration-150 text-center ${formData.basicInfo.maritalStatus === opt
                                    ? 'bg-primary text-primary-foreground border-primary shadow-sm'
                                    : 'bg-background border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                                    }`}
                            >
                                {opt}
                            </button>
                        ))}
                    </div>
                </div>
            </Section>

            {/* ── Contact Info ── */}
            <Section
                title="Contact Info"
                icon={<Phone className="w-4 h-4" />}
                isExpanded={isContactExpanded}
                onToggle={() => setIsContactExpanded(!isContactExpanded)}
            >
                <FormInput
                    label="Mobile Number" required
                    value={formData.contactInfo.mobileNumber}
                    onChange={(v: string) => handleChange("contactInfo", "mobileNumber", v)}
                    placeholder="10-digit mobile number"
                    prefix={<Phone className="w-4 h-4 text-muted-foreground" />}
                />

                <div className="mt-4">
                    <FormTextArea
                        label="Address"
                        value={formData.contactInfo.address}
                        onChange={(v: string) => handleChange("contactInfo", "address", v)}
                        placeholder="Street, Sector, Landmark…"
                        icon={<MapPin className="w-4 h-4 text-muted-foreground" />}
                    />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                    <FormSelect
                        label="State" required
                        options={["Delhi", "Maharashtra", "Karnataka", "Gujarat", "Uttar Pradesh"]}
                        value={formData.contactInfo.state}
                        onChange={(v: string) => handleChange("contactInfo", "state", v)}
                    />
                    <FormSelect
                        label="City" required
                        options={["New Delhi", "Mumbai", "Bangalore", "Ahmedabad", "Lucknow"]}
                        value={formData.contactInfo.city}
                        onChange={(v: string) => handleChange("contactInfo", "city", v)}
                    />
                </div>

                <div className="mt-4 max-w-xs">
                    <FormInput
                        label="Pincode"
                        value={formData.contactInfo.pincode}
                        onChange={(v: string) => handleChange("contactInfo", "pincode", v)}
                        placeholder="6-digit PIN"
                        prefix={<MapPin className="w-4 h-4 text-muted-foreground" />}
                    />
                </div>
            </Section>

            {/* ── Other Info ── */}
            <Section
                title="Other Info"
                icon={<FileText className="w-4 h-4" />}
                isExpanded={isOtherInfoExpanded}
                onToggle={() => setIsOtherInfoExpanded(!isOtherInfoExpanded)}
            >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormInput
                        label="Occupation"
                        value={formData.otherInfo.occupation}
                        onChange={(v: string) => handleChange("otherInfo", "occupation", v)}
                        placeholder="e.g. Engineer, Teacher…"
                        prefix={<Briefcase className="w-4 h-4 text-muted-foreground" />}
                    />
                    <FormSelect
                        label="Blood Group"
                        options={["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]}
                        value={formData.otherInfo.bloodGroup}
                        onChange={(v: string) => handleChange("otherInfo", "bloodGroup", v)}
                        icon={<Droplets className="w-4 h-4 text-muted-foreground" />}
                    />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                    <FormSelect
                        label="ID Type"
                        options={["Aadhar", "PAN Card", "Voter ID"]}
                        value={formData.otherInfo.idType}
                        onChange={(v: string) => handleChange("otherInfo", "idType", v)}
                        icon={<CreditCard className="w-4 h-4 text-muted-foreground" />}
                    />
                    <FormInput
                        label="ID Number"
                        value={formData.otherInfo.idNumber}
                        onChange={(v: string) => handleChange("otherInfo", "idNumber", v)}
                        placeholder={
                            formData.otherInfo.idType === "Aadhar" ? "12-digit Aadhaar" :
                                formData.otherInfo.idType === "PAN Card" ? "e.g. ABCDE1234F" :
                                    formData.otherInfo.idType === "Voter ID" ? "e.g. ABC1234567" :
                                        "ID Number"
                        }
                        prefix={<CreditCard className="w-4 h-4 text-muted-foreground" />}
                    />
                </div>
            </Section>

            {/* ── Bottom Bar — scoped to form column, does not overlap sidebar ── */}
            <div className="sticky bottom-0 z-30 bg-background/90 backdrop-blur-lg border-t border-border rounded-b-xl -mx-0">
                <div className="px-4 py-3 flex flex-col sm:flex-row items-center gap-3">
                    {/* Status message */}
                    <div className="flex-1 w-full">
                        {status && (
                            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border ${statusType === "error"
                                ? "bg-destructive/10 text-destructive border-destructive/20"
                                : statusType === "success"
                                    ? "bg-green-500/10 text-green-600 border-green-500/20"
                                    : statusType === "loading"
                                        ? "bg-primary/10 text-primary border-primary/20"
                                        : "bg-muted text-muted-foreground border-border"
                                }`}>
                                {statusType === "loading" && <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
                                {statusType === "error" && <AlertCircle className="w-4 h-4 shrink-0" />}
                                {statusType === "success" && <CheckCircle2 className="w-4 h-4 shrink-0" />}
                                <span className="truncate">{status}</span>
                            </div>
                        )}
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        className="w-full sm:w-auto flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 active:scale-[0.98] text-primary-foreground px-8 py-2.5 rounded-xl font-bold text-sm tracking-wide uppercase shadow-md hover:shadow-lg transition-all duration-200 shrink-0"
                    >
                        <CheckCircle2 className="w-4 h-4" />
                        Complete Registration
                    </button>
                </div>
            </div>

            {/* ── All chat controls portalled into .copilotKitInput ── */}
            {chatInputNode && createPortal(
                <>
                    {/* New Chat button + inline confirm — sits just above the input box */}
                    <div className="absolute -top-11 left-0 right-0 flex items-center justify-center z-[1000] pointer-events-auto">
                        {!showNewChatConfirm ? (
                            <button
                                type="button"
                                onClick={() => setShowNewChatConfirm(true)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-background/90 backdrop-blur border border-border text-muted-foreground hover:text-primary hover:border-primary/50 hover:bg-primary/5 shadow-sm transition-all duration-150"
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                                New Chat
                            </button>
                        ) : (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-background/95 backdrop-blur border border-border shadow-md text-xs font-medium">
                                <span className="text-muted-foreground">Clear form too?</span>
                                <button
                                    type="button"
                                    onClick={() => handleNewChat(true)}
                                    className="px-2.5 py-1 rounded-full bg-destructive/10 text-destructive hover:bg-destructive/20 border border-destructive/20 transition-colors"
                                >Yes, clear</button>
                                <button
                                    type="button"
                                    onClick={() => handleNewChat(false)}
                                    className="px-2.5 py-1 rounded-full bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20 transition-colors"
                                >Keep form</button>
                                <button
                                    type="button"
                                    onClick={() => setShowNewChatConfirm(false)}
                                    className="w-5 h-5 flex items-center justify-center rounded-full hover:bg-muted text-muted-foreground transition-colors"
                                ><X className="w-3 h-3" /></button>
                            </div>
                        )}
                    </div>

                    {/* Language selector — left of input */}
                    <div className="absolute bottom-1.5 left-1 z-[1000] pointer-events-auto">
                        <LanguageSelector selectedLanguage={selectedLanguage} onLanguageChange={setSelectedLanguage} />
                    </div>
                    {/* Voice button — right of input */}
                    <div className="absolute bottom-1.5 right-12 z-[1000] pointer-events-auto">
                        <VoiceInputButton
                            onTranscript={handleVoiceTranscript}
                            onError={(err) => setVoiceError(err)}
                            language={selectedLanguage}
                        />
                        {isListening && (
                            <span className="absolute top-0 right-0 flex h-2 w-2 -mt-0.5 -mr-0.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-destructive opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-destructive" />
                            </span>
                        )}
                    </div>
                </>,
                chatInputNode
            )}

            {/* Voice Error */}
            {isChatOpen && voiceError && (
                <div className="fixed bottom-24 right-4 z-[1000]">
                    <div className="bg-destructive/10 text-destructive px-3 py-1.5 rounded-lg border border-destructive/20 shadow-sm text-xs animate-in fade-in slide-in-from-bottom-4">
                        {voiceError}
                    </div>
                </div>
            )}
        </form>
    );
}

// ── Section Card ──────────────────────────────────────────────────────────────

function Section({
    title, icon, isExpanded, onToggle, children,
}: {
    title: string;
    icon: React.ReactNode;
    isExpanded: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}) {
    return (
        <div className={`rounded-2xl border bg-card shadow-sm transition-shadow hover:shadow-md overflow-hidden ${isExpanded ? 'border-border' : 'border-border/60'}`}>
            {/* Header */}
            <button
                type="button"
                onClick={onToggle}
                className={`w-full flex items-center justify-between px-5 py-4 transition-colors duration-200 ${isExpanded ? 'bg-card' : 'bg-muted/30 hover:bg-muted/50'}`}
            >
                <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${isExpanded ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                        {icon}
                    </div>
                    <span className={`font-bold text-sm uppercase tracking-wider ${isExpanded ? 'text-foreground' : 'text-muted-foreground'}`}>{title}</span>
                </div>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${isExpanded ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                    {isExpanded ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                </div>
            </button>

            {/* Body */}
            {isExpanded && (
                <div className="px-5 pt-2 pb-6 border-t border-border/60 animate-in fade-in slide-in-from-top-2 duration-200">
                    {children}
                </div>
            )}
        </div>
    );
}

// ── FormInput ─────────────────────────────────────────────────────────────────

function FormInput({ label, value, onChange, placeholder, type = "text", required, disabled, prefix }: {
    label: string; value: string; onChange: (v: string) => void; placeholder?: string;
    type?: string; required?: boolean; disabled?: boolean; prefix?: React.ReactNode;
}) {
    return (
        <div className="flex flex-col gap-1.5 w-full">
            <label className="text-xs font-semibold text-foreground uppercase tracking-wide">
                {label} {required && <span className="text-destructive">*</span>}
            </label>
            <div className="relative">
                {prefix && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                        {prefix}
                    </div>
                )}
                <input
                    type={type}
                    placeholder={placeholder}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    className={`w-full h-11 border border-input rounded-lg text-sm text-foreground bg-background placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-150 shadow-sm
                        ${prefix ? 'pl-9 pr-4' : 'px-4'}
                        ${disabled ? 'bg-muted text-muted-foreground cursor-not-allowed' : ''}
                    `}
                />
            </div>
        </div>
    );
}

// ── FormTextArea ──────────────────────────────────────────────────────────────

function FormTextArea({ label, value, onChange, placeholder, disabled, icon }: {
    label: string; value: string; onChange: (v: string) => void;
    placeholder?: string; disabled?: boolean; icon?: React.ReactNode;
}) {
    return (
        <div className="flex flex-col gap-1.5 w-full">
            <label className="text-xs font-semibold text-foreground uppercase tracking-wide flex items-center gap-1.5">
                {icon}{label}
            </label>
            <textarea
                placeholder={placeholder}
                rows={3}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled}
                className={`w-full p-3 border border-input rounded-lg text-sm text-foreground bg-background placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-150 shadow-sm resize-none ${disabled ? 'bg-muted cursor-not-allowed' : ''}`}
            />
        </div>
    );
}

// ── FormSelect ────────────────────────────────────────────────────────────────

function FormSelect({ label, value, onChange, options, required, disabled, icon }: {
    label: string; value: string; onChange: (v: string) => void;
    options: string[]; required?: boolean; disabled?: boolean; icon?: React.ReactNode;
}) {
    return (
        <div className="flex flex-col gap-1.5 w-full">
            <label className="text-xs font-semibold text-foreground uppercase tracking-wide">
                {label} {required && <span className="text-destructive">*</span>}
            </label>
            <div className="relative">
                {icon && (
                    <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                        {icon}
                    </div>
                )}
                <select
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    className={`w-full h-11 border border-input rounded-lg text-sm text-foreground bg-background focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-150 shadow-sm appearance-none cursor-pointer
                        ${icon ? 'pl-9 pr-9' : 'pl-4 pr-9'}
                        ${disabled ? 'bg-muted cursor-not-allowed' : ''}
                        ${value === '' ? 'text-muted-foreground/70' : ''}
                    `}
                >
                    <option value="">Select {label}</option>
                    {options.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>
        </div>
    );
}
