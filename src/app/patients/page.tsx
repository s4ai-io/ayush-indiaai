'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
    Search, UserPlus, Stethoscope, ChevronRight,
    Calendar, Phone, Activity, FileText, X, Loader2
} from 'lucide-react';
import { Button } from "@/components/ui/button";

interface PatientDirectoryItem {
    id: string;
    first_name: string;
    last_name: string;
    mobile: string;
    gender: string;
    age: number;
    city: string;
    visited: boolean;
}

export default function PatientsDirectoryPage() {
    const [patients, setPatients] = useState<PatientDirectoryItem[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);

    const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
    const [patientHistory, setPatientHistory] = useState<any[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);

    useEffect(() => {
        const fetchPatients = async () => {
            setLoading(true);
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await fetch(`${API_URL}/api/patients`);
                if (!response.ok) throw new Error("Failed connecting to patient API.");
                const data = await response.json();

                // Format the API response (which uses snake_case and various properties) to match our UI types
                const formatted = data.map((p: any) => ({
                    id: p.id,
                    first_name: p.first_name || p.firstName || "Unknown",
                    last_name: p.last_name || p.lastName || "",
                    mobile: p.mobile || "Unknown",
                    gender: p.gender || "Unknown",
                    age: parseInt(p.age) || 0,
                    city: p.city || "Unknown",
                    visited: p.diagnosis_done === true || p.diagnosis_done === "True"
                }));

                setPatients(formatted);
            } catch (err) {
                console.error("Error fetching patient directory:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchPatients();
    }, []);

    const fetchPatientHistory = async (patientId: string) => {
        setSelectedPatientId(patientId);
        setHistoryLoading(true);
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/patients/${patientId}/history`);
            if (!response.ok) throw new Error("Failed resolving patient history.");

            const data = await response.json();

            // Format incoming diagnoses from csv_service into UI chronological history blocks
            if (data.history && Array.isArray(data.history)) {
                const chronological = data.history.map((record: any) => {
                    let treatmentText = "No treatment prescribed yet";
                    if (record.prescription && record.prescription.doctor_notes) {
                        treatmentText = record.prescription.doctor_notes;
                    } else if (record.herbs) {
                        treatmentText = `Herbs: ${record.herbs}`;
                    }

                    return {
                        visit_id: record.id,
                        date: record.visit_date ? record.visit_date.split('T')[0] : "Unknown",
                        symptoms: record.symptoms || "No symptoms recorded",
                        diagnosis: record.diagnosis || "Pending Evaluation",
                        treatment: treatmentText,
                        doctor: "General Physician"
                    };
                });
                setPatientHistory(chronological);
            } else {
                setPatientHistory([]);
            }

        } catch (err) {
            console.error("Error fetching patient history", err);
            setPatientHistory([]);
        } finally {
            setHistoryLoading(false);
        }
    };

    const q = searchQuery.toLowerCase();
    const filteredPatients = patients.filter(p =>
        p.first_name.toLowerCase().includes(q) ||
        p.last_name.toLowerCase().includes(q) ||
        p.mobile.includes(q) ||
        p.city.toLowerCase().includes(q)
    );

    return (
        <div className="min-h-screen bg-slate-50 p-4 md:p-8">
            <div className="max-w-7xl mx-auto space-y-6">

                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800">Patient Directory</h1>
                        <p className="text-slate-500 text-sm">Manage all registered patients and view complete visit history.</p>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
                        <div className="relative w-full sm:w-64">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                placeholder="Search Name, Phone, City..."
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                        </div>
                        <Link href="/consultation" className="w-full sm:w-auto">
                            <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
                                <UserPlus className="w-4 h-4 mr-2" /> Register New Patient
                            </Button>
                        </Link>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 align-top items-start">

                    {/* Left Col: Patient List */}
                    <div className="lg:col-span-1 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[600px]">
                        <div className="p-4 border-b border-slate-100 bg-slate-50/50">
                            <h2 className="font-semibold text-slate-700">All Patients ({filteredPatients.length})</h2>
                        </div>

                        <div className="overflow-y-auto flex-1 p-2 space-y-2">
                            {loading ? (
                                <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-indigo-400" /></div>
                            ) : filteredPatients.length === 0 ? (
                                <div className="text-center py-8 text-slate-400 text-sm">No patients found.</div>
                            ) : (
                                filteredPatients.map((patient) => (
                                    <button
                                        key={patient.id}
                                        onClick={() => fetchPatientHistory(patient.id)}
                                        className={`w-full text-left p-4 rounded-xl transition-all border ${selectedPatientId === patient.id ? 'bg-indigo-50 border-indigo-200 shadow-sm' : 'bg-white border-transparent hover:border-slate-200 hover:bg-slate-50'}`}
                                    >
                                        <div className="flex justify-between items-start mb-1">
                                            <span className="font-medium text-slate-800">{patient.first_name} {patient.last_name}</span>
                                            {patient.visited && (
                                                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">Visited</span>
                                            )}
                                        </div>
                                        <div className="flex items-center text-xs text-slate-500 space-x-3">
                                            <span className="flex items-center"><Phone className="w-3 h-3 mr-1" />{patient.mobile}</span>
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Right Col: Patient Details & History */}
                    <div className="lg:col-span-2">
                        {!selectedPatientId ? (
                            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 h-[600px] flex flex-col items-center justify-center text-slate-400">
                                <FileText className="w-12 h-12 mb-4 text-slate-200" />
                                <p>Select a patient from the directory to view their complete history.</p>
                            </div>
                        ) : (
                            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 h-[600px] flex flex-col overflow-hidden">
                                {(() => {
                                    const patientDetail = patients.find(p => p.id === selectedPatientId);
                                    if (!patientDetail) return null;

                                    return (
                                        <>
                                            {/* Top Banner Context */}
                                            <div className="p-6 border-b border-indigo-50 bg-gradient-to-r from-indigo-50/50 to-white">
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <h2 className="text-2xl font-bold text-indigo-900 mb-1">{patientDetail.first_name} {patientDetail.last_name}</h2>
                                                        <div className="flex gap-4 text-sm text-slate-600">
                                                            <span>{patientDetail.gender}, {patientDetail.age} yrs</span>
                                                            <span className="flex items-center"><Phone className="w-4 h-4 mr-1 text-slate-400" /> {patientDetail.mobile}</span>
                                                        </div>
                                                    </div>

                                                    {/* Directly jump to start a consultation for THIS patient */}
                                                    <Link href={`/consultation?patientId=${patientDetail.id}`}>
                                                        <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
                                                            <Stethoscope className="w-4 h-4 mr-2" /> Start Consultation
                                                        </Button>
                                                    </Link>
                                                </div>
                                            </div>

                                            {/* History Stream */}
                                            <div className="flex-1 overflow-y-auto p-6 bg-slate-50/30">
                                                <h3 className="font-semibold text-slate-800 mb-4 flex items-center">
                                                    <Activity className="w-4 h-4 mr-2 text-indigo-500" /> Visit History
                                                </h3>

                                                {historyLoading ? (
                                                    <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-indigo-400" /></div>
                                                ) : patientHistory.length === 0 ? (
                                                    <div className="text-center py-12 bg-white rounded-xl border border-dashed border-slate-200 text-slate-500">
                                                        No previous visits recorded for this patient.
                                                    </div>
                                                ) : (
                                                    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
                                                        {patientHistory.map((visit, idx) => (
                                                            <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                                                <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-indigo-100 text-indigo-600 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                                                                    <Calendar className="w-4 h-4" />
                                                                </div>
                                                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                                                                    <div className="flex justify-between items-start mb-2">
                                                                        <span className="font-semibold text-slate-800 text-sm">{visit.date}</span>
                                                                        <span className="text-xs text-slate-500">{visit.visit_id}</span>
                                                                    </div>
                                                                    <div className="space-y-1 mb-3">
                                                                        <div className="text-sm"><span className="text-slate-500 font-medium mr-1">Symptoms:</span><span className="text-slate-700">{visit.symptoms}</span></div>
                                                                        <div className="text-sm"><span className="text-slate-500 font-medium mr-1">Diagnosis:</span><span className="text-emerald-700 font-medium">{visit.diagnosis}</span></div>
                                                                        {visit.treatment !== "No treatment prescribed yet" && (
                                                                            <div className="text-sm mt-2 p-2 bg-slate-50 rounded-md border border-slate-100"><span className="text-slate-500 font-medium block mb-1">Treatment Plan:</span><span className="text-slate-700 whitespace-pre-wrap">{visit.treatment}</span></div>
                                                                        )}
                                                                    </div>
                                                                    <div className="pt-3 border-t border-slate-100 flex justify-between items-center">
                                                                        <span className="text-xs text-slate-400">Consulted by {visit.doctor}</span>
                                                                        <Button variant="ghost" size="sm" className="h-8 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50">
                                                                            View full details <ChevronRight className="w-3 h-3 ml-1" />
                                                                        </Button>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </>
                                    );
                                })()}
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </div>
    );
}
