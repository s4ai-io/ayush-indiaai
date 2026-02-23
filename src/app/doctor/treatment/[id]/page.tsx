'use client';

import { useEffect, useState, use } from 'react';
import { getPatient } from '@/app/actions/getPatient';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
    Brain, Activity, Leaf, Coffee, Moon, Sun, ArrowRight, CheckCircle, Info,
    ThumbsUp, ThumbsDown, Save, AlertTriangle, Shield, Heart, Stethoscope,
    FileText, Pill, ClipboardList, Sparkles, TrendingUp, Clock, Target
} from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"
import { DiseaseSearchDropdown } from '@/components/ui/DiseaseSearchDropdown';

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
    const [patient, setPatient] = useState<Patient | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [treatmentPlan, setTreatmentPlan] = useState<TreatmentPlan | null>(null);

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

    // Doctor Prescription State
    const [doctorPrescription, setDoctorPrescription] = useState<string>("");
    const [doctorMedicines, setDoctorMedicines] = useState<string>("");
    const [doctorNotes, setDoctorNotes] = useState<string>("");

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

    const generatePlan = async () => {
        if (!prakriti || !vikriti) {
            alert("Please complete the Clinical Assessment (Prakriti & Vikriti) first.");
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
                    severity,
                    bmi: 24.0
                })
            });

            if (!response.ok) throw new Error("Failed to generate plan");

            const plan = await response.json();
            setTreatmentPlan(plan);
        } catch (error) {
            console.error(error);
            alert("Error generating treatment plan.");
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
                    doctorMedicines,
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
        <div className="min-h-screen bg-slate-50 p-6 pb-24">
            <div className="max-w-6xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Personalized Treatment Plan</h1>
                        <p className="text-slate-500 mt-1">AI-driven Clinical Decision Support System</p>
                    </div>
                    <div className="bg-white px-4 py-3 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center text-purple-700 font-bold text-lg">
                            {patient.first_name[0]}{patient.last_name ? patient.last_name[0] : ''}
                        </div>
                        <div>
                            <div className="font-bold text-slate-900 text-lg">{patient.first_name} {patient.last_name}</div>
                            <div className="text-sm text-slate-500 font-medium">{patient.gender} • {patient.age} Years</div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* LEFT COLUMN: Clinical Assessment */}
                    <div className="space-y-6">
                        <Card className="border-t-4 border-t-purple-500 shadow-md">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-slate-800">
                                    <Activity className="w-5 h-5 text-purple-500" />
                                    Clinical Assessment
                                </CardTitle>
                                <CardDescription>Input patient parameters for AI analysis</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-5">
                                {/* Disease Input */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700">Primary Condition <span className="text-red-500">*</span></label>
                                    <DiseaseSearchDropdown
                                        value={disease}
                                        onChange={setDisease}
                                        required
                                        placeholder="Search for a disease..."
                                    />
                                </div>

                                {/* Symptoms Input */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700 flex items-center gap-2">
                                        <Stethoscope className="w-4 h-4 text-purple-400" />
                                        Symptoms <span className="text-xs text-slate-400 font-normal">(optional)</span>
                                    </label>
                                    <textarea
                                        value={symptoms}
                                        onChange={(e) => setSymptoms(e.target.value)}
                                        className="w-full p-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all resize-none"
                                        placeholder="e.g. excessive thirst, frequent urination, fatigue..."
                                        rows={3}
                                    />
                                </div>

                                {/* Severity Slider */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700">Severity (1-10)</label>
                                    <div className="flex items-center gap-4">
                                        <Slider
                                            value={[severity]}
                                            onValueChange={(vals) => setSeverity(vals[0])}
                                            max={10} min={1} step={1}
                                            className="flex-1"
                                        />
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${severity > 7 ? 'bg-red-100 text-red-700' :
                                            severity > 4 ? 'bg-amber-100 text-amber-700' :
                                                'bg-green-100 text-green-700'
                                            }`}>
                                            {severity}
                                        </div>
                                    </div>
                                </div>

                                {/* Prakriti */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700">Prakriti (Constitution)</label>
                                    <Select onValueChange={setPrakriti} value={prakriti}>
                                        <SelectTrigger className="focus:ring-purple-500">
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

                                {/* Vikriti */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-slate-700">Vikriti (Current Imbalance)</label>
                                    <Select onValueChange={setVikriti} value={vikriti}>
                                        <SelectTrigger className="focus:ring-purple-500">
                                            <SelectValue placeholder="Select Imbalance" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="Vata">Vata Aggravation</SelectItem>
                                            <SelectItem value="Pitta">Pitta Aggravation</SelectItem>
                                            <SelectItem value="Kapha">Kapha Aggravation</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <Button
                                    className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg shadow-purple-200"
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
                            <Card className="bg-slate-900 text-slate-100 border-none shadow-xl overflow-hidden relative">
                                <div className="absolute top-0 right-0 p-3 opacity-10">
                                    <Brain className="w-24 h-24 text-white" />
                                </div>
                                <CardHeader>
                                    <CardTitle className="text-lg flex items-center gap-2 text-purple-300">
                                        <Info className="w-5 h-5" />
                                        AI Clinical Rationale
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4 relative z-10">
                                    {/* Match Info Badge */}
                                    <div className="mb-3">
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
                            <div className="h-full border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 min-h-[400px] bg-slate-50/50">
                                <Leaf className="w-16 h-16 mb-4 opacity-10 text-slate-900" />
                                <h3 className="text-lg font-medium text-slate-600">Awaiting Clinical Inputs</h3>
                                <p className="text-slate-400 max-w-xs text-center mt-1">Complete the assessment on the left to generate a personalized Ayurvedic treatment plan.</p>
                            </div>
                        ) : (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                                {/* ===== HERBAL INTERVENTIONS ===== */}
                                <Card className="overflow-hidden border-l-4 border-l-green-500">
                                    <CardHeader className="pb-3 bg-green-50/30">
                                        <CardTitle className="flex items-center gap-2 text-green-800">
                                            <Leaf className="w-5 h-5 text-green-600" />
                                            Herbal Interventions
                                            {treatmentPlan.formulation && (
                                                <Badge variant="outline" className="ml-auto text-green-700 border-green-300 bg-green-50 font-normal">
                                                    {treatmentPlan.formulation}
                                                </Badge>
                                            )}
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="grid gap-3 pt-5">
                                        {treatmentPlan.herbs.map((herb, idx) => (
                                            <div key={idx} className="flex items-start justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                                                <div>
                                                    <h4 className="font-bold text-slate-900 text-lg">{herb.name}</h4>
                                                    <p className="text-green-700 font-medium mt-1 text-sm">{herb.dosage}</p>
                                                </div>
                                                <TooltipProvider>
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center hover:bg-green-50 text-slate-400 hover:text-green-600 transition-colors">
                                                                <Info className="w-4 h-4" />
                                                            </div>
                                                        </TooltipTrigger>
                                                        <TooltipContent side="left" className="max-w-xs">
                                                            <p>{herb.benefits}</p>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </TooltipProvider>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>

                                {/* ===== YOGA & PHYSICAL THERAPY ===== */}
                                <Card className="overflow-hidden border-l-4 border-l-orange-500">
                                    <CardHeader className="pb-3 bg-orange-50/30">
                                        <CardTitle className="flex items-center gap-2 text-orange-800">
                                            <Activity className="w-5 h-5 text-orange-600" />
                                            Yoga & Physical Therapy
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="grid gap-3 pt-5">
                                        {treatmentPlan.yoga.map((yoga, idx) => (
                                            <div key={idx} className="flex items-start justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                                                <div>
                                                    <h4 className="font-bold text-slate-900 text-lg">{yoga.practice}</h4>
                                                    <p className="text-orange-700 font-medium mt-1 text-sm">{yoga.duration}</p>
                                                </div>
                                                <TooltipProvider>
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <div className="w-8 h-8 rounded-full bg-slate-50 flex items-center justify-center hover:bg-orange-50 text-slate-400 hover:text-orange-600 transition-colors">
                                                                <Info className="w-4 h-4" />
                                                            </div>
                                                        </TooltipTrigger>
                                                        <TooltipContent side="left" className="max-w-xs">
                                                            <p>{yoga.benefits}</p>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </TooltipProvider>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>

                                {/* ===== DIET & LIFESTYLE GRID ===== */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <Card className="border-l-4 border-l-amber-400">
                                        <CardHeader className="pb-3 bg-amber-50/30">
                                            <CardTitle className="flex items-center gap-2 text-amber-800">
                                                <Coffee className="w-5 h-5 text-amber-600" />
                                                Dietary Guidelines
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="pt-5">
                                            <ul className="space-y-2.5">
                                                {treatmentPlan.diet.map((item, idx) => (
                                                    <li key={idx} className="flex gap-3 text-sm text-slate-700 bg-amber-50/50 p-2.5 rounded-lg">
                                                        <span className="text-amber-500 font-bold">•</span> {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>

                                    <Card className="border-l-4 border-l-indigo-400">
                                        <CardHeader className="pb-3 bg-indigo-50/30">
                                            <CardTitle className="flex items-center gap-2 text-indigo-800">
                                                <Sun className="w-5 h-5 text-indigo-600" />
                                                Lifestyle Changes
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="pt-5">
                                            <ul className="space-y-2.5">
                                                {treatmentPlan.lifestyle.map((item, idx) => (
                                                    <li key={idx} className="flex gap-3 text-sm text-slate-700 bg-indigo-50/50 p-2.5 rounded-lg">
                                                        <span className="text-indigo-500 font-bold">•</span> {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>
                                </div>

                                {/* ===== PREVENTION, PROGNOSIS & COMPLICATIONS ===== */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {/* Prevention */}
                                    {treatmentPlan.prevention.length > 0 && (
                                        <Card className="border-l-4 border-l-emerald-400">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="flex items-center gap-2 text-emerald-800 text-base">
                                                    <Shield className="w-4 h-4 text-emerald-600" />
                                                    Prevention
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-2">
                                                <ul className="space-y-2">
                                                    {treatmentPlan.prevention.map((item, idx) => (
                                                        <li key={idx} className="flex gap-2 text-sm text-slate-700">
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
                                        <Card className="border-l-4 border-l-blue-400">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="flex items-center gap-2 text-blue-800 text-base">
                                                    <Heart className="w-4 h-4 text-blue-600" />
                                                    Prognosis
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-2">
                                                <p className="text-sm text-slate-700 bg-blue-50/50 p-3 rounded-lg">{treatmentPlan.prognosis}</p>
                                            </CardContent>
                                        </Card>
                                    )}

                                    {/* Complications */}
                                    {treatmentPlan.complications.length > 0 && (
                                        <Card className="border-l-4 border-l-red-400">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="flex items-center gap-2 text-red-800 text-base">
                                                    <AlertTriangle className="w-4 h-4 text-red-600" />
                                                    Complications
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-2">
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
                                <div className="mt-8 border-t-2 border-purple-200 pt-8">
                                    <h3 className="font-bold text-slate-900 mb-5 flex items-center gap-2 text-xl">
                                        <ClipboardList className="w-6 h-6 text-purple-600" />
                                        Doctor&apos;s Prescription
                                    </h3>

                                    <div className="space-y-5">
                                        {/* Medicines */}
                                        <Card className="border-l-4 border-l-rose-500 shadow-sm">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="flex items-center gap-2 text-rose-800 text-base">
                                                    <Pill className="w-4 h-4 text-rose-600" />
                                                    Prescribed Medicines
                                                </CardTitle>
                                                <CardDescription>Enter prescribed medicines with dosage</CardDescription>
                                            </CardHeader>
                                            <CardContent className="pt-2">
                                                <textarea
                                                    className="w-full p-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-rose-400 outline-none shadow-inner bg-white"
                                                    placeholder={"e.g.\nMetformin 500mg — 1 tablet after meals, twice daily\nVitamin D3 60K — Once weekly\nTriphala Churna — 1 tsp with warm water at bedtime"}
                                                    rows={4}
                                                    value={doctorMedicines}
                                                    onChange={(e) => setDoctorMedicines(e.target.value)}
                                                />
                                            </CardContent>
                                        </Card>

                                        {/* Prescription Notes */}
                                        <Card className="border-l-4 border-l-violet-500 shadow-sm">
                                            <CardHeader className="pb-2">
                                                <CardTitle className="flex items-center gap-2 text-violet-800 text-base">
                                                    <FileText className="w-4 h-4 text-violet-600" />
                                                    Prescription Notes
                                                </CardTitle>
                                                <CardDescription>Additional instructions and clinical notes</CardDescription>
                                            </CardHeader>
                                            <CardContent className="pt-2">
                                                <textarea
                                                    className="w-full p-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-violet-400 outline-none shadow-inner bg-white"
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
                                <div className="mt-6 border-t border-slate-200 pt-6">
                                    <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2 text-lg">
                                        <Brain className="w-5 h-5 text-purple-600" />
                                        AI Feedback
                                    </h3>

                                    <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-2xl border border-purple-100 shadow-sm space-y-4">
                                        <div className="flex items-center justify-between">
                                            <label className="text-sm font-semibold text-purple-900">How accurate was this AI plan?</label>
                                            <div className="flex gap-2">
                                                <Button
                                                    variant={rating === 'positive' ? "default" : "outline"}
                                                    size="sm"
                                                    onClick={() => setRating('positive')}
                                                    className={rating === 'positive' ? "bg-green-600 hover:bg-green-700 text-white shadow-md" : "text-green-700 border-green-200 hover:bg-green-50"}
                                                >
                                                    <ThumbsUp className="w-4 h-4 mr-1" /> Accurate
                                                </Button>
                                                <Button
                                                    variant={rating === 'negative' ? "default" : "outline"}
                                                    size="sm"
                                                    onClick={() => setRating('negative')}
                                                    className={rating === 'negative' ? "bg-red-600 hover:bg-red-700 text-white shadow-md" : "text-red-700 border-red-200 hover:bg-red-50"}
                                                >
                                                    <ThumbsDown className="w-4 h-4 mr-1" /> Needs Changes
                                                </Button>
                                            </div>
                                        </div>

                                        <textarea
                                            className="w-full p-3 border border-purple-200 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 outline-none shadow-inner bg-white"
                                            placeholder="Notes on AI accuracy — what was correct/incorrect?"
                                            rows={2}
                                            value={feedback}
                                            onChange={(e) => setFeedback(e.target.value)}
                                        />

                                        <div className="flex justify-end">
                                            <Button
                                                size="lg"
                                                className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700 w-full md:w-auto shadow-lg hover:shadow-xl transition-all"
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
    );
}
