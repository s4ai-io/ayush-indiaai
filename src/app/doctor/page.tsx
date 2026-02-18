'use client';

import { useEffect, useState } from 'react';
import { getRegistrations } from '../actions/getRegistrations';
import { Search, User, FileText, Activity, MapPin, Briefcase, ClipboardCheck, Clock, ChevronDown, ChevronUp, Pill, Leaf, Dumbbell, Calendar, Stethoscope } from 'lucide-react';
import Link from 'next/link';


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

export default function DoctorDashboard() {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [completedDiagnoses, setCompletedDiagnoses] = useState<CompletedDiagnosis[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'pending' | 'completed'>('pending');
    const [expandedCard, setExpandedCard] = useState<string | null>(null);
    const [diagnosisDetails, setDiagnosisDetails] = useState<Record<string, DiagnosisDetail[]>>({});
    const [loadingDetails, setLoadingDetails] = useState<string | null>(null);

    // Fetch patients for either tab
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            if (activeTab === 'pending') {
                const data = await getRegistrations('pending');
                setPatients(data);
            } else {
                try {
                    const res = await fetch('http://localhost:8000/api/diagnoses/completed');
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

    // Expand/collapse a completed card and fetch detail
    const toggleCard = async (patientId: string) => {
        if (expandedCard === patientId) {
            setExpandedCard(null);
            return;
        }
        setExpandedCard(patientId);

        if (!diagnosisDetails[patientId]) {
            setLoadingDetails(patientId);
            try {
                const res = await fetch(`http://localhost:8000/api/patients/${patientId}/diagnoses`);
                const data = await res.json();
                setDiagnosisDetails(prev => ({ ...prev, [patientId]: data }));
            } catch (err) {
                console.error('Error fetching diagnosis details:', err);
            } finally {
                setLoadingDetails(null);
            }
        }
    };

    // Filter logic
    const filteredPatients = patients.filter(patient => {
        const lowerQuery = searchQuery.toLowerCase();
        return (
            (patient.first_name?.toLowerCase() || '').includes(lowerQuery) ||
            (patient.last_name?.toLowerCase() || '').includes(lowerQuery) ||
            (patient.mobile?.includes(lowerQuery)) ||
            (patient.id_number?.toLowerCase() || '').includes(lowerQuery)
        );
    });

    const filteredDiagnoses = completedDiagnoses.filter(d => {
        const lowerQuery = searchQuery.toLowerCase();
        return (
            d.patient_name.toLowerCase().includes(lowerQuery) ||
            d.diagnosis.toLowerCase().includes(lowerQuery) ||
            d.patient_city?.toLowerCase().includes(lowerQuery)
        );
    });

    // Stats
    const pendingCount = activeTab === 'pending' ? patients.length : '—';
    const completedCount = activeTab === 'completed' ? completedDiagnoses.length : '—';

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Doctor Dashboard</h1>
                        <p className="text-slate-600">Clinical Queue & Patient Management</p>
                    </div>
                    <div className="flex items-center gap-2 bg-white px-4 py-3 rounded-xl shadow-sm border border-slate-200 w-full md:w-auto focus-within:ring-2 focus-within:ring-purple-100 transition-all">
                        <Search className="w-5 h-5 text-slate-400" />
                        <input
                            type="text"
                            placeholder={activeTab === 'pending' ? "Search by name, mobile, or ID..." : "Search by patient, disease, or city..."}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-transparent border-none outline-none text-slate-900 placeholder-slate-400 w-full md:w-64"
                        />
                    </div>
                </header>

                {/* Tab Toggle */}
                <div className="flex items-center gap-3 bg-white rounded-xl p-1.5 shadow-sm border border-slate-200 w-fit">
                    <button
                        onClick={() => { setActiveTab('pending'); setSearchQuery(''); }}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${activeTab === 'pending'
                                ? 'bg-purple-600 text-white shadow-sm'
                                : 'text-slate-600 hover:bg-slate-100'
                            }`}
                    >
                        <Clock className="w-4 h-4" />
                        Pending Queue
                    </button>
                    <button
                        onClick={() => { setActiveTab('completed'); setSearchQuery(''); }}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-sm transition-all ${activeTab === 'completed'
                                ? 'bg-emerald-600 text-white shadow-sm'
                                : 'text-slate-600 hover:bg-slate-100'
                            }`}
                    >
                        <ClipboardCheck className="w-4 h-4" />
                        Completed Diagnoses
                    </button>
                </div>

                {/* Content */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-500 space-y-4">
                        <Activity className="w-8 h-8 animate-pulse text-purple-400" />
                        <p>Loading {activeTab === 'pending' ? 'patient queue' : 'completed diagnoses'}...</p>
                    </div>
                ) : activeTab === 'pending' ? (
                    /* ───── PENDING QUEUE ───── */
                    filteredPatients.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredPatients.map((patient) => (
                                <div key={patient.id} className="group bg-white rounded-xl shadow-sm border border-slate-200 border-t-4 border-t-purple-500 overflow-hidden hover:shadow-lg transition-all duration-300">
                                    <div className="p-6 space-y-5">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="w-14 h-14 bg-purple-50 rounded-2xl flex items-center justify-center text-purple-600 font-bold text-xl ring-4 ring-white shadow-sm">
                                                    {patient.first_name?.[0]}{patient.last_name?.[0]}
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-slate-900 text-lg leading-tight group-hover:text-purple-700 transition-colors">
                                                        {patient.first_name} {patient.last_name}
                                                    </h3>
                                                    <div className="flex items-center gap-2 mt-1">
                                                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
                                                            {patient.gender}
                                                        </span>
                                                        <span className="text-sm text-slate-400">•</span>
                                                        <span className="text-sm text-slate-500">{patient.age} Yrs</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-3 pt-2">
                                            <div className="flex items-center gap-3 text-sm text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                                                <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shadow-sm text-purple-500">
                                                    <User className="w-4 h-4" />
                                                </div>
                                                <span className="font-medium">{patient.mobile || 'No Mobile'}</span>
                                            </div>

                                            <div className="grid grid-cols-2 gap-2">
                                                <div className="flex items-center gap-2 text-xs text-slate-500">
                                                    <MapPin className="w-3.5 h-3.5" />
                                                    <span className="truncate">{patient.city}, {patient.state}</span>
                                                </div>
                                                {patient.occupation && (
                                                    <div className="flex items-center gap-2 text-xs text-slate-500 justify-end">
                                                        <Briefcase className="w-3.5 h-3.5" />
                                                        <span className="truncate">{patient.occupation}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        <div className="pt-4 mt-2 border-t border-slate-100 flex items-center justify-between gap-4">
                                            <div className="text-xs text-slate-400 flex flex-col">
                                                <span className="font-medium text-slate-500">Registered</span>
                                                {new Date(patient.created_at).toLocaleDateString()}
                                            </div>
                                            <Link
                                                href={`/doctor/treatment/${patient.id}`}
                                                className="flex-1"
                                            >
                                                <button className="w-full bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white font-medium py-2.5 px-4 rounded-lg transition-all flex items-center justify-center gap-2 shadow-sm hover:shadow-purple-200">
                                                    <span>Diagnose</span>
                                                    <FileText className="w-4 h-4" />
                                                </button>
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20 bg-white rounded-xl border border-slate-200 border-dashed">
                            <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <ClipboardCheck className="w-8 h-8 text-green-400" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-900">All patients diagnosed!</h3>
                            <p className="text-slate-500 mt-1">No pending patients in the queue. Check the Completed tab.</p>
                        </div>
                    )
                ) : (
                    /* ───── COMPLETED DIAGNOSES ───── */
                    filteredDiagnoses.length > 0 ? (
                        <div className="space-y-4">
                            {filteredDiagnoses.map((d) => (
                                <div key={d.record_id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden transition-all duration-300 hover:shadow-md">
                                    {/* Card Header — always visible */}
                                    <button
                                        onClick={() => toggleCard(d.patient_id)}
                                        className="w-full p-5 flex items-center gap-5 text-left hover:bg-slate-50 transition-colors"
                                    >
                                        <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 font-bold text-lg ring-2 ring-emerald-100 flex-shrink-0">
                                            {d.patient_name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 flex-wrap">
                                                <h3 className="font-bold text-slate-900 text-base">{d.patient_name}</h3>
                                                <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-semibold">
                                                    {d.diagnosis}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-3 mt-1.5 text-sm text-slate-500">
                                                <span>{d.patient_gender} • {d.patient_age} Yrs</span>
                                                {d.patient_city && (
                                                    <>
                                                        <span className="text-slate-300">|</span>
                                                        <span className="flex items-center gap-1">
                                                            <MapPin className="w-3 h-3" />
                                                            {d.patient_city}
                                                        </span>
                                                    </>
                                                )}
                                                {d.visit_date && (
                                                    <>
                                                        <span className="text-slate-300">|</span>
                                                        <span className="flex items-center gap-1">
                                                            <Calendar className="w-3 h-3" />
                                                            {new Date(d.visit_date).toLocaleDateString()}
                                                        </span>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-slate-400 flex-shrink-0">
                                            {expandedCard === d.patient_id ? (
                                                <ChevronUp className="w-5 h-5" />
                                            ) : (
                                                <ChevronDown className="w-5 h-5" />
                                            )}
                                        </div>
                                    </button>

                                    {/* Expanded Details */}
                                    {expandedCard === d.patient_id && (
                                        <div className="border-t border-slate-100 p-5 bg-gradient-to-b from-slate-50 to-white animate-in slide-in-from-top-2 duration-300">
                                            {loadingDetails === d.patient_id ? (
                                                <div className="flex items-center justify-center py-8 text-slate-400">
                                                    <Activity className="w-5 h-5 animate-spin mr-2" />
                                                    Loading diagnosis details...
                                                </div>
                                            ) : diagnosisDetails[d.patient_id]?.length > 0 ? (
                                                <div className="space-y-6">
                                                    {diagnosisDetails[d.patient_id].map((detail, idx) => (
                                                        <div key={detail.id} className="space-y-4">
                                                            {idx > 0 && <hr className="border-slate-200" />}

                                                            {/* Symptoms */}
                                                            <div>
                                                                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-1">
                                                                    <Stethoscope className="w-4 h-4 text-blue-500" />
                                                                    Symptoms
                                                                </h4>
                                                                <p className="text-sm text-slate-600 bg-white p-3 rounded-lg border border-slate-100">
                                                                    {detail.symptoms || 'No symptoms recorded'}
                                                                </p>
                                                            </div>

                                                            {/* Treatment Grid */}
                                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                                {/* Herbs */}
                                                                <div className="bg-white p-4 rounded-lg border border-slate-100">
                                                                    <h4 className="text-sm font-semibold text-emerald-700 flex items-center gap-2 mb-2">
                                                                        <Leaf className="w-4 h-4" />
                                                                        Herbs Prescribed
                                                                    </h4>
                                                                    <p className="text-sm text-slate-600 leading-relaxed">
                                                                        {detail.herbs || 'None'}
                                                                    </p>
                                                                </div>

                                                                {/* Yoga */}
                                                                <div className="bg-white p-4 rounded-lg border border-slate-100">
                                                                    <h4 className="text-sm font-semibold text-purple-700 flex items-center gap-2 mb-2">
                                                                        <Dumbbell className="w-4 h-4" />
                                                                        Yoga Therapy
                                                                    </h4>
                                                                    <p className="text-sm text-slate-600 leading-relaxed">
                                                                        {detail.yoga || 'None'}
                                                                    </p>
                                                                </div>

                                                                {/* Diet */}
                                                                <div className="bg-white p-4 rounded-lg border border-slate-100">
                                                                    <h4 className="text-sm font-semibold text-amber-700 flex items-center gap-2 mb-2">
                                                                        <Pill className="w-4 h-4" />
                                                                        Diet Plan
                                                                    </h4>
                                                                    <p className="text-sm text-slate-600 leading-relaxed">
                                                                        {detail.diet || 'None'}
                                                                    </p>
                                                                </div>
                                                            </div>

                                                            {/* Stats Row */}
                                                            <div className="flex flex-wrap gap-4 text-sm">
                                                                {detail.duration_weeks && (
                                                                    <span className="px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 font-medium">
                                                                        {detail.duration_weeks} weeks treatment
                                                                    </span>
                                                                )}
                                                                {detail.improvement && (
                                                                    <span className="px-3 py-1.5 rounded-full bg-green-50 text-green-700 font-medium">
                                                                        {detail.improvement}% expected improvement
                                                                    </span>
                                                                )}
                                                                {detail.outcome && (
                                                                    <span className="px-3 py-1.5 rounded-full bg-purple-50 text-purple-700 font-medium">
                                                                        {detail.outcome}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-center text-slate-400 py-6">No diagnosis details available.</p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-20 bg-white rounded-xl border border-slate-200 border-dashed">
                            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Search className="w-8 h-8 text-slate-300" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-900">No completed diagnoses found</h3>
                            <p className="text-slate-500">Try adjusting your search terms</p>
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
