'use client';

import { useState, useEffect } from 'react';
import { createPortal } from "react-dom";
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronDown, ChevronUp, UserPlus, Search, SearchCode, CheckCircle2, XCircle, RefreshCw, X } from 'lucide-react';
import type { PatientRegistrationData, ConsultationData } from '@/types/clinical';
import { savePatient, saveConsultation } from '@/app/actions/saveConsultation';

// CopilotKit and Voice
import { CopilotKit, useCopilotChat, useCopilotAction } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { VoiceInputButton } from '@/components/VoiceInputButton';
import { LanguageSelector } from '@/components/LanguageSelector';

// Re-using the same icons and structure as the old registration form for consistency
import { User, Phone, Info, FileText } from 'lucide-react';
import { PatientSearchCombobox, PatientSearchResult } from '@/components/ui/PatientSearchCombobox';

function ConsultationForm({ isChatOpen }: { isChatOpen: boolean }) {
    const router = useRouter();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState('');

    // --- State: View Toggles ---
    const [isExistingPatient, setIsExistingPatient] = useState(false);

    // --- State: Patient Context ---
    const [searchResult, setSearchResult] = useState<PatientRegistrationData | null>(null);

    // --- State: Copilot Ambient Listening ---
    const [selectedLanguage, setSelectedLanguage] = useState("hi-IN");
    const [isListening, setIsListening] = useState(false);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [proposedData, setProposedData] = useState<any>(null);
    const [chatInputNode, setChatInputNode] = useState<Element | null>(null);
    const [showNewChatConfirm, setShowNewChatConfirm] = useState(false);

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
        if (clearForm) {
            setRegistrationData({
                basicInfo: { firstName: '', lastName: '', age: '', gender: '', maritalStatus: '' },
                contactInfo: { mobile: '', address: '', city: '', state: '', pincode: '' },
                otherInfo: { occupation: '', bloodGroup: '', idType: '', idNumber: '' },
            });
            setConsultationData({ symptoms: '', diagnosis: '', prakriti: '', vikriti: '', severity: 5, comorbidities: '', notes: '' });
            setProposedData(null);
            setSearchResult(null);
        }
        setShowNewChatConfirm(false);
    };

    useCopilotAction({
        name: "propose_consultation_data",
        description: "Extract ALL demographic and clinical data from the doctor-patient conversation and propose them to the UI for doctor review. Always populate as many fields as possible from the dialogue.",
        parameters: [
            {
                name: "basicInfo", type: "object", required: false,
                description: "Patient's basic personal information extracted from the conversation",
                attributes: [
                    { name: "firstName", type: "string", description: "Patient's first name" },
                    { name: "lastName", type: "string", description: "Patient's last name or surname" },
                    { name: "gender", type: "string", description: "Must be exactly: 'Male', 'Female', or 'Transgender'" },
                    { name: "age", type: "string", description: "Patient's age in years as a string (e.g. '34')" },
                    { name: "maritalStatus", type: "string", description: "Must be exactly: 'Married', 'Unmarried', 'Divorcee', or 'Widow'" },
                ],
            },
            {
                name: "contactInfo", type: "object", required: false,
                description: "Patient's contact and address details extracted from the conversation",
                attributes: [
                    { name: "mobile", type: "string", description: "10-digit mobile number. Extract ONLY digits, strip spaces, hyphens, and +91 country code" },
                    { name: "address", type: "string", description: "Full street/residential address" },
                    { name: "city", type: "string", description: "City name (e.g. Surat, Mumbai, Ahmedabad)" },
                    { name: "state", type: "string", description: "Indian state name (e.g. Gujarat, Maharashtra)" },
                    { name: "pincode", type: "string", description: "6-digit Indian postal pincode" },
                ],
            },
            {
                name: "otherInfo", type: "object", required: false,
                description: "Other personal information like occupation and ID details",
                attributes: [
                    { name: "occupation", type: "string", description: "Patient's profession or job (e.g. Software Engineer, Farmer)" },
                    { name: "bloodGroup", type: "string", description: "Must be exactly one of: A+, A-, B+, B-, O+, O-, AB+, AB-" },
                    { name: "idType", type: "string", description: "Must be exactly: 'Aadhar', 'PAN Card', or 'Voter ID'" },
                    { name: "idNumber", type: "string", description: "The ID document number" },
                ],
            },
            {
                name: "assessment", type: "object", required: false,
                description: "Clinical assessment and Ayurvedic evaluation from the doctor",
                attributes: [
                    { name: "symptoms", type: "string", description: "Patient's presenting complaints, symptoms and duration" },
                    { name: "diagnosis", type: "string", description: "Doctor's provisional clinical diagnosis" },
                    { name: "notes", type: "string", description: "Any additional clinical observations by the doctor" },
                    { name: "prakriti", type: "string", description: "Ayurvedic constitutional type. One of: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha, Tridosha" },
                    { name: "vikriti", type: "string", description: "Current doshic imbalance. One of: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha" },
                    { name: "severity", type: "number", description: "Severity score from 1 (mild) to 10 (severe)" },
                    { name: "comorbidities", type: "string", description: "Any existing conditions or comorbidities the patient has" },
                ],
            },
        ],
        handler: async (args) => {
            setProposedData((prev: any) => {
                // Deep merge: new fields WIN over — but empty/null fields do NOT clear existing ones
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
                return {
                    basicInfo: mergeObj(prev?.basicInfo, args.basicInfo),
                    contactInfo: mergeObj(prev?.contactInfo, args.contactInfo),
                    otherInfo: mergeObj(prev?.otherInfo, args.otherInfo),
                    assessment: mergeObj(prev?.assessment, args.assessment),
                };
            });
            return "Proposed data updated for doctor review.";
        }
    });

    const handleVoiceTranscript = async (transcript: string) => {
        setVoiceError(null);
        // Clear the interim text from the input box first
        const inputEl = document.querySelector('.copilotKitInputTextarea') as HTMLTextAreaElement | null;
        if (inputEl) {
            inputEl.value = transcript;
            // Fire React synthetic event so CopilotKit picks up the value
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
            if (nativeInputValueSetter) {
                nativeInputValueSetter.call(inputEl, transcript);
                inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
        } else {
            // Fallback: append message programmatically
            await appendMessage(
                new TextMessage({
                    role: MessageRole.User,
                    content: transcript
                })
            );
        }
    };

    const handleInterimTranscript = (text: string) => {
        // Write live transcription text into the CopilotKit chat input box
        const inputEl = document.querySelector('.copilotKitInputTextarea') as HTMLTextAreaElement | null;
        if (inputEl) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
            if (nativeInputValueSetter) {
                nativeInputValueSetter.call(inputEl, text);
                inputEl.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    };

    // --- State: Registration Form ---
    const [expandedSections, setExpandedSections] = useState({
        basic: true,
        contact: true,
        other: true
    });

    const [registrationData, setRegistrationData] = useState<PatientRegistrationData>({
        basicInfo: {
            firstName: '',
            lastName: '',
            age: '',
            gender: '',
            maritalStatus: '',
        },
        contactInfo: {
            mobile: '',
            address: '',
            city: '',
            state: '',
            pincode: '',
        },
        otherInfo: {
            occupation: '',
            bloodGroup: '',
            idType: '',
            idNumber: '',
        }
    });

    const [consultationData, setConsultationData] = useState<ConsultationData['assessment']>({
        symptoms: '',
        diagnosis: '',
        prakriti: '',
        vikriti: '',
        severity: 5,
        comorbidities: '',
        notes: ''
    });

    const doshaOptions = [
        'Vata',
        'Pitta',
        'Kapha',
        'Vata-Pitta',
        'Pitta-Kapha',
        'Vata-Kapha',
        'Tridosha'
    ];

    const toggleSection = (section: keyof typeof expandedSections) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

    // The API is now handled by the PatientSearchCombobox component directly.
    const handlePatientSelect = (p: PatientSearchResult) => {
        setSearchResult({
            id: p.id,
            basicInfo: {
                firstName: p.first_name || p.firstName || "",
                lastName: p.last_name || p.lastName || "",
                age: p.age ? String(p.age) : "",
                gender: (p.gender as "Male" | "Female" | "Transgender" | "Other" | "Prefer not to say" | "") || "",
                maritalStatus: p.marital_status || p.maritalStatus || ""
            },
            contactInfo: {
                mobile: p.mobile || "",
                address: p.address || "",
                city: p.city || "",
                state: p.state || "",
                pincode: p.pincode || ""
            },
            otherInfo: {
                occupation: p.occupation || "",
                bloodGroup: p.blood_group || p.bloodGroup || "",
                idType: p.id_type || p.idType || "",
                idNumber: p.id_number || p.idNumber || ""
            }
        });
    };

    const handleRegistrationChange = (section: 'basicInfo' | 'contactInfo' | 'otherInfo', field: string, value: string) => {
        setRegistrationData(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [field]: value
            }
        }));
    };

    const handleConsultationChange = (field: keyof ConsultationData['assessment'], value: string | number) => {
        setConsultationData(prev => ({ ...prev, [field]: value }));
    };

    const handleAcceptProposed = () => {
        if (!proposedData) return;

        if (proposedData.basicInfo) {
            setRegistrationData(prev => ({ ...prev, basicInfo: { ...prev.basicInfo, ...proposedData.basicInfo } }));
        }
        if (proposedData.contactInfo) {
            setRegistrationData(prev => ({ ...prev, contactInfo: { ...prev.contactInfo, ...proposedData.contactInfo } }));
        }
        if (proposedData.otherInfo) {
            setRegistrationData(prev => ({ ...prev, otherInfo: { ...prev.otherInfo, ...proposedData.otherInfo } }));
        }
        if (proposedData.assessment) {
            setConsultationData(prev => ({ ...prev, ...proposedData.assessment }));
        }

        setProposedData(null);
    };

    const handleDiscardProposed = () => {
        setProposedData(null);
    };

    const validateForm = (): string | null => {
        if (!isExistingPatient) {
            if (!registrationData.basicInfo.firstName.trim()) return "Please enter the patient's first name.";
            if (!registrationData.basicInfo.lastName.trim()) return "Please enter the patient's last name.";
            if (!registrationData.basicInfo.gender) return "Please select a gender.";
            if (!registrationData.basicInfo.maritalStatus) return "Please select a marital status.";

            const ageNum = Number(registrationData.basicInfo.age);
            if (isNaN(ageNum) || ageNum <= 0 || ageNum > 120) return "Please enter a valid age (1–120).";

            const mobileRegex = /^[6-9]\d{9}$/;
            if (!mobileRegex.test(registrationData.contactInfo.mobile)) return "Please enter a valid 10-digit Indian mobile number.";

            const pincodeRegex = /^[1-9][0-9]{5}$/;
            if (registrationData.contactInfo.pincode && !pincodeRegex.test(registrationData.contactInfo.pincode)) return "Please enter a valid 6-digit PIN code.";

            const idType = registrationData.otherInfo.idType;
            const idNumber = registrationData.otherInfo.idNumber?.toUpperCase() || '';
            if (idType && idNumber) {
                if (idType === "Aadhar" && !/^\d{12}$/.test(idNumber)) return "Please enter a valid 12-digit Aadhaar number.";
                if (idType === "PAN Card" && !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(idNumber)) return "Please enter a valid PAN number (e.g., ABCDE1234F).";
                if (idType === "Voter ID" && !/^[A-Z]{3}[0-9]{7}$/.test(idNumber)) return "Please enter a valid Voter ID (e.g., ABC1234567).";
            }
        } else {
            if (!searchResult?.id) return "Must select an existing patient before saving a consultation.";
        }

        if (!consultationData.symptoms.trim()) return "Please enter the key symptoms.";
        if (!consultationData.diagnosis.trim()) return "Please enter an initial diagnosis.";

        return null;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const errorMsg = validateForm();
        if (errorMsg) {
            setSubmitError(errorMsg);
            return;
        }

        setIsSubmitting(true);
        setSubmitError('');

        try {
            let activePatientId = '';

            // 1. Resolve Patient ID
            if (isExistingPatient) {
                activePatientId = searchResult?.id || '';
            } else {
                // Save new patient
                const patientRes = await savePatient(registrationData);
                if (!patientRes.success || !patientRes.patientId) {
                    throw new Error(patientRes.message || "Failed to create new patient");
                }
                activePatientId = patientRes.patientId;
            }

            // 2. Save Consultation Visit
            const visitResult = await saveConsultation(activePatientId, {
                patientId: activePatientId,
                assessment: consultationData
            });

            if (visitResult.success) {
                // 3. Redirect to Treatment Plan Generation
                router.push(`/doctor/treatment/${visitResult.visitId}`);
            } else {
                throw new Error(visitResult.message);
            }

        } catch (err: any) {
            setSubmitError(err.message || "An unexpected error occurred");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="container mx-auto p-4 max-w-4xl space-y-8">
            <div className="flex justify-between items-center mb-6 border-b pb-4">
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-teal-500">
                    New Clinical Consultation
                </h1>
            </div>

            {proposedData && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 shadow-sm mb-8 animate-in slide-in-from-top-4">
                    <h3 className="text-lg font-semibold text-amber-800 mb-4 flex items-center">
                        <CheckCircle2 className="w-5 h-5 mr-2" /> AI Extracted Data Available for Review
                    </h3>
                    <div className="text-sm text-slate-700 space-y-2 mb-6">
                        <p>The AI listener has extracted the following details from your conversation:</p>
                        <div className="bg-white p-4 rounded-lg border border-amber-100 max-h-64 overflow-y-auto w-full">
                            <ul className="list-disc list-inside space-y-1">
                                {proposedData.basicInfo?.firstName && <li><strong>Name:</strong> {proposedData.basicInfo.firstName} {proposedData.basicInfo.lastName || ''}</li>}
                                {proposedData.basicInfo?.age && <li><strong>Age:</strong> {proposedData.basicInfo.age}</li>}
                                {proposedData.basicInfo?.gender && <li><strong>Gender:</strong> {proposedData.basicInfo.gender}</li>}
                                {proposedData.basicInfo?.maritalStatus && <li><strong>Marital Status:</strong> {proposedData.basicInfo.maritalStatus}</li>}

                                {proposedData.contactInfo?.mobile && <li><strong>Mobile:</strong> {proposedData.contactInfo.mobile}</li>}
                                {proposedData.contactInfo?.address && <li><strong>Address:</strong> {proposedData.contactInfo.address}</li>}
                                {proposedData.contactInfo?.city && <li><strong>City:</strong> {proposedData.contactInfo.city}</li>}
                                {proposedData.contactInfo?.state && <li><strong>State:</strong> {proposedData.contactInfo.state}</li>}
                                {proposedData.contactInfo?.pincode && <li><strong>Pincode:</strong> {proposedData.contactInfo.pincode}</li>}

                                {proposedData.otherInfo?.occupation && <li><strong>Occupation:</strong> {proposedData.otherInfo.occupation}</li>}
                                {proposedData.otherInfo?.bloodGroup && <li><strong>Blood Group:</strong> {proposedData.otherInfo.bloodGroup}</li>}
                                {proposedData.otherInfo?.idType && <li><strong>ID Type:</strong> {proposedData.otherInfo.idType} ({proposedData.otherInfo.idNumber})</li>}

                                {proposedData.assessment?.symptoms && <li><strong>Symptoms:</strong> {proposedData.assessment.symptoms}</li>}
                                {proposedData.assessment?.diagnosis && <li><strong>Diagnosis:</strong> {proposedData.assessment.diagnosis}</li>}
                                {proposedData.assessment?.prakriti && <li><strong>Prakriti:</strong> {proposedData.assessment.prakriti}</li>}
                                {proposedData.assessment?.vikriti && <li><strong>Vikriti:</strong> {proposedData.assessment.vikriti}</li>}
                                {proposedData.assessment?.severity && <li><strong>Severity:</strong> {proposedData.assessment.severity}/10</li>}
                                {proposedData.assessment?.comorbidities && <li><strong>Comorbidities:</strong> {proposedData.assessment.comorbidities}</li>}
                                {proposedData.assessment?.notes && <li><strong>Notes:</strong> {proposedData.assessment.notes}</li>}
                            </ul>
                        </div>
                    </div>
                    <div className="flex gap-4">
                        <Button
                            type="button"
                            variant="default"
                            onClick={handleAcceptProposed}
                            className="bg-amber-600 hover:bg-amber-700 text-white"
                        >
                            <CheckCircle2 className="w-4 h-4 mr-2" />
                            Accept & Fill Form
                        </Button>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={handleDiscardProposed}
                            className="border-amber-300 text-amber-700 hover:bg-amber-100"
                        >
                            <XCircle className="w-4 h-4 mr-2" />
                            Discard
                        </Button>
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-8">

                {/* --- Section 1: Patient Context --- */}
                <div className="bg-white rounded-xl shadow-sm border border-emerald-100">
                    <div className="bg-gradient-to-r from-emerald-50 to-teal-50 p-6 border-b border-emerald-100 rounded-t-xl">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-slate-800 flex items-center">
                                <UserPlus className="w-5 h-5 mr-2 text-emerald-600" />
                                Patient Details
                            </h2>
                            <div className="flex space-x-2 p-1 bg-white rounded-lg shadow-sm border">
                                <button
                                    type="button"
                                    onClick={() => setIsExistingPatient(false)}
                                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${!isExistingPatient ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}
                                >
                                    New Patient
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setIsExistingPatient(true)}
                                    className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${isExistingPatient ? 'bg-emerald-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-50'}`}
                                >
                                    Existing Patient
                                </button>
                            </div>
                        </div>

                        {isExistingPatient ? (
                            <div className="w-full max-w-md">
                                <PatientSearchCombobox
                                    onSelect={handlePatientSelect}
                                    placeholder="Search patients by name or mobile (e.g., Utsav)"
                                />
                            </div>
                        ) : (
                            <p className="text-sm text-slate-500">
                                Please fill out the registration form below to create a new patient profile.
                            </p>
                        )}
                    </div>

                    {/* Show Patient Details IF existing patient is selected AND found */}
                    {isExistingPatient && searchResult && (
                        <div className="p-6 bg-emerald-50/50">
                            <h3 className="text-lg font-semibold text-emerald-800 mb-2">Patient Profile Confirmed</h3>
                            <div className="grid grid-cols-2 gap-4 text-sm text-slate-700">
                                <div><span className="font-semibold">Name:</span> {searchResult.basicInfo.firstName} {searchResult.basicInfo.lastName}</div>
                                <div><span className="font-semibold">Mobile:</span> {searchResult.contactInfo.mobile}</div>
                                <div><span className="font-semibold">Gender:</span> {searchResult.basicInfo.gender}</div>
                                <div><span className="font-semibold">Age:</span> {searchResult.basicInfo.age}</div>
                            </div>
                        </div>
                    )}

                    {/* Show Registration Form IF new patient is selected */}
                    {!isExistingPatient && (
                        <div className="p-0 border-t border-emerald-100 divide-y divide-emerald-50">

                            {/* Basic Info */}
                            <div className="p-6">
                                <button type="button" onClick={() => toggleSection('basic')} className="flex items-center justify-between w-full mb-4">
                                    <h3 className="text-lg font-semibold text-slate-800 flex items-center">
                                        <User className="w-5 h-5 mr-2 text-emerald-500" /> Basic Details
                                    </h3>
                                    {expandedSections.basic ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                                </button>

                                {expandedSections.basic && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <Label>First Name *</Label>
                                            <Input required value={registrationData.basicInfo.firstName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('basicInfo', 'firstName', e.target.value)} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Last Name *</Label>
                                            <Input required value={registrationData.basicInfo.lastName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('basicInfo', 'lastName', e.target.value)} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Age *</Label>
                                            <Input type="number" required value={registrationData.basicInfo.age} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('basicInfo', 'age', e.target.value)} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Gender *</Label>
                                            <Select value={registrationData.basicInfo.gender} onValueChange={(v) => handleRegistrationChange('basicInfo', 'gender', v)}>
                                                <SelectTrigger><SelectValue placeholder="Select gender" /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="Male">Male</SelectItem>
                                                    <SelectItem value="Female">Female</SelectItem>
                                                    <SelectItem value="Transgender">Transgender</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2 md:col-span-2">
                                            <Label>Marital Status *</Label>
                                            <Select value={registrationData.basicInfo.maritalStatus} onValueChange={(v) => handleRegistrationChange('basicInfo', 'maritalStatus', v)}>
                                                <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="Married">Married</SelectItem>
                                                    <SelectItem value="Unmarried">Unmarried</SelectItem>
                                                    <SelectItem value="Divorcee">Divorcee</SelectItem>
                                                    <SelectItem value="Widow">Widow</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Contact Info */}
                            <div className="p-6">
                                <button type="button" onClick={() => toggleSection('contact')} className="flex items-center justify-between w-full mb-4">
                                    <h3 className="text-lg font-semibold text-slate-800 flex items-center">
                                        <Phone className="w-5 h-5 mr-2 text-emerald-500" /> Contact Details
                                    </h3>
                                    {expandedSections.contact ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                                </button>

                                {expandedSections.contact && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <Label>Mobile Number *</Label>
                                            <Input required type="tel" value={registrationData.contactInfo.mobile} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('contactInfo', 'mobile', e.target.value)} />
                                        </div>
                                        <div className="space-y-2 md:col-span-2">
                                            <Label>Address</Label>
                                            <Input value={registrationData.contactInfo.address || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('contactInfo', 'address', e.target.value)} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>State</Label>
                                            <Select value={registrationData.contactInfo.state} onValueChange={(v) => handleRegistrationChange('contactInfo', 'state', v)}>
                                                <SelectTrigger><SelectValue placeholder="Select state" /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="Delhi">Delhi</SelectItem>
                                                    <SelectItem value="Maharashtra">Maharashtra</SelectItem>
                                                    <SelectItem value="Karnataka">Karnataka</SelectItem>
                                                    <SelectItem value="Gujarat">Gujarat</SelectItem>
                                                    <SelectItem value="Uttar Pradesh">Uttar Pradesh</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>City</Label>
                                            <Select value={registrationData.contactInfo.city} onValueChange={(v) => handleRegistrationChange('contactInfo', 'city', v)}>
                                                <SelectTrigger><SelectValue placeholder="Select city" /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="New Delhi">New Delhi</SelectItem>
                                                    <SelectItem value="Mumbai">Mumbai</SelectItem>
                                                    <SelectItem value="Bangalore">Bangalore</SelectItem>
                                                    <SelectItem value="Ahmedabad">Ahmedabad</SelectItem>
                                                    <SelectItem value="Lucknow">Lucknow</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Pincode</Label>
                                            <Input value={registrationData.contactInfo.pincode || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('contactInfo', 'pincode', e.target.value)} />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Other Info */}
                            <div className="p-6">
                                <button type="button" onClick={() => toggleSection('other')} className="flex items-center justify-between w-full mb-4">
                                    <h3 className="text-lg font-semibold text-slate-800 flex items-center">
                                        <FileText className="w-5 h-5 mr-2 text-emerald-500" /> Other Details
                                    </h3>
                                    {expandedSections.other ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                                </button>

                                {expandedSections.other && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <Label>Occupation</Label>
                                            <Input value={registrationData.otherInfo.occupation || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('otherInfo', 'occupation', e.target.value)} />
                                        </div>
                                        <div className="space-y-2">
                                            <Label>Blood Group</Label>
                                            <Select value={registrationData.otherInfo.bloodGroup} onValueChange={(v) => handleRegistrationChange('otherInfo', 'bloodGroup', v)}>
                                                <SelectTrigger><SelectValue placeholder="Select blood group" /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="A+">A+</SelectItem>
                                                    <SelectItem value="A-">A-</SelectItem>
                                                    <SelectItem value="B+">B+</SelectItem>
                                                    <SelectItem value="B-">B-</SelectItem>
                                                    <SelectItem value="O+">O+</SelectItem>
                                                    <SelectItem value="O-">O-</SelectItem>
                                                    <SelectItem value="AB+">AB+</SelectItem>
                                                    <SelectItem value="AB-">AB-</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>ID Type</Label>
                                            <Select value={registrationData.otherInfo.idType} onValueChange={(v) => handleRegistrationChange('otherInfo', 'idType', v)}>
                                                <SelectTrigger><SelectValue placeholder="Select ID Type" /></SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="Aadhar">Aadhar</SelectItem>
                                                    <SelectItem value="PAN Card">PAN Card</SelectItem>
                                                    <SelectItem value="Voter ID">Voter ID</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="space-y-2">
                                            <Label>ID Number</Label>
                                            <Input value={registrationData.otherInfo.idNumber || ''} onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleRegistrationChange('otherInfo', 'idNumber', e.target.value)} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* --- Section 2: Clinical Assessment --- */}
                {/* Only render this section if a patient is ready Context is valid (Either new is fully filled or existing is found) */}
                {/* --- Section 2: Clinical Assessment --- */}
                {/* Only render this section if a patient Context is valid */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mt-8 space-y-4">
                    <div className="flex justify-between items-center border-b border-slate-100 pb-4">
                        <h2 className="text-xl font-semibold flex items-center gap-2 text-slate-800">
                            <FileText className="w-5 h-5 text-blue-600" />
                            Clinical Notes
                        </h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Symptoms *</label>
                            <textarea
                                required
                                className="w-full p-3 border border-slate-200 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 outline-none resize-y"
                                placeholder="Patient reported symptoms..."
                                value={consultationData.symptoms}
                                onChange={(e) => handleConsultationChange('symptoms', e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Diagnosis *</label>
                            <textarea
                                required
                                className="w-full p-3 border border-slate-200 rounded-lg h-32 focus:ring-2 focus:ring-blue-500 outline-none resize-y"
                                placeholder="Clinical diagnosis..."
                                value={consultationData.diagnosis}
                                onChange={(e) => handleConsultationChange('diagnosis', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2 pt-4">
                        <label className="text-sm font-medium text-slate-700">Doctor's Internal Notes</label>
                        <textarea
                            className="w-full p-3 border border-slate-200 rounded-lg h-24 focus:ring-2 focus:ring-blue-500 outline-none resize-y"
                            placeholder="Any additional observations..."
                            value={consultationData.notes}
                            onChange={(e) => handleConsultationChange('notes', e.target.value)}
                        />
                    </div>

                    {/* AYUSH ML Context Fields */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 mt-4 border-t border-slate-100">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Prakriti (Natural Constitution)</label>
                            <Select value={consultationData.prakriti || ''} onValueChange={(v) => handleConsultationChange('prakriti', v)}>
                                <SelectTrigger className="border-slate-200"><SelectValue placeholder="Select Prakriti" /></SelectTrigger>
                                <SelectContent>
                                    {doshaOptions.map(dosha => <SelectItem key={dosha} value={dosha}>{dosha}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700">Vikriti (Current Imbalance)</label>
                            <Select value={consultationData.vikriti || ''} onValueChange={(v) => handleConsultationChange('vikriti', v)}>
                                <SelectTrigger className="border-slate-200"><SelectValue placeholder="Select Vikriti" /></SelectTrigger>
                                <SelectContent>
                                    {doshaOptions.filter(d => d !== 'Tridosha').map(dosha => <SelectItem key={dosha} value={dosha}>{dosha}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium flex justify-between text-slate-700">
                                <span>Severity <span className="text-xs text-slate-400 font-normal">(1-10)</span></span>
                                <span className="font-bold text-blue-600">{consultationData.severity}/10</span>
                            </label>
                            <input
                                type="range"
                                className="w-full mt-2"
                                min="1"
                                max="10"
                                value={consultationData.severity || 5}
                                onChange={(e) => handleConsultationChange('severity', parseInt(e.target.value))}
                            />
                            <div className="flex justify-between text-xs text-slate-400">
                                <span>Mild</span>
                                <span>Moderate</span>
                                <span>Severe</span>
                            </div>
                        </div>
                        <div className="space-y-2 md:col-span-3">
                            <label className="text-sm font-medium text-slate-700">Comorbidities / Other Conditions <span className="text-xs text-slate-400 font-normal">(Optional)</span></label>
                            <Input
                                placeholder="eg. Hypertension, Diabetes, Asthma..."
                                value={consultationData.comorbidities || ''}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleConsultationChange('comorbidities', e.target.value)}
                                className="h-12 border-slate-200"
                            />
                        </div>
                    </div>
                </div>

                {submitError && (
                    <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
                        {submitError}
                    </div>
                )}

                <div className="flex justify-end pt-4 pb-12">
                    <Button
                        type="submit"
                        disabled={isSubmitting || (isExistingPatient && !searchResult)}
                        className="bg-slate-900 hover:bg-slate-800 text-white min-w-[200px] h-12 text-lg font-medium shadow-md"
                    >
                        {isSubmitting ? 'Saving...' : 'Save & Proceed to Treatment'}
                    </Button>
                </div>

            </form>

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
        </div>
    );
}

export default function ConsultationPage() {
    const [isChatOpen, setIsChatOpen] = useState(true);

    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="consultation_agent">
            <CopilotSidebar
                instructions="You are an ambient AI scribe. Listen to the conversation and extract the clinical and demographic data."
                defaultOpen={true}
                clickOutsideToClose={false}
                onSetOpen={(open) => setIsChatOpen(open)}
                labels={{
                    title: "Ambient Scribe",
                    initial: "Listening to the consultation... Please speak.",
                }}
            >
                <div className="flex-1 h-full min-h-screen overflow-y-auto bg-gradient-to-br from-background via-muted/10 to-background">
                    <ConsultationForm isChatOpen={isChatOpen} />
                </div>
            </CopilotSidebar>
        </CopilotKit>
    );
}
