'use client';

import { useEffect, useState } from 'react';
import { Loader2, Stethoscope, History, ChevronRight } from 'lucide-react';
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';
import { API_BASE } from '@/lib/config';
import type { PatientCondition } from '@/types';

interface FollowupChoiceDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    patientId: string;
    patientName: string;
    /** Called with the parent visit ID for a follow-up, or null for a brand-new consultation. */
    onConfirm: (parentVisitId: string | null) => void;
}

export function FollowupChoiceDialog({ open, onOpenChange, patientId, patientName, onConfirm }: FollowupChoiceDialogProps) {
    const [loading, setLoading] = useState(true);
    const [diseases, setDiseases] = useState<PatientCondition[]>([]);

    useEffect(() => {
        if (!open) return;
        setLoading(true);
        // Lightweight, role-agnostic endpoint — diagnosis name + visit id/date
        // only, no symptoms/notes/prescription/vitals. Safe for receptionists too.
        fetch(`${API_BASE}/api/patients/${patientId}/conditions`)
            .then(res => res.ok ? res.json() : [])
            .then((data: PatientCondition[]) => setDiseases(data || []))
            .catch(() => setDiseases([]))
            .finally(() => setLoading(false));
    }, [open, patientId]);

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Start Consultation — {patientName}</DialogTitle>
                    <DialogDescription>
                        Is this a new condition, or a follow-up for a condition already being treated?
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    <button
                        onClick={() => onConfirm(null)}
                        className="w-full flex items-center gap-3 p-4 rounded-xl border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 transition-colors text-left"
                    >
                        <div className="w-9 h-9 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                            <Stethoscope className="w-4 h-4" />
                        </div>
                        <div className="flex-1">
                            <div className="font-medium text-slate-800 text-sm">New Consultation</div>
                            <div className="text-xs text-slate-500">A new or unrelated condition</div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                    </button>

                    <div>
                        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <History className="w-3.5 h-3.5" /> Follow-up for a previous condition
                        </div>
                        {loading ? (
                            <div className="flex justify-center py-6"><Loader2 className="w-5 h-5 animate-spin text-slate-400" /></div>
                        ) : diseases.length === 0 ? (
                            <div className="text-sm text-slate-400 py-4 text-center border border-dashed border-slate-200 rounded-xl">
                                No previous visits recorded for this patient.
                            </div>
                        ) : (
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {diseases.map(d => (
                                    <button
                                        key={d.visit_id}
                                        onClick={() => onConfirm(d.visit_id)}
                                        className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 transition-colors text-left"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium text-slate-800 text-sm truncate">{d.diagnosis}</div>
                                            <div className="text-xs text-slate-500">
                                                Last visit: {d.visit_date ? new Date(d.visit_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Unknown'}
                                            </div>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
