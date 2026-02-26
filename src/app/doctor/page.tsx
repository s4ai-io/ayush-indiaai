'use client';

import { useEffect, useState } from 'react';
import { getRegistrations } from '../actions/getRegistrations';
import {
    Search, User, FileText, Activity, MapPin, Briefcase,
    ClipboardCheck, Clock, ChevronDown, ChevronUp,
    Pill, Leaf, Dumbbell, Calendar, Stethoscope,
    Phone, PhoneOff, Users, TrendingUp, X, Loader2,
} from 'lucide-react';
import Link from 'next/link';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Patient {
    id: string;
    first_name: string;
    last_name: string;
    gender: string;
    age: number;
    marital_status: string;
    mobile: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    blood_group: string;
    occupation: string;
    id_type: string;
    id_number: string;
    created_at: string;
    diagnosis_done: boolean;
}

interface CompletedDiagnosis {
    record_id: string;
    patient_id: string;
    patient_name: string;
    patient_age: number;
    patient_gender: string;
    patient_city: string;
    patient_mobile: string;
    diagnosis: string;
    symptoms: string;
    visit_date: string;
}

interface DiagnosisDetail {
    id: string;
    diagnosis: string;
    symptoms: string;
    notes: string;
    prescription: any;
    visit_date: string;
    herbs: string;
    yoga: string;
    diet: string;
    duration_weeks: number;
    improvement: number;
    outcome: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Returns "City, State" but skips falsy parts so we never show ", Gujarat" */
function formatLocation(city?: string, state?: string): string {
    return [city, state].filter(Boolean).join(', ');
}

function formatDate(iso: string): string {
    try {
        return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
        return iso;
    }
}

function initials(name: string): string {
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DoctorDashboard() {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [completedDiagnoses, setCompletedDiagnoses] = useState<CompletedDiagnosis[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'pending' | 'completed'>('pending');
    const [expandedCard, setExpandedCard] = useState<string | null>(null);
    const [diagnosisDetails, setDiagnosisDetails] = useState<Record<string, DiagnosisDetail[]>>({});
    const [loadingDetails, setLoadingDetails] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            setSearchQuery('');
            if (activeTab === 'pending') {
                const data = await getRegistrations('pending');
                setPatients(data);
            } else {
                try {
                    const res = await fetch(`${API_BASE}/api/diagnoses/completed`);
                    const data = await res.json();
                    setCompletedDiagnoses(data);
                } catch (err) {
                    console.error('Error fetching completed diagnoses:', err);
                    setCompletedDiagnoses([]);
                }
            }
            setLoading(false);
        };
        fetchData();
    }, [activeTab]);

    const toggleCard = async (patientId: string) => {
        if (expandedCard === patientId) { setExpandedCard(null); return; }
        setExpandedCard(patientId);
        if (!diagnosisDetails[patientId]) {
            setLoadingDetails(patientId);
            try {
                const res = await fetch(`${API_BASE}/api/patients/${patientId}/diagnoses`);
                const data = await res.json();
                setDiagnosisDetails(prev => ({ ...prev, [patientId]: data }));
            } catch (err) {
                console.error('Error fetching diagnosis details:', err);
            } finally {
                setLoadingDetails(null);
            }
        }
    };

    // Filter
    const q = searchQuery.toLowerCase();
    const filteredPatients = patients.filter(p =>
        (p.first_name?.toLowerCase() || '').includes(q) ||
        (p.last_name?.toLowerCase() || '').includes(q) ||
        (p.mobile || '').includes(q) ||
        (p.id_number?.toLowerCase() || '').includes(q)
    );
    const filteredDiagnoses = completedDiagnoses.filter(d =>
        d.patient_name.toLowerCase().includes(q) ||
        d.diagnosis.toLowerCase().includes(q) ||
        (d.patient_city?.toLowerCase() || '').includes(q)
    );

    const switchTab = (tab: 'pending' | 'completed') => {
        setActiveTab(tab);
        setExpandedCard(null);
    };

