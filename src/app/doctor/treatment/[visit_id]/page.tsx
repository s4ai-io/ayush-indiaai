'use client';

import { useEffect, useState, use } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
    Brain, Activity, Leaf, Coffee, Moon, Sun, CheckCircle, AlertTriangle,
    Shield, Heart, Stethoscope, FileText, ClipboardList, Sparkles, TrendingUp,
    Clock, Target, Plus, Trash2, X, Save, Phone, History,
    HeartPulse, Droplet, Thermometer, Gauge,
} from 'lucide-react';
import { DiseaseSearchDropdown } from '@/components/ui/DiseaseSearchDropdown';
import { useRouter } from "next/navigation";
import { GemmaVoiceChatPanel } from "@/components/GemmaVoiceChatPanel";
import { API_BASE } from '@/lib/config';
import type { VisitPatient, VisitContext, TreatmentPlan, Vitals, PreviousVisitSummary } from '@/types';

const VITAL_FIELDS: { key: keyof Vitals; label: string; unit: string; icon: typeof HeartPulse }[] = [
    { key: 'bpm', label: 'Heart Rate', unit: 'BPM', icon: HeartPulse },
    { key: 'sugar_level', label: 'Blood Sugar', unit: 'mg/dL', icon: Droplet },
    { key: 'spo2', label: 'SpO2', unit: '%', icon: Activity },
    { key: 'temperature', label: 'Temperature', unit: '°C', icon: Thermometer },
    { key: 'systolic_bp', label: 'BP Systolic', unit: 'mmHg', icon: Gauge },
    { key: 'diastolic_bp', label: 'BP Diastolic', unit: 'mmHg', icon: Gauge },
];

