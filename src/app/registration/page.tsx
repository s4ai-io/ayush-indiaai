"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { useState } from "react";
import "@copilotkit/react-ui/styles.css";
import { saveRegistration } from "../actions/saveRegistration";
import { Minus, Plus, ChevronDown } from "lucide-react";
import { VoiceInputButton } from "@/components/VoiceInputButton";

interface RegistrationData {
    contactInfo: {
        mobileNumber: string;
        emailId: string;
        correspondenceAddress: string;
        correspondenceCountry: string;
        correspondenceState: string;
        correspondenceCity: string;
        correspondencePincode: string;
        isPermanentSame: boolean;
        permanentAddress: string;
        permanentCountry: string;
        permanentState: string;
        permanentCity: string;
        permanentPincode: string;
        emergencyContactName: string;
        emergencyContactNumber: string;
    };
    basicInfo: {
        firstName: string;
        lastName: string;
        gender: string;
        dateOfBirth: string;
        onlyYearOfBirth: boolean;
        relationshipType: string;
        relationName: string;
        nationality: string;
        maritalStatus: string;
        abhaId: string;
        insuranceProvider: string;
    };
    otherInfo: {
        qualification: string;
        occupation: string;
        bloodGroup: string;
        idType: string;
        idNumber: string;
    };
}

const INITIAL_DATA: RegistrationData = {
    contactInfo: {
        mobileNumber: "",
        emailId: "",
        correspondenceAddress: "",
        correspondenceCountry: "India",
        correspondenceState: "",
        correspondenceCity: "",
        correspondencePincode: "",
        isPermanentSame: false,
        permanentAddress: "",
        permanentCountry: "India",
        permanentState: "",
        permanentCity: "",
        permanentPincode: "",
        emergencyContactName: "",
        emergencyContactNumber: "",
    },
    basicInfo: {
        firstName: "",
        lastName: "",
        gender: "",
        dateOfBirth: "",
        onlyYearOfBirth: false,
        relationshipType: "",
        relationName: "",
        nationality: "Indian",
        maritalStatus: "",
        abhaId: "",
        insuranceProvider: "",
    },
    otherInfo: {
        qualification: "",
        occupation: "",
        bloodGroup: "",
        idType: "",
        idNumber: "",
    },
};

export default function RegistrationPage() {
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
            >
                <div className="flex-1 h-screen overflow-y-auto bg-gray-50">
                    <div className="max-w-5xl mx-auto p-4 md:p-8">
                        <RegistrationForm />
                    </div>
                </div>
            </CopilotSidebar>
        </CopilotKit>
    );
}

