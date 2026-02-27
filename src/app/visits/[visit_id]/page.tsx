'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { API_BASE } from '@/lib/config';
import {
    User, Stethoscope, Leaf, Activity, FileText, Star,
    Phone, MapPin, Calendar, ArrowLeft, Loader2,
    Heart, Pill, BookOpen, Clock, TrendingUp
} from 'lucide-react';
import type { VisitDetails } from '@/types';



// ─── Helpers ─────────────────────────────────────────────────────
function Field({ label, value }: { label: string; value?: string | number | null }) {
    if (!value && value !== 0) return null;
    return (
        <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-0.5">{label}</p>
            <p className="text-sm text-slate-800">{String(value)}</p>
        </div>
    );
}

function Section({ icon, title, children, accent = 'indigo' }: { icon: React.ReactNode; title: string; children: React.ReactNode; accent?: string }) {
    const colors: Record<string, string> = {
        indigo: 'border-indigo-200 bg-indigo-50/40',
        emerald: 'border-emerald-200 bg-emerald-50/40',
        amber: 'border-amber-200 bg-amber-50/40',
        violet: 'border-violet-200 bg-violet-50/40',
        sky: 'border-sky-200 bg-sky-50/40',
    };
    return (
        <div className={`rounded-xl border p-5 ${colors[accent] ?? colors.indigo}`}>
            <h2 className="flex items-center gap-2 text-sm font-bold text-slate-700 mb-4">
                {icon} {title}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-3">
                {children}
            </div>
        </div>
    );
}

function SeverityBar({ value }: { value: string }) {
    const n = parseInt(value) || 0;
    const pct = (n / 10) * 100;
    const color = n <= 3 ? 'bg-emerald-400' : n <= 6 ? 'bg-amber-400' : 'bg-red-400';
    return (
        <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Severity</p>
            <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="text-sm font-bold text-slate-700">{n}/10</span>
            </div>
        </div>
    );
}

function StarRating({ value }: { value: string }) {
    const n = parseInt(value) || 0;
    if (!n) return null;
    return (
        <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Doctor Rating</p>
            <div className="flex gap-0.5">
                {[1, 2, 3, 4, 5].map(i => (
                    <Star key={i} className={`w-4 h-4 ${i <= n ? 'text-amber-400 fill-amber-400' : 'text-slate-200'}`} />
                ))}
            </div>
        </div>
    );
}

