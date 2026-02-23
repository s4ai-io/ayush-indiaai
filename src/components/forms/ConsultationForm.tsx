'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { getMLRecommendation, validatePatientProfile, MLAPIError, type PatientProfile, type TreatmentRecommendation } from '@/lib/api/ml-client';
import { DiseaseSearchDropdown } from '@/components/ui/DiseaseSearchDropdown';
import { Stethoscope, Leaf, Pizza, Activity, AlertCircle, Loader2, TrendingUp, Calendar } from 'lucide-react';

export function ConsultationForm({ initialCondition }: { initialCondition?: string }) {
    // Form state
    const [age, setAge] = useState<number>(35);
    const [gender, setGender] = useState<'Male' | 'Female'>('Male');
    const [prakriti, setPrakriti] = useState<string>('Vata');
    const [vikriti, setVikriti] = useState<string>('Vata');
    const [condition, setCondition] = useState<string>(initialCondition || 'Anxiety');
    const [symptoms, setSymptoms] = useState<string>('');
    const [severity, setSeverity] = useState<number>(5);
    const [bmi, setBmi] = useState<number | undefined>(undefined);
    const [height, setHeight] = useState<number | undefined>(undefined);
    const [weight, setWeight] = useState<number | undefined>(undefined);

    // UI state
    const [result, setResult] = useState<TreatmentRecommendation | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Calculate BMI when height and weight change
    const calculateBMI = () => {
        if (height && weight && height > 0) {
            const heightInMeters = height / 100;
            const calculatedBMI = weight / (heightInMeters * heightInMeters);
            setBmi(parseFloat(calculatedBMI.toFixed(1)));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            // Build patient profile
            const profile: PatientProfile = {
                age,
                gender,
                prakriti,
                vikriti,
                disease: condition,
                symptoms,
                severity,
                bmi
            };

            // Validate profile
            const validationErrors = validatePatientProfile(profile);
            if (validationErrors.length > 0) {
                setError(validationErrors.join(', '));
                setLoading(false);
                return;
            }

            // Get ML recommendation
            const recommendation = await getMLRecommendation(profile);
            setResult(recommendation);

        } catch (err) {
            if (err instanceof MLAPIError) {
                setError(err.message);
            } else {
                setError('An unexpected error occurred. Please try again.');
            }
            console.error('Error getting recommendation:', err);
        } finally {
            setLoading(false);
        }
    };

    const doshaOptions = [
        'Vata',
        'Pitta',
        'Kapha',
        'Vata-Pitta',
        'Pitta-Kapha',
        'Vata-Kapha',
        'Tridosha'
    ];

    return (
        <div className="grid gap-6 lg:grid-cols-2">
            <Card>
                <CardHeader>
                    <CardTitle>Patient Assessment</CardTitle>
                    <CardDescription>Provide patient details for AI-powered AYUSH treatment recommendations</CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Demographics */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Age</label>
                                <input
                                    type="number"
                                    className="w-full p-2 border rounded-md"
                                    value={age}
                                    onChange={(e) => setAge(parseInt(e.target.value) || 0)}
                                    min="0"
                                    max="120"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Gender</label>
                                <select
                                    className="w-full p-2 border rounded-md"
                                    value={gender}
                                    onChange={(e) => setGender(e.target.value as 'Male' | 'Female')}
                                    required
                                >
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                </select>
                            </div>
                        </div>

                        {/* BMI Calculator */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">BMI (Optional)</label>
                            <div className="grid grid-cols-3 gap-2">
                                <input
                                    type="number"
                                    placeholder="Height (cm)"
                                    className="p-2 border rounded-md text-sm"
                                    value={height || ''}
                                    onChange={(e) => setHeight(parseFloat(e.target.value) || undefined)}
                                    onBlur={calculateBMI}
                                />
                                <input
                                    type="number"
                                    placeholder="Weight (kg)"
                                    className="p-2 border rounded-md text-sm"
                                    value={weight || ''}
                                    onChange={(e) => setWeight(parseFloat(e.target.value) || undefined)}
                                    onBlur={calculateBMI}
                                />
                                <input
                                    type="number"
                                    placeholder="BMI"
                                    className="p-2 border rounded-md text-sm bg-gray-50"
                                    value={bmi || ''}
                                    onChange={(e) => setBmi(parseFloat(e.target.value) || undefined)}
                                    step="0.1"
                                />
                            </div>
                        </div>

                        {/* Primary Health Concern */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Primary Health Concern <span className="text-red-500">*</span></label>
                            <DiseaseSearchDropdown
                                value={condition}
                                onChange={setCondition}
                                required
                                placeholder="Search for a disease..."
                            />
                        </div>

                        {/* Symptoms */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Symptoms <span className="text-xs text-slate-400 font-normal">(optional)</span></label>
                            <textarea
                                className="w-full p-2 border rounded-md resize-none"
                                value={symptoms}
                                onChange={(e) => setSymptoms(e.target.value)}
                                placeholder="e.g. excessive thirst, frequent urination, fatigue..."
                                rows={3}
                            />
                        </div>

                        {/* Severity Slider */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">
                                Severity: <span className="text-primary font-bold">{severity}/10</span>
                            </label>
                            <input
                                type="range"
                                className="w-full"
                                min="1"
                                max="10"
                                value={severity}
                                onChange={(e) => setSeverity(parseInt(e.target.value))}
                            />
                            <div className="flex justify-between text-xs text-muted-foreground">
                                <span>Mild</span>
                                <span>Moderate</span>
                                <span>Severe</span>
                            </div>
                        </div>

                        {/* Prakriti */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Prakriti (Natural Constitution)</label>
                            <select
                                className="w-full p-2 border rounded-md"
                                value={prakriti}
                                onChange={(e) => setPrakriti(e.target.value)}
                                required
                            >
                                {doshaOptions.map(dosha => (
                                    <option key={dosha} value={dosha}>{dosha}</option>
                                ))}
                            </select>
                        </div>

                        {/* Vikriti */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Vikriti (Current Imbalance)</label>
                            <select
                                className="w-full p-2 border rounded-md"
                                value={vikriti}
                                onChange={(e) => setVikriti(e.target.value)}
                                required
                            >
                                {doshaOptions.filter(d => d !== 'Tridosha').map(dosha => (
                                    <option key={dosha} value={dosha}>{dosha}</option>
                                ))}
                            </select>
                        </div>

                        <div className="p-3 bg-blue-50 text-blue-800 text-xs rounded-md flex gap-2">
                            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                            <p>AI will analyze the intersection of the disease pathology (Samprapti) and patient constitution (Prakriti) to generate personalized recommendations.</p>
                        </div>

                        {/* Error Display */}
                        {error && (
                            <div className="p-3 bg-red-50 text-red-800 text-sm rounded-md flex gap-2">
                                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                <p>{error}</p>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-md hover:opacity-90 transition-opacity font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Generating AI Recommendation...
                                </>
                            ) : (
                                'Generate Treatment Protocol'
                            )}
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
                                AI-Powered AYUSH Protocol: {condition}
                            </CardTitle>
                            <p className="text-sm text-emerald-700">Tailored for {prakriti} constitution with {vikriti} imbalance</p>
                        </CardHeader>
                        <CardContent className="space-y-5">
                            {/* ML Predictions */}
                            {(result.predicted_improvement || result.recommended_duration_weeks) && (
                                <div className="grid grid-cols-2 gap-3 p-3 bg-white rounded-lg border border-emerald-200">
                                    {result.predicted_improvement && (
                                        <div className="flex items-center gap-2">
                                            <TrendingUp className="w-4 h-4 text-emerald-600" />
                                            <div>
                                                <p className="text-xs text-gray-600">Expected Improvement</p>
                                                <p className="text-lg font-bold text-emerald-700">{result.predicted_improvement}%</p>
                                            </div>
                                        </div>
                                    )}
                                    {result.recommended_duration_weeks && (
                                        <div className="flex items-center gap-2">
                                            <Calendar className="w-4 h-4 text-emerald-600" />
                                            <div>
                                                <p className="text-xs text-gray-600">Duration</p>
                                                <p className="text-lg font-bold text-emerald-700">{result.recommended_duration_weeks} weeks</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Herbs */}
                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Leaf className="w-5 h-5 text-emerald-600" /></div>
                                <div className="flex-1">
                                    <h4 className="font-semibold text-emerald-900">Medicinal Herbs (Aushadhi)</h4>
                                    <div className="mt-2 space-y-2">
                                        {result.herbs.map((herb, idx) => (
                                            <div key={idx} className="text-sm">
                                                <p className="font-medium text-emerald-800">{herb.name} - {herb.dosage}</p>
                                                <p className="text-emerald-700 text-xs">{herb.benefits}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Yoga */}
                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Activity className="w-5 h-5 text-blue-600" /></div>
                                <div className="flex-1">
                                    <h4 className="font-semibold text-blue-900">Yoga & Pranayama (Vihara)</h4>
                                    <div className="mt-2 space-y-2">
                                        {result.yoga.map((yoga, idx) => (
                                            <div key={idx} className="text-sm">
                                                <p className="font-medium text-blue-800">{yoga.practice} - {yoga.duration}</p>
                                                <p className="text-blue-700 text-xs">{yoga.benefits}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Diet */}
                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Pizza className="w-5 h-5 text-orange-600" /></div>
                                <div className="flex-1">
                                    <h4 className="font-semibold text-orange-900">Dietary Guidelines (Ahara)</h4>
                                    <ul className="list-disc pl-4 text-sm text-orange-800 marker:text-orange-500 mt-2 space-y-1">
                                        {result.diet.map((guideline, idx) => (
                                            <li key={idx}>{guideline}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            {/* Lifestyle */}
                            <div className="flex gap-4">
                                <div className="mt-1 p-2 bg-white rounded-full shadow-sm h-fit"><Activity className="w-5 h-5 text-purple-600" /></div>
                                <div className="flex-1">
                                    <h4 className="font-semibold text-purple-900">Lifestyle Modifications</h4>
                                    <ul className="list-disc pl-4 text-sm text-purple-800 marker:text-purple-500 mt-2 space-y-1">
                                        {result.lifestyle.map((modification, idx) => (
                                            <li key={idx}>{modification}</li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
