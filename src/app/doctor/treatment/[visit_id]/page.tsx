'use client';

import { useEffect, useState, use } from 'react';
import { createPortal } from 'react-dom';
import { CopilotKit, useCopilotReadable, useCopilotAction, useCopilotChat } from "@copilotkit/react-core";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
    Brain, Activity, Leaf, Coffee, Moon, Sun, CheckCircle, AlertTriangle,
    Shield, Heart, Stethoscope, FileText, ClipboardList, Sparkles, TrendingUp,
    Clock, Target, Plus, Trash2, X, RefreshCw, ThumbsUp, ThumbsDown, Save, Phone,
} from 'lucide-react';
import { DiseaseSearchDropdown } from '@/components/ui/DiseaseSearchDropdown';
import { useRouter } from "next/navigation";
import { VoiceInputButton } from "@/components/VoiceInputButton";
import { LanguageSelector } from "@/components/LanguageSelector";
import { API_BASE } from '@/lib/config';
import type { VisitPatient, VisitContext, TreatmentPlan } from '@/types';



// ─── Outer shell (CopilotKit provider) ───────────────────────────────────────
export default function TreatmentPage({ params }: { params: Promise<{ visit_id: string }> }) {
    const { visit_id } = use(params);
    return (
        <CopilotKit runtimeUrl="/api/copilotkit" agent="treatment_agent">
            <CopilotSidebar
                instructions="You are an AI Clinical Assistant helping the doctor fill the treatment assessment form."
                labels={{
                    title: "🩺 Treatment Assistant",
                    initial: "Hello Doctor! Describe the patient's condition and I'll fill the clinical assessment for you.",
                }}
                defaultOpen={false}
                clickOutsideToClose={false}
            >
                <TreatmentPageContent visitId={visit_id} />
            </CopilotSidebar>
        </CopilotKit>
    );
}