// ─── Main Page ───────────────────────────────────────────────────
export default function VisitDetailsPage({ params }: { params: Promise<{ visit_id: string }> }) {
    const { visit_id } = use(params);
    const [data, setData] = useState<VisitDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/visits/${visit_id}`, { cache: 'no-store' });
                if (!res.ok) throw new Error(`Status ${res.status}`);
                setData(await res.json());
            } catch (err: any) {
                setError(err.message || 'Failed to load visit details.');
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [visit_id]);

    if (loading) return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
        </div>
    );

    if (error || !data) return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 gap-4">
            <FileText className="w-12 h-12 text-slate-300" />
            <p className="text-slate-500">{error || 'Visit not found.'}</p>
            <Link href="/patients" className="text-indigo-600 text-sm hover:underline">← Back to Patients</Link>
        </div>
    );

    const { patient: p, visit: v, treatment: t, feedback: fb } = data;
    const visitDate = v.visitDate ? new Date(v.visitDate).toLocaleString('en-IN', { dateStyle: 'long', timeStyle: 'short' }) : '—';

    return (
        <div className="min-h-screen bg-slate-50 py-8 px-4 md:px-8">
            <div className="max-w-5xl mx-auto space-y-6">

                {/* Back + Header */}
                <div className="flex items-start justify-between">
                    <Link href="/patients" className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-indigo-600 transition-colors">
                        <ArrowLeft className="w-4 h-4" /> Back to Patients
                    </Link>
                    <span className="text-xs font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded">{v.id}</span>
                </div>

                {/* Patient identity banner */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 flex flex-col sm:flex-row justify-between gap-4">
                    <div className="flex gap-4 items-center">
                        <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-2xl shrink-0">
                            {p.firstName?.[0] ?? '?'}{p.lastName?.[0] ?? ''}
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-slate-900">{p.firstName} {p.lastName}</h1>
                            <div className="flex flex-wrap gap-3 text-sm text-slate-500 mt-1">
                                {p.gender && <span>{p.gender}</span>}
                                {p.age && <span>• {p.age} yrs</span>}
                                {p.bloodGroup && <span>• {p.bloodGroup}</span>}
                                {p.mobile && <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" />{p.mobile}</span>}
                            </div>
                        </div>
                    </div>
                    <div className="flex items-start gap-2 text-sm text-slate-500 sm:text-right">
                        <Calendar className="w-4 h-4 mt-0.5 text-indigo-400 shrink-0" />
                        <div>
                            <p className="text-xs text-slate-400 font-medium">Visit Date</p>
                            <p className="text-slate-700 font-medium">{visitDate}</p>
                        </div>
                    </div>
                </div>

                {/* Patient Demographics */}
                <Section icon={<User className="w-4 h-4 text-indigo-500" />} title="Patient Demographics" accent="indigo">
                    <Field label="Marital Status" value={p.maritalStatus} />
                    <Field label="Occupation" value={p.occupation} />
                    <div className="col-span-2 md:col-span-3">
                        {(p.address || p.city) && (
                            <div>
                                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-0.5">Address</p>
                                <p className="text-sm text-slate-800 flex items-start gap-1">
                                    <MapPin className="w-3.5 h-3.5 mt-0.5 text-slate-400 shrink-0" />
                                    {[p.address, p.city, p.state, p.pincode].filter(Boolean).join(', ')}
                                </p>
                            </div>
                        )}
                    </div>
                    <Field label={p.idType || 'ID Type'} value={p.idNumber} />
                </Section>

                {/* Clinical Assessment */}
                <Section icon={<Stethoscope className="w-4 h-4 text-emerald-600" />} title="Clinical Assessment" accent="emerald">
                    <div className="col-span-2 md:col-span-3">
                        <Field label="Symptoms / Chief Complaint" value={v.symptoms} />
                    </div>
                    <div className="col-span-2 md:col-span-3">
                        <Field label="Diagnosis" value={v.diagnosis} />
                    </div>
                    <Field label="Prakriti (Constitution)" value={v.prakriti} />
                    <Field label="Vikriti (Imbalance)" value={v.vikriti} />
                    <Field label="Comorbidities" value={v.comorbidities} />
                    {v.severity && (
                        <div className="col-span-2 md:col-span-3">
                            <SeverityBar value={v.severity} />
                        </div>
                    )}
                    {v.notes && (
                        <div className="col-span-2 md:col-span-3">
                            <Field label="Doctor Notes" value={v.notes} />
                        </div>
                    )}
                </Section>

                {/* Prescription (if present) */}
                {Boolean(v.prescription) && Boolean((v.prescription as Record<string, unknown>).doctor_notes || (v.prescription as Record<string, unknown>).ai_plan) && (
                    <Section icon={<Pill className="w-4 h-4 text-violet-600" />} title="Prescription" accent="violet">
                        {Boolean((v.prescription as Record<string, unknown>).doctor_notes) && (
                            <div className="col-span-2 md:col-span-3">
                                <Field label="Doctor Prescription" value={(v.prescription as Record<string, string>).doctor_notes} />
                            </div>
                        )}
                    </Section>
                )}


                {/* AYUSH Treatment Plan */}
                {(t.herbs || t.yoga || t.diet) && (
                    <Section icon={<Leaf className="w-4 h-4 text-emerald-700" />} title="AYUSH Treatment Plan" accent="emerald">
                        {t.herbs && (
                            <div className="col-span-2 md:col-span-3">
                                <Field label="Herbs Prescribed" value={t.herbs} />
                            </div>
                        )}
                        {t.yoga && (
                            <div className="col-span-2 md:col-span-3">
                                <Field label="Yoga / Practices" value={t.yoga} />
                            </div>
                        )}
                        {t.diet && (
                            <div className="col-span-2 md:col-span-3">
                                <Field label="Diet Plan" value={t.diet} />
                            </div>
                        )}
                        {t.durationWeeks && <Field label="Duration (weeks)" value={t.durationWeeks} />}
                        {t.predictedImprovement && <Field label="Predicted Improvement" value={`${t.predictedImprovement}%`} />}
                        {t.outcome && <Field label="Outcome" value={t.outcome} />}
                    </Section>
                )}

                {/* Doctor Feedback */}
                {(fb.rating || fb.comments) && (
                    <Section icon={<Star className="w-4 h-4 text-amber-500" />} title="Doctor Feedback" accent="amber">
                        <StarRating value={fb.rating} />
                        {fb.comments && (
                            <div className="col-span-2 md:col-span-3">
                                <Field label="Doctor Comments" value={fb.comments} />
                            </div>
                        )}
                    </Section>
                )}

            </div>
        </div>
    );
}
