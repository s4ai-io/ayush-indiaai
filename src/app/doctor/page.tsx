'use client';

import { useEffect, useState } from 'react';
import { getRegistrations } from '../actions/getRegistrations';
import { Search, User, FileText, Activity, MapPin, Briefcase } from 'lucide-react';
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
}

export default function DoctorDashboard() {
    const [patients, setPatients] = useState<Patient[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPatients = async () => {
            const data = await getRegistrations();
            setPatients(data);
            setLoading(false);
        };
        fetchPatients();
    }, []);

    const filteredPatients = patients.filter(patient => {
        const lowerQuery = searchQuery.toLowerCase();
        return (
            (patient.first_name?.toLowerCase() || '').includes(lowerQuery) ||
            (patient.last_name?.toLowerCase() || '').includes(lowerQuery) ||
            (patient.mobile?.includes(lowerQuery)) ||
            (patient.id_number?.toLowerCase() || '').includes(lowerQuery)
        );
    });

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
                            placeholder="Search by name, mobile, or ID..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-transparent border-none outline-none text-slate-900 placeholder-slate-400 w-full md:w-64"
                        />
                    </div>
                </header>

                {/* Patient List */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-20 text-slate-500 space-y-4">
                        <Activity className="w-8 h-8 animate-pulse text-purple-400" />
                        <p>Loading patient queue...</p>
                    </div>
                ) : filteredPatients.length > 0 ? (
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
                        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Search className="w-8 h-8 text-slate-300" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900">No patients found</h3>
                        <p className="text-slate-500">Try adjusting your search terms</p>
                    </div>
                )}
            </div>
        </div>
    );
}
