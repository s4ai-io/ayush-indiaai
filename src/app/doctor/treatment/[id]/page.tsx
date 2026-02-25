'use client';

import { useEffect, useState, use } from 'react';
import { createPortal } from 'react-dom';
import { CopilotKit, useCopilotReadable, useCopilotAction, useCopilotChat } from "@copilotkit/react-core";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { getPatient } from '@/app/actions/getPatient';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
    Brain, Activity, Leaf, Coffee, Moon, Sun, ArrowRight, CheckCircle, Info,
    ThumbsUp, ThumbsDown, Save, AlertTriangle, Shield, Heart, Stethoscope,
    FileText, Pill, ClipboardList, Sparkles, TrendingUp, Clock, Target,
    Plus, Trash2, X, RefreshCw
} from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { DiseaseSearchDropdown } from '@/components/ui/DiseaseSearchDropdown';
import { useRouter } from "next/navigation";
import { VoiceInputButton } from "@/components/VoiceInputButton";
import { LanguageSelector } from "@/components/LanguageSelector";

interface MedicalRecord {
    diagnosis: string;
    symptoms: string;
}

interface Patient {
    id: string;
    first_name: string;
    last_name: string;
    gender: string;
    age: number;
    medical_records: MedicalRecord[];
}

interface TreatmentPlan {
    herbs: { name: string; dosage: string; benefits: string }[];
    yoga: { practice: string; duration: string; benefits: string }[];
    diet: string[];
    lifestyle: string[];
    formulation?: string;
    prevention: string[];
    prognosis?: string;
    complications: string[];
    medical_intervention?: string;
    doshas_affected?: string;
    source_disease?: string;
    match_confidence?: number;
    match_method?: string;
    predicted_improvement: number;
    recommended_duration_weeks: number;
    explainability: string[];
}

export default function TreatmentPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);

    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="treatment_agent">
            <CopilotSidebar
                instructions="You are an AI Clinical Assistant helping the doctor fill the Ayurvedic treatment assessment form. Map patient conditions to the specific fields in the form accurately. Pay special attention to exact Ayurvedic terms for Dosha and Prakriti. Always use the provided mapping_rules."
                labels={{
                    title: "Treatment Assistant",
                    initial: "Hello Doctor! Tell me the patient's condition and I'll fill the clinical assessment for you.",
                }}
                defaultOpen={false}
                clickOutsideToClose={false}
            >
                <TreatmentPageContent id={id} />
            </CopilotSidebar>
        </CopilotKit>
    );
}

