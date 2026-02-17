'use client';

import { useEffect, useState, use } from 'react';
import { getPatient } from '@/app/actions/getPatient';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Brain, Activity, Leaf, Coffee, Moon, Sun, ArrowRight, CheckCircle, Info } from 'lucide-react';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip"

interface Patient {
    id: string;
    basicInfo: {
        firstName: string;
        lastName: string;
        gender: string;
        dateOfBirth: string;
        abhaId: string;
    };
    medicalRecords: {
        diagnosis: string;
        symptoms: string;
    }[];
}

interface TreatmentPlan {
    herbs: { name: string; dosage: string; benefits: string }[];
    yoga: { practice: string; duration: string; benefits: string }[];
    diet: string[];
    lifestyle: string[];
    predicted_improvement: number;
    recommended_duration_weeks: number;
    cluster_id?: number;
    explainability: string[];
}

export default function TreatmentPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [patient, setPatient] = useState<Patient | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [treatmentPlan, setTreatmentPlan] = useState<TreatmentPlan | null>(null);

    // Assessment State
    const [prakriti, setPrakriti] = useState<string>("");
    const [vikriti, setVikriti] = useState<string>("");
    const [severity, setSeverity] = useState<number>(5);
    const [disease, setDisease] = useState<string>("");

    useEffect(() => {
        const fetchPatient = async () => {
            const data = await getPatient(id);
            setPatient(data);
            if (data && data.medicalRecords.length > 0) {
                // Pre-fill disease from last record
                setDisease(data.medicalRecords[data.medicalRecords.length - 1].diagnosis);
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

        setGenerating(true);
        try {
            const age = new Date().getFullYear() - new Date(patient?.basicInfo.dateOfBirth || "").getFullYear();

            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    age,
                    gender: patient?.basicInfo.gender,
                    prakriti,
                    vikriti,
                    disease,
                    severity,
                    bmi: 24.0 // Mock BMI for now
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

    if (loading) return <div className="p-8 text-center">Loading patient data...</div>;
    if (!patient) return <div className="p-8 text-center text-red-500">Patient not found</div>;

    return (
        <div className="min-h-screen bg-slate-50 p-6 pb-24">
            <div className="max-w-6xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Personalized Treatment Plan</h1>
                        <p className="text-slate-500 mt-1">AI-driven Clinical Decision Support System</p>
                    </div>
                    <div className="bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold">
                            {patient.basicInfo.firstName[0]}{patient.basicInfo.lastName[0]}
                        </div>
                        <div>
                            <div className="font-semibold">{patient.basicInfo.firstName} {patient.basicInfo.lastName}</div>
                            <div className="text-xs text-slate-500">{patient.basicInfo.gender}, {new Date().getFullYear() - new Date(patient.basicInfo.dateOfBirth).getFullYear()} years</div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* LEFT COLUMN: Clinical Assessment */}
                    <div className="space-y-6">
                        <Card className="border-t-4 border-t-blue-500 shadow-md">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Activity className="w-5 h-5 text-blue-500" />
                                    Clinical Assessment
                                </CardTitle>
                                <CardDescription>Input patient parameters for AI analysis</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Primary Condition</label>
                                    <input
                                        type="text"
                                        value={disease}
                                        onChange={(e) => setDisease(e.target.value)}
                                        className="w-full p-2 border rounded-md"
                                        placeholder="e.g. Dengue, Arthritis"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Severity (1-10)</label>
                                    <div className="flex items-center gap-4">
                                        <Slider
                                            value={[severity]}
                                            onValueChange={(vals) => setSeverity(vals[0])}
                                            max={10} min={1} step={1}
                                            className="flex-1"
                                        />
                                        <span className="font-bold w-6">{severity}</span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Prakriti (Constitution)</label>
                                    <Select onValueChange={setPrakriti} value={prakriti}>
                                        <SelectTrigger>
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

                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Vikriti (Current Imbalance)</label>
                                    <Select onValueChange={setVikriti} value={vikriti}>
                                        <SelectTrigger>
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
                                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
                                    onClick={generatePlan}
                                    disabled={generating}
                                >
                                    {generating ? (
                                        <span className="flex items-center gap-2">
                                            <Brain className="w-4 h-4 animate-pulse" /> Analying...
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-2">
                                            <Brain className="w-4 h-4" /> Generate AI Plan
                                        </span>
                                    )}
                                </Button>
                            </CardContent>
                        </Card>

                        {/* Explainability Panel (Visible after generation) */}
                        {treatmentPlan && (
                            <Card className="bg-slate-900 text-slate-100 border-none shadow-lg">
                                <CardHeader>
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <Info className="w-5 h-5 text-sky-400" />
                                        AI Clinical Rationale
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {treatmentPlan.cluster_id && (
                                        <div className="bg-white/10 p-3 rounded-lg text-sm">
                                            <span className="text-sky-300 font-semibold block mb-1">Population Health Insight</span>
                                            Patient matches <strong>Cluster #{treatmentPlan.cluster_id}</strong> (similar demographics & prakriti).
                                        </div>
                                    )}
                                    <div className="space-y-2">
                                        {treatmentPlan.explainability.map((reason, idx) => (
                                            <div key={idx} className="flex gap-2 text-sm text-slate-300">
                                                <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                                                {reason}
                                            </div>
                                        ))}
                                    </div>
                                    <div className="pt-2 border-t border-white/10">
                                        <div className="flex justify-between items-center text-sm">
                                            <span>Predicted Improvement</span>
                                            <span className="text-green-400 font-bold text-lg">{treatmentPlan.predicted_improvement}%</span>
                                        </div>
                                        <div className="flex justify-between items-center text-sm">
                                            <span>Est. Duration</span>
                                            <span className="font-semibold">{treatmentPlan.recommended_duration_weeks} Weeks</span>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )}
                    </div>

                    {/* RIGHT COLUMN: Treatment Plan */}
                    <div className="lg:col-span-2 space-y-6">
                        {!treatmentPlan ? (
                            <div className="h-full border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 min-h-[400px]">
                                <Leaf className="w-12 h-12 mb-4 opacity-20" />
                                <p>Complete assessment to generate personalized plan</p>
                            </div>
                        ) : (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                                {/* Herbs Section */}
                                <Card>
                                    <CardHeader className="pb-3">
                                        <CardTitle className="flex items-center gap-2 text-green-700">
                                            <Leaf className="w-5 h-5" />
                                            Herbal Interventions
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="grid gap-4">
                                        {treatmentPlan.herbs.map((herb, idx) => (
                                            <div key={idx} className="flex items-start justify-between p-3 bg-green-50 rounded-lg border border-green-100">
                                                <div>
                                                    <h4 className="font-semibold text-green-900">{herb.name}</h4>
                                                    <p className="text-sm text-green-700">{herb.dosage}</p>
                                                </div>
                                                <TooltipProvider>
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <Info className="w-4 h-4 text-green-400" />
                                                        </TooltipTrigger>
                                                        <TooltipContent>
                                                            <p>{herb.benefits}</p>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </TooltipProvider>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>

                                {/* Yoga Section */}
                                <Card>
                                    <CardHeader className="pb-3">
                                        <CardTitle className="flex items-center gap-2 text-orange-700">
                                            <Activity className="w-5 h-5" />
                                            Yoga & Pranayama
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="grid gap-4">
                                        {treatmentPlan.yoga.map((yoga, idx) => (
                                            <div key={idx} className="flex items-start justify-between p-3 bg-orange-50 rounded-lg border border-orange-100">
                                                <div>
                                                    <h4 className="font-semibold text-orange-900">{yoga.practice}</h4>
                                                    <p className="text-sm text-orange-700">{yoga.duration}</p>
                                                </div>
                                                <TooltipProvider>
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <Info className="w-4 h-4 text-orange-400" />
                                                        </TooltipTrigger>
                                                        <TooltipContent>
                                                            <p>{yoga.benefits}</p>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </TooltipProvider>
                                            </div>
                                        ))}
                                    </CardContent>
                                </Card>

                                {/* Diet & Lifestyle Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <Card>
                                        <CardHeader className="pb-3">
                                            <CardTitle className="flex items-center gap-2 text-amber-700">
                                                <Coffee className="w-5 h-5" />
                                                Dietary Guidelines
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <ul className="space-y-2">
                                                {treatmentPlan.diet.map((item, idx) => (
                                                    <li key={idx} className="flex gap-2 text-sm text-slate-700">
                                                        <span className="text-amber-500">•</span> {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>

                                    <Card>
                                        <CardHeader className="pb-3">
                                            <CardTitle className="flex items-center gap-2 text-indigo-700">
                                                <Sun className="w-5 h-5" />
                                                Lifestyle Changes
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <ul className="space-y-2">
                                                {treatmentPlan.lifestyle.map((item, idx) => (
                                                    <li key={idx} className="flex gap-2 text-sm text-slate-700">
                                                        <span className="text-indigo-500">•</span> {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </CardContent>
                                    </Card>
                                </div>

                                <div className="flex justify-end pt-4">
                                    <Button size="lg" className="bg-slate-900 text-white hover:bg-slate-800">
                                        Accept & Prescribe Plan
                                        <ArrowRight className="w-4 h-4 ml-2" />
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
