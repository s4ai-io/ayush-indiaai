"use client";

import { useState } from "react";
import { saveRegistration } from "../actions/saveRegistration";
import {
    Minus, Plus, ChevronDown,
    User, Phone, FileText, Stethoscope,
    CheckCircle2, AlertCircle, Loader2,
    MapPin, Briefcase, Droplets, CreditCard
} from "lucide-react";
import { GemmaVoiceChatPanel } from "@/components/GemmaVoiceChatPanel";
import { useRouter } from "next/navigation";
import { INDIAN_STATES, INDIAN_STATE_CITY_MAP } from "@/data/indianLocations";

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
    const [proposedData, setProposedData] = useState<any>(null);

    // Merges newly-extracted fields from the Gemma-4 assistant into
    // proposedData for the user to review before accepting into the form.
    const applyProposedRegistrationData = (args: any) => {
        setProposedData((prev: any) => {
            const mergeObj = (existing: any, incoming: any) => {
                if (!incoming) return existing || undefined;
                const merged = { ...(existing || {}) };
                for (const key in incoming) {
                    if (incoming[key] !== null && incoming[key] !== undefined && incoming[key] !== '') {
                        merged[key] = incoming[key];
                    }
                }
                return merged;
            };

            // Format mobile number before merging. The model can return this as
            // a number even though the schema declares it a string.
            const incomingContact = { ...args.contactInfo };
            if (incomingContact.mobileNumber !== undefined && incomingContact.mobileNumber !== null) {
                let mobile = String(incomingContact.mobileNumber).replace(/\D/g, '');
                if (mobile.length > 10) mobile = mobile.substring(mobile.length - 10);
                incomingContact.mobileNumber = mobile;
            }

            // Format age
            const incomingBasic = { ...args.basicInfo };
            if (incomingBasic.age) {
                incomingBasic.age = String(Number(incomingBasic.age) || 0);
            }

            return {
                basicInfo: mergeObj(prev?.basicInfo, incomingBasic),
                contactInfo: mergeObj(prev?.contactInfo, incomingContact),
                otherInfo: mergeObj(prev?.otherInfo, args.otherInfo),
            };
        });
    };

    return (
        <div className="min-h-screen w-full md:pr-96 bg-gradient-to-br from-background via-muted/10 to-background">
            <div className="max-w-4xl mx-auto px-4 py-6 md:px-8 md:py-10">
                <RegistrationForm proposedData={proposedData} setProposedData={setProposedData} />
            </div>
            <GemmaVoiceChatPanel flow="registration" onExtracted={applyProposedRegistrationData} />
        </div>
    );
}