    return (
        <div className="min-h-screen bg-background">
            <div className="max-w-6xl mx-auto px-4 py-6 md:px-8 md:py-10 space-y-6">

                {/* ── Header ── */}
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                            <Stethoscope className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-foreground tracking-tight leading-none">Doctor Dashboard</h1>
                            <p className="text-sm text-muted-foreground mt-0.5">Clinical Queue &amp; Patient Management</p>
                        </div>
                    </div>

                    {/* Search and New Consultation Action */}
                    <div className="flex flex-col md:flex-row w-full md:w-auto gap-3 items-center">
                        <div className="relative w-full md:w-72">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                            <input
                                type="text"
                                placeholder={activeTab === 'pending' ? 'Search name, mobile, ID…' : 'Search patient, disease, city…'}
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                className="w-full h-10 pl-9 pr-9 rounded-xl border border-input bg-card text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary shadow-sm transition-all"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                        <Link href="/consultation" className="w-full md:w-auto">
                            <button className="w-full md:w-auto flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl shadow-sm transition-colors font-medium h-10">
                                <Stethoscope className="w-4 h-4" />
                                <span>New Consultation</span>
                            </button>
                        </Link>
                    </div>
                </div>

                {/* ── Tab Strip ── */}
                <div className="flex items-center gap-1 bg-muted/40 rounded-xl p-1 w-fit border border-border">
                    <TabButton
                        active={activeTab === 'pending'}
                        onClick={() => switchTab('pending')}
                        icon={<Clock className="w-4 h-4" />}
                        label="Pending Queue"
                        count={activeTab === 'pending' && !loading ? patients.length : undefined}
                        activeColor="bg-primary text-primary-foreground"
                    />
                    <TabButton
                        active={activeTab === 'completed'}
                        onClick={() => switchTab('completed')}
                        icon={<ClipboardCheck className="w-4 h-4" />}
                        label="Completed"
                        count={activeTab === 'completed' && !loading ? completedDiagnoses.length : undefined}
                        activeColor="bg-emerald-600 text-white"
                    />
                </div>

                {/* ── Content ── */}
                {loading ? (
                    <LoadingSkeleton />
                ) : activeTab === 'pending' ? (
                    filteredPatients.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {filteredPatients.map(patient => (
                                <PatientCard key={patient.id} patient={patient} />
                            ))}
                        </div>
                    ) : (
                        <EmptyState
                            icon={searchQuery ? <Search className="w-8 h-8" /> : <ClipboardCheck className="w-8 h-8" />}
                            title={searchQuery ? `No results for "${searchQuery}"` : 'All patients diagnosed!'}
                            subtitle={searchQuery ? 'Try adjusting your search terms.' : 'No pending patients in the queue. Check the Completed tab.'}
                            color={searchQuery ? 'amber' : 'emerald'}
                        />
                    )
                ) : (
                    filteredDiagnoses.length > 0 ? (
                        <div className="space-y-3">
                            {filteredDiagnoses.map(d => (
                                <CompletedCard
                                    key={d.record_id}
                                    d={d}
                                    isExpanded={expandedCard === d.patient_id}
                                    isLoadingDetails={loadingDetails === d.patient_id}
                                    details={diagnosisDetails[d.patient_id]}
                                    onToggle={() => toggleCard(d.patient_id)}
                                />
                            ))}
                        </div>
                    ) : (
                        <EmptyState
                            icon={<Search className="w-8 h-8" />}
                            title={searchQuery ? `No results for "${searchQuery}"` : 'No completed diagnoses yet'}
                            subtitle={searchQuery ? 'Try adjusting your search terms.' : 'Diagnoses you complete will appear here.'}
                            color="amber"
                        />
                    )
                )}
            </div>
        </div>
    );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatChip({ icon, label, value, color }: {
    icon: React.ReactNode; label: string; value: string;
    color: 'primary' | 'emerald' | 'amber';
}) {
    const colors = {
        primary: 'bg-primary/10 text-primary border-primary/20',
        emerald: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
        amber: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
    };
    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium ${colors[color]}`}>
            {icon}
            <span>{label}</span>
            <span className="font-bold">{value}</span>
        </div>
    );
}

function TabButton({ active, onClick, icon, label, count, activeColor }: {
    active: boolean; onClick: () => void; icon: React.ReactNode;
    label: string; count?: number; activeColor: string;
}) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 ${active
                ? `${activeColor} shadow-sm`
                : 'text-muted-foreground hover:text-foreground hover:bg-background/60'
                }`}
        >
            {icon}
            {label}
            {count !== undefined && (
                <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${active ? 'bg-white/20' : 'bg-border text-muted-foreground'}`}>
                    {count}
                </span>
            )}
        </button>
    );
}

function PatientCard({ patient }: { patient: Patient }) {
    const location = formatLocation(patient.city, patient.state);
    const hasMobile = patient.mobile && patient.mobile.trim().length > 0;

    // Gender accent color
    const accentClass = patient.gender === 'Female'
        ? 'border-t-pink-400'
        : patient.gender === 'Transgender'
            ? 'border-t-amber-400'
            : 'border-t-primary';

    const avatarClass = patient.gender === 'Female'
        ? 'bg-pink-50 text-pink-600'
        : patient.gender === 'Transgender'
            ? 'bg-amber-50 text-amber-600'
            : 'bg-primary/10 text-primary';

    return (
        <div className={`group relative bg-card rounded-2xl shadow-sm border border-border border-t-4 ${accentClass} hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 overflow-hidden`}>
            <div className="p-5 space-y-4">

                {/* Avatar + Name */}
                <div className="flex items-center gap-3.5">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-base shrink-0 ${avatarClass}`}>
                        {patient.first_name?.[0]}{patient.last_name?.[0]}
                    </div>
                    <div className="min-w-0">
                        <h3 className="font-bold text-foreground text-base leading-tight truncate group-hover:text-primary transition-colors">
                            {patient.first_name} {patient.last_name}
                        </h3>
                        <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                            <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                                {patient.gender}
                            </span>
                            <span className="text-muted-foreground/50 text-xs">•</span>
                            <span className="text-muted-foreground text-xs">{patient.age} yrs</span>
                            {patient.blood_group && (
                                <>
                                    <span className="text-muted-foreground/50 text-xs">•</span>
                                    <span className="text-xs font-semibold text-destructive/70">{patient.blood_group}</span>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Mobile */}
                <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm ${hasMobile
                    ? 'bg-primary/5 border border-primary/10 text-foreground'
                    : 'bg-muted/40 border border-border text-muted-foreground'
                    }`}>
                    {hasMobile
                        ? <Phone className="w-4 h-4 text-primary shrink-0" />
                        : <PhoneOff className="w-4 h-4 shrink-0" />
                    }
                    <span className="font-medium truncate">{hasMobile ? patient.mobile : 'No mobile on record'}</span>
                </div>

                {/* Location + Occupation */}
                <div className="grid grid-cols-2 gap-2">
                    {location && (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground min-w-0">
                            <MapPin className="w-3.5 h-3.5 shrink-0" />
                            <span className="truncate">{location}</span>
                        </div>
                    )}
                    {patient.occupation && (
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground justify-end min-w-0">
                            <Briefcase className="w-3.5 h-3.5 shrink-0" />
                            <span className="truncate">{patient.occupation}</span>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="pt-3 border-t border-border flex items-center justify-between gap-3">
                    <div className="text-xs text-muted-foreground">
                        <span className="block font-medium text-foreground/60">Registered</span>
                        {formatDate(patient.created_at)}
                    </div>
                    <Link href={`/consultation?patientId=${patient.id}`} className="flex-1">
                        <button className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 active:scale-95 text-primary-foreground py-2.5 px-4 rounded-xl font-semibold text-sm transition-all shadow-sm hover:shadow-primary/20 hover:shadow-md">
                            <Stethoscope className="w-4 h-4" />
                            Consult
                        </button>
                    </Link>
                </div>
            </div>
        </div>
    );
}

function CompletedCard({ d, isExpanded, isLoadingDetails, details, onToggle }: {
    d: CompletedDiagnosis;
    isExpanded: boolean;
    isLoadingDetails: boolean;
    details?: DiagnosisDetail[];
    onToggle: () => void;
}) {
    return (
        <div className={`bg-card rounded-2xl border shadow-sm transition-all duration-200 hover:shadow-md overflow-hidden ${isExpanded ? 'border-emerald-200' : 'border-border'}`}>
            {/* Clickable header */}
            <button
                onClick={onToggle}
                className="w-full p-4 flex items-center gap-4 text-left hover:bg-muted/20 transition-colors"
            >
                <div className="w-11 h-11 bg-emerald-50 rounded-xl flex items-center justify-center text-emerald-700 font-bold text-sm ring-2 ring-emerald-100 shrink-0">
                    {initials(d.patient_name)}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-bold text-foreground text-sm">{d.patient_name}</h3>
                        <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold border border-emerald-200">
                            {d.diagnosis}
                        </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 flex-wrap text-xs text-muted-foreground">
                        <span>{d.patient_gender} · {d.patient_age} yrs</span>
                        {d.patient_city && (
                            <>
                                <span className="text-border">|</span>
                                <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{d.patient_city}</span>
                            </>
                        )}
                        {d.patient_mobile && (
                            <>
                                <span className="text-border">|</span>
                                <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{d.patient_mobile}</span>
                            </>
                        )}
                        {d.visit_date && (
                            <>
                                <span className="text-border">|</span>
                                <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{formatDate(d.visit_date)}</span>
                            </>
                        )}
                    </div>
                </div>
                <div className="text-muted-foreground shrink-0">
                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
            </button>

            {/* Expanded detail */}
            {isExpanded && (
                <div className="border-t border-emerald-100 p-5 bg-gradient-to-b from-emerald-50/30 to-transparent animate-in slide-in-from-top-2 duration-200">
                    {isLoadingDetails ? (
                        <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
                            <Loader2 className="w-5 h-5 animate-spin text-primary" />
                            <span className="text-sm">Loading diagnosis details…</span>
                        </div>
                    ) : details && details.length > 0 ? (
                        <div className="space-y-6">
                            {details.map((detail, idx) => (
                                <div key={detail.id} className="space-y-4">
                                    {idx > 0 && <hr className="border-border" />}

                                    {/* Symptoms */}
                                    <div>
                                        <h4 className="text-xs font-semibold text-foreground uppercase tracking-wide flex items-center gap-2 mb-2">
                                            <Stethoscope className="w-3.5 h-3.5 text-blue-500" />
                                            Symptoms
                                        </h4>
                                        <p className="text-sm text-muted-foreground bg-card p-3 rounded-lg border border-border">
                                            {detail.symptoms || 'No symptoms recorded'}
                                        </p>
                                    </div>

                                    {/* Treatment grid */}
                                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                        <TreatmentCard
                                            icon={<Leaf className="w-4 h-4" />}
                                            label="Herbs"
                                            value={detail.herbs}
                                            color="emerald"
                                        />
                                        <TreatmentCard
                                            icon={<Dumbbell className="w-4 h-4" />}
                                            label="Yoga"
                                            value={detail.yoga}
                                            color="primary"
                                        />
                                        <TreatmentCard
                                            icon={<Pill className="w-4 h-4" />}
                                            label="Diet"
                                            value={detail.diet}
                                            color="amber"
                                        />
                                    </div>

                                    {/* Stats */}
                                    {(detail.duration_weeks || detail.improvement || detail.outcome) && (
                                        <div className="flex flex-wrap gap-2">
                                            {detail.duration_weeks ? (
                                                <span className="px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 text-xs font-medium border border-blue-100">
                                                    {detail.duration_weeks} weeks treatment
                                                </span>
                                            ) : null}
                                            {detail.improvement ? (
                                                <span className="px-3 py-1.5 rounded-full bg-green-50 text-green-700 text-xs font-medium border border-green-100">
                                                    {detail.improvement}% improvement expected
                                                </span>
                                            ) : null}
                                            {detail.outcome ? (
                                                <span className="px-3 py-1.5 rounded-full bg-purple-50 text-purple-700 text-xs font-medium border border-purple-100">
                                                    {detail.outcome}
                                                </span>
                                            ) : null}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-center text-muted-foreground text-sm py-6">No diagnosis details found.</p>
                    )}
                </div>
            )}
        </div>
    );
}

function TreatmentCard({ icon, label, value, color }: {
    icon: React.ReactNode; label: string; value?: string;
    color: 'emerald' | 'primary' | 'amber';
}) {
    const colors = {
        emerald: 'text-emerald-700 bg-emerald-50 border-emerald-100',
        primary: 'text-primary bg-primary/5 border-primary/10',
        amber: 'text-amber-700 bg-amber-50 border-amber-100',
    };
    return (
        <div className={`p-4 rounded-xl border ${colors[color]}`}>
            <h4 className="text-xs font-bold uppercase tracking-wide flex items-center gap-1.5 mb-2">
                {icon}{label}
            </h4>
            <p className="text-sm text-muted-foreground leading-relaxed">{value || 'None'}</p>
        </div>
    );
}

function EmptyState({ icon, title, subtitle, color }: {
    icon: React.ReactNode; title: string; subtitle: string;
    color: 'emerald' | 'amber' | 'primary';
}) {
    const colors = {
        emerald: 'bg-emerald-50 text-emerald-400',
        amber: 'bg-amber-50 text-amber-400',
        primary: 'bg-primary/10 text-primary',
    };
    return (
        <div className="text-center py-20 bg-card rounded-2xl border border-dashed border-border">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${colors[color]}`}>
                {icon}
            </div>
            <h3 className="text-base font-semibold text-foreground">{title}</h3>
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
        </div>
    );
}

function LoadingSkeleton() {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-card rounded-2xl border border-border p-5 space-y-4 animate-pulse">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-muted" />
                        <div className="space-y-2 flex-1">
                            <div className="h-4 bg-muted rounded w-2/3" />
                            <div className="h-3 bg-muted rounded w-1/2" />
                        </div>
                    </div>
                    <div className="h-9 bg-muted rounded-lg" />
                    <div className="h-3 bg-muted rounded w-3/4" />
                    <div className="h-10 bg-muted rounded-xl" />
                </div>
            ))}
        </div>
    );
}