// ─── Inner page content ───────────────────────────────────────────────────────
function TreatmentPageContent({ visitId }: { visitId: string }) {
    const router = useRouter();

    // Visit / patient state
    const [visitCtx, setVisitCtx] = useState<VisitContext | null>(null);
    const [loading, setLoading] = useState(true);

    // Generation
    const [generating, setGenerating] = useState(false);
    const [treatmentPlan, setTreatmentPlan] = useState<TreatmentPlan | null>(null);

    // Clinical assessment — pre-filled from visit, editable
    const [disease, setDisease] = useState('');
    const [symptoms, setSymptoms] = useState('');
    const [medicalHistory, setMedicalHistory] = useState('');
    const [prakriti, setPrakriti] = useState('');
    const [vikriti, setVikriti] = useState('');

    // Doctor prescribed manual inputs mapped from Agent
    const [doctorHerbs, setDoctorHerbs] = useState<string[]>([]);
    const [doctorYoga, setDoctorYoga] = useState<string[]>([]);
    const [doctorDiet, setDoctorDiet] = useState<string[]>([]);
    const [doctorLifestyle, setDoctorLifestyle] = useState<string[]>([]);

    // Doctor prescription / feedback
    const [doctorNotes, setDoctorNotes] = useState('');
    const [rating, setRating] = useState<'positive' | 'negative' | null>(null);
    const [feedback, setFeedback] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // AI Proposal Banner State
    const [proposedData, setProposedData] = useState<any>(null);

    // Inline add/delete state
    const [addingHerb, setAddingHerb] = useState(false);
    const [newHerbName, setNewHerbName] = useState('');
    const [addingYoga, setAddingYoga] = useState(false);
    const [newYogaName, setNewYogaName] = useState('');
    const [addingDiet, setAddingDiet] = useState(false);
    const [newDietItem, setNewDietItem] = useState('');
    const [addingLifestyle, setAddingLifestyle] = useState(false);
    const [newLifestyleItem, setNewLifestyleItem] = useState('');
    const [suggestedDiseases, setSuggestedDiseases] = useState<string[]>([]);
    const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);

    // Voice / CopilotKit portal
    const [selectedLanguage, setSelectedLanguage] = useState('hi-IN');
    const [isListening, setIsListening] = useState(false);
    const [chatInputNode, setChatInputNode] = useState<Element | null>(null);
    const [showNewChatConfirm, setShowNewChatConfirm] = useState(false);

    const { appendMessage, reset: resetChat } = useCopilotChat();

    useEffect(() => {
        const iv = setInterval(() => {
            const el = document.querySelector('.copilotKitInput');
            if (el) { (el as HTMLElement).style.position = 'relative'; setChatInputNode(el); clearInterval(iv); }
        }, 100);
        return () => clearInterval(iv);
    }, []);

    const handleVoiceTranscript = async (transcript: string) => {
        await appendMessage(new TextMessage({ role: MessageRole.User, content: transcript }));
    };

    const handleNewChat = (clearForm: boolean) => {
        resetChat();
        if (clearForm) {
            setDisease(''); setSymptoms(''); setMedicalHistory('');
            setVikriti(''); setPrakriti(''); setTreatmentPlan(null);
            setDoctorNotes(''); setRating(null); setFeedback('');
            setDoctorHerbs([]); setDoctorYoga([]); setDoctorDiet([]); setDoctorLifestyle([]);
            setProposedData(null);
        }
        setShowNewChatConfirm(false);
    };

    // ── Load visit context ─────────────────────────────────────────────────
    useEffect(() => {
        const fetchVisit = async () => {
            try {
                // Use the full visit endpoint to get patient demographics too
                const res = await fetch(`${API_BASE}/api/visits/${visitId}`, { cache: 'no-store' });
                if (!res.ok) throw new Error('Visit not found');
                const data = await res.json();

                setVisitCtx({
                    patientId: data.patient?.id || '',
                    patientName: `${data.patient?.firstName || ''} ${data.patient?.lastName || ''}`.trim(),
                    patientMobile: data.patient?.mobile || '',
                    symptoms: data.visit?.symptoms || '',
                    diagnosis: data.visit?.diagnosis || '',
                    doctorNotes: data.visit?.notes || '',
                    prakriti: data.visit?.prakriti || '',
                    vikriti: data.visit?.vikriti || '',
                    severity: data.visit?.severity || '5',
                    comorbidities: data.visit?.comorbidities || '',
                    patient: data.patient,
                });

                // Pre-fill clinical assessment from visit
                setDisease(data.visit?.diagnosis || '');
                setSymptoms(data.visit?.symptoms || '');
                setMedicalHistory(data.visit?.comorbidities || '');
                setPrakriti(data.visit?.prakriti || '');
                setVikriti(data.visit?.vikriti || '');
            } catch {
                // fallback to the lighter endpoint
                try {
                    const res2 = await fetch(`${API_BASE}/api/consultations/${visitId}/treatment`);
                    if (res2.ok) {
                        const d = await res2.json();
                        setVisitCtx({
                            patientId: d.patientId || '', patientName: d.patientName || 'Unknown',
                            patientMobile: d.patientMobile || '', symptoms: d.symptoms || '',
                            diagnosis: d.diagnosis || '', doctorNotes: d.doctorNotes || '',
                            prakriti: d.prakriti || '', vikriti: d.vikriti || '',
                            severity: d.severity || '5', comorbidities: d.comorbidities || '',
                        });
                        setDisease(d.diagnosis || '');
                        setSymptoms(d.symptoms || '');
                        setMedicalHistory(d.comorbidities || '');
                        setPrakriti(d.prakriti || '');
                        setVikriti(d.vikriti || '');
                    }
                } catch { }
            } finally {
                setLoading(false);
            }
        };
        fetchVisit();
    }, [visitId]);

    // ── CopilotKit readable + actions ──────────────────────────────────────
    useCopilotReadable({
        description: "Current clinical assessment form state",
        value: { disease, symptoms, medicalHistory, vikriti, prakriti },
    });

    useCopilotAction({
        name: "propose_clinical_assessment",
        description: "Extract the doctor's spoken notes and propose them to be added into the clinical assessment.",
        parameters: [
            { name: "disease", type: "string", description: "Disease name" },
            { name: "symptoms", type: "string", description: "Comma-separated symptoms" },
            { name: "comorbidity", type: "string", description: "Medical history / comorbidities" },
            { name: "doshas", type: "string", description: "Current dosha imbalance: Vata, Pitta, or Kapha" },
            { name: "prakriti", type: "string", description: "Constitution: Vata, Pitta, Kapha, Vata-Pitta, Pitta-Kapha, Vata-Kapha" },
            { name: "herbs", type: "string", description: "Doctor prescribed herbs" },
            { name: "yoga", type: "string", description: "Doctor prescribed yoga" },
            { name: "diet", type: "string", description: "Doctor prescribed diet" },
            { name: "lifestyle", type: "string", description: "Doctor prescribed lifestyle" },
        ],
        handler: async (args: any) => {
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
                return mergeObj(prev, args);
            });
            return "Proposed data updated for doctor review.";
        },
    });

    const handleAcceptProposed = () => {
        if (!proposedData) return;
        if (proposedData.disease) setDisease(proposedData.disease);
        if (proposedData.symptoms) setSymptoms(proposedData.symptoms);
        if (proposedData.comorbidity) setMedicalHistory(proposedData.comorbidity);
        if (proposedData.doshas) setVikriti(proposedData.doshas);
        if (proposedData.prakriti) setPrakriti(proposedData.prakriti);

        if (proposedData.herbs) setDoctorHerbs(proposedData.herbs.split(',').map((h: string) => h.trim()).filter(Boolean));
        if (proposedData.yoga) setDoctorYoga(proposedData.yoga.split(',').map((y: string) => y.trim()).filter(Boolean));
        if (proposedData.diet) setDoctorDiet(proposedData.diet.split(',').map((d: string) => d.trim()).filter(Boolean));
        if (proposedData.lifestyle) setDoctorLifestyle(proposedData.lifestyle.split(',').map((l: string) => l.trim()).filter(Boolean));

        setProposedData(null);
    };

    const handleDiscardProposed = () => {
        setProposedData(null);
        setSuggestedDiseases([]);
        setSelectedSuggestion(null);
    };

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (proposedData?.disease) {
                try {
                    const res = await fetch(`${API_BASE}/api/diseases/suggestions?q=${encodeURIComponent(proposedData.disease)}`);
                    if (res.ok) {
                        const data = await res.json();
                        setSuggestedDiseases(data.suggestions || []);
                    }
                } catch (err) {
                    console.error("Error fetching suggestions:", err);
                }
            } else {
                setSuggestedDiseases([]);
            }
        };
        fetchSuggestions();
    }, [proposedData?.disease]);

    const handleProceedWithUpdated = () => {
        if (!proposedData) return;
        const finalDisease = selectedSuggestion || proposedData.disease;

        setDisease(finalDisease);
        if (proposedData.symptoms) setSymptoms(proposedData.symptoms);
        if (proposedData.comorbidity) setMedicalHistory(proposedData.comorbidity);
        if (proposedData.doshas) setVikriti(proposedData.doshas);
        if (proposedData.prakriti) setPrakriti(proposedData.prakriti);

        if (proposedData.herbs) setDoctorHerbs(proposedData.herbs.split(',').map((h: string) => h.trim()).filter(Boolean));
        if (proposedData.yoga) setDoctorYoga(proposedData.yoga.split(',').map((y: string) => y.trim()).filter(Boolean));
        if (proposedData.diet) setDoctorDiet(proposedData.diet.split(',').map((d: string) => d.trim()).filter(Boolean));
        if (proposedData.lifestyle) setDoctorLifestyle(proposedData.lifestyle.split(',').map((l: string) => l.trim()).filter(Boolean));

        setProposedData(null);
        setSuggestedDiseases([]);
        setSelectedSuggestion(null);
    };

    useCopilotAction({
        name: "generate_treatment_plan",
        description: "Trigger AI treatment plan generation.",
        parameters: [],
        handler: async () => { await generatePlan(); return "Treatment plan generated."; },
    });

    // ── Add/delete helpers ─────────────────────────────────────────────────
    const addHerb = () => {
        if (!newHerbName.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, herbs: [...treatmentPlan.herbs, { name: newHerbName.trim(), dosage: '', benefits: 'Added by doctor' }] });
        setNewHerbName(''); setAddingHerb(false);
    };
    const deleteHerb = (i: number) => treatmentPlan && setTreatmentPlan({ ...treatmentPlan, herbs: treatmentPlan.herbs.filter((_, idx) => idx !== i) });

    const addYoga = () => {
        if (!newYogaName.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, yoga: [...treatmentPlan.yoga, { practice: newYogaName.trim(), duration: '', benefits: 'Added by doctor' }] });
        setNewYogaName(''); setAddingYoga(false);
    };
    const deleteYoga = (i: number) => treatmentPlan && setTreatmentPlan({ ...treatmentPlan, yoga: treatmentPlan.yoga.filter((_, idx) => idx !== i) });

    const addDiet = () => {
        if (!newDietItem.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, diet: [...treatmentPlan.diet, newDietItem.trim()] });
        setNewDietItem(''); setAddingDiet(false);
    };
    const deleteDiet = (i: number) => treatmentPlan && setTreatmentPlan({ ...treatmentPlan, diet: treatmentPlan.diet.filter((_, idx) => idx !== i) });

    const addLifestyle = () => {
        if (!newLifestyleItem.trim() || !treatmentPlan) return;
        setTreatmentPlan({ ...treatmentPlan, lifestyle: [...treatmentPlan.lifestyle, newLifestyleItem.trim()] });
        setNewLifestyleItem(''); setAddingLifestyle(false);
    };
    const deleteLifestyle = (i: number) => treatmentPlan && setTreatmentPlan({ ...treatmentPlan, lifestyle: treatmentPlan.lifestyle.filter((_, idx) => idx !== i) });

    // ── Generate plan ──────────────────────────────────────────────────────
    const generatePlan = async () => {
        if (!disease) { alert("Please enter a disease name."); return; }
        if (!prakriti || !vikriti) { alert("Please fill Doshas & Prakriti."); return; }

        setGenerating(true);
        try {
            const res = await fetch('/api/ml/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    age: visitCtx?.patient?.age || '',
                    gender: visitCtx?.patient?.gender || '',
                    prakriti, vikriti, disease,
                    symptoms: symptoms || undefined,
                    medical_history: medicalHistory || undefined
                }),
            });
            if (!res.ok) throw new Error('Failed to generate plan');
            const generatedPlan = await res.json();

            if (!generatedPlan.no_match_found) {
                // Merge doctor specifics
                if (doctorHerbs.length > 0) {
                    generatedPlan.herbs = generatedPlan.herbs || [];
                    const existingNames = generatedPlan.herbs.map((h: any) => h.name.toLowerCase());
                    doctorHerbs.forEach(herb => {
                        if (!existingNames.includes(herb.toLowerCase())) {
                            generatedPlan.herbs.unshift({ name: herb, dosage: 'As prescribed', benefits: 'Added by doctor' });
                        }
                    });
                }
                if (doctorYoga.length > 0) {
                    generatedPlan.yoga = generatedPlan.yoga || [];
                    const existingNames = generatedPlan.yoga.map((y: any) => y.practice.toLowerCase());
                    doctorYoga.forEach(yoga => {
                        if (!existingNames.includes(yoga.toLowerCase())) {
                            generatedPlan.yoga.unshift({ practice: yoga, duration: 'As prescribed', benefits: 'Added by doctor' });
                        }
                    });
                }
                if (doctorDiet.length > 0) {
                    generatedPlan.diet = generatedPlan.diet || [];
                    doctorDiet.forEach(diet => {
                        if (!generatedPlan.diet.some((d: string) => d.toLowerCase() === diet.toLowerCase())) {
                            generatedPlan.diet.unshift(diet);
                        }
                    });
                }
                if (doctorLifestyle.length > 0) {
                    generatedPlan.lifestyle = generatedPlan.lifestyle || [];
                    doctorLifestyle.forEach(lifestyle => {
                        if (!generatedPlan.lifestyle.some((l: string) => l.toLowerCase() === lifestyle.toLowerCase())) {
                            generatedPlan.lifestyle.unshift(lifestyle);
                        }
                    });
                }
            }

            setTreatmentPlan(generatedPlan);
        } catch {
            alert("Error generating treatment plan.");
        } finally {
            setGenerating(false);
        }
    };

    // ── Submit prescription ────────────────────────────────────────────────
    const submitPrescription = async () => {
        setIsSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/api/prescribe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patientId: visitCtx?.patientId || '',
                    visitId,
                    disease, symptoms, prakriti, vikriti, comorbidities: medicalHistory,
                    treatmentPlan,
                    doctorNotes,
                    rating,
                    feedback,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Failed to save');
            alert("Treatment Plan Prescribed & Saved Successfully!");
            setTimeout(() => router.push('/doctor?tab=completed'), 500);
        } catch (err: any) {
            alert(err.message || "Failed to save prescription");
        } finally {
            setIsSubmitting(false);
        }
    };

    // ── NAMC Code Badge ───────────────────────────────────────────────────
    const getConfidenceBadge = () => {
        if (!treatmentPlan?.namc_code) return null;
        return (
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border bg-emerald-100 text-emerald-800 border-emerald-200`}>
                <Target className="w-3 h-3" />
                NAMC: {treatmentPlan.namc_code}
                {treatmentPlan.namc_term && <span className="font-normal ml-1">→ {treatmentPlan.namc_term} {treatmentPlan.namc_term_devanagari ? `(${treatmentPlan.namc_term_devanagari})` : ''}</span>}
            </div>
        );
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Loading visit data...</div>;

    const patientGender = visitCtx?.patient?.gender?.toLowerCase() || '';
    const avatarBg = patientGender === 'female' ? 'bg-pink-100 text-pink-700 border-pink-200' :
        patientGender === 'transgender' ? 'bg-amber-100 text-amber-700 border-amber-200' :
            'bg-primary/10 text-primary border-primary/20';
    const headerBorder = patientGender === 'female' ? 'border-t-pink-500' :
        patientGender === 'transgender' ? 'border-t-amber-500' : 'border-t-primary';
    const patientInitial = visitCtx?.patientName?.[0] ?? '?';

    return (
        <>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100/50 p-6 pb-24 font-sans text-slate-800">
                <div className="max-w-6xl mx-auto space-y-8">

                    {/* ── Header ── */}
                    <div className="flex justify-between items-start flex-wrap gap-4">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-[0_0_15px_-3px_rgba(20,184,166,0.2)]">
                                <Stethoscope className="w-6 h-6" />
                            </div>
                            <div>
                                <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Personalized Treatment Plan</h1>
                                <p className="text-muted-foreground mt-0.5 font-medium text-sm">AI-driven Clinical Decision Support System</p>
                            </div>
                        </div>

                        {/* Patient badge */}
                        <div className={`bg-white/80 backdrop-blur-sm px-5 py-3 rounded-2xl border-t-4 shadow-sm flex items-center gap-4 ${headerBorder} border-slate-200`}>
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg border ${avatarBg}`}>
                                {patientInitial}
                            </div>
                            <div>
                                <div className="font-bold text-slate-900 text-lg tracking-tight">{visitCtx?.patientName || 'Unknown'}</div>
                                <div className="text-sm text-slate-500 font-medium flex items-center gap-2">
                                    {visitCtx?.patient?.gender && <span>{visitCtx.patient.gender}</span>}
                                    {visitCtx?.patient?.age && <span>• {visitCtx.patient.age} yrs</span>}
                                    {visitCtx?.patientMobile && (
                                        <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{visitCtx.patientMobile}</span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {proposedData && (
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 shadow-sm mb-8 animate-in slide-in-from-top-4">
                            <h3 className="text-lg font-semibold text-amber-800 mb-4 flex items-center">
                                <CheckCircle className="w-5 h-5 mr-2" /> AI Extracted Data Available for Review
                            </h3>
                            <div className="text-sm text-slate-700 space-y-2 mb-6">
                                <p>The AI listener has extracted the following details from your conversation:</p>
                                <div className="bg-white p-4 rounded-lg border border-amber-100 max-h-64 overflow-y-auto w-full">
                                    <ul className="list-disc list-inside space-y-1">
                                        {proposedData.disease && <li><strong>Disease:</strong> {proposedData.disease}</li>}
                                        {proposedData.symptoms && <li><strong>Symptoms:</strong> {proposedData.symptoms}</li>}
                                        {proposedData.comorbidity && <li><strong>Comorbidity:</strong> {proposedData.comorbidity}</li>}
                                        {proposedData.doshas && <li><strong>Doshas:</strong> {proposedData.doshas}</li>}
                                        {proposedData.comorbidity && <li><strong>Comorbidity:</strong> {proposedData.comorbidity}</li>}
                                        {proposedData.doshas && <li><strong>Doshas:</strong> {proposedData.doshas}</li>}
                                        {proposedData.prakriti && <li><strong>Prakriti:</strong> {proposedData.prakriti}</li>}
                                        {proposedData.herbs && <li><strong>Herbs:</strong> {proposedData.herbs}</li>}
                                        {proposedData.yoga && <li><strong>Yoga:</strong> {proposedData.yoga}</li>}
                                        {proposedData.diet && <li><strong>Diet:</strong> {proposedData.diet}</li>}
                                        {proposedData.diet && <li><strong>Diet:</strong> {proposedData.diet}</li>}
                                        {proposedData.lifestyle && <li><strong>Lifestyle:</strong> {proposedData.lifestyle}</li>}
                                    </ul>
                                </div>
                            </div>

                            {suggestedDiseases.length > 0 && (
                                <div className="mb-6 animate-in fade-in slide-in-from-left-4 duration-500">
                                    <label className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-2 block flex items-center gap-1.5 font-sans">
                                        <Sparkles className="w-3.5 h-3.5" /> Standardized Disease Matches (Select One)
                                    </label>
                                    <div className="flex flex-wrap gap-2">
                                        {suggestedDiseases.map((sug) => (
                                            <button
                                                key={sug}
                                                onClick={() => setSelectedSuggestion(sug === selectedSuggestion ? null : sug)}
                                                className={`px-4 py-2 rounded-full text-sm font-medium transition-all border-2 ${selectedSuggestion === sug
                                                    ? "bg-amber-600 border-amber-700 text-white shadow-md scale-105"
                                                    : "bg-white border-amber-200 text-amber-700 hover:border-amber-400 hover:bg-amber-50"
                                                    }`}
                                            >
                                                {sug}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-4">
                                <Button
                                    type="button"
                                    variant="default"
                                    onClick={handleAcceptProposed}
                                    className="bg-amber-600 hover:bg-amber-700 text-white shadow-sm font-semibold"
                                >
                                    <CheckCircle className="w-4 h-4 mr-2" />
                                    Accept Raw Info
                                </Button>
                                <Button
                                    type="button"
                                    variant="secondary"
                                    onClick={handleProceedWithUpdated}
                                    className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-md font-bold px-6 border-b-4 border-emerald-800 active:border-b-0 active:translate-y-1 transition-all"
                                >
                                    <RefreshCw className="w-4 h-4 mr-2" />
                                    Proceed with Updated Disease
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={handleDiscardProposed}
                                    className="border-amber-300 text-amber-700 hover:bg-amber-100"
                                >
                                    <X className="w-4 h-4 mr-2" />
                                    Discard
                                </Button>
                            </div>
                        </div>
                    )}

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                        {/* ── LEFT: Clinical Assessment ── */}
                        <div className="space-y-6">
                            <Card className="border-t-4 border-t-primary shadow-md bg-white/90 backdrop-blur-sm">
                                <CardHeader className="pb-4">
                                    <div className="flex items-center gap-2 mb-1">
                                        <div className="p-2 bg-primary/10 rounded-lg text-primary"><Activity className="w-4 h-4" /></div>
                                        <CardTitle className="text-lg text-slate-800 tracking-tight">Clinical Assessment</CardTitle>
                                    </div>
                                    <CardDescription>Input patient parameters for AI analysis</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-5">
                                    {/* Disease */}
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">Primary Condition <span className="text-red-500">*</span></label>
                                        <DiseaseSearchDropdown value={disease} onChange={setDisease} required placeholder="Search for a disease..." />
                                    </div>

                                    {/* Symptoms */}
                                    <div className="space-y-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                            <Stethoscope className="w-3.5 h-3.5 text-primary" /> Symptoms
                                        </label>
                                        <textarea
                                            value={symptoms}
                                            onChange={e => setSymptoms(e.target.value)}
                                            className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                            placeholder="e.g. excessive thirst, frequent urination, fatigue..."
                                            rows={3}
                                        />
                                    </div>

                                    {/* Comorbidity */}
                                    <div className="space-y-2 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                            <Activity className="w-3.5 h-3.5 text-primary" /> Comorbidity
                                        </label>
                                        <textarea
                                            value={medicalHistory}
                                            onChange={e => setMedicalHistory(e.target.value)}
                                            className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                            placeholder="Any known medical history or comorbidities..."
                                            rows={2}
                                        />
                                    </div>

                                    {/* Doshas */}
                                    <div className="space-y-2 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">Doshas (Current Imbalance)</label>
                                        <Select onValueChange={setVikriti} value={vikriti}>
                                            <SelectTrigger className="bg-slate-50 border-slate-200 rounded-xl hover:bg-slate-100 transition-colors">
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
                                            <SelectTrigger className="bg-slate-50 border-slate-200 rounded-xl hover:bg-slate-100 transition-colors">
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
                                        className="w-full mt-4 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white shadow-lg h-12 rounded-xl text-base font-bold tracking-wide transition-all hover:scale-[1.02] active:scale-[0.98]"
                                        onClick={generatePlan}
                                        disabled={generating}
                                    >
                                        {generating
                                            ? <span className="flex items-center gap-2"><Brain className="w-4 h-4 animate-pulse" /> Analyzing...</span>
                                            : <span className="flex items-center gap-2"><Sparkles className="w-4 h-4" /> Generate AI Plan</span>
                                        }
                                    </Button>
                                </CardContent>
                            </Card>

                            {/* Explainability Panel 
                            {treatmentPlan && (
                                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 text-slate-100 border-none shadow-xl overflow-hidden relative rounded-2xl">
                                    <div className="absolute -top-4 -right-4 p-3 opacity-10">
                                        <Brain className="w-32 h-32 text-white" />
                                    </div>
                                    <CardHeader className="pb-3 border-b border-white/5 bg-black/10">
                                        <CardTitle className="text-lg flex items-center gap-2 text-primary tracking-wide">
                                            <Sparkles className="w-5 h-5 text-primary animate-pulse" /> AI Clinical Rationale
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4 pt-5 relative z-10 px-5 pb-6">
                                        <div className="mb-4">{getConfidenceBadge()}</div>
                                        <div className="space-y-2">
                                            {(treatmentPlan.explainability || []).map((reason, idx) => (
                                                <div key={idx} className="flex gap-2 text-sm text-slate-300">
                                                    <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" /> {reason}
                                                </div>
                                            ))}
                                        </div>
                                        <div className="pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
                                            <div>
                                                <span className="text-xs text-slate-400 uppercase tracking-wider">Improvement</span>
                                                <div className="text-green-400 font-bold text-2xl flex items-center gap-1">
                                                    <TrendingUp className="w-5 h-5" /> {treatmentPlan.predicted_improvement}%
                                                </div>
                                            </div>
                                            <div>
                                                <span className="text-xs text-slate-400 uppercase tracking-wider">Duration</span>
                                                <div className="font-bold text-xl flex items-center gap-1">
                                                    <Clock className="w-4 h-4 text-slate-400" /> {treatmentPlan.recommended_duration_weeks} Weeks
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
                            */}
                        </div>

                        {/* ── RIGHT: Treatment Plan ── */}
                        <div className="lg:col-span-2 space-y-6">
                            {!treatmentPlan ? (
                                <div className="h-full border-2 border-dashed border-slate-200/60 rounded-3xl flex flex-col items-center justify-center text-slate-400 min-h-[500px] bg-slate-50/30 backdrop-blur-sm relative overflow-hidden group">
                                    <div className="absolute inset-0 bg-gradient-to-b from-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                                    <div className="relative z-10 flex flex-col items-center">
                                        <div className="w-24 h-24 mb-6 rounded-full bg-primary/5 flex items-center justify-center animate-pulse">
                                            <Leaf className="w-12 h-12 text-primary/40" />
                                        </div>
                                        <h3 className="text-xl font-bold text-slate-600 tracking-tight">Awaiting Clinical Inputs</h3>
                                        <p className="text-slate-500 max-w-sm text-center mt-2 leading-relaxed">
                                            Complete the assessment on the left to generate a personalized Ayurvedic treatment plan.
                                        </p>
                                    </div>
                                </div>
                            ) : treatmentPlan.no_match_found ? (
                                <div className="h-full border-2 border-dashed border-amber-200/60 rounded-3xl flex flex-col items-center justify-center text-amber-600 min-h-[500px] bg-amber-50/30 backdrop-blur-sm relative overflow-hidden">
                                    <div className="relative z-10 flex flex-col items-center text-center p-6">
                                        <AlertTriangle className="w-16 h-16 text-amber-400 mb-6" />
                                        <h3 className="text-2xl font-bold text-amber-800 tracking-tight mb-2">No Matches Found</h3>
                                        <p className="text-amber-700 max-w-md leading-relaxed">
                                            {treatmentPlan.message || "No matches found with National Ayurveda Morbidity Codes."}
                                        </p>
                                        <Button variant="outline" onClick={() => setTreatmentPlan(null)} className="mt-6 border-amber-300 text-amber-700 hover:bg-amber-100">
                                            Clear Result
                                        </Button>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
                                    {/* Explainability / NAMC Details Banner */}
                                    {/* 
                                    <Card className="bg-gradient-to-br from-slate-900 to-slate-800 text-slate-100 border-none shadow-xl overflow-hidden relative rounded-2xl">
                                        <div className="absolute -top-4 -right-4 p-3 opacity-10">
                                            <Brain className="w-32 h-32 text-white" />
                                        </div>
                                        <CardHeader className="pb-3 border-b border-white/5 bg-black/10">
                                            <CardTitle className="text-lg flex items-center gap-2 text-primary tracking-wide">
                                                <Sparkles className="w-5 h-5 text-primary animate-pulse" /> AI Clinical Rationale
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-4 pt-5 relative z-10 px-5 pb-6">
                                            <div className="mb-4">{getConfidenceBadge()}</div>
                                            <div className="space-y-2">
                                                {(treatmentPlan.explainability || []).map((reason: string, idx: number) => (
                                                    <div key={idx} className="flex gap-2 text-sm text-slate-300">
                                                        <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" /> {reason}
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
                                                <div>
                                                    <span className="text-xs text-slate-400 uppercase tracking-wider">Improvement</span>
                                                    <div className="text-green-400 font-bold text-2xl flex items-center gap-1">
                                                        <TrendingUp className="w-5 h-5" /> {treatmentPlan.predicted_improvement}%
                                                    </div>
                                                </div>
                                                <div>
                                                    <span className="text-xs text-slate-400 uppercase tracking-wider">Duration</span>
                                                    <div className="font-bold text-xl flex items-center gap-1">
                                                        <Clock className="w-4 h-4 text-slate-400" /> {treatmentPlan.recommended_duration_weeks} Weeks
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
                                    */}

                                    {/* Herbal Interventions */}
                                    <Card className="overflow-hidden border-none shadow-md ring-1 ring-emerald-100 bg-white/90 rounded-2xl">
                                        <CardHeader className="pb-4 bg-gradient-to-r from-emerald-50 to-white relative">
                                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500" />
                                            <CardTitle className="flex items-center gap-2 text-emerald-900 text-lg">
                                                <div className="p-1.5 bg-emerald-100 rounded-lg text-emerald-600"><Leaf className="w-4 h-4" /></div>
                                                Herbal Interventions
                                                <button onClick={() => setAddingHerb(true)} className="ml-auto w-8 h-8 rounded-full bg-emerald-100 hover:bg-emerald-200 flex items-center justify-center text-emerald-700 transition-transform hover:scale-105 shadow-sm">
                                                    <Plus className="w-4 h-4" strokeWidth={3} />
                                                </button>
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="grid gap-3 pt-5 px-5 pb-5">
                                            {(treatmentPlan.herbs || []).length === 0 && !addingHerb && (
                                                <p className="text-sm text-slate-400 italic py-2">No herbal interventions specified for this condition.</p>
                                            )}
                                            {(treatmentPlan.herbs || []).map((herb: any, idx: number) => (
                                                <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                                                    <div>
                                                        <h4 className="font-bold text-slate-900">{herb.name}</h4>
                                                        {herb.benefits && <p className="text-xs text-slate-400 mt-0.5">{herb.benefits}</p>}
                                                    </div>
                                                    <button onClick={() => deleteHerb(idx)} className="w-8 h-8 rounded-full bg-slate-50 hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                            {addingHerb && (
                                                <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-200">
                                                    <input type="text" value={newHerbName} onChange={e => setNewHerbName(e.target.value)} onKeyDown={e => e.key === 'Enter' && addHerb()} placeholder="Enter herb name..." autoFocus className="flex-1 px-3 py-2 rounded-lg border border-green-300 text-sm outline-none focus:ring-2 focus:ring-green-400" />
                                                    <button onClick={addHerb} className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">Add</button>
                                                    <button onClick={() => { setAddingHerb(false); setNewHerbName(''); }} className="w-8 h-8 rounded-full hover:bg-green-100 flex items-center justify-center text-slate-500"><X className="w-4 h-4" /></button>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* Yoga */}
                                    <Card className="overflow-hidden border-none shadow-md ring-1 ring-amber-100 bg-white/90 rounded-2xl">
                                        <CardHeader className="pb-4 bg-gradient-to-r from-amber-50 to-white relative">
                                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500" />
                                            <CardTitle className="flex items-center gap-2 text-amber-900 text-lg">
                                                <div className="p-1.5 bg-amber-100 rounded-lg text-amber-600"><Activity className="w-4 h-4" /></div>
                                                Yoga & Physical Therapy
                                                <button onClick={() => setAddingYoga(true)} className="ml-auto w-8 h-8 rounded-full bg-amber-100 hover:bg-amber-200 flex items-center justify-center text-amber-700 transition-transform hover:scale-105 shadow-sm">
                                                    <Plus className="w-4 h-4" strokeWidth={3} />
                                                </button>
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="grid gap-3 pt-5 px-5 pb-5">
                                            {(treatmentPlan.yoga || []).length === 0 && !addingYoga && (
                                                <p className="text-sm text-slate-400 italic py-2">No targeted yoga practices specified.</p>
                                            )}
                                            {(treatmentPlan.yoga || []).map((yoga: any, idx: number) => (
                                                <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                                                    <div>
                                                        <h4 className="font-bold text-slate-900">{yoga.practice}</h4>
                                                        {yoga.duration && <p className="text-xs text-slate-500">{yoga.duration}</p>}
                                                        {yoga.benefits && <p className="text-xs text-slate-400 mt-0.5">{yoga.benefits}</p>}
                                                    </div>
                                                    <button onClick={() => deleteYoga(idx)} className="w-8 h-8 rounded-full bg-slate-50 hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                            {addingYoga && (
                                                <div className="flex items-center gap-2 p-3 bg-orange-50 rounded-xl border border-orange-200">
                                                    <input type="text" value={newYogaName} onChange={e => setNewYogaName(e.target.value)} onKeyDown={e => e.key === 'Enter' && addYoga()} placeholder="Enter yoga/exercise name..." autoFocus className="flex-1 px-3 py-2 rounded-lg border border-orange-300 text-sm outline-none focus:ring-2 focus:ring-orange-400" />
                                                    <button onClick={addYoga} className="px-3 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-700">Add</button>
                                                    <button onClick={() => { setAddingYoga(false); setNewYogaName(''); }} className="w-8 h-8 rounded-full hover:bg-orange-100 flex items-center justify-center text-slate-500"><X className="w-4 h-4" /></button>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>

                                    {/* Diet + Lifestyle */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Diet */}
                                        <Card className="overflow-hidden border-none shadow-md ring-1 ring-rose-100 bg-white/90 rounded-2xl">
                                            <CardHeader className="pb-4 bg-gradient-to-r from-rose-50 to-white relative">
                                                <div className="absolute left-0 top-0 bottom-0 w-1 bg-rose-500" />
                                                <CardTitle className="flex items-center gap-2 text-rose-900 text-lg">
                                                    <div className="p-1.5 bg-rose-100 rounded-lg text-rose-600"><Coffee className="w-4 h-4" /></div>
                                                    Dietary Guidelines
                                                    <button onClick={() => setAddingDiet(true)} className="ml-auto w-8 h-8 rounded-full bg-rose-100 hover:bg-rose-200 flex items-center justify-center text-rose-700 hover:scale-105 shadow-sm">
                                                        <Plus className="w-4 h-4" strokeWidth={3} />
                                                    </button>
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-4 px-5 pb-5">
                                                <ul className="space-y-2.5">
                                                    {(treatmentPlan.diet || []).length === 0 && !addingDiet && (
                                                        <li className="text-sm text-slate-400 italic py-2">No dietary guidelines specified.</li>
                                                    )}
                                                    {(treatmentPlan.diet || []).map((item: string, idx: number) => (
                                                        <li key={idx} className="flex items-center gap-3 text-sm text-slate-700 bg-amber-50/50 p-2.5 rounded-lg">
                                                            <span className="text-amber-500 font-bold">•</span>
                                                            <span className="flex-1">{item}</span>
                                                            <button onClick={() => deleteDiet(idx)} className="w-6 h-6 rounded-full hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                                        </li>
                                                    ))}
                                                </ul>
                                                {addingDiet && (
                                                    <div className="flex items-center gap-2 mt-3 p-2.5 bg-amber-50 rounded-lg border border-amber-200">
                                                        <input type="text" value={newDietItem} onChange={e => setNewDietItem(e.target.value)} onKeyDown={e => e.key === 'Enter' && addDiet()} placeholder="New dietary guideline..." autoFocus className="flex-1 px-3 py-1.5 rounded-lg border border-amber-300 text-sm outline-none focus:ring-2 focus:ring-amber-400" />
                                                        <button onClick={addDiet} className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-medium hover:bg-amber-700">Add</button>
                                                        <button onClick={() => { setAddingDiet(false); setNewDietItem(''); }} className="text-slate-500 hover:text-slate-700"><X className="w-4 h-4" /></button>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>

                                        {/* Lifestyle */}
                                        <Card className="overflow-hidden border-none shadow-md ring-1 ring-blue-100 bg-white/90 rounded-2xl">
                                            <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-white relative">
                                                <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500" />
                                                <CardTitle className="flex items-center gap-2 text-blue-900 text-lg">
                                                    <div className="p-1.5 bg-blue-100 rounded-lg text-blue-600"><Sun className="w-4 h-4" /></div>
                                                    Lifestyle Changes
                                                    <button onClick={() => setAddingLifestyle(true)} className="ml-auto w-8 h-8 rounded-full bg-blue-100 hover:bg-blue-200 flex items-center justify-center text-blue-700 hover:scale-105 shadow-sm">
                                                        <Plus className="w-4 h-4" strokeWidth={3} />
                                                    </button>
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="pt-4 px-5 pb-5">
                                                <ul className="space-y-2.5">
                                                    {(treatmentPlan.lifestyle || []).length === 0 && !addingLifestyle && (
                                                        <li className="text-sm text-slate-400 italic py-2">No lifestyle changes specified.</li>
                                                    )}
                                                    {(treatmentPlan.lifestyle || []).map((item: string, idx: number) => (
                                                        <li key={idx} className="flex items-center gap-3 text-sm text-slate-700 bg-indigo-50/50 p-2.5 rounded-lg">
                                                            <span className="text-indigo-500 font-bold">•</span>
                                                            <span className="flex-1">{item}</span>
                                                            <button onClick={() => deleteLifestyle(idx)} className="w-6 h-6 rounded-full hover:bg-red-50 flex items-center justify-center text-slate-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                                                        </li>
                                                    ))}
                                                </ul>
                                                {addingLifestyle && (
                                                    <div className="flex items-center gap-2 mt-3 p-2.5 bg-indigo-50 rounded-lg border border-indigo-200">
                                                        <input type="text" value={newLifestyleItem} onChange={e => setNewLifestyleItem(e.target.value)} onKeyDown={e => e.key === 'Enter' && addLifestyle()} placeholder="New lifestyle change..." autoFocus className="flex-1 px-3 py-1.5 rounded-lg border border-indigo-300 text-sm outline-none focus:ring-2 focus:ring-indigo-400" />
                                                        <button onClick={addLifestyle} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700">Add</button>
                                                        <button onClick={() => { setAddingLifestyle(false); setNewLifestyleItem(''); }} className="text-slate-500 hover:text-slate-700"><X className="w-4 h-4" /></button>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    </div>

                                    {/* Prevention / Prognosis / Complications */}
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        {treatmentPlan.prevention?.length > 0 && (
                                            <Card className="overflow-hidden border-none shadow-sm ring-1 ring-emerald-100 bg-white/90 rounded-2xl">
                                                <CardHeader className="pb-3 bg-emerald-50/50">
                                                    <CardTitle className="flex items-center gap-2 text-emerald-800 text-base font-bold">
                                                        <Shield className="w-4 h-4 text-emerald-600" /> Prevention
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pt-4 px-4 pb-4">
                                                    <ul className="space-y-2.5">
                                                        {treatmentPlan.prevention.map((item, idx) => (
                                                            <li key={idx} className="flex gap-2.5 text-sm text-slate-700 leading-snug">
                                                                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" /> {item}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </CardContent>
                                            </Card>
                                        )}
                                        {treatmentPlan.prognosis && (
                                            <Card className="overflow-hidden border-none shadow-sm ring-1 ring-blue-100 bg-white/90 rounded-2xl">
                                                <CardHeader className="pb-3 bg-blue-50/50">
                                                    <CardTitle className="flex items-center gap-2 text-blue-800 text-base font-bold">
                                                        <Heart className="w-4 h-4 text-blue-600" /> Prognosis
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pt-4 px-4 pb-4">
                                                    <p className="text-sm text-slate-700 leading-relaxed">{treatmentPlan.prognosis}</p>
                                                </CardContent>
                                            </Card>
                                        )}
                                        {treatmentPlan.complications?.length > 0 && (
                                            <Card className="overflow-hidden border-none shadow-sm ring-1 ring-red-100 bg-white/90 rounded-2xl">
                                                <CardHeader className="pb-3 bg-red-50/50">
                                                    <CardTitle className="flex items-center gap-2 text-red-800 text-base font-bold">
                                                        <AlertTriangle className="w-4 h-4 text-red-600" /> Complications
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pt-4 px-4 pb-4">
                                                    <ul className="space-y-2">
                                                        {treatmentPlan.complications.map((item, idx) => (
                                                            <li key={idx} className="flex gap-2 text-sm text-slate-700">
                                                                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" /> {item}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </CardContent>
                                            </Card>
                                        )}
                                    </div>

                                    {/* Medical intervention */}
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

                                    {/* Doctor prescription notes */}
                                    <div className="mt-10 border-t border-slate-200/60 pt-8">
                                        <h3 className="font-bold text-slate-900 mb-5 flex items-center gap-2 text-xl tracking-tight">
                                            <div className="p-1.5 bg-primary/10 rounded-lg text-primary"><ClipboardList className="w-5 h-5" /></div>
                                            Doctor&apos;s Notes
                                        </h3>
                                        <Card className="border-none shadow-sm ring-1 ring-primary/20 rounded-2xl overflow-hidden">
                                            <CardHeader className="pb-3 bg-primary/5">
                                                <CardTitle className="flex items-center gap-2 text-primary text-base font-bold">
                                                    <FileText className="w-4 h-4" /> Prescription Notes
                                                </CardTitle>
                                                <CardDescription>Additional instructions and clinical notes</CardDescription>
                                            </CardHeader>
                                            <CardContent className="pt-4 pb-5 px-5">
                                                <textarea
                                                    className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                                    placeholder="e.g. Follow up after 2 weeks. Blood sugar test before next visit. Avoid cold beverages..."
                                                    rows={3}
                                                    value={doctorNotes}
                                                    onChange={e => setDoctorNotes(e.target.value)}
                                                />
                                            </CardContent>
                                        </Card>
                                    </div>

                                    {/* Feedback & Submit */}
                                    <div className="mt-8 border-t border-slate-200/60 pt-8">
                                        <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2 text-lg tracking-tight">
                                            <div className="p-1.5 bg-indigo-100 rounded-lg text-indigo-600"><Brain className="w-4 h-4" /></div>
                                            AI Feedback
                                        </h3>
                                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5 ring-1 ring-slate-100">
                                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                                <label className="text-sm font-bold text-slate-700">How accurate was this AI plan?</label>
                                                <div className="flex gap-3">
                                                    <Button variant={rating === 'positive' ? "default" : "outline"} size="sm" onClick={() => setRating('positive')}
                                                        className={`rounded-xl transition-all ${rating === 'positive' ? "bg-emerald-500 hover:bg-emerald-600 text-white" : "text-emerald-700 border-emerald-200 hover:bg-emerald-50"}`}>
                                                        <ThumbsUp className="w-4 h-4 mr-1.5" /> Accurate
                                                    </Button>
                                                    <Button variant={rating === 'negative' ? "default" : "outline"} size="sm" onClick={() => setRating('negative')}
                                                        className={`rounded-xl transition-all ${rating === 'negative' ? "bg-red-500 hover:bg-red-600 text-white" : "text-red-700 border-red-200 hover:bg-red-50"}`}>
                                                        <ThumbsDown className="w-4 h-4 mr-1.5" /> Needs Changes
                                                    </Button>
                                                </div>
                                            </div>
                                            <textarea
                                                className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-indigo-100 focus:border-indigo-300 outline-none transition-all resize-none shadow-sm"
                                                placeholder="Notes on AI accuracy — what was correct/incorrect?"
                                                rows={2}
                                                value={feedback}
                                                onChange={e => setFeedback(e.target.value)}
                                            />
                                            <div className="flex justify-end pt-2">
                                                <Button
                                                    size="lg"
                                                    className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white shadow-lg h-12 rounded-xl text-base font-bold tracking-wide transition-all hover:scale-[1.02] active:scale-[0.98] w-full md:w-auto px-8"
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

            {/* ── Voice / chat controls portalled into CopilotKit input ── */}
            {chatInputNode && createPortal(
                <>
                    <div className="absolute -top-11 left-0 right-0 flex items-center justify-center z-[1000] pointer-events-auto">
                        {!showNewChatConfirm ? (
                            <button type="button" onClick={() => setShowNewChatConfirm(true)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-background/90 backdrop-blur border border-border text-muted-foreground hover:text-primary hover:border-primary/50 hover:bg-primary/5 shadow-sm transition-all">
                                <RefreshCw className="w-3.5 h-3.5" /> New Chat
                            </button>
                        ) : (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-background/95 backdrop-blur border border-border shadow-md text-xs font-medium">
                                <span className="text-muted-foreground">Clear form too?</span>
                                <button type="button" onClick={() => handleNewChat(true)} className="px-2.5 py-1 rounded-full bg-destructive/10 text-destructive hover:bg-destructive/20 border border-destructive/20">Yes, clear</button>
                                <button type="button" onClick={() => handleNewChat(false)} className="px-2.5 py-1 rounded-full bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20">Keep form</button>
                                <button type="button" onClick={() => setShowNewChatConfirm(false)} className="w-5 h-5 flex items-center justify-center rounded-full hover:bg-muted text-muted-foreground"><X className="w-3 h-3" /></button>
                            </div>
                        )}
                    </div>
                    <div className="absolute bottom-1.5 left-1 z-[1000] pointer-events-auto">
                        <LanguageSelector selectedLanguage={selectedLanguage} onLanguageChange={setSelectedLanguage} />
                    </div>
                    <div className="absolute bottom-1.5 right-12 z-[1000] pointer-events-auto">
                        <VoiceInputButton onTranscript={handleVoiceTranscript} onError={(err) => { console.error('Voice error:', err); }} language={selectedLanguage} />
                    </div>
                </>,
                chatInputNode
            )}
        </>
    );
}
