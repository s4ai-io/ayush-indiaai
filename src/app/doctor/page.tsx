'use client';

import { useEffect, useState } from 'react';
import { getRegistrations } from '../actions/getRegistrations';
import { Search, User, FileText, Activity } from 'lucide-react';
import Link from 'next/link';

interface Patient {
    id: string;
    timestamp: string;
    basicInfo: {
        firstName: string;
        lastName: string;
        gender: string;
        dateOfBirth: string;
        abhaId: string;
    };
    contactInfo: {
        mobileNumber: string;
        correspondenceCity: string;
    };
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
            patient.basicInfo.firstName.toLowerCase().includes(lowerQuery) ||
            patient.basicInfo.lastName.toLowerCase().includes(lowerQuery) ||
            patient.basicInfo.abhaId.includes(lowerQuery) ||
            patient.contactInfo.mobileNumber.includes(lowerQuery)
        );
    });

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Doctor Dashboard</h1>
                        <p className="text-slate-600">Patient Queue & Clinical Entry</p>
                    </div>
                    <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-200 w-full md:w-auto">
                        <Search className="w-5 h-5 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search by Name, ABHA, or Mobile..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-transparent border-none outline-none text-slate-900 placeholder-slate-400 w-full md:w-64"
                        />
                    </div>
                </header>

                {/* Patient List */}
                {loading ? (
                    <div className="text-center py-20 text-slate-500">Loading patient records...</div>
                ) : filteredPatients.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredPatients.map((patient) => (
                            <div key={patient.id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
                                <div className="p-6 space-y-4">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold text-lg">
                                                {patient.basicInfo?.firstName?.[0] || '?'}{patient.basicInfo?.lastName?.[0] || '?'}
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-slate-900">{patient.basicInfo?.firstName} {patient.basicInfo?.lastName}</h3>
                                                <p className="text-sm text-slate-500">
                                                    {patient.basicInfo?.gender || 'Unknown'} •
                                                    {patient.basicInfo?.dateOfBirth ? `${new Date().getFullYear() - new Date(patient.basicInfo.dateOfBirth).getFullYear()} Years` : 'Age N/A'}
                                                </p>
                                            </div>
                                        </div>
                                        <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-1 rounded">
                                            {patient.basicInfo?.abhaId || 'No ABHA'}
                                        </span>
                                    </div>

                                    <div className="space-y-2 text-sm text-slate-600">
                                        <div className="flex items-center gap-2">
                                            <User className="w-4 h-4 text-slate-400" />
                                            <span>{patient.contactInfo?.mobileNumber || 'N/A'}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Activity className="w-4 h-4 text-slate-400" />
                                            <span>Last Visit: {new Date(patient.timestamp).toLocaleDateString()}</span>
                                        </div>
                                    </div>

                                    <div className="pt-4 border-t border-slate-100">
                                        <Link
                                            href={`/doctor/diagnosis/${patient.id}`}
                                            className="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                                        >
                                            <FileText className="w-4 h-4" />
                                            Start Diagnosis
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20 bg-white rounded-xl border border-slate-200 border-dashed">
                        <p className="text-slate-500">No patients found matching your search.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