// ─── Outer shell ────────────────────────────────────────────────────────────
export default function TreatmentPage({ params }: { params: Promise<{ visit_id: string }> }) {
    const { visit_id } = use(params);
    return <TreatmentPageContent visitId={visit_id} />;
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

    // Follow-up linkage + health parameters (vitals)
    const [parentVisitId, setParentVisitId] = useState<string | null>(null);
    const [previousVisit, setPreviousVisit] = useState<PreviousVisitSummary | null>(null);
    const [vitals, setVitals] = useState<Vitals>({});
    const isFollowup = !!parentVisitId;

    // Doctor prescribed manual inputs mapped from Agent
    const [doctorHerbs, setDoctorHerbs] = useState<string[]>([]);
    const [doctorYoga, setDoctorYoga] = useState<string[]>([]);
    const [doctorDiet, setDoctorDiet] = useState<string[]>([]);
    const [doctorLifestyle, setDoctorLifestyle] = useState<string[]>([]);

    // Doctor prescription / feedback
    const [doctorNotes, setDoctorNotes] = useState('');
    const [feedback, setFeedback] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Follow-up only: did the PREVIOUS plan work? Drives the RL reward for the
    // parent visit's herbs/yoga/diet/lifestyle — the only thing that ever moves a
    // Q-value in production now (see POST /api/visits/{visit_id}/outcome).
    const [doctorReportedOutcome, setDoctorReportedOutcome] = useState<'improved' | 'no_change' | 'worsened' | null>(null);

    // AI Proposal Banner State
    const [proposedData, setProposedData] = useState<any>(null);

    // Step 9: original AI plan + feedback_id storage
    const [originalAiPlan, setOriginalAiPlan] = useState<Record<string, unknown> | null>(null);
    const [feedbackId, setFeedbackId] = useState<string | null>(null);

    // Step 11: follow-up outcome state
    const [medicalRecordId, setMedicalRecordId] = useState<string | null>(null);

    // Inline add/delete state
    const [addingHerb, setAddingHerb] = useState(false);
    const [newHerbName, setNewHerbName] = useState('');
    const [addingYoga, setAddingYoga] = useState(false);
    const [newYogaName, setNewYogaName] = useState('');
    const [addingDiet, setAddingDiet] = useState(false);
    const [newDietItem, setNewDietItem] = useState('');
    const [addingLifestyle, setAddingLifestyle] = useState(false);
    const [newLifestyleItem, setNewLifestyleItem] = useState('');
    // Ayurvedic dietary plan from CSV
    const [ayurvedicDietPlan, setAyurvedicDietPlan] = useState<{ plan: string; disease: string } | null>(null);

    // Assistant panel open/closed state for dynamic page padding
    const [isAssistantOpen, setIsAssistantOpen] = useState(true);

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
                    comorbidities: data.visit?.comorbidities || '',
                    patient: data.patient,
                });

                // Pre-fill clinical assessment from visit
                setDisease(data.visit?.diagnosis || '');
                setSymptoms(data.visit?.symptoms || '');
                setMedicalHistory(data.visit?.comorbidities || '');
                setPrakriti(data.visit?.prakriti || '');
                setVikriti(data.visit?.vikriti || '');

                // Follow-up linkage + vitals
                setParentVisitId(data.visit?.parentVisitId || null);
                setPreviousVisit(data.previousVisit || null);
                setVitals(data.visit?.vitals || {});

                // Auto-load parent's last prescribed plan for follow-up visits
                if (data.visit?.parentVisitId && data.previousVisit?.treatmentPlan) {
                    setTreatmentPlan(data.previousVisit.treatmentPlan);
                    setOriginalAiPlan(data.previousVisit.treatmentPlan);
                }
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
                            comorbidities: d.comorbidities || '',
                        });
                        setDisease(d.diagnosis || '');
                        setSymptoms(d.symptoms || '');
                        setMedicalHistory(d.comorbidities || '');
                        setPrakriti(d.prakriti || '');
                        setVikriti(d.vikriti || '');

                        setParentVisitId(d.parentVisitId || null);
                        setPreviousVisit(d.previousVisit || null);
                        setVitals(d.vitals || {});

                        if (d.parentVisitId && d.previousVisit?.treatmentPlan) {
                            setTreatmentPlan(d.previousVisit.treatmentPlan);
                            setOriginalAiPlan(d.previousVisit.treatmentPlan);
                        }
                    }
                } catch { }
            } finally {
                setLoading(false);
            }
        };
        fetchVisit();
    }, [visitId]);

    const splitExtractedItems = (value: unknown): string[] => {
        if (Array.isArray(value)) {
            return value.map((item) => String(item).trim()).filter(Boolean);
        }
        if (typeof value !== 'string') return [];
        return value
            .split(/[,;\n]+/)
            .map((item) => item.trim())
            .filter(Boolean);
    };

    const mergeUnique = (existing: string[], incoming: string[]) => {
        const seen = new Set(existing.map((item) => item.toLowerCase()));
        return [
            ...existing,
            ...incoming.filter((item) => {
                const key = item.toLowerCase();
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            }),
        ];
    };

    const mergeDoctorItemsIntoPlan = (updates: { herbs?: string[]; yoga?: string[]; diet?: string[]; lifestyle?: string[] }) => {
        setTreatmentPlan((prev) => {
            if (!prev || prev.no_match_found) return prev;
            const next = { ...prev };

            if (updates.herbs?.length) {
                const existingNames = new Set((next.herbs || []).map((h: any) => String(h.name || '').toLowerCase()));
                const newHerbs = updates.herbs
                    .filter((herb) => !existingNames.has(herb.toLowerCase()))
                    .map((herb) => ({ name: herb, dosage: 'As prescribed', benefits: 'Added by doctor' }));
                next.herbs = [...newHerbs, ...(next.herbs || [])];
            }

            if (updates.yoga?.length) {
                const existingNames = new Set((next.yoga || []).map((y: any) => String(y.practice || '').toLowerCase()));
                const newYoga = updates.yoga
                    .filter((yoga) => !existingNames.has(yoga.toLowerCase()))
                    .map((yoga) => ({ practice: yoga, duration: 'As prescribed', benefits: 'Added by doctor' }));
                next.yoga = [...newYoga, ...(next.yoga || [])];
            }

            if (updates.diet?.length) {
                next.diet = mergeUnique(next.diet || [], updates.diet);
            }

            if (updates.lifestyle?.length) {
                next.lifestyle = mergeUnique(next.lifestyle || [], updates.lifestyle);
            }

            return next;
        });
    };

    const applyExtractedClinicalAssessment = (args: any) => {
        if (!args || typeof args !== 'object') return;

        if (typeof args.disease === 'string' && args.disease.trim()) setDisease(args.disease.trim());
        if (typeof args.symptoms === 'string' && args.symptoms.trim()) setSymptoms(args.symptoms.trim());
        if (typeof args.comorbidities === 'string' && args.comorbidities.trim()) setMedicalHistory(args.comorbidities.trim());
        if (typeof args.vikriti === 'string' && args.vikriti.trim()) setVikriti(args.vikriti.trim());
        if (typeof args.prakriti === 'string' && args.prakriti.trim()) setPrakriti(args.prakriti.trim());

        const extractedVitals: Vitals = {};
        for (const { key } of VITAL_FIELDS) {
            const value = args[key];
            const num = typeof value === 'number' ? value : typeof value === 'string' ? parseFloat(value) : NaN;
            if (!Number.isNaN(num)) extractedVitals[key] = num;
        }
        if (Object.keys(extractedVitals).length) {
            setVitals((prev) => ({ ...prev, ...extractedVitals }));
        }

        const extractedHerbs = splitExtractedItems(args.herbs);
        const extractedYoga = splitExtractedItems(args.yoga);
        const extractedDiet = splitExtractedItems(args.diet);
        const extractedLifestyle = splitExtractedItems(args.lifestyle);

        if (extractedHerbs.length) setDoctorHerbs((prev) => mergeUnique(prev, extractedHerbs));
        if (extractedYoga.length) setDoctorYoga((prev) => mergeUnique(prev, extractedYoga));
        if (extractedDiet.length) setDoctorDiet((prev) => mergeUnique(prev, extractedDiet));
        if (extractedLifestyle.length) setDoctorLifestyle((prev) => mergeUnique(prev, extractedLifestyle));

        mergeDoctorItemsIntoPlan({
            herbs: extractedHerbs,
            yoga: extractedYoga,
            diet: extractedDiet,
            lifestyle: extractedLifestyle,
        });
    };

    // Fetch Ayurvedic dietary plan from CSV whenever disease + prakriti change
    useEffect(() => {
        const fetchDietaryPlan = async () => {
            if (!disease || !prakriti) { setAyurvedicDietPlan(null); return; }
            try {
                const res = await fetch(`/api/ml/dietary-plan?disease=${encodeURIComponent(disease)}&prakriti=${encodeURIComponent(prakriti)}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.dietary_plan) {
                        setAyurvedicDietPlan({ plan: data.dietary_plan, disease: data.disease_matched || disease });
                    } else {
                        setAyurvedicDietPlan(null);
                    }
                } else {
                    setAyurvedicDietPlan(null);
                }
            } catch {
                setAyurvedicDietPlan(null);
            }
        };
        fetchDietaryPlan();
    }, [disease, prakriti]);

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
                    comorbidities: medicalHistory || undefined
                }),
            });
            if (!res.ok) throw new Error('Failed to generate plan');
            const generatedPlan = await res.json();

            // Step 9a: store the original AI plan
            setOriginalAiPlan(generatedPlan.original_ai_plan ?? generatedPlan);

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
        if (isFollowup) {
            const missingVitals = VITAL_FIELDS.filter(f => vitals[f.key] == null);
            if (missingVitals.length > 0) {
                alert(`Please fill in all health parameters for this follow-up: ${missingVitals.map(f => f.label).join(', ')}.`);
                return;
            }
            if (!doctorReportedOutcome) {
                alert('Please indicate whether the previous treatment plan showed improvement.');
                return;
            }
        }
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
                    feedback,
                    // Step 9b: send original AI plan
                    original_ai_plan: originalAiPlan,
                    // Health parameters (vitals) captured this visit
                    ...vitals,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Failed to save');
            // Step 9e: store feedback_id for retrain-instant
            if (data.feedback_id) setFeedbackId(data.feedback_id);
            // Step 11: store medical_record_id from response
            if (data.medical_record_id || data.record_id) {
                setMedicalRecordId(data.medical_record_id || data.record_id);
            }

            // Follow-up only: close out the PARENT visit's pending outcome now that
            // this visit's vitals are saved — this is what actually moves the
            // parent plan's Q-values, based on doctorReportedOutcome + the vitals delta.
            if (isFollowup && doctorReportedOutcome) {
                try {
                    await fetch(`${API_BASE}/api/visits/${visitId}/outcome`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ doctor_reported_outcome: doctorReportedOutcome }),
                    });
                } catch {
                    // Non-fatal — the prescription itself already saved successfully.
                }
            }

            alert("Treatment Plan Prescribed & Saved Successfully!");
            setTimeout(() => router.push('/doctor?tab=completed'), 500);
        } catch (err: any) {
            alert(err.message || "Failed to save prescription");
        } finally {
            setIsSubmitting(false);
        }
    };

    // ── Step 11: Save follow-up outcome ───────────────────────────────────
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
        <div className={`min-h-screen w-full transition-all duration-300 ${isAssistantOpen ? "md:pr-96" : "md:pr-0"}`}>
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

                    {isFollowup && (
                        <div className="flex items-center gap-3 bg-indigo-50 border border-indigo-200 text-indigo-800 rounded-2xl px-5 py-3 shadow-sm">
                            <History className="w-5 h-5 shrink-0" />
                            <div className="text-sm">
                                <span className="font-bold">Follow-up Consultation:</span>{' '}
                                {disease || previousVisit?.diagnosis || 'Previous condition'}
                                {previousVisit?.visitDate && (
                                    <span className="text-indigo-500"> — previous visit {new Date(previousVisit.visitDate).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                                )}
                                {previousVisit?.treatmentPlan && (
                                    <div className="text-indigo-600 mt-0.5">Showing last prescribed plan — edit the herbs, yoga, diet, and lifestyle sections below as needed for this follow-up.</div>
                                )}
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
                                        <DiseaseSearchDropdown value={disease} onChange={setDisease} required placeholder="Search for a disease..." disabled={isFollowup} />
                                        {isFollowup && (
                                            <p className="text-xs text-slate-400">Locked to the condition being followed up. Start a new consultation to change the diagnosis.</p>
                                        )}
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
                                            <Activity className="w-3.5 h-3.5 text-primary" /> Comorbidities
                                        </label>
                                        <textarea
                                            value={medicalHistory}
                                            onChange={e => setMedicalHistory(e.target.value)}
                                            className="w-full text-sm p-3 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none shadow-sm"
                                            placeholder="Any known medical history or comorbidities..."
                                            rows={2}
                                        />
                                    </div>

                                    {/* Vikriti */}
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

                                    {/* Health Parameters / Vitals */}
                                    <div className="space-y-3 pt-2">
                                        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                            <HeartPulse className="w-3.5 h-3.5 text-primary" /> Health Parameters / Vitals
                                            {isFollowup && <span className="text-red-500">*</span>}
                                        </label>
                                        <div className="space-y-2.5">
                                            {VITAL_FIELDS.map(f => {
                                                const prevVal = previousVisit?.vitals?.[f.key];
                                                return (
                                                    <div key={f.key} className="space-y-1">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-xs text-slate-500 flex items-center gap-1.5">
                                                                <f.icon className="w-3.5 h-3.5 text-slate-400" /> {f.label}
                                                            </span>
                                                            {isFollowup && (
                                                                <span className="text-[11px] text-slate-400">
                                                                    Previous: <span className="font-medium text-slate-500">{prevVal != null ? `${prevVal} ${f.unit}` : '—'}</span>
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <input
                                                                type="number"
                                                                value={vitals[f.key] ?? ''}
                                                                onChange={e => {
                                                                    const raw = e.target.value;
                                                                    setVitals(prev => ({ ...prev, [f.key]: raw === '' ? null : Number(raw) }));
                                                                }}
                                                                placeholder={isFollowup ? 'Current value' : f.label}
                                                                className={`w-full text-sm p-2 bg-slate-50 border rounded-lg focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all ${isFollowup && vitals[f.key] == null ? 'border-red-300' : 'border-slate-200'}`}
                                                            />
                                                            <span className="text-xs text-slate-400 w-14 shrink-0">{f.unit}</span>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    {/* Follow-up only: did the PREVIOUS plan actually help? This — plus the
                                        vitals above — is what updates the previous plan's herb/yoga/diet/
                                        lifestyle Q-scores. Nothing about today's plan affects that score. */}
                                    {isFollowup && (
                                        <div className="space-y-2 pt-2">
                                            <label className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                                                <TrendingUp className="w-3.5 h-3.5 text-primary" /> Did the Previous Treatment Plan Improve the Patient?
                                                <span className="text-red-500">*</span>
                                            </label>
                                            <Select value={doctorReportedOutcome ?? undefined} onValueChange={(v) => setDoctorReportedOutcome(v as 'improved' | 'no_change' | 'worsened')}>
                                                <SelectTrigger className={`w-full bg-slate-50 border rounded-lg ${!doctorReportedOutcome ? 'border-red-300' : 'border-slate-200'}`}>
                                                    <SelectValue placeholder="Select an outcome..." />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="improved">Improved</SelectItem>
                                                    <SelectItem value="no_change">No Change</SelectItem>
                                                    <SelectItem value="worsened">Worsened</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    )}

                                    {(doctorHerbs.length > 0 || doctorYoga.length > 0 || doctorDiet.length > 0 || doctorLifestyle.length > 0) && (
                                        <div className="rounded-xl border border-primary/15 bg-primary/5 p-4 space-y-3">
                                            <div className="flex items-center gap-2 text-xs font-bold text-primary uppercase tracking-wider">
                                                <Sparkles className="w-3.5 h-3.5" />
                                                Doctor Provided Inputs
                                            </div>
                                            {[
                                                { label: 'Herbs', items: doctorHerbs, color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
                                                { label: 'Yoga', items: doctorYoga, color: 'bg-amber-100 text-amber-800 border-amber-200' },
                                                { label: 'Diet', items: doctorDiet, color: 'bg-rose-100 text-rose-800 border-rose-200' },
                                                { label: 'Lifestyle', items: doctorLifestyle, color: 'bg-blue-100 text-blue-800 border-blue-200' },
                                            ].filter(group => group.items.length > 0).map(group => (
                                                <div key={group.label} className="space-y-1.5">
                                                    <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{group.label}</p>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {group.items.map(item => (
                                                            <Badge key={`${group.label}-${item}`} variant="outline" className={`${group.color} rounded-full`}>
                                                                {item}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    <Button
                                        className="w-full mt-4 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 text-white shadow-lg h-12 rounded-xl text-base font-bold tracking-wide transition-all hover:scale-[1.02] active:scale-[0.98]"
                                        onClick={generatePlan}
                                        disabled={generating || isFollowup}
                                    >
                                        {generating
                                            ? <span className="flex items-center gap-2"><Brain className="w-4 h-4 animate-pulse" /> Analyzing...</span>
                                            : <span className="flex items-center gap-2"><Sparkles className="w-4 h-4" /> Generate AI Plan</span>
                                        }
                                    </Button>
                                    {isFollowup && (
                                        <p className="text-xs text-slate-400 text-center mt-2">
                                            Editing the previously prescribed plan for this follow-up. Start a new consultation to generate a fresh AI plan.
                                        </p>
                                    )}
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
                                        {treatmentPlan.vikriti_affected && (
                                            <div className="pt-3 border-t border-white/10">
                                                <span className="text-xs text-slate-400 uppercase tracking-wider">Doshas Affected</span>
                                                <div className="text-purple-300 font-semibold mt-1">{treatmentPlan.vikriti_affected}</div>
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
                                    {/* Step 9d: Low confidence match banner */}
                                    {treatmentPlan.match_requires_confirmation && (
                                        <div className="bg-yellow-50 border border-yellow-300 rounded-xl px-4 py-3 text-sm text-yellow-800 flex flex-col gap-1">
                                            <span className="font-semibold">Low confidence match.</span>
                                            <span>Consider reviewing alternatives:{' '}
                                                {Array.isArray(treatmentPlan.match_alternatives)
                                                    ? treatmentPlan.match_alternatives.join(', ')
                                                    : treatmentPlan.match_alternatives}
                                            </span>
                                        </div>
                                    )}
                                    {/* Explainability / NAMC Details Banner */}
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
                                            {treatmentPlan.vikriti_affected && (
                                                <div className="pt-3 border-t border-white/10">
                                                    <span className="text-xs text-slate-400 uppercase tracking-wider">Doshas Affected</span>
                                                    <div className="text-purple-300 font-semibold mt-1">{treatmentPlan.vikriti_affected}</div>
                                                </div>
                                            )}
                                        </CardContent>
                                    </Card>

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
                                                        <div className="flex items-center flex-wrap gap-1">
                                                            <h4 className="font-bold text-slate-900">{herb.name}</h4>
                                                            {/* Step 9c: AI-learned badge */}
                                                            {(herb.ai_learned || (herb.source && herb.source.includes('RL'))) && (
                                                                <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                                                                    ✦ AI-learned
                                                                </span>
                                                            )}
                                                        </div>
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
                                                {/* Ayurvedic Dietary Plan from CSV */}
                                                {ayurvedicDietPlan && (
                                                    <div className="mb-4 p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl border border-amber-200 shadow-sm">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <Leaf className="w-4 h-4 text-amber-600" />
                                                            <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">
                                                                Ayurvedic Plan · {prakriti} Prakriti
                                                            </span>
                                                            <span className="ml-auto text-xs text-amber-500 font-medium bg-amber-100 px-2 py-0.5 rounded-full">{ayurvedicDietPlan.disease}</span>
                                                        </div>
                                                        <p className="text-sm text-amber-900 leading-relaxed">{ayurvedicDietPlan.plan}</p>
                                                    </div>
                                                )}
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
            <GemmaVoiceChatPanel flow="treatment" onExtracted={applyExtractedClinicalAssessment} isOpen={isAssistantOpen} onOpenChange={setIsAssistantOpen} />
        </div>
    );
}