function RegistrationForm() {
    const [formData, setFormData] = useState<RegistrationData>(INITIAL_DATA);
    const [status, setStatus] = useState<string | null>(null);
    const [isBasicInfoExpanded, setIsBasicInfoExpanded] = useState(true);
    const [isContactExpanded, setIsContactExpanded] = useState(true);
    const [isOtherInfoExpanded, setIsOtherInfoExpanded] = useState(true);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [isListening, setIsListening] = useState(false);

    const handleVoiceTranscript = (transcript: string) => {
        setVoiceError(null); // Clear error on new input
        const textarea = document.querySelector('.copilotKitInput textarea') as HTMLTextAreaElement;

        if (textarea) {
            const currentValue = textarea.value;
            const newValue = currentValue ? `${currentValue} ${transcript}` : transcript;

            const nativeTextAreaValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
            if (nativeTextAreaValueSetter) {
                nativeTextAreaValueSetter.call(textarea, newValue);
            }

            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.focus();
        } else {
            console.warn("CopilotKit chat textarea not found. Voice input ignored.");
            setVoiceError("Chat window not found. Please open the assistant.");
        }
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
                    { name: "mobileNumber", type: "string" },
                    { name: "emailId", type: "string" },
                    { name: "correspondenceAddress", type: "string" },
                    { name: "correspondenceCountry", type: "string" },
                    { name: "correspondenceState", type: "string" },
                    { name: "correspondenceCity", type: "string" },
                    { name: "correspondencePincode", type: "string" },
                    { name: "isPermanentSame", type: "boolean" },
                    { name: "permanentAddress", type: "string" },
                    { name: "permanentCountry", type: "string" },
                    { name: "permanentState", type: "string" },
                    { name: "permanentCity", type: "string" },
                    { name: "permanentPincode", type: "string" },
                    { name: "emergencyContactName", type: "string" },
                    { name: "emergencyContactNumber", type: "string" },
                ],
            },
            {
                name: "basicInfo",
                type: "object",
                attributes: [
                    { name: "firstName", type: "string" },
                    { name: "lastName", type: "string" },
                    { name: "gender", type: "string", description: "Male, Female, or Transgender" },
                    { name: "dateOfBirth", type: "string" },
                    { name: "onlyYearOfBirth", type: "boolean" },
                    { name: "relationshipType", type: "string", description: "Father, Guardian, or Spouse" },
                    { name: "relationName", type: "string" },
                    { name: "nationality", type: "string", description: "Indian or Others" },
                    { name: "maritalStatus", type: "string", description: "Married, Unmarried, Divorcee, or Widow" },
                    { name: "abhaId", type: "string", description: "Ayushman Bharat Health Account ID" },
                    { name: "insuranceProvider", type: "string" },
                ],
            },
            {
                name: "otherInfo",
                type: "object",
                attributes: [
                    { name: "qualification", type: "string" },
                    { name: "occupation", type: "string" },
                    { name: "bloodGroup", type: "string" },
                    { name: "idType", type: "string" },
                    { name: "idNumber", type: "string" },
                ],
            },
        ],
        handler: async (args: Partial<RegistrationData>) => {
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
            return "Form updated.";
        },
    });

    const handleChange = (section: keyof RegistrationData, field: string, value: any) => {
        setFormData((prev) => {
            const newData = { ...prev };
            if (section === 'contactInfo' && field === 'isPermanentSame') {
                newData.contactInfo = {
                    ...newData.contactInfo,
                    isPermanentSame: value,
                    permanentAddress: value ? newData.contactInfo.correspondenceAddress : newData.contactInfo.permanentAddress,
                    permanentCountry: value ? newData.contactInfo.correspondenceCountry : newData.contactInfo.permanentCountry,
                    permanentState: value ? newData.contactInfo.correspondenceState : newData.contactInfo.permanentState,
                    permanentCity: value ? newData.contactInfo.correspondenceCity : newData.contactInfo.permanentCity,
                    permanentPincode: value ? newData.contactInfo.correspondencePincode : newData.contactInfo.permanentPincode,
                };
            } else {
                (newData[section] as any)[field] = value;
            }
            return newData;
        });
    };

    const submitForm = async () => {
        setStatus("Saving...");
        const result = await saveRegistration(formData);
        setStatus(result.message);
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
            return `Registration submitted. Status: ${result}`;
        },
    });

    return (
        <form onSubmit={handleSubmit} className="space-y-8 pb-20">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Patient Registration</h1>
                <p className="text-gray-500 mt-2">Enter patient details to register for Ayurvedic consultation.</p>
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

                    <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <div className="flex items-center justify-between mb-1">
                                <label className="text-sm font-semibold text-gray-700">Date of Birth <span className="text-red-500">*</span></label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="h-4 w-4 text-[#00A9B4] focus:ring-[#00A9B4] border-gray-300 rounded"
                                        checked={formData.basicInfo.onlyYearOfBirth}
                                        onChange={(e) => handleChange("basicInfo", "onlyYearOfBirth", e.target.checked)}
                                    />
                                    <span className="text-xs text-gray-500">Year Only</span>
                                </label>
                            </div>
                            <input
                                type="date"
                                className="w-full h-12 px-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#00A9B4]/20 focus:border-[#00A9B4] outline-none transition-all text-gray-700 bg-white shadow-sm"
                                value={formData.basicInfo.dateOfBirth}
                                onChange={(e) => handleChange("basicInfo", "dateOfBirth", e.target.value)}
                            />
                        </div>

                        <FormInput
                            label="Age"
                            value={formData.basicInfo.dateOfBirth ? calculateAge(formData.basicInfo.dateOfBirth) : ""}
                            readOnly
                            placeholder="Calculated automatically"
                            className="bg-gray-50 text-gray-500 cursor-not-allowed"
                        />
                    </div>

                    <div className="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <FormRadioGroup
                            label="Relationship Type"
                            required
                            options={["Father", "Guardian", "Spouse"]}
                            value={formData.basicInfo.relationshipType}
                            onChange={(v: string) => handleChange("basicInfo", "relationshipType", v)}
                        />
                        <FormInput label="Relation Name" value={formData.basicInfo.relationName} onChange={(v: string) => handleChange("basicInfo", "relationName", v)} placeholder="Full Name of Relation" />
                    </div>

                    <FormRadioGroup
                        label="Nationality"
                        required
                        options={["Indian", "Others"]}
                        value={formData.basicInfo.nationality}
                        onChange={(v: string) => handleChange("basicInfo", "nationality", v)}
                    />

                    <FormRadioGroup
                        label="Marital Status"
                        required
                        options={["Married", "Unmarried", "Divorcee", "Widow"]}
                        value={formData.basicInfo.maritalStatus}
                        onChange={(v: string) => handleChange("basicInfo", "maritalStatus", v)}
                    />

                    <FormInput label="ABHA ID" value={formData.basicInfo.abhaId} onChange={(v: string) => handleChange("basicInfo", "abhaId", v)} placeholder="XX-XXXX-XXXX-XXXX" helperText="Ayushman Bharat Health Account ID" />
                    <FormInput label="Insurance Provider" value={formData.basicInfo.insuranceProvider} onChange={(v: string) => handleChange("basicInfo", "insuranceProvider", v)} placeholder="e.g. LIC, Star Health" />
                </div>
            </Section>

            {/* Contact Info Section */}
            <Section title="Contact Info" isExpanded={isContactExpanded} onToggle={() => setIsContactExpanded(!isContactExpanded)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormInput label="Mobile Number" required value={formData.contactInfo.mobileNumber} onChange={(v: string) => handleChange("contactInfo", "mobileNumber", v)} placeholder="10-digit Mobile Number" />
                    <FormInput label="Email ID" type="email" value={formData.contactInfo.emailId} onChange={(v: string) => handleChange("contactInfo", "emailId", v)} placeholder="example@email.com" />

                    <div className="col-span-1 md:col-span-2 border-t border-gray-100 my-2"></div>

                    <div className="col-span-1 md:col-span-2">
                        <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">Correspondence Address</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="md:col-span-2">
                                <FormTextArea label="Address" value={formData.contactInfo.correspondenceAddress} onChange={(v: string) => handleChange("contactInfo", "correspondenceAddress", v)} placeholder="Street, Sector, Landmark" />
                            </div>
                            <FormSelect label="Country" required options={["India", "USA", "UK"]} value={formData.contactInfo.correspondenceCountry} onChange={(v: string) => handleChange("contactInfo", "correspondenceCountry", v)} />
                            <FormSelect label="State" required options={["Delhi", "Maharashtra", "Karnataka", "Gujarat"]} value={formData.contactInfo.correspondenceState} onChange={(v: string) => handleChange("contactInfo", "correspondenceState", v)} />
                            <FormSelect label="City" required options={["New Delhi", "Mumbai", "Bangalore", "Ahmedabad"]} value={formData.contactInfo.correspondenceCity} onChange={(v: string) => handleChange("contactInfo", "correspondenceCity", v)} />
                            <FormInput label="Pincode" value={formData.contactInfo.correspondencePincode} onChange={(v: string) => handleChange("contactInfo", "correspondencePincode", v)} placeholder="6-digit Pincode" />
                        </div>
                    </div>

                    <div className="col-span-1 md:col-span-2 flex items-center gap-3 bg-teal-50 p-4 rounded-lg border border-teal-100">
                        <input
                            type="checkbox"
                            id="sameAddress"
                            className="h-5 w-5 text-[#00A9B4] focus:ring-[#00A9B4] border-gray-300 rounded"
                            checked={formData.contactInfo.isPermanentSame}
                            onChange={(e) => handleChange("contactInfo", "isPermanentSame", e.target.checked)}
                        />
                        <label htmlFor="sameAddress" className="text-sm font-medium text-gray-700 cursor-pointer select-none">Permanent Address is same as Correspondence Address</label>
                    </div>

                    <div className={`col-span-1 md:col-span-2 transition-opacity duration-200 ${formData.contactInfo.isPermanentSame ? 'opacity-50 pointer-events-none' : ''}`}>
                        <h3 className="text-sm font-semibold text-gray-900 mb-4 uppercase tracking-wider">Permanent Address</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="md:col-span-2">
                                <FormTextArea label="Address" disabled={formData.contactInfo.isPermanentSame} value={formData.contactInfo.permanentAddress} onChange={(v: string) => handleChange("contactInfo", "permanentAddress", v)} placeholder="Street, Sector, Landmark" />
                            </div>
                            <FormSelect label="Country" required disabled={formData.contactInfo.isPermanentSame} options={["India", "USA", "UK"]} value={formData.contactInfo.permanentCountry} onChange={(v: string) => handleChange("contactInfo", "permanentCountry", v)} />
                            <FormSelect label="State" required disabled={formData.contactInfo.isPermanentSame} options={["Delhi", "Maharashtra", "Karnataka", "Gujarat"]} value={formData.contactInfo.permanentState} onChange={(v: string) => handleChange("contactInfo", "permanentState", v)} />
                            <FormSelect label="City" required disabled={formData.contactInfo.isPermanentSame} options={["New Delhi", "Mumbai", "Bangalore", "Ahmedabad"]} value={formData.contactInfo.permanentCity} onChange={(v: string) => handleChange("contactInfo", "permanentCity", v)} />
                            <FormInput label="Pincode" disabled={formData.contactInfo.isPermanentSame} value={formData.contactInfo.permanentPincode} onChange={(v: string) => handleChange("contactInfo", "permanentPincode", v)} placeholder="6-digit Pincode" />
                        </div>
                    </div>

                    <div className="col-span-1 md:col-span-2 border-t border-gray-100 my-2"></div>

                    <div className="col-span-1 md:col-span-2">
                        <h3 className="text-sm font-semibold text-red-600 mb-4 uppercase tracking-wider flex items-center gap-2">
                            Emergency Contact
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <FormInput label="Contact Name" value={formData.contactInfo.emergencyContactName} onChange={(v: string) => handleChange("contactInfo", "emergencyContactName", v)} placeholder="Name of relative/friend" />
                            <FormInput label="Contact Number" value={formData.contactInfo.emergencyContactNumber} onChange={(v: string) => handleChange("contactInfo", "emergencyContactNumber", v)} placeholder="Emergency Contact Number" />
                        </div>
                    </div>
                </div>
            </Section>

            {/* Other Info Section */}
            <Section title="Other Info" isExpanded={isOtherInfoExpanded} onToggle={() => setIsOtherInfoExpanded(!isOtherInfoExpanded)}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormSelect label="Qualification" options={["High School", "Bachelor", "Master", "PhD"]} value={formData.otherInfo.qualification} onChange={(v: string) => handleChange("otherInfo", "qualification", v)} />
                    <FormInput label="Occupation" value={formData.otherInfo.occupation} onChange={(v: string) => handleChange("otherInfo", "occupation", v)} placeholder="Current Occupation" />
                    <FormSelect label="Blood Group" options={["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]} value={formData.otherInfo.bloodGroup} onChange={(v: string) => handleChange("otherInfo", "bloodGroup", v)} />

                    <div className="grid grid-cols-2 gap-4">
                        <FormSelect label="ID Type" options={["Aadhar", "Passport", "Driving License"]} value={formData.otherInfo.idType} onChange={(v: string) => handleChange("otherInfo", "idType", v)} />
                        <FormInput label="ID Number" value={formData.otherInfo.idNumber} onChange={(v: string) => handleChange("otherInfo", "idNumber", v)} placeholder="ID Number" />
                    </div>
                </div>
            </Section>

            <div className="flex justify-end pt-6 sticky bottom-0 bg-gray-50/80 backdrop-blur-sm pb-4 border-t border-gray-200 mt-8">
                {status && <span className="mr-6 text-green-600 self-center font-medium bg-green-50 px-3 py-1 rounded-full text-sm border border-green-200">{status}</span>}
                <button
                    type="submit"
                    className="bg-gradient-to-r from-[#00A9B4] to-[#008f99] text-white px-10 py-3 rounded-xl shadow-lg hover:shadow-xl hover:from-[#008f99] hover:to-[#007a82] transform hover:-translate-y-0.5 transition-all duration-200 font-bold tracking-wide uppercase text-sm"
                >
                    Complete Registration
                </button>
            </div>

            {/* Voice Input Button Overlay */}
            <div className="fixed bottom-24 right-6 z-[1000] flex flex-col items-end gap-2">
                {voiceError && (
                    <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg border border-red-200 shadow-sm text-sm animate-in fade-in slide-in-from-right-4">
                        {voiceError}
                    </div>
                )}
                <div className="flex items-center gap-3">
                    {isListening && (
                        <div className="bg-black/75 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm animate-pulse">
                            Listening...
                        </div>
                    )}
                    <VoiceInputButton
                        onTranscript={handleVoiceTranscript}
                        onError={(err) => setVoiceError(err)}
                        onStateChange={setIsListening}
                    />
                </div>
            </div>
        </form>
    );
}

// --- Reusable UI Components ---

function Section({ title, isExpanded, onToggle, children }: { title: string; isExpanded: boolean; onToggle: () => void; children: React.ReactNode }) {
    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden transition-shadow hover:shadow-md">
            <div
                className={`px-8 py-5 flex justify-between items-center cursor-pointer select-none transition-colors duration-200 ${isExpanded ? 'bg-white border-b border-gray-100' : 'bg-gray-50 hover:bg-gray-100'}`}
                onClick={onToggle}
            >
                <div className="flex items-center gap-3">
                    <div className={`w-1 h-6 rounded-full ${isExpanded ? 'bg-[#00A9B4]' : 'bg-gray-300'}`}></div>
                    <h2 className={`font-bold uppercase tracking-wide text-sm ${isExpanded ? 'text-gray-900' : 'text-gray-500'}`}>{title}</h2>
                </div>
                {isExpanded ? <Minus className="text-[#00A9B4] w-5 h-5" /> : <Plus className="text-gray-400 w-5 h-5" />}
            </div>
            {isExpanded && <div className="p-8 animate-in fade-in slide-in-from-top-4 duration-300">{children}</div>}
        </div>
    );
}

function FormInput({ label, value, onChange, placeholder, type = "text", required, disabled, readOnly, className, helperText }: any) {
    return (
        <div className="flex flex-col gap-2 w-full">
            <label className="text-sm font-semibold text-gray-700 flex justify-between">
                <span>{label} {required && <span className="text-red-500">*</span>}</span>
            </label>
            <input
                type={type}
                placeholder={placeholder}
                className={`w-full h-12 px-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#00A9B4]/20 focus:border-[#00A9B4] outline-none transition-all text-gray-700 bg-white placeholder-gray-400 shadow-sm ${className} ${disabled ? 'bg-gray-100 text-gray-500' : ''}`}
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
            <label className="text-sm font-semibold text-gray-700">{label}</label>
            <textarea
                placeholder={placeholder}
                rows={3}
                className={`w-full p-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#00A9B4]/20 focus:border-[#00A9B4] outline-none transition-all text-gray-700 bg-white placeholder-gray-400 shadow-sm resize-none ${disabled ? 'bg-gray-100 text-gray-500' : ''}`}
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
            <label className="text-sm font-semibold text-gray-700">{label} {required && <span className="text-red-500">*</span>}</label>
            <div className="relative">
                <select
                    className={`w-full h-12 px-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-[#00A9B4]/20 focus:border-[#00A9B4] outline-none transition-all text-gray-700 bg-white shadow-sm appearance-none cursor-pointer ${disabled ? 'bg-gray-100 text-gray-500' : ''}`}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                >
                    <option value="">Select {label}</option>
                    {options.map((opt: string) => (
                        <option key={opt} value={opt}>{opt}</option>
                    ))}
                </select>
                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
        </div>
    );
}

function FormRadioGroup({ label, value, onChange, options, required }: any) {
    return (
        <div className="flex flex-col gap-3 w-full">
            <label className="text-sm font-semibold text-gray-700">{label} {required && <span className="text-red-500">*</span>}</label>
            <div className="flex flex-wrap gap-3">
                {options.map((opt: string) => (
                    <label
                        key={opt}
                        className={`
                            flex items-center gap-2 px-4 py-2.5 rounded-lg border cursor-pointer transition-all select-none text-sm font-medium
                            ${value === opt
                                ? 'bg-teal-50 border-[#00A9B4] text-[#00A9B4] shadow-sm ring-1 ring-[#00A9B4]'
                                : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300'
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
                        <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${value === opt ? 'border-[#00A9B4]' : 'border-gray-400'}`}>
                            {value === opt && <div className="w-2 h-2 rounded-full bg-[#00A9B4]"></div>}
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