function TreatmentPageContent({ id }: { id: string }) {
    const [patient, setPatient] = useState<Patient | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [treatmentPlan, setTreatmentPlan] = useState<TreatmentPlan | null>(null);
    const router = useRouter();

    // ── Voice / Language portal (mirrors registration page) ──────────────────
    const [selectedLanguage, setSelectedLanguage] = useState('en-IN');
    const [isListening, setIsListening] = useState(false);
    const [voiceError, setVoiceError] = useState<string | null>(null);
    const [chatInputNode, setChatInputNode] = useState<Element | null>(null);
    const [showNewChatConfirm, setShowNewChatConfirm] = useState(false);

    const { appendMessage, reset: resetChat } = useCopilotChat();

    useEffect(() => {
        const interval = setInterval(() => {
            const inputContainer = document.querySelector('.copilotKitInput');
            if (inputContainer) {
                (inputContainer as HTMLElement).style.position = 'relative';
                setChatInputNode(inputContainer);
                clearInterval(interval);
            }
        }, 100);
        return () => clearInterval(interval);
    }, []);

    const handleVoiceTranscript = async (transcript: string) => {
        setVoiceError(null);
        await appendMessage(new TextMessage({ role: MessageRole.User, content: transcript }));
    };

    const handleNewChat = (clearForm: boolean) => {
        resetChat();
        if (clearForm) {
            setDisease('');
            setSymptoms('');
            setSeverity(5);
            setMedicalHistory('');
            setVikriti('');
            setPrakriti('');
            setTreatmentPlan(null);
            setDoctorPrescription('');
            setDoctorNotes('');
            setRating(null);
            setFeedback('');
        }
        setShowNewChatConfirm(false);
    };
    // ─────────────────────────────────────────────────────────────────────────

    // Feedback State
    const [rating, setRating] = useState<'positive' | 'negative' | null>(null);
    const [feedback, setFeedback] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Assessment State
    const [prakriti, setPrakriti] = useState<string>("");
    const [vikriti, setVikriti] = useState<string>("");
    const [severity, setSeverity] = useState<number>(5);
    const [disease, setDisease] = useState<string>("");
    const [symptoms, setSymptoms] = useState<string>("");
    const [medicalHistory, setMedicalHistory] = useState<string>("");

    // Doctor Prescription State
    const [doctorPrescription, setDoctorPrescription] = useState<string>("");
    const [doctorNotes, setDoctorNotes] = useState<string>("");

    // Disease validation state for AI
    const [allowedDiseases, setAllowedDiseases] = useState<string[]>([]);

    // Inline Add State
    const [addingHerb, setAddingHerb] = useState(false);
    const [newHerbName, setNewHerbName] = useState("");
    const [addingYoga, setAddingYoga] = useState(false);
    const [newYogaName, setNewYogaName] = useState("");
    const [addingDiet, setAddingDiet] = useState(false);
    const [newDietItem, setNewDietItem] = useState("");
    const [addingLifestyle, setAddingLifestyle] = useState(false);
    const [newLifestyleItem, setNewLifestyleItem] = useState("");

    // --- Add/Delete Handlers ---
    const addHerb = () => {
        if (!newHerbName.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, herbs: [...treatmentPlan.herbs, { name: newHerbName.trim(), dosage: '', benefits: 'Added by doctor' }] });
        setNewHerbName(""); setAddingHerb(false);
    };
    const deleteHerb = (idx: number) => {
        if (!treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, herbs: treatmentPlan.herbs.filter((_, i) => i !== idx) });
    };
    const addYoga = () => {
        if (!newYogaName.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, yoga: [...treatmentPlan.yoga, { practice: newYogaName.trim(), duration: '', benefits: 'Added by doctor' }] });
        setNewYogaName(""); setAddingYoga(false);
    };
    const deleteYoga = (idx: number) => {
        if (!treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, yoga: treatmentPlan.yoga.filter((_, i) => i !== idx) });
    };
    const addDiet = () => {
        if (!newDietItem.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, diet: [...treatmentPlan.diet, newDietItem.trim()] });
        setNewDietItem(""); setAddingDiet(false);
    };
    const deleteDiet = (idx: number) => {
        if (!treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, diet: treatmentPlan.diet.filter((_, i) => i !== idx) });
    };
    const addLifestyle = () => {
        if (!newLifestyleItem.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, lifestyle: [...treatmentPlan.lifestyle, newLifestyleItem.trim()] });
        setNewLifestyleItem(""); setAddingLifestyle(false);
    };
    const deleteLifestyle = (idx: number) => {
        if (!treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, lifestyle: treatmentPlan.lifestyle.filter((_, i) => i !== idx) });
    };

    // --- CopilotKit Integration ---
    useCopilotReadable({
        description: "Guidelines and Knowledge for Mapping Ayurvedic Form Fields",
        value: {
            mapping_rules: [
                "Map 'doshas' (current imbalance/vikriti) STRICTLY to one of these exact values: 'Vata', 'Pitta', 'Kapha'.",
                "Map 'prakriti' (constitution) STRICTLY to one of these exact values: 'Vata', 'Pitta', 'Kapha', 'Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha'.",
                "Extract the primary diagnosis or condition as 'disease'.",
                "Extract all symptoms into a comma-separated 'symptoms' string.",
                "Always map 'medicalHistory' to the 'comorbidity' parameter.",
                "If severity is not explicitly stated, estimate based on symptoms or default to 5."
            ]
        },
    });

    useCopilotReadable({
        description: "Current clinical assessment form state",
        value: { disease, symptoms, severity, medicalHistory, vikriti, prakriti },
    });

    useCopilotAction({
        name: "fill_clinical_assessment",
        description: "Fill the clinical assessment form with patient details. Always call this action to map doctor's input to the form.",
        parameters: [
            { name: "disease", type: "string", description: "Primary condition or disease name (e.g., Diabetes, Hypertension)" },
            { name: "symptoms", type: "string", description: "Comma-separated list of symptoms" },
            { name: "severity", type: "number", description: "Severity scale from 1 (mild) to 10 (severe)" },
            { name: "comorbidity", type: "string", description: "Medical history or comorbidities" },
            { name: "doshas", type: "string", description: "Current dosha imbalance (Vikriti). Allowed values: Vata, Pitta, Kapha" },
            { name: "prakriti", type: "string", description: "Constitution (Prakriti). Allowed values: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha" },
        ],
        handler: async (args: any) => {
            let returnMessage = "Clinical assessment form updated successfully.";

            if (args.disease) {
                const query = args.disease.trim().toLowerCase();
                const exactMatch = allowedDiseases.find(d => d.toLowerCase() === query);

                if (exactMatch) {
                    setDisease(exactMatch);
                } else if (allowedDiseases.length > 0) {
                    // Try to find similar diseases
                    const similar = allowedDiseases
                        .filter(d => d.toLowerCase().includes(query) || query.includes(d.toLowerCase()))
                        .slice(0, 5);

                    if (similar.length > 0) {
                        returnMessage = `Validation Error: The disease '${args.disease}' is not in the allowed list. DO NOT fill the disease field yet. Please ask the doctor if they meant one of these similar options: ${similar.join(', ')}.`;
                    } else {
                        returnMessage = `Validation Error: The disease '${args.disease}' is not recognized in the database. DO NOT fill the disease field yet. Please ask the doctor to clarify or use a standard medical term.`;
                    }
                } else {
                    // Fallback if list didn't load
                    setDisease(args.disease);
                }
            }

            if (args.symptoms) setSymptoms(args.symptoms);
            if (args.severity !== undefined && args.severity !== null) setSeverity(Number(args.severity));
            if (args.comorbidity) setMedicalHistory(args.comorbidity);
            if (args.doshas) setVikriti(args.doshas);
            if (args.prakriti) setPrakriti(args.prakriti);

            return returnMessage;
        },
    });

    useCopilotAction({
        name: "generate_treatment_plan",
        description: "Trigger AI treatment plan generation.",
        parameters: [],
        handler: async () => {
            await generatePlan();
            return "Treatment plan generated.";
        },
    });

    useEffect(() => {
        const fetchPatient = async () => {
            const data = await getPatient(id);
            setPatient(data);
            if (data && data.medical_records && data.medical_records.length > 0) {
                const lastRecord = data.medical_records[data.medical_records.length - 1];
                setDisease(lastRecord.diagnosis || "");
                setSymptoms(lastRecord.symptoms || "");
            }
            setLoading(false);
        };
        fetchPatient();
    }, [id]);

    useEffect(() => {
        const fetchDiseases = async () => {
            try {
                const res = await fetch('/api/ml/diseases');
                const data = await res.json();
                setAllowedDiseases(data.diseases || []);
            } catch (err) {
                console.error('Failed to fetch diseases for AI validation:', err);
            }
        };
        fetchDiseases();
    }, []);

    const generatePlan = async () => {
        if (!prakriti || !vikriti) {
            alert("Please complete the Clinical Assessment (Doshas & Prakriti) first.");
            return;
        }
        if (!disease) {
            alert("Please enter a disease name.");
            return;
        }

        setGenerating(true);
        try {
            const response = await fetch('/api/ml/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    age: patient?.age,
                    gender: patient?.gender,
                    prakriti,
                    vikriti,
                    disease,
                    symptoms: symptoms || undefined,
                    medical_history: medicalHistory || undefined,
                    severity,
                    bmi: 24.0
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                const errorMessage = errorData?.error || "Failed to generate plan";
                throw new Error(errorMessage);
            }

            const plan = await response.json();
            setTreatmentPlan(plan);
        } catch (error: any) {
            console.error("Failed to generate plan:", error);
            alert(error.message || "Error generating treatment plan.");
        } finally {
            setGenerating(false);
        }
    };

    const submitPrescription = async () => {
        setIsSubmitting(true);
        try {
            const res = await fetch('http://localhost:8000/api/prescribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patientId: id,
                    disease,
                    symptoms,
                    severity,
                    prakriti,
                    vikriti,
                    treatmentPlan,
                    doctorPrescription,
                    doctorNotes,
                    rating,
                    feedback,
                })
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || 'Failed to save');
            }
            alert("Treatment Plan Prescribed & Saved Successfully!");
            setTimeout(() => {
                router.push('/doctor?tab=completed');
            }, 500);
        } catch (error: any) {
            console.error(error);
            alert(error.message || "Failed to save prescription");
        } finally {
            setIsSubmitting(false);
        }
    };

    const getConfidenceBadge = () => {
        if (!treatmentPlan?.match_confidence) return null;
        const confidence = Math.round(treatmentPlan.match_confidence * 100);
        const method = treatmentPlan.match_method;

        let color = "bg-green-100 text-green-800 border-green-200";
        let label = "Exact Match";

        if (method === "fuzzy") {
            color = "bg-amber-100 text-amber-800 border-amber-200";
            label = "Fuzzy Match";
        } else if (method === "symptom_similarity") {
            color = "bg-blue-100 text-blue-800 border-blue-200";
            label = "Symptom Match";
        }

        return (
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${color}`}>
                <Target className="w-3 h-3" />
                {label} • {confidence}%
                {treatmentPlan.source_disease && (
                    <span className="font-normal ml-1">→ {treatmentPlan.source_disease}</span>
                )}
            </div>
        );
    };

    if (loading) return <div className="p-8 text-center">Loading patient data...</div>;
    if (!patient) return <div className="p-8 text-center text-red-500">Patient not found</div>;

    return (
        <>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100/50 p-6 pb-24 font-sans text-slate-800">
                <div className="max-w-6xl mx-auto space-y-8">

                    {/* Header */}
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-[0_0_15px_-3px_rgba(20,184,166,0.2)]">
                                <Stethoscope className="w-6 h-6" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Personalized Treatment Plan</h1>
                                <p className="text-muted-foreground mt-0.5 font-medium">AI-driven Clinical Decision Support System</p>
                            </div>
                        </div>
                        <div className={`bg-white/80 backdrop-blur-sm px-5 py-3 rounded-2xl border-t-4 shadow-sm flex items-center gap-4 ${patient.gender.toLowerCase() === 'female' ? 'border-t-pink-500 border-slate-200' :
                            patient.gender.toLowerCase() === 'transgender' ? 'border-t-amber-500 border-slate-200' :
                                'border-t-primary border-slate-200'
                            }`}>
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${patient.gender.toLowerCase() === 'female' ? 'bg-pink-100 text-pink-700' :
                                patient.gender.toLowerCase() === 'transgender' ? 'bg-amber-100 text-amber-700' :
                                    'bg-primary/10 text-primary'
                                }`}>
                                {patient.first_name[0]}{patient.last_name ? patient.last_name[0] : ''}
                            </div>
                            <div>
                                <div className="font-bold text-slate-900 text-lg tracking-tight">{patient.first_name} {patient.last_name}</div>
                                <div className="text-sm text-slate-500 font-medium">{patient.gender} • {patient.age} Years</div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                        {/* LEFT COLUMN: Clinical Assessment */}
                        <div className="space-y-6">
                            <Card className="border-t-4 border-t-primary shadow-md bg-white/90 backdrop-blur-sm">
                                <CardHeader className="pb-4">
                                    <div className="flex items-center gap-2 mb-1">
                                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                                            <Activity className="w-4 h-4" />
                                        </div>
                                        <CardTitle className="text-lg text-slate-800 tracking-tight">Clinical Assessment</CardTitle>
                                    </div>
                                    <CardDescription>Input patient parameters for AI analysis</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-5">
                                    {/* Disease Input */}
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">Primary Condition <span className="text-red-500">*</span></label>
                                        <DiseaseSearchDropdown
                                            value={disease}
                                            onChange={setDisease}
                                            required
                                            placeholder="Search for a disease..."
                                        />
                                    </div>

                                    {/* Symptoms Input */}
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                            <Stethoscope className="w-3.5 h-3.5 text-primary" />
                                            Symptoms
                                        </label>
                                        <div className="relative group">
                                            <textarea
                                                value={symptoms}
                                                onChange={(e) => setSymptoms(e.target.value)}
                                                className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                                placeholder="e.g. excessive thirst, frequent urination, fatigue..."
                                                rows={3}
                                            />
                                        </div>
                                    </div>

                                    {/* Severity Slider */}
                                    <div className="space-y-3 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center justify-between">
                                            <span>Severity (1-10)</span>
                                            <span className={`px-2 py-0.5 rounded-full font-bold text-xs ${severity > 7 ? 'bg-red-100 text-red-700' :
                                                severity > 4 ? 'bg-amber-100 text-amber-700' :
                                                    'bg-green-100 text-green-700'
                                                }`}>
                                                {severity} / 10
                                            </span>
                                        </label>
                                        <div className="flex items-center gap-4 px-1">
                                            <Slider
                                                value={[severity]}
                                                onValueChange={(vals) => setSeverity(vals[0])}
                                                max={10} min={1} step={1}
                                                className="flex-1 cursor-pointer"
                                            />
                                        </div>
                                    </div>

                                    {/* Comorbidity Input */}
                                    <div className="space-y-2 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                            <Activity className="w-3.5 h-3.5 text-primary" />
                                            Comorbidity
                                        </label>
                                        <textarea
                                            value={medicalHistory}
                                            onChange={(e) => setMedicalHistory(e.target.value)}
                                            className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                            placeholder="Any known medical history or comorbidities..."
                                            rows={2}
                                        />
                                    </div>

                                    {/* Doshas */}
                                    <div className="space-y-2 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">Doshas (Current Imbalance)</label>
                                        <Select onValueChange={setVikriti} value={vikriti}>
                                            <SelectTrigger className="bg-slate-50 focus:bg-white focus:ring-primary/20 focus:border-primary border-slate-200 rounded-xl hover:bg-slate-100 transition-colors">
                                                <SelectValue placeholder="Select Doshas" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Vata">Vata Aggravation</SelectItem>
                                                <SelectItem value="Pitta">Pitta Aggravation</SelectItem>
                                                <SelectItem value="Kapha">Kapha Aggravation</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    {/* Prakriti */}
                                    <div className="space-y-2 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">Prakriti (Constitution)</label>
                                        <Select onValueChange={setPrakriti} value={prakriti}>
                                            <SelectTrigger className="bg-slate-50 focus:bg-white focus:ring-primary/20 focus:border-primary border-slate-200 rounded-xl hover:bg-slate-100 transition-colors">
                                                <SelectValue placeholder="Select Prakriti" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="Vata">Vata (Air/Ether)</SelectItem>
                                                <SelectItem value="Pitta">Pitta (Fire/Water)</SelectItem>
                                                <SelectItem value="Kapha">Kapha (Earth/Water)</SelectItem>
                                                <SelectItem value="Vata-Pitta">Vata-Pitta</SelectItem>
                                                <SelectItem value="Pitta-Kapha">Pitta-Kapha</SelectItem>
                                                <SelectItem value="Vata-Kapha">Vata-Kapha</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <Button
                                        className="w-full mt-4 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white shadow-lg shadow-primary/20 hover:shadow-primary/30 h-12 rounded-xl text-base font-bold tracking-wide transition-all hover:scale-[1.02] active:scale-[0.98]"
                                        onClick={generatePlan}
                                        disabled={generating}
                                    >
                                        {generating ? (
                                            <span className="flex items-center gap-2">
                                                <Brain className="w-4 h-4 animate-pulse" /> Analyzing...
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-2">
                                                <Sparkles className="w-4 h-4" /> Generate AI Plan
                                            </span>
                                        )}
                                    </Button>
                                </CardContent>
                            </Card>

                            {/* Explainability Panel */}
                            {treatmentPlan && (
                                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 text-slate-100 border-none shadow-xl overflow-hidden relative rounded-2xl">
                                    <div className="absolute -top-4 -right-4 p-3 opacity-10">
                                        <Brain className="w-32 h-32 text-white" />
                                    </div>
                                    <CardHeader className="pb-3 border-b border-white/5 bg-black/10">
                                        <CardTitle className="text-lg flex items-center gap-2 text-primary tracking-wide">
                                            <Sparkles className="w-5 h-5 text-primary animate-pulse" />
                                            AI Clinical Rationale
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4 pt-5 relative z-10 px-5 pb-6">
                                        {/* Match Info Badge */}
                                        <div className="mb-4">
                                            {getConfidenceBadge()}
                                        </div>

                                        <div className="space-y-2">
                                            {treatmentPlan.explainability.map((reason, idx) => (
                                                <div key={idx} className="flex gap-2 text-sm text-slate-300">
                                                    <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                                                    {reason}
                                                </div>
                                            ))}
                                        </div>
                                        <div className="pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
                                            <div>
                                                <span className="text-xs text-slate-400 uppercase tracking-wider">Improvement</span>
                                                <div className="text-green-400 font-bold text-2xl flex items-center gap-1">
                                                    <TrendingUp className="w-5 h-5" />
                                                    {treatmentPlan.predicted_improvement}%
                                                </div>
                                            </div>
                                            <div>
                                                <span className="text-xs text-slate-400 uppercase tracking-wider">Duration</span>
                                                <div className="font-bold text-xl flex items-center gap-1">
                                                    <Clock className="w-4 h-4 text-slate-400" />
                                                    {treatmentPlan.recommended_duration_weeks} Weeks
                                                </div>
                                            </div>
                                        </div>
                                        {treatmentPlan.doshas_affected && (
                                            <div className="pt-3 border-t border-white/10">
                                                <span className="text-xs text-slate-400 uppercase tracking-wider">Doshas Affected</span>
                                                <div className="text-purple-300 font-semibold mt-1">{treatmentPlan.doshas_affected}</div>
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            )}
                        </div>

                        {/* RIGHT COLUMN: Treatment Plan */}
                        <div className="lg:col-span-2 space-y-6">
                            {!treatmentPlan ? (
                                <div className="h-full border-2 border-dashed border-slate-200/60 rounded-3xl flex flex-col items-center justify-center text-slate-400 min-h-[500px] bg-slate-50/30 backdrop-blur-sm relative overflow-hidden group">
                                    <div className="absolute inset-0 bg-gradient-to-b from-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
                                    <div className="relative z-10 flex flex-col items-center">
                                        <div className="w-24 h-24 mb-6 rounded-full bg-primary/5 flex items-center justify-center animate-pulse">
                                            <Leaf className="w-12 h-12 text-primary/40" />
                                        </div>
                                        <h3 className="text-xl font-bold text-slate-600 tracking-tight">Awaiting Clinical Inputs</h3>
                                        <p className="text-slate-500 max-w-sm text-center mt-2 leading-relaxed">Complete the assessment on the left to generate a personalized Ayurvedic treatment plan.</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">

                                    {/* ===== HERBAL INTERVENTIONS ===== */}
                                    <Card className="overflow-hidden border-none shadow-md ring-1 ring-emerald-100 bg-white/90 backdrop-blur-sm rounded-2xl">
                                        <CardHeader className="pb-4 bg-gradient-to-r from-emerald-50 to-white relative">
                                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500"></div>
                                            <CardTitle className="flex items-center gap-2 text-emerald-900 text-lg">
                                                <div className="p-1.5 bg-emerald-100 rounded-lg text-emerald-600">
                                                    <Leaf className="w-4 h-4" />
                                                </div>
                                                Herbal Interventions
                                                {treatmentPlan.formulation && (
                                                    <Badge variant="outline" className="text-emerald-700 border-emerald-300 bg-emerald-50 font-medium ml-2 text-xs">
                                                        {treatmentPlan.formulation}
                                                    </Badge>
                                                )}
                                                <button onClick={() => setAddingHerb(true)} className="ml-auto w-8 h-8 rounded-full bg-emerald-100 hover:bg-emerald-200 flex items-center justify-center text-emerald-700 transition-transform hover:scale-105 shadow-sm" title="Add herb">
                                                    <Plus className="w-4 h-4 text-emerald-700" strokeWidth={3} />
                                                </button>
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="grid gap-3 pt-5 px-5 pb-5">
                                            {treatmentPlan.herbs.map((herb, idx) => (
                                                <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                                                    <h4 className="font-bold text-slate-900 text-lg">{herb.name}</h4>
                                                    <button onClick={() => deleteHerb(idx)} className="w-8 h-8 rounded-full bg-slate-50 hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors" title="Remove">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                            {addingHerb && (
                                                <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-200">
                                                    <input type="text" value={newHerbName} onChange={e => setNewHerbName(e.target.value)} onKeyDown={e => e.key === 'Enter' && addHerb()} placeholder="Enter herb name..." autoFocus className="flex-1 px-3 py-2 rounded-lg border border-green-300 text-sm focus:ring-2 focus:ring-green-400 outline-none" />
                                                    <button onClick={addHerb} className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors">Add</button>
                                                    <button onClick={() => { setAddingHerb(false); setNewHerbName(""); }} className="w-8 h-8 rounded-full hover:bg-green-100 flex items-center justify-center text-slate-500"><X className="w-4 h-4" /></button>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* ===== YOGA & PHYSICAL THERAPY ===== */}
                                    <Card className="overflow-hidden border-none shadow-md ring-1 ring-amber-100 bg-white/90 backdrop-blur-sm rounded-2xl">
                                        <CardHeader className="pb-4 bg-gradient-to-r from-amber-50 to-white relative">
                                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500"></div>
                                            <CardTitle className="flex items-center gap-2 text-amber-900 text-lg">
                                                <div className="p-1.5 bg-amber-100 rounded-lg text-amber-600">
                                                    <Activity className="w-4 h-4" />
                                                </div>
                                                Yoga & Physical Therapy
                                                <button onClick={() => setAddingYoga(true)} className="ml-auto w-8 h-8 rounded-full bg-amber-100 hover:bg-amber-200 flex items-center justify-center text-amber-700 transition-transform hover:scale-105 shadow-sm" title="Add yoga">
                                                    <Plus className="w-4 h-4 text-amber-700" strokeWidth={3} />
                                                </button>
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="grid gap-3 pt-5 px-5 pb-5">
                                            {treatmentPlan.yoga.map((yoga, idx) => (
                                                <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                                                    <h4 className="font-bold text-slate-900 text-lg">{yoga.practice}</h4>
                                                    <button onClick={() => deleteYoga(idx)} className="w-8 h-8 rounded-full bg-slate-50 hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors" title="Remove">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                            {addingYoga && (
                                                <div className="flex items-center gap-2 p-3 bg-orange-50 rounded-xl border border-orange-200">
                                                    <input type="text" value={newYogaName} onChange={e => setNewYogaName(e.target.value)} onKeyDown={e => e.key === 'Enter' && addYoga()} placeholder="Enter yoga/exercise name..." autoFocus className="flex-1 px-3 py-2 rounded-lg border border-orange-300 text-sm focus:ring-2 focus:ring-orange-400 outline-none" />
                                                    <button onClick={addYoga} className="px-3 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700 transition-colors">Add</button>
                                                    <button onClick={() => { setAddingYoga(false); setNewYogaName(""); }} className="w-8 h-8 rounded-full hover:bg-orange-100 flex items-center justify-center text-slate-500"><X className="w-4 h-4" /></button>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* ===== DIET & LIFESTYLE GRID ===== */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <Card className="overflow-hidden border-none shadow-md ring-1 ring-rose-100 bg-white/90 backdrop-blur-sm rounded-2xl">
                                            <CardHeader className="pb-4 bg-gradient-to-r from-rose-50 to-white relative">
                                                <div className="absolute left-0 top-0 bottom-0 w-1 bg-rose-500"></div>
                                                <CardTitle className="flex items-center gap-2 text-rose-900 text-lg">
                                                    <div className="p-1.5 bg-rose-100 rounded-lg text-rose-600">
                                                        <Coffee className="w-4 h-4" />
                                                    </div>
                                                    Dietary Guidelines
                                                    <button onClick={() => setAddingDiet(true)} className="ml-auto w-8 h-8 rounded-full bg-rose-100 hover:bg-rose-200 flex items-center justify-center text-rose-700 transition-transform hover:scale-105 shadow-sm" title="Add diet item">
                                                        <Plus className="w-4 h-4 text-rose-700" strokeWidth={3} />
                                                    </button>
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-4 px-5 pb-5">
                                                <ul className="space-y-2.5">
                                                    {treatmentPlan.diet.map((item, idx) => (
                                                        <li key={idx} className="flex items-center gap-3 text-sm text-slate-700 bg-amber-50/50 p-2.5 rounded-lg">
                                                            <span className="text-amber-500 font-bold">•</span>
                                                            <span className="flex-1">{item}</span>
                                                            <button onClick={() => deleteDiet(idx)} className="w-6 h-6 rounded-full hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors shrink-0" title="Remove">
                                                                <Trash2 className="w-3.5 h-3.5" />
                                                            </button>
                                                        </li>
                                                    ))}
                                                </ul>
                                                {addingDiet && (
                                                    <div className="flex items-center gap-2 mt-3 p-2.5 bg-amber-50 rounded-lg border border-amber-200">
                                                        <input type="text" value={newDietItem} onChange={e => setNewDietItem(e.target.value)} onKeyDown={e => e.key === 'Enter' && addDiet()} placeholder="New dietary guideline..." autoFocus className="flex-1 px-3 py-1.5 rounded-lg border border-amber-300 text-sm focus:ring-2 focus:ring-amber-400 outline-none" />
                                                        <button onClick={addDiet} className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-medium hover:bg-amber-700 transition-colors">Add</button>
                                                        <button onClick={() => { setAddingDiet(false); setNewDietItem(""); }} className="text-slate-500 hover:text-slate-700"><X className="w-4 h-4" /></button>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>

                                        <Card className="overflow-hidden border-none shadow-md ring-1 ring-blue-100 bg-white/90 backdrop-blur-sm rounded-2xl">
                                            <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-white relative">
                                                <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500"></div>
                                                <CardTitle className="flex items-center gap-2 text-blue-900 text-lg">
                                                    <div className="p-1.5 bg-blue-100 rounded-lg text-blue-600">
                                                        <Sun className="w-4 h-4" />
                                                    </div>
                                                    Lifestyle Changes
                                                    <button onClick={() => setAddingLifestyle(true)} className="ml-auto w-8 h-8 rounded-full bg-blue-100 hover:bg-blue-200 flex items-center justify-center text-blue-700 transition-transform hover:scale-105 shadow-sm" title="Add lifestyle item">
                                                        <Plus className="w-4 h-4 text-blue-700" strokeWidth={3} />
                                                    </button>
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-4 px-5 pb-5">
                                                <ul className="space-y-2.5">
                                                    {treatmentPlan.lifestyle.map((item, idx) => (
                                                        <li key={idx} className="flex items-center gap-3 text-sm text-slate-700 bg-indigo-50/50 p-2.5 rounded-lg">
                                                            <span className="text-indigo-500 font-bold">•</span>
                                                            <span className="flex-1">{item}</span>
                                                            <button onClick={() => deleteLifestyle(idx)} className="w-6 h-6 rounded-full hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors shrink-0" title="Remove">
                                                                <Trash2 className="w-3.5 h-3.5" />
                                                            </button>
                                                        </li>
                                                    ))}
                                                </ul>
                                                {addingLifestyle && (
                                                    <div className="flex items-center gap-2 mt-3 p-2.5 bg-indigo-50 rounded-lg border border-indigo-200">
                                                        <input type="text" value={newLifestyleItem} onChange={e => setNewLifestyleItem(e.target.value)} onKeyDown={e => e.key === 'Enter' && addLifestyle()} placeholder="New lifestyle change..." autoFocus className="flex-1 px-3 py-1.5 rounded-lg border border-indigo-300 text-sm focus:ring-2 focus:ring-indigo-400 outline-none" />
                                                        <button onClick={addLifestyle} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 transition-colors">Add</button>
                                                        <button onClick={() => { setAddingLifestyle(false); setNewLifestyleItem(""); }} className="text-slate-500 hover:text-slate-700"><X className="w-4 h-4" /></button>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    </div>

                                    {/* ===== PREVENTION, PROGNOSIS & COMPLICATIONS ===== */}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        {/* Prevention */}
                                        {treatmentPlan.prevention.length > 0 && (
                                            <Card className="overflow-hidden border-none shadow-sm ring-1 ring-emerald-100 bg-white/90 rounded-2xl">
                                                <CardHeader className="pb-3 bg-emerald-50/50">
                                                    <CardTitle className="flex items-center gap-2 text-emerald-800 text-base font-bold">
                                                        <Shield className="w-4 h-4 text-emerald-600" />
                                                        Prevention
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pt-4 px-4 pb-4">
                                                    <ul className="space-y-2.5">
                                                        {treatmentPlan.prevention.map((item, idx) => (
                                                            <li key={idx} className="flex gap-2.5 text-sm text-slate-700 leading-snug">
                                                                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                                                                {item}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Prognosis */}
                                        {treatmentPlan.prognosis && (
                                            <Card className="overflow-hidden border-none shadow-sm ring-1 ring-blue-100 bg-white/90 rounded-2xl">
                                                <CardHeader className="pb-3 bg-blue-50/50">
                                                    <CardTitle className="flex items-center gap-2 text-blue-800 text-base font-bold">
                                                        <Heart className="w-4 h-4 text-blue-600" />
                                                        Prognosis
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pt-4 px-4 pb-4">
                                                    <p className="text-sm text-slate-700 leading-relaxed">{treatmentPlan.prognosis}</p>
                                                </CardContent>
                                            </Card>
                                        )}

                                        {/* Complications */}
                                        {treatmentPlan.complications.length > 0 && (
                                            <Card className="overflow-hidden border-none shadow-sm ring-1 ring-red-100 bg-white/90 rounded-2xl">
                                                <CardHeader className="pb-3 bg-red-50/50">
                                                    <CardTitle className="flex items-center gap-2 text-red-800 text-base font-bold">
                                                        <AlertTriangle className="w-4 h-4 text-red-600" />
                                                        Complications
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pt-4 px-4 pb-4">
                                                    <ul className="space-y-2">
                                                        {treatmentPlan.complications.map((item, idx) => (
                                                            <li key={idx} className="flex gap-2 text-sm text-slate-700">
                                                                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                                                                {item}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>

                                    {/* ===== MEDICAL INTERVENTION (if applicable) ===== */}
                                    {treatmentPlan.medical_intervention && (
                                        <Card className="border border-slate-200 bg-slate-50">
                                            <CardContent className="py-4 px-5">
                                                <div className="flex items-center gap-3">
                                                    <Stethoscope className="w-5 h-5 text-slate-500" />
                                                    <div>
                                                        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Medical Intervention (if needed)</span>
                                                        <p className="text-sm text-slate-700 mt-0.5">{treatmentPlan.medical_intervention}</p>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    )}

                                    {/* ===== DOCTOR'S PRESCRIPTION & MEDICINES ===== */}
                                    <div className="mt-10 border-t border-slate-200/60 pt-8">
                                        <h3 className="font-bold text-slate-900 mb-5 flex items-center gap-2 text-xl tracking-tight">
                                            <div className="p-1.5 bg-primary/10 rounded-lg text-primary">
                                                <ClipboardList className="w-5 h-5" />
                                            </div>
                                            Doctor&apos;s Prescription
                                        </h3>

                                        <div className="space-y-5">
                                            {/* Prescription Notes */}
                                            <Card className="border-none shadow-sm ring-1 ring-primary/20 rounded-2xl overflow-hidden">
                                                <CardHeader className="pb-3 bg-primary/5">
                                                    <CardTitle className="flex items-center gap-2 text-primary text-base font-bold">
                                                        <FileText className="w-4 h-4" />
                                                        Prescription Notes
                                                    </CardTitle>
                                                    <CardDescription>Additional instructions and clinical notes</CardDescription>
                                                </CardHeader>
                                                <CardContent className="pt-4 pb-5 px-5">
                                                    <textarea
                                                        className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                                        placeholder="e.g. Follow up after 2 weeks. Blood sugar test before next visit. Avoid cold beverages..."
                                                        rows={3}
                                                        value={doctorNotes}
                                                        onChange={(e) => setDoctorNotes(e.target.value)}
                                                    />
                                                </CardContent>
                                            </Card>
                                        </div>
                                    </div>

                                    {/* ===== FEEDBACK & SUBMIT ===== */}
                                    <div className="mt-8 border-t border-slate-200/60 pt-8">
                                        <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2 text-lg tracking-tight">
                                            <div className="p-1.5 bg-indigo-100 rounded-lg text-indigo-600">
                                                <Brain className="w-4 h-4" />
                                            </div>
                                            AI Feedback
                                        </h3>

                                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5 ring-1 ring-slate-100">
                                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                                <label className="text-sm font-bold text-slate-700">How accurate was this AI plan?</label>
                                                <div className="flex gap-3">
                                                    <Button
                                                        variant={rating === 'positive' ? "default" : "outline"}
                                                        size="sm"
                                                        onClick={() => setRating('positive')}
                                                        className={`rounded-xl transition-all ${rating === 'positive' ? "bg-emerald-500 hover:bg-emerald-600 text-white shadow-emerald-200 shadow-md" : "text-emerald-700 border-emerald-200 hover:bg-emerald-50"}`}
                                                    >
                                                        <ThumbsUp className="w-4 h-4 mr-1.5" /> Accurate
                                                    </Button>
                                                    <Button
                                                        variant={rating === 'negative' ? "default" : "outline"}
                                                        size="sm"
                                                        onClick={() => setRating('negative')}
                                                        className={`rounded-xl transition-all ${rating === 'negative' ? "bg-red-500 hover:bg-red-600 text-white shadow-red-200 shadow-md" : "text-red-700 border-red-200 hover:bg-red-50"}`}
                                                    >
                                                        <ThumbsDown className="w-4 h-4 mr-1.5" /> Needs Changes
                                                    </Button>
                                                </div>
                                            </div>

                                            <textarea
                                                className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-100 focus:border-indigo-300 outline-none transition-all resize-none shadow-sm"
                                                placeholder="Notes on AI accuracy — what was correct/incorrect?"
                                                rows={2}
                                                value={feedback}
                                                onChange={(e) => setFeedback(e.target.value)}
                                            />

                                            <div className="flex justify-end pt-2">
                                                <Button
                                                    size="lg"
                                                    className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white shadow-lg shadow-primary/20 hover:shadow-primary/30 h-12 rounded-xl text-base font-bold tracking-wide transition-all hover:scale-[1.02] active:scale-[0.98] w-full md:w-auto px-8"
                                                    onClick={submitPrescription}
                                                    disabled={isSubmitting}
                                                >
                                                    {isSubmitting ? 'Saving...' : 'Save & Prescribe Treatment'}
                                                    <Save className="w-4 h-4 ml-2" />
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
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
                            language={selectedLanguage}
                            isListening={isListening}
                            setIsListening={setIsListening}
                        />
                    </div>
                </>,
                chatInputNode
            )}
        </>
    );
}