function RegistrationForm({ proposedData, setProposedData }: { proposedData: any; setProposedData: (v: any) => void }) {
    const [formData, setFormData] = useState<RegistrationData>(INITIAL_DATA);
    const [status, setStatus] = useState<string | null>(null);
    const [statusType, setStatusType] = useState<StatusType>("info");
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
    const [isBasicInfoExpanded, setIsBasicInfoExpanded] = useState(true);
    const [isContactExpanded, setIsContactExpanded] = useState(true);
    const [isOtherInfoExpanded, setIsOtherInfoExpanded] = useState(true);
    const router = useRouter();

    const handleAcceptProposed = () => {
        if (!proposedData) return;

        setFormData(prev => ({
            ...prev,
            basicInfo: { ...prev.basicInfo, ...proposedData.basicInfo },
            contactInfo: { ...prev.contactInfo, ...proposedData.contactInfo },
            otherInfo: { ...prev.otherInfo, ...proposedData.otherInfo }
        }));

        if (proposedData.basicInfo) setIsBasicInfoExpanded(true);
        if (proposedData.contactInfo) setIsContactExpanded(true);
        if (proposedData.otherInfo) setIsOtherInfoExpanded(true);

        setProposedData(null);
    };

    const handleDiscardProposed = () => {
        setProposedData(null);
    };

    const handleChange = (section: keyof RegistrationData, field: string, value: any) => {
        setFormData((prev) => {
            const newData = { ...prev };
            (newData[section] as any)[field] = value;
            // Changing state invalidates a previously-picked city that no longer belongs to it.
            if (section === "contactInfo" && field === "state") {
                const validCities = INDIAN_STATE_CITY_MAP[value] || [];
                if (!validCities.includes((newData.contactInfo as any).city)) {
                    (newData.contactInfo as any).city = "";
                }
            }
            return newData;
        });
        // Clear the error for this field as soon as the user starts fixing it.
        setFieldErrors((prev) => {
            if (!prev[field]) return prev;
            const next = { ...prev };
            delete next[field];
            return next;
        });
    };

    const validateForm = (): Record<string, string> => {
        const errors: Record<string, string> = {};
        if (!formData.basicInfo.firstName.trim()) errors.firstName = "Please enter the patient's first name.";
        if (!formData.basicInfo.gender) errors.gender = "Please select a gender.";
        if (!formData.basicInfo.maritalStatus) errors.maritalStatus = "Please select a marital status.";
        if (!formData.basicInfo.age || Number(formData.basicInfo.age) <= 0 || Number(formData.basicInfo.age) > 120) errors.age = "Please enter a valid age (1–120).";
        if (!formData.contactInfo.state) errors.state = "Please select a state.";
        if (!formData.contactInfo.city) errors.city = "Please select a city.";
        const mobileRegex = /^[6-9]\d{9}$/;
        if (!mobileRegex.test(formData.contactInfo.mobileNumber)) errors.mobileNumber = "Please enter a valid 10-digit Indian mobile number.";
        const pincodeRegex = /^[1-9][0-9]{5}$/;
        if (formData.contactInfo.pincode && !pincodeRegex.test(formData.contactInfo.pincode)) errors.pincode = "Please enter a valid 6-digit PIN code.";
        const idType = formData.otherInfo.idType;
        const idNumber = formData.otherInfo.idNumber.toUpperCase();
        if (idType && idNumber) {
            if (idType === "Aadhar" && !/^\d{12}$/.test(idNumber)) errors.idNumber = "Please enter a valid 12-digit Aadhaar number.";
            if (idType === "PAN Card" && !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(idNumber)) errors.idNumber = "Please enter a valid PAN number (e.g., ABCDE1234F).";
            if (idType === "Voter ID" && !/^[A-Z]{3}[0-9]{7}$/.test(idNumber)) errors.idNumber = "Please enter a valid Voter ID (e.g., ABC1234567).";
        }
        return errors;
    };

    const FIELD_LABELS: Record<string, string> = {
        firstName: "First Name", gender: "Gender", maritalStatus: "Marital Status", age: "Age",
        state: "State", city: "City", mobileNumber: "Mobile Number", pincode: "Pincode", idNumber: "ID Number",
    };

    // Applies a fresh set of field errors: expands any collapsed section that
    // now contains an error and scrolls/focuses the first invalid field so
    // the user isn't left guessing which field the banner refers to.
    const applyFieldErrors = (errors: Record<string, string>) => {
        setFieldErrors(errors);
        const keys = Object.keys(errors);
        if (keys.length === 0) return;

        const basicKeys = ["firstName", "gender", "maritalStatus", "age"];
        const contactKeys = ["state", "city", "mobileNumber", "pincode"];
        if (basicKeys.some((k) => errors[k])) setIsBasicInfoExpanded(true);
        if (contactKeys.some((k) => errors[k])) setIsContactExpanded(true);
        if (errors.idNumber) setIsOtherInfoExpanded(true);

        const summary = keys.length === 1
            ? errors[keys[0]]
            : `${keys.length} fields need attention — starting with ${FIELD_LABELS[keys[0]] || keys[0]}.`;
        setStatus(summary);
        setStatusType("error");

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                const el = document.getElementById(`field-${keys[0]}`);
                el?.scrollIntoView({ behavior: "smooth", block: "center" });
            });
        });
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
        const errors = validateForm();
        if (Object.keys(errors).length > 0) { applyFieldErrors(errors); return; }
        setFieldErrors({});
        await submitForm();
    };

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

            {proposedData && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 shadow-sm mb-8 animate-in slide-in-from-top-4">
                    <h3 className="text-lg font-semibold text-amber-800 mb-4 flex items-center">
                        <CheckCircle2 className="w-5 h-5 mr-2" /> AI Extracted Data Available for Review
                    </h3>
                    <div className="text-sm text-slate-700 space-y-2 mb-6">
                        <p>The AI listener has extracted the following details from the conversation:</p>
                        <div className="bg-white p-4 rounded-lg border border-amber-100 max-h-64 overflow-y-auto w-full">
                            <ul className="list-disc list-inside space-y-1">
                                {proposedData.basicInfo?.firstName && <li><strong>Name:</strong> {proposedData.basicInfo.firstName} {proposedData.basicInfo.lastName || ''}</li>}
                                {proposedData.basicInfo?.age && <li><strong>Age:</strong> {proposedData.basicInfo.age}</li>}
                                {proposedData.basicInfo?.gender && <li><strong>Gender:</strong> {proposedData.basicInfo.gender}</li>}
                                {proposedData.basicInfo?.maritalStatus && <li><strong>Marital Status:</strong> {proposedData.basicInfo.maritalStatus}</li>}

                                {proposedData.contactInfo?.mobileNumber && <li><strong>Mobile:</strong> {proposedData.contactInfo.mobileNumber}</li>}
                                {proposedData.contactInfo?.address && <li><strong>Address:</strong> {proposedData.contactInfo.address}</li>}
                                {proposedData.contactInfo?.city && <li><strong>City:</strong> {proposedData.contactInfo.city}</li>}
                                {proposedData.contactInfo?.state && <li><strong>State:</strong> {proposedData.contactInfo.state}</li>}
                                {proposedData.contactInfo?.pincode && <li><strong>Pincode:</strong> {proposedData.contactInfo.pincode}</li>}

                                {proposedData.otherInfo?.occupation && <li><strong>Occupation:</strong> {proposedData.otherInfo.occupation}</li>}
                                {proposedData.otherInfo?.bloodGroup && <li><strong>Blood Group:</strong> {proposedData.otherInfo.bloodGroup}</li>}
                                {proposedData.otherInfo?.idType && <li><strong>ID Type:</strong> {proposedData.otherInfo.idType} ({proposedData.otherInfo.idNumber})</li>}
                            </ul>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={handleAcceptProposed}
                            className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                            <CheckCircle2 className="w-4 h-4" />
                            Accept & Fill Form
                        </button>
                        <button
                            type="button"
                            onClick={handleDiscardProposed}
                            className="flex items-center gap-2 border border-amber-300 text-amber-700 hover:bg-amber-100 px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                            <AlertCircle className="w-4 h-4" />
                            Discard
                        </button>
                    </div>
                </div>
            )
            }

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
                        label="First Name" required name="firstName" error={fieldErrors.firstName}
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
                    <div id="field-gender" className="flex flex-col gap-2 scroll-mt-24">
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
                                        : fieldErrors.gender
                                            ? 'bg-background border-destructive/60 text-muted-foreground hover:border-destructive hover:text-foreground'
                                            : 'bg-background border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                                        }`}
                                >
                                    {opt}
                                </button>
                            ))}
                        </div>
                        {fieldErrors.gender && (
                            <p className="flex items-center gap-1 text-xs font-medium text-destructive animate-in fade-in slide-in-from-top-1 duration-150">
                                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                                {fieldErrors.gender}
                            </p>
                        )}
                    </div>
                    <FormInput
                        label="Age" required type="number" name="age" error={fieldErrors.age}
                        value={formData.basicInfo.age}
                        onChange={(v: string) => handleChange("basicInfo", "age", v)}
                        placeholder="Years"
                    />
                </div>

                {/* Marital Status */}
                <div id="field-maritalStatus" className="mt-4 scroll-mt-24">
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
                                    : fieldErrors.maritalStatus
                                        ? 'bg-background border-destructive/60 text-muted-foreground hover:border-destructive hover:text-foreground'
                                        : 'bg-background border-border text-muted-foreground hover:border-primary/50 hover:text-foreground'
                                    }`}
                            >
                                {opt}
                            </button>
                        ))}
                    </div>
                    {fieldErrors.maritalStatus && (
                        <p className="flex items-center gap-1 text-xs font-medium text-destructive mt-2 animate-in fade-in slide-in-from-top-1 duration-150">
                            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                            {fieldErrors.maritalStatus}
                        </p>
                    )}
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
                    label="Mobile Number" required name="mobileNumber" error={fieldErrors.mobileNumber}
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
                        label="State" required name="state" error={fieldErrors.state}
                        options={INDIAN_STATES}
                        value={formData.contactInfo.state}
                        onChange={(v: string) => handleChange("contactInfo", "state", v)}
                    />
                    <FormSelect
                        label="City" required name="city" error={fieldErrors.city}
                        options={INDIAN_STATE_CITY_MAP[formData.contactInfo.state] || []}
                        value={formData.contactInfo.city}
                        onChange={(v: string) => handleChange("contactInfo", "city", v)}
                        disabled={!formData.contactInfo.state}
                        placeholder={formData.contactInfo.state ? "Select City" : "Select a state first"}
                    />
                </div>

                <div className="mt-4 max-w-xs">
                    <FormInput
                        label="Pincode" name="pincode" error={fieldErrors.pincode}
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
                        label="ID Number" name="idNumber" error={fieldErrors.idNumber}
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

function FormInput({ label, value, onChange, placeholder, type = "text", required, disabled, prefix, name, error }: {
    label: string; value: string; onChange: (v: string) => void; placeholder?: string;
    type?: string; required?: boolean; disabled?: boolean; prefix?: React.ReactNode; name?: string; error?: string;
}) {
    return (
        <div id={name ? `field-${name}` : undefined} className="flex flex-col gap-1.5 w-full scroll-mt-24">
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
                    aria-invalid={!!error}
                    className={`w-full h-11 border rounded-lg text-sm text-foreground bg-background placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 transition-all duration-150 shadow-sm
                        ${prefix ? 'pl-9 pr-4' : 'px-4'}
                        ${disabled ? 'bg-muted text-muted-foreground cursor-not-allowed' : ''}
                        ${error ? 'border-destructive focus:ring-destructive/30 focus:border-destructive' : 'border-input focus:ring-primary/30 focus:border-primary'}
                    `}
                />
            </div>
            {error && (
                <p className="flex items-center gap-1 text-xs font-medium text-destructive animate-in fade-in slide-in-from-top-1 duration-150">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    {error}
                </p>
            )}
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

function FormSelect({ label, value, onChange, options, required, disabled, icon, name, error, placeholder }: {
    label: string; value: string; onChange: (v: string) => void;
    options: string[]; required?: boolean; disabled?: boolean; icon?: React.ReactNode; name?: string; error?: string; placeholder?: string;
}) {
    return (
        <div id={name ? `field-${name}` : undefined} className="flex flex-col gap-1.5 w-full scroll-mt-24">
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
                    aria-invalid={!!error}
                    className={`w-full h-11 border rounded-lg text-sm text-foreground bg-background focus:outline-none focus:ring-2 transition-all duration-150 shadow-sm appearance-none cursor-pointer
                        ${icon ? 'pl-9 pr-9' : 'pl-4 pr-9'}
                        ${disabled ? 'bg-muted cursor-not-allowed' : ''}
                        ${value === '' ? 'text-muted-foreground/70' : ''}
                        ${error ? 'border-destructive focus:ring-destructive/30 focus:border-destructive' : 'border-input focus:ring-primary/30 focus:border-primary'}
                    `}
                >
                    <option value="">{placeholder || `Select ${label}`}</option>
                    {options.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            </div>
            {error && (
                <p className="flex items-center gap-1 text-xs font-medium text-destructive animate-in fade-in slide-in-from-top-1 duration-150">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    {error}
                </p>
            )}
        </div>
    );
}
