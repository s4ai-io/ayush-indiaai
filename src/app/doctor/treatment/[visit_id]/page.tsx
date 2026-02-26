'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ClipboardCheck, Pill, Stethoscope, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface PrescriptionItem {
    id: string; // Add ID for easy deletion
    medicine: string;
    dosage: string;
    frequency: string;
    duration: string;
}

export default function TreatmentPlanPage({ params }: { params: Promise<{ visit_id: string }> }) {
    const { visit_id } = use(params);
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState('');

    // Mock incoming assessment info
    const [visitContext, setVisitContext] = useState<any>(null);

    // Form states
    const [prescription, setPrescription] = useState<PrescriptionItem[]>([]);
    const [treatmentNotes, setTreatmentNotes] = useState('');

    useEffect(() => {
        const fetchVisitContext = async () => {
            setLoading(true);
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await fetch(`${API_URL}/api/consultations/${visit_id}/treatment`);
                if (!response.ok) throw new Error("Failed to fetch visit details relative to the backed APIs.");
                const data = await response.json();

                setVisitContext({
                    patientId: data.patientId || "",
                    patientName: data.patientName || "Unknown",
                    patientMobile: data.patientMobile || "Unknown",
                    symptoms: data.symptoms || "",
                    diagnosis: data.diagnosis || "",
                    doctorNotes: data.doctorNotes || "",
                    prakriti: data.prakriti || "",
                    vikriti: data.vikriti || "",
                    severity: data.severity || 5,
                    comorbidities: data.comorbidities || ""
                });
            } catch (err) {
                console.error("Failed to load visit context", err);
                setError("Could not load consultation context.");
            } finally {
                setLoading(false);
            }
        };
        fetchVisitContext();
    }, [visit_id]);

    const handleAddMedicine = () => {
        setPrescription([...prescription, { id: Date.now().toString(), medicine: '', dosage: '', frequency: '', duration: '' }]);
    };

    const handleMedicineChange = (id: string, field: keyof PrescriptionItem, value: string) => {
        setPrescription(prev => prev.map(item =>
            item.id === id ? { ...item, [field]: value } : item
        ));
    };

    const handleRemoveMedicine = (id: string) => {
        setPrescription(prev => prev.filter(item => item.id !== id));
    };

    const handleSaveTreatment = async () => {
        const invalidPrescription = prescription.some(p => !p.medicine.trim());
        if (invalidPrescription && prescription.length > 0) {
            setError("Please provide a medicine name for all prescription rows, or remove empty ones.");
            setIsSaving(false);
            return;
        }

        setIsSaving(true);
        setError('');
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

            // Format prescription into an AI-friendly generic shape for now
            const herbsList = prescription.map(p => ({
                name: p.medicine,
                dosage: p.dosage,
                benefits: `${p.frequency} for ${p.duration}`
            }));

            // Generate simple string instructions format for human reading
            const prescript_string = prescription.map(p => `${p.medicine} (${p.dosage}) - ${p.frequency} [${p.duration}]`).join('\n');

            const payload = {
                patientId: visitContext?.patientId || "",
                visitId: visit_id,
                disease: visitContext?.diagnosis || "Unknown",
                symptoms: visitContext?.symptoms || "",
                treatmentPlan: { herbs: herbsList }, // Temporary mock of Ayurgenix format 
                doctorNotes: treatmentNotes,
                doctorPrescription: prescript_string,
                severity: parseInt(visitContext?.severity) || 5,
                prakriti: visitContext?.prakriti || "Vata",
                vikriti: visitContext?.vikriti || "Vata",
            };

            const response = await fetch(`${API_URL}/api/prescribe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error("Failed connecting to the backend for Treatment Saving.");
            }

            // Redirect back to doctor dashboard
            router.push('/doctor');
        } catch (err) {
            setError("Failed to save treatment plan.");
        } finally {
            setIsSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                <span className="ml-3 text-lg text-slate-600 font-medium">Loading visit context...</span>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-4 max-w-5xl space-y-6">

            <div className="flex items-center space-x-4 mb-8">
                <Link href="/doctor">
                    <Button variant="outline" size="icon" className="h-10 w-10 border-slate-200">
                        <ArrowLeft className="w-4 h-4" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">Generate Treatment Plan</h1>
                    <p className="text-slate-500">Visit ID: {visit_id}</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* LEFT COL: Read-only Consultation Context */}
                <div className="lg:col-span-1 space-y-4">
                    <div className="bg-slate-50 border border-slate-200 p-5 rounded-xl">
                        <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4 border-b pb-2">Patient Details</h3>
                        <div className="space-y-2 text-sm text-slate-700">
                            <p><span className="font-semibold text-slate-900">Name:</span> {visitContext?.patientName}</p>
                            <p><span className="font-semibold text-slate-900">Mobile:</span> {visitContext?.patientMobile}</p>
                        </div>
                    </div>

                    <div className="bg-indigo-50 border border-indigo-100 p-5 rounded-xl">
                        <h3 className="text-sm font-bold text-indigo-800 uppercase tracking-wider mb-4 flex items-center border-b border-indigo-200 pb-2">
                            <Stethoscope className="w-4 h-4 mr-2" /> Clinical Assessment
                        </h3>
                        <div className="space-y-4 text-sm text-slate-800">
                            <div>
                                <span className="font-bold text-indigo-900 block mb-1">Symptoms:</span>
                                <p className="bg-white p-2 rounded border border-indigo-100">{visitContext?.symptoms}</p>
                            </div>
                            <div>
                                <span className="font-bold text-indigo-900 block mb-1">Diagnosis:</span>
                                <p className="bg-white p-2 rounded border border-indigo-100">{visitContext?.diagnosis}</p>
                            </div>
                            <div>
                                <span className="font-bold text-indigo-900 block mb-1">Doctor Notes:</span>
                                <p className="bg-white p-2 rounded border border-indigo-100">{visitContext?.doctorNotes}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT COL: Prescription / Treatment Input */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white border text-emerald-900 border-emerald-200 p-6 rounded-xl shadow-sm">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold flex items-center text-emerald-800">
                                <Pill className="w-5 h-5 mr-2 text-emerald-600" /> Prescription
                            </h2>
                            <Button onClick={handleAddMedicine} variant="outline" className="border-emerald-300 text-emerald-700 hover:bg-emerald-50">
                                + Add Medicine
                            </Button>
                        </div>

                        {prescription.length === 0 ? (
                            <div className="text-center py-8 text-emerald-600/60 border-2 border-dashed border-emerald-100 rounded-lg bg-emerald-50/50">
                                No medicines added yet.
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {prescription.map((item, index) => (
                                    <div key={item.id} className="relative grid grid-cols-1 md:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-lg border border-slate-200 group">
                                        <button
                                            onClick={() => handleRemoveMedicine(item.id)}
                                            className="absolute -top-2 -right-2 bg-red-100 text-red-600 rounded-full w-6 h-6 flex items-center justify-center text-xs shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            ✕
                                        </button>
                                        <div className="space-y-1">
                                            <Label className="text-xs text-slate-500">Medicine</Label>
                                            <Input
                                                value={item.medicine}
                                                onChange={(e) => handleMedicineChange(item.id, 'medicine', e.target.value)}
                                                placeholder="e.g. Paracetamol"
                                                className="bg-white"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs text-slate-500">Dosage</Label>
                                            <Input
                                                value={item.dosage}
                                                onChange={(e) => handleMedicineChange(item.id, 'dosage', e.target.value)}
                                                placeholder="e.g. 500mg"
                                                className="bg-white"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs text-slate-500">Frequency</Label>
                                            <Input
                                                value={item.frequency}
                                                onChange={(e) => handleMedicineChange(item.id, 'frequency', e.target.value)}
                                                placeholder="e.g. 1-0-1"
                                                className="bg-white"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs text-slate-500">Duration</Label>
                                            <Input
                                                value={item.duration}
                                                onChange={(e) => handleMedicineChange(item.id, 'duration', e.target.value)}
                                                placeholder="e.g. 5 days"
                                                className="bg-white"
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm">
                        <h2 className="text-xl font-bold flex items-center text-slate-800 mb-4">
                            <ClipboardCheck className="w-5 h-5 mr-2 text-slate-600" /> Treatment Instructions
                        </h2>
                        <textarea
                            value={treatmentNotes}
                            onChange={(e) => setTreatmentNotes(e.target.value)}
                            placeholder="Add generic advice like 'Drink warm water, take proper rest...'"
                            className="w-full min-h-[100px] p-4 text-slate-700 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-400 focus:border-slate-400 resize-y"
                        />
                    </div>

                    <div className="flex justify-end pt-4">
                        <Button
                            onClick={handleSaveTreatment}
                            disabled={isSaving}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white min-w-[200px] h-12 text-lg shadow-md"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Saving...
                                </>
                            ) : (
                                "Confirm Treatment Plan"
                            )}
                        </Button>
                    </div>
                </div>

            </div>
        </div>
    );
}
