'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { conditionProtocols } from '@/lib/mockData';
import { Stethoscope, Leaf, Pizza, Activity, AlertCircle } from 'lucide-react';

export function ConsultationForm() {
    const [prakriti, setPrakriti] = useState<string>('Vata');
    const [condition, setCondition] = useState<string>('Diabetes (Madhumeha)');
    const [result, setResult] = useState<any>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Logic to fetch protocols from nested object
        const conditionData = conditionProtocols[condition as keyof typeof conditionProtocols];

        // Fallback to 'General' if specific Prakriti protocol isn't defined for that condition
        // Fallback to 'General' if specific Prakriti protocol isn't defined for that condition
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const protocol = (conditionData as any)[prakriti] || (conditionData as any)['General'];

        setResult(protocol);
    };

    return (
        <div className="grid gap-6 lg:grid-cols-2">
            <Card>
                <CardHeader>
                    <CardTitle>Patient Assessment</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Primary Health Concern</label>
                            <select
                                className="w-full p-2 border rounded-md"
                                value={condition}
                                onChange={(e) => setCondition(e.target.value)}
                            >
                                {Object.keys(conditionProtocols).map(c => (
                                    <option key={c} value={c}>{c}</option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Dominant Prakriti (Body Type)</label>
                            <select
                                className="w-full p-2 border rounded-md"
                                value={prakriti}
                                onChange={(e) => setPrakriti(e.target.value)}
                            >
                                <option value="Vata">Vata (Air/Ether)</option>
                                <option value="Pitta">Pitta (Fire/Water)</option>
                                <option value="Kapha">Kapha (Earth/Water)</option>
                            </select>
                        </div>

                        <div className="p-3 bg-blue-50 text-blue-800 text-xs rounded-md flex gap-2">
                            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                            <p>AI will analyze the intersection of the disease pathology (Samprapti) and patient constitution (Prakriti).</p>
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-md hover:opacity-90 transition-opacity font-medium"
                        >
                            Generate Treatment Protocol
                        </button>
                    </form>
                </CardContent>
            </Card>

            {result && (
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <Card className="bg-emerald-50/40 border-emerald-100 shadow-sm">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-emerald-900 flex items-center gap-2 text-lg">
                                <Stethoscope className="w-5 h-5" />
                                AYUSH Protocol: {condition}
                            </CardTitle>
                            <p className="text-sm text-emerald-700">Tailored for {prakriti} constitution</p>
                        </CardHeader>
                        <CardContent className="space-y-5">
                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Leaf className="w-5 h-5 text-emerald-600" /></div>
                                <div>
                                    <h4 className="font-semibold text-emerald-900">Medicinal Herbs (Aushadhi)</h4>
                                    <ul className="list-disc pl-4 text-sm text-emerald-800 marker:text-emerald-500 mt-1 space-y-1">
                                        {result.herbs.map((h: string) => <li key={h}>{h}</li>)}
                                    </ul>
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Pizza className="w-5 h-5 text-orange-600" /></div>
                                <div>
                                    <h4 className="font-semibold text-orange-900">Dietary Rules (Ahara)</h4>
                                    <p className="text-sm text-orange-800 mt-1 leading-relaxed">{result.diet}</p>
                                </div>
                            </div>

                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Activity className="w-5 h-5 text-blue-600" /></div>
                                <div>
                                    <h4 className="font-semibold text-blue-900">Lifestyle & Yoga (Vihara)</h4>
                                    <p className="text-sm text-blue-800 mt-1 mb-2">{result.lifestyle}</p>
                                    <div className="flex flex-wrap gap-2">
                                        {result.yoga.map((y: string) => (
                                            <span key={y} className="px-2 py-1 bg-white border border-blue-100 text-blue-700 text-xs rounded-md font-medium">
                                                {y}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
