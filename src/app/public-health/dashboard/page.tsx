'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer, RadarChart, Radar,
    PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import {
    AlertTriangle, Activity, MapPin, TrendingUp, TrendingDown,
    Brain, RefreshCw, ShieldAlert,
    Users, Stethoscope, BarChart2, Globe
} from 'lucide-react';
import { API_BASE } from '@/lib/config';

// ─── Types ───────────────────────────────────────────────────────────────────

interface TrendData { date: string;[disease: string]: number | string; }
interface HotspotData { city: string; pincode: string; diagnosis: string; count: number; devanagari?: string; iast?: string; hindi?: string; }
interface AlertData {
    disease: string; severity: string; message: string; date?: string;
    z_score?: number; cusum_value?: number; surge_month?: string;
    recent_cases?: number; pct_increase?: number; baseline_avg?: number;
    triggered_by?: string;
    devanagari?: string; iast?: string; hindi?: string;
    week?: string; recent_weeks?: number; baseline_std?: number; detection_type?: string;
    window_start?: string; window_end?: string;
}
interface DashboardSummary {
    total_patients: number;
    total_medical_records: number;
    top_diseases: { disease: string; count: number }[];
    top_cities: { city: string; count: number }[];
}
interface SpreadPrediction {
    city: string; predicted_cases: number; risk_level: string;
    day_offset: number; lat?: number; lon?: number;
}
interface ForecastData {
    disease: string;
    forecast_data: { month: string; month_name?: string; disease?: string; predicted_cases: number; season: string; ritu_sandhi?: boolean }[];
    by_disease?: Record<string, { month_name: string; predicted_cases: number; season: string; ritu_sandhi?: boolean }[]>;
    trend: string; risk_level: string;
}
interface EmergingTrend {
    disease: string; growth_rate: number; current_cases: number;
    alert_level: string; trend: string;
    window_start?: string; window_end?: string;
}
interface ClusterData {
    cluster_id: number; disease: string; is_noise: boolean;
    cities: string[]; city_cases: Record<string, number>; total_cases: number;
    centroid_lat: number; centroid_lon: number; spread_km: number; period_days: number;
    devanagari?: string; iast?: string;
}
type NameMap = Record<string, { devanagari: string; iast: string; hindi: string; english: string }>;

// ─── Case-details drill-down ─────────────────────────────────────────────────

interface CaseDetail {
    patient_id: string; name: string; age: number; gender: string;
    city: string; state: string; visit_date: string; severity: string;
    symptoms: string; prakriti: string; vikriti: string; comorbidities: string;
}
interface CaseQuery {
    title: string; disease: string; cities?: string;
    startDate?: string; endDate?: string; days?: number;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const DISEASE_COLORS = [
    '#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#6366f1',
    '#ec4899', '#14b8a6', '#f97316', '#8b5cf6', '#84cc16'
];

/**
 * Extracts the Ayurvedic (Sanskrit) name from strings like:
 *   "Dengue (Dandashthaka Jwara)"  →  "Dandashthaka Jwara"
 *   "Fever (Jwara)"                →  "Jwara"
 *   "Cough"                        →  "Cough"  (no parentheses, fallback)
 */
function ayurvedicName(raw: string, maxLen?: number): string {
    const match = raw?.match(/\(([^)]+)\)/);
    const name = match ? match[1] : raw ?? '';
    return maxLen ? name.substring(0, maxLen) : name;
}

const SEVERITY_STYLES: Record<string, string> = {
    Critical: 'bg-red-600 text-white',
    High: 'bg-orange-500 text-white',
    Medium: 'bg-yellow-400 text-slate-900',
    Low: 'bg-green-500 text-white',
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-400 text-slate-900',
    low: 'bg-green-500 text-white',
};

const RITU_EMOJI: Record<string, string> = {
    Shishira: '❄️', Vasanta: '🌸', Grishma: '☀️',
    Varsha: '🌧️', Sharad: '🍂', Hemanta: '🌾',
};

function StatCard({
    icon, label, value, sub, color
}: { icon: React.ReactNode; label: string; value: string | number; sub?: string; color: string }) {
    return (
        <div className={`rounded-2xl p-5 text-white shadow-lg ${color} flex items-start gap-4`}>
            <div className="p-2 rounded-xl bg-white/20 flex-shrink-0">{icon}</div>
            <div>
                <p className="text-sm font-medium text-white/80">{label}</p>
                <p className="text-3xl font-bold mt-0.5">{value}</p>
                {sub && <p className="text-xs text-white/70 mt-0.5">{sub}</p>}
            </div>
        </div>
    );
}

function SectionHeader({ icon, title, subtitle, info }: {
    icon: React.ReactNode; title: string; subtitle?: string;
    info?: string;
}) {
    const [show, setShow] = React.useState(false);
    return (
        <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-slate-100 text-slate-600">{icon}</div>
            <div className="flex-1">
                <div className="flex items-center gap-1.5">
                    <h2 className="text-lg font-bold text-slate-800">{title}</h2>
                    {info && (
                        <div className="relative inline-flex" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
                            <button className="text-slate-400 hover:text-slate-600 transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
                                </svg>
                            </button>
                            {show && (
                                <div className="absolute left-5 top-0 z-50 w-64 bg-slate-900 text-white text-xs rounded-xl p-3 shadow-xl leading-relaxed">
                                    {info}
                                </div>
                            )}
                        </div>
                    )}
                </div>
                {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
            </div>
        </div>
    );
}

/** Small text-link trigger placed inside alert/threat/hotspot/cluster cards. */
function ViewCasesButton({ onClick, className = '' }: { onClick: () => void; className?: string }) {
    return (
        <button
            onClick={onClick}
            className={`text-[11px] font-semibold text-slate-500 hover:text-amber-600 transition-colors inline-flex items-center gap-1 ${className}`}
        >
            🔍 View Cases
        </button>
    );
}

/**
 * Case-level drill-down modal — fetches /api/analytics/case-details for
 * whichever signal (alert / emerging threat / hotspot / cluster) triggered it.
 * Rendered once at the page level; opened by setting `query`, closed via onClose.
 */
function CaseDetailsModal({ query, onClose }: { query: CaseQuery | null; onClose: () => void }) {
    const [cases, setCases] = useState<CaseDetail[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [nameInfo, setNameInfo] = useState<{ devanagari?: string; iast?: string }>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!query) return;
        setLoading(true);
        setError(null);
        const params = new URLSearchParams({ disease: query.disease });
        if (query.cities) params.set('cities', query.cities);
        if (query.startDate) params.set('start_date', query.startDate);
        if (query.endDate) params.set('end_date', query.endDate);
        if (query.days !== undefined) params.set('days', String(query.days));

        fetch(`${API_BASE}/api/analytics/case-details?${params.toString()}`)
            .then(r => r.json())
            .then(data => {
                setCases(Array.isArray(data.cases) ? data.cases : []);
                setTotalCount(data.total_count ?? 0);
                setNameInfo({ devanagari: data.devanagari, iast: data.iast });
            })
            .catch(() => setError('Failed to load case details.'))
            .finally(() => setLoading(false));
    }, [query]);

    if (!query) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/50" onClick={onClose}>
            <div
                className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col"
                onClick={e => e.stopPropagation()}
            >
                <div className="p-5 border-b border-slate-100 flex items-start justify-between gap-4">
                    <div>
                        <p className="text-xs text-slate-400">{query.title}</p>
                        <h3 className="text-lg font-bold text-slate-800" style={{ fontFamily: 'serif' }}>
                            {nameInfo.devanagari || query.disease}
                        </h3>
                        <p className="text-xs text-slate-400 italic">{nameInfo.iast}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-700 text-xl leading-none px-2"
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto p-5">
                    {loading ? (
                        <p className="text-slate-400 text-sm text-center py-8">Loading cases...</p>
                    ) : error ? (
                        <p className="text-red-500 text-sm text-center py-8">{error}</p>
                    ) : cases.length === 0 ? (
                        <p className="text-slate-400 text-sm text-center py-8">No case records found for this signal.</p>
                    ) : (
                        <table className="w-full text-xs">
                            <thead>
                                <tr className="border-b border-slate-100 text-left text-slate-500">
                                    <th className="py-2 pr-3 font-medium">Patient</th>
                                    <th className="py-2 pr-3 font-medium">Age/Gender</th>
                                    <th className="py-2 pr-3 font-medium">City</th>
                                    <th className="py-2 pr-3 font-medium">Visit Date</th>
                                    <th className="py-2 pr-3 font-medium">Severity</th>
                                    <th className="py-2 font-medium">Symptoms</th>
                                </tr>
                            </thead>
                            <tbody>
                                {cases.map((c, i) => (
                                    <tr key={c.patient_id + i} className="border-b border-slate-50 hover:bg-slate-50">
                                        <td className="py-2 pr-3 font-semibold text-slate-700 whitespace-nowrap">{c.name}</td>
                                        <td className="py-2 pr-3 text-slate-500 whitespace-nowrap">{c.age}/{c.gender?.[0]}</td>
                                        <td className="py-2 pr-3 text-slate-500 capitalize whitespace-nowrap">{c.city}</td>
                                        <td className="py-2 pr-3 text-slate-500 whitespace-nowrap">
                                            {c.visit_date ? new Date(c.visit_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                                        </td>
                                        <td className="py-2 pr-3">
                                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${SEVERITY_STYLES[c.severity] ?? 'bg-slate-100 text-slate-600'}`}>
                                                {c.severity}
                                            </span>
                                        </td>
                                        <td className="py-2 text-slate-500 max-w-xs">{c.symptoms}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
                {!loading && cases.length > 0 && (
                    <div className="px-5 py-3 border-t border-slate-100 text-xs text-slate-400">
                        Showing {cases.length} of {totalCount} case{totalCount !== 1 ? 's' : ''}
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PublicHealthDashboard() {
    const [summary, setSummary] = useState<DashboardSummary | null>(null);
    const [trends, setTrends] = useState<TrendData[]>([]);
    const [alerts, setAlerts] = useState<AlertData[]>([]);
    const [hotspots, setHotspots] = useState<HotspotData[]>([]);
    const [spread, setSpread] = useState<SpreadPrediction[]>([]);
    const [forecast, setForecast] = useState<ForecastData | null>(null);
    const [emerging, setEmerging] = useState<EmergingTrend[]>([]);
    const [nameMap, setNameMap] = useState<NameMap>({});
    const [weeklyAlerts, setWeeklyAlerts] = useState<AlertData[]>([]);
    const [clusters, setClusters] = useState<ClusterData[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const [mounted, setMounted] = useState(false);
    const [selectedDisease, setSelectedDisease] = useState('');
    const [alertTab, setAlertTab] = useState<'monthly' | 'weekly'>('monthly');
    const [caseQuery, setCaseQuery] = useState<CaseQuery | null>(null);

    /** Resolves the best Devanagari label for a disease string.
     *  Priority: inline field  >  nameMap  >  ayurvedicName() fallback. */
    const dName = useCallback((raw: string, inlineDevanagari?: string): string => {
        if (inlineDevanagari) return inlineDevanagari;
        if (nameMap[raw]?.devanagari) return nameMap[raw].devanagari;
        return ayurvedicName(raw);
    }, [nameMap]);

    const dNameIast = useCallback((raw: string, inlineIast?: string): string => {
        if (inlineIast) return inlineIast;
        return nameMap[raw]?.iast ?? '';
    }, [nameMap]);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const [summaryR, trendsR, alertsR, hotspotR, spreadR, forecastR, emergingR, nameMapR, weeklyR, clustersR] =
                await Promise.allSettled([
                    fetch(`${API_BASE}/api/analytics/dashboard`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/trends?days=90`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/alerts`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/hotspots`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/predictions`).then(r => r.json()),
                    fetch(`${API_BASE}/api/forecast?months=3`).then(r => r.json()),
                    fetch(`${API_BASE}/api/forecast/emerging`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/disease-names`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/weekly-alerts`).then(r => r.json()),
                    fetch(`${API_BASE}/api/analytics/clusters?days=90`).then(r => r.json()),
                ]);

            if (summaryR.status === 'fulfilled') setSummary(summaryR.value);
            if (trendsR.status === 'fulfilled') setTrends(Array.isArray(trendsR.value) ? trendsR.value : []);
            if (alertsR.status === 'fulfilled') setAlerts(Array.isArray(alertsR.value) ? alertsR.value : []);
            if (hotspotR.status === 'fulfilled') setHotspots(Array.isArray(hotspotR.value) ? hotspotR.value : []);
            if (spreadR.status === 'fulfilled') {
                const raw = spreadR.value;
                setSpread(Array.isArray(raw) ? raw : (raw?.predictions ?? []));
            }
            if (forecastR.status === 'fulfilled') setForecast(forecastR.value);
            if (emergingR.status === 'fulfilled') {
                const raw = emergingR.value;
                setEmerging(raw?.trends ?? (Array.isArray(raw) ? raw : []));
            }
            if (nameMapR.status === 'fulfilled' && typeof nameMapR.value === 'object') {
                setNameMap(nameMapR.value as NameMap);
            }
            if (weeklyR.status === 'fulfilled') setWeeklyAlerts(Array.isArray(weeklyR.value) ? weeklyR.value : []);
            if (clustersR.status === 'fulfilled') setClusters(clustersR.value?.clusters ?? []);

            setLastRefresh(new Date());
        } catch (err) {
            console.error('Failed to load dashboard data:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { setMounted(true); loadData(); }, [loadData]);

    // ── Client-side by_disease grouping from forecast_data ─────────────────────
    // Groups flat forecast_data into { diseaseName: [{month_name, predicted_cases, season}] }
    // Works even if the backend's by_disease field is missing.
    const forecastByDisease = React.useMemo(() => {
        if (!forecast?.forecast_data?.length) return {};

        // If backend already sent by_disease with entries, use it
        const backendBD = forecast.by_disease;
        if (backendBD && Object.keys(backendBD).length > 0) return backendBD;

        // ── Build from forecast_data client-side ──────────────────────────────
        // Forecast entries are ordered: [D1M1, D1M2, D1M3, D2M1, D2M2, D2M3 ...]
        // Detect disease group boundaries when month number resets to 1.
        const now = new Date();
        const monthLabel = (offset: number) => {
            const d = new Date(now.getFullYear(), now.getMonth() + offset, 1);
            return d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
        };

        // Build an extended disease name list: summary top_diseases (all of them)
        const topDiseases = summary?.top_diseases ?? [];

        type MonthEntry = { month_name: string; predicted_cases: number; season: string; ritu_sandhi: boolean };
        const grouped: Record<string, MonthEntry[]> = {};
        let diseaseIndex = 0;
        let groupKey = '';

        for (const entry of forecast.forecast_data) {
            const monthOffset = parseInt((entry.month ?? 'Month 1').replace('Month ', ''), 10);

            // New disease starts when month resets to 1 (or on first entry)
            if (monthOffset === 1 || groupKey === '') {
                if (monthOffset === 1 && groupKey !== '') diseaseIndex++;
                // Try: (1) entry's own disease field, (2) top_diseases[index], (3) numbered fallback
                const entryDisease = (entry as any).disease as string | undefined;
                groupKey = entryDisease
                    || topDiseases[diseaseIndex]?.disease
                    || `Disease ${diseaseIndex + 1}`;
                if (!grouped[groupKey]) grouped[groupKey] = [];
            }

            grouped[groupKey].push({
                month_name: (entry as any).month_name ?? monthLabel(monthOffset),
                predicted_cases: entry.predicted_cases,
                season: entry.season ?? '',
                ritu_sandhi: (entry as any).ritu_sandhi ?? false,
            });
        }
        return grouped;
    }, [forecast, summary]);

    // Extract the top 6 diseases across the entire trend period for the chart
    const diseases = useMemo(() => {
        if (!trends.length) return [];
        const counts: Record<string, number> = {};
        trends.forEach(day => {
            Object.keys(day).forEach(k => {
                if (k !== 'date') {
                    counts[k] = (counts[k] || 0) + (day[k] as number);
                }
            });
        });
        return Object.entries(counts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 6)
            .map(entry => entry[0]);
    }, [trends]);

    const topHotspots = hotspots
        .filter(h => !selectedDisease || h.diagnosis?.toLowerCase().includes(selectedDisease.toLowerCase()))
        .slice(0, 8);

    const uniqueDiseaseList = [...new Set(hotspots.map(h => h.diagnosis))].sort();

    // Radar data from top diseases — use Devanagari labels from nameMap
    const radarData = summary?.top_diseases.slice(0, 6).map(d => ({
        disease: dName(d.disease, nameMap[d.disease]?.devanagari).substring(0, 24),
        count: d.count,
    })) ?? [];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 space-y-6">

            {/* ── Header ─────────────────────────────────────────────────────── */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
                        <ShieldAlert className="h-8 w-8 text-amber-500" />
                        Public Health Intelligence
                    </h1>
                    <p className="text-slate-500 text-sm mt-1">
                        Real-time Ayurvedic epidemiological monitoring · Anomaly Detection · Forecasting
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                        <RefreshCw className="h-3 w-3" />
                        <span suppressHydrationWarning className="text-xs text-slate-400">
                            {mounted && lastRefresh ? lastRefresh.toLocaleTimeString() : '—'}
                        </span>
                    </span>
                    <button
                        onClick={loadData}
                        disabled={loading}
                        className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-xl font-medium text-sm hover:bg-amber-600 disabled:opacity-50 transition-colors shadow-sm"
                    >
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        {loading ? 'Loading...' : 'Refresh'}
                    </button>
                </div>
            </div>

            {/* ── KPI Summary Strip ───────────────────────────────────────────── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={<Users className="h-5 w-5" />}
                    label="Total Patients"
                    value={summary?.total_patients?.toLocaleString() ?? '—'}
                    sub="in surveillance"
                    color="bg-gradient-to-br from-blue-500 to-blue-700"
                />
                <StatCard
                    icon={<Stethoscope className="h-5 w-5" />}
                    label="Clinical Records"
                    value={summary?.total_medical_records?.toLocaleString() ?? '—'}
                    sub="all-time"
                    color="bg-gradient-to-br from-purple-500 to-purple-700"
                />
                <StatCard
                    icon={<AlertTriangle className="h-5 w-5" />}
                    label="Active Alerts"
                    value={alerts.length}
                    sub={alerts.length > 0 ? 'surge detected' : 'all clear'}
                    color={alerts.length > 0
                        ? 'bg-gradient-to-br from-red-500 to-red-700'
                        : 'bg-gradient-to-br from-emerald-500 to-emerald-700'}
                />
                <StatCard
                    icon={<Globe className="h-5 w-5" />}
                    label="Cities Monitored"
                    value={[...new Set(hotspots.map(h => h.city))].length || '—'}
                    sub="geospatial graph"
                    color="bg-gradient-to-br from-amber-500 to-orange-600"
                />
            </div>

            {/* ── Active Alerts Banner ────────────────────────────────────────── */}
            {(alerts.length > 0 || weeklyAlerts.length > 0) && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-4">
                    <div className="flex items-start gap-3">
                        <div className="p-2 rounded-xl bg-red-100 text-red-600 flex-shrink-0">
                            <AlertTriangle className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                            {/* Header + Tabs */}
                            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                                <h3 className="font-bold text-red-800">
                                    🚨 {alerts.length + weeklyAlerts.length} Active Surge Signal{alerts.length + weeklyAlerts.length > 1 ? 's' : ''}
                                </h3>
                                <div className="flex rounded-lg overflow-hidden border border-red-200 text-xs">
                                    <button
                                        onClick={() => setAlertTab('monthly')}
                                        className={`px-3 py-1 font-semibold transition-colors ${alertTab === 'monthly' ? 'bg-red-600 text-white' : 'bg-white text-red-600 hover:bg-red-50'}`}
                                    >
                                        📅 Monthly ({alerts.length})
                                    </button>
                                    <button
                                        onClick={() => setAlertTab('weekly')}
                                        className={`px-3 py-1 font-semibold transition-colors ${alertTab === 'weekly' ? 'bg-amber-500 text-white' : 'bg-white text-amber-600 hover:bg-amber-50'}`}
                                    >
                                        ⚡ Weekly Early ({weeklyAlerts.length})
                                    </button>
                                </div>
                            </div>

                            {alertTab === 'monthly' && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {alerts.map((a, i) => (
                                        <div key={i} className="bg-white rounded-xl p-3 border border-red-100">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`px-2 py-0.5 rounded-full text-xs font-bold flex-shrink-0 ${SEVERITY_STYLES[a.severity] ?? 'bg-slate-200 text-slate-700'}`}>
                                                    {a.severity}
                                                </span>
                                            </div>
                                            <p className="text-base font-bold text-slate-900" style={{ fontFamily: 'serif' }}>
                                                {dName(a.disease, a.devanagari)}
                                            </p>
                                            {a.iast && <p className="text-[10px] text-slate-400 italic mb-1">{a.iast}</p>}
                                            <div className="flex items-center gap-3 flex-wrap">
                                                {a.surge_month && (
                                                    <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-lg">📅 {a.surge_month}</span>
                                                )}
                                                {a.z_score !== undefined && (
                                                    <span className="relative group cursor-help">
                                                        <span className="text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded-lg flex items-center gap-1">
                                                            Z = {a.z_score.toFixed(1)}
                                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
                                                            </svg>
                                                        </span>
                                                        <div className="absolute bottom-full left-0 mb-2 z-50 hidden group-hover:block w-72 bg-slate-900 text-white text-xs rounded-xl p-3 shadow-2xl leading-relaxed pointer-events-none">
                                                            <p className="font-bold text-amber-400 mb-1">📊 Z-Score (Anomaly Strength)</p>
                                                            <p className="mb-2">Measures how many <strong>standard deviations</strong> the current month's cases are above the historical average.</p>
                                                            <p className="font-mono bg-slate-800 rounded p-1 mb-2 text-green-300">Z = (Current − Baseline μ) / σ</p>
                                                            {a.recent_cases !== undefined && a.baseline_avg !== undefined && (
                                                                <p className="mb-2 text-slate-300">
                                                                    Current: <strong>{a.recent_cases} cases</strong> · Baseline avg: <strong>{a.baseline_avg.toFixed(1)}</strong>
                                                                </p>
                                                            )}
                                                            <div className="border-t border-slate-700 pt-2 mt-1 space-y-0.5">
                                                                <p><span className="text-yellow-400">Z &gt; 2</span> — Unusual (elevated)</p>
                                                                <p><span className="text-orange-400">Z &gt; 3</span> — Significant surge</p>
                                                                <p><span className="text-red-400">Z &gt; 5</span> — Extreme outbreak signal</p>
                                                                <p className="text-slate-400 mt-1">This alert: <strong className="text-white">Z = {a.z_score.toFixed(2)}</strong> — {a.z_score >= 5 ? 'Extreme 🔴' : a.z_score >= 3 ? 'Significant 🟠' : 'Elevated 🟡'}</p>
                                                            </div>
                                                        </div>
                                                    </span>
                                                )}
                                                {a.pct_increase !== undefined && (
                                                    <span className="text-xs font-bold text-orange-600">{a.pct_increase > 0 ? '+' : ''}{a.pct_increase}% cases</span>
                                                )}
                                                {a.triggered_by && (
                                                    <span className="text-[10px] text-slate-400">{a.triggered_by}</span>
                                                )}
                                            </div>
                                            <ViewCasesButton
                                                className="mt-2"
                                                onClick={() => setCaseQuery({
                                                    title: `Monthly surge · ${a.surge_month ?? ''}`,
                                                    disease: a.disease,
                                                    startDate: a.window_start,
                                                    endDate: a.window_end,
                                                })}
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}

                            {alertTab === 'weekly' && (
                                <>
                                    <p className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-1.5 mb-3 border border-amber-200">
                                        ⚡ <strong>Early warning</strong> — bi-weekly rolling Z-score detects surges <strong>3–6 weeks earlier</strong> than the monthly detector.
                                        Uses last 6-week window vs 20-week baseline. Threshold: Z ≥ 1.6.
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        {weeklyAlerts.map((a, i) => (
                                            <div key={i} className="bg-white rounded-xl p-3 border border-amber-100">
                                                <div className="flex items-center gap-2 mb-1 flex-wrap">
                                                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold flex-shrink-0 ${SEVERITY_STYLES[a.severity] ?? 'bg-slate-200 text-slate-700'}`}>
                                                        {a.severity}
                                                    </span>
                                                    <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">EARLY SIGNAL</span>
                                                </div>
                                                <p className="text-base font-bold text-slate-900" style={{ fontFamily: 'serif' }}>
                                                    {dName(a.disease, a.devanagari)}
                                                </p>
                                                {a.iast && <p className="text-[10px] text-slate-400 italic mb-1">{a.iast}</p>}
                                                <div className="flex items-center gap-3 flex-wrap">
                                                    {a.week && (
                                                        <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-lg">🗓 {a.week}</span>
                                                    )}
                                                    {a.z_score !== undefined && (
                                                        <span className="relative group cursor-help">
                                                            <span className="text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-lg flex items-center gap-1">
                                                                Z = {a.z_score.toFixed(1)}
                                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                                    <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
                                                                </svg>
                                                            </span>
                                                            <div className="absolute bottom-full left-0 mb-2 z-50 hidden group-hover:block w-72 bg-slate-900 text-white text-xs rounded-xl p-3 shadow-2xl leading-relaxed pointer-events-none">
                                                                <p className="font-bold text-amber-400 mb-1">⚡ Weekly Z-Score</p>
                                                                <p className="mb-2">Bi-weekly rolling Z-score using the last <strong>6 weeks</strong> vs a <strong>20-week baseline</strong>.</p>
                                                                <p className="font-mono bg-slate-800 rounded p-1 mb-2 text-green-300">Z = (6wk avg − baseline μ) / σ</p>
                                                                {a.recent_cases !== undefined && a.baseline_avg !== undefined && (
                                                                    <p className="mb-2 text-slate-300">
                                                                        Recent {a.recent_weeks}wk: <strong>{a.recent_cases} cases</strong> · Baseline: <strong>{a.baseline_avg.toFixed(2)}/bi-wk</strong>
                                                                    </p>
                                                                )}
                                                                <p className="text-slate-400">This signal: Z = {a.z_score.toFixed(2)} — {a.z_score >= 5 ? 'Extreme 🔴' : a.z_score >= 3 ? 'Strong 🟠' : 'Early 🟡'}</p>
                                                            </div>
                                                        </span>
                                                    )}
                                                    {a.pct_increase !== undefined && (
                                                        <span className="text-xs font-bold text-orange-600">{a.pct_increase > 0 ? '+' : ''}{a.pct_increase}% vs baseline</span>
                                                    )}
                                                </div>
                                                <ViewCasesButton
                                                    className="mt-2"
                                                    onClick={() => setCaseQuery({
                                                        title: `Weekly early signal · ${a.week ?? ''}`,
                                                        disease: a.disease,
                                                        startDate: a.window_start,
                                                        endDate: a.window_end,
                                                    })}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ── Spatial Clusters Panel (DBSCAN) ─────────────────────────────── */}
            {clusters.length > 0 && (
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <h2 className="text-lg font-bold text-slate-800">🗺️ Geospatial Disease Clusters</h2>
                                <span className="relative group cursor-help">
                                    <span className="text-slate-400 text-xs border border-slate-300 rounded-full px-1.5 py-0.5 hover:bg-slate-50">ℹ</span>
                                    <div className="absolute bottom-full left-0 mb-2 z-50 hidden group-hover:block w-80 bg-slate-900 text-white text-xs rounded-xl p-3 shadow-2xl pointer-events-none leading-relaxed">
                                        <p className="font-bold text-emerald-400 mb-1">🔬 DBSCAN Spatial Clustering</p>
                                        <p className="mb-2">Groups cities with elevated disease burden that are within <strong>400 km</strong> of each other using DBSCAN (Density-Based Spatial Clustering of Applications with Noise).</p>
                                        <p className="font-mono bg-slate-800 rounded p-1 mb-2 text-green-300">ε = 400 km · min_points = 2</p>
                                        <p className="text-slate-400">A <strong className="text-white">cluster</strong> = ≥2 nearby cities with co-occurring disease. A <strong className="text-white">hotspot</strong> = isolated high-burden city.</p>
                                    </div>
                                </span>
                            </div>
                            <p className="text-xs text-slate-400">Last 90 days · DBSCAN ε=400 km · {clusters.filter(c => !c.is_noise).length} clusters + {clusters.filter(c => c.is_noise).length} isolated hotspots</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                        {clusters.slice(0, 8).map((cluster, i) => (
                            <div
                                key={i}
                                className={`rounded-xl p-4 border-2 ${cluster.is_noise
                                    ? 'border-amber-200 bg-amber-50'
                                    : 'border-emerald-200 bg-emerald-50'
                                    }`}
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${cluster.is_noise
                                        ? 'bg-amber-200 text-amber-800'
                                        : 'bg-emerald-200 text-emerald-800'
                                        }`}>
                                        {cluster.is_noise ? '📍 HOTSPOT' : `🔵 CLUSTER-${cluster.cluster_id}`}
                                    </span>
                                    <span className="text-xs font-bold text-slate-600">{cluster.total_cases} cases</span>
                                </div>
                                <p className="text-sm font-bold text-slate-800 mb-0.5" style={{ fontFamily: 'serif' }}>
                                    {dName(cluster.disease, cluster.devanagari)}
                                </p>
                                {cluster.iast && <p className="text-[10px] text-slate-400 italic mb-2">{cluster.iast}</p>}
                                <div className="space-y-1">
                                    {cluster.cities.slice(0, 4).map((city: string, ci: number) => (
                                        <div key={ci} className="flex items-center justify-between">
                                            <span className="text-xs text-slate-600 capitalize">{city}</span>
                                            <span className="text-xs font-semibold text-slate-700">{cluster.city_cases?.[city] ?? 0}</span>
                                        </div>
                                    ))}
                                    {cluster.cities.length > 4 && (
                                        <p className="text-[10px] text-slate-400">+{cluster.cities.length - 4} more cities</p>
                                    )}
                                </div>
                                {!cluster.is_noise && (
                                    <p className="text-[10px] text-slate-400 mt-2 pt-2 border-t border-slate-200">
                                        spanning {cluster.spread_km} km
                                    </p>
                                )}
                                <ViewCasesButton
                                    className="mt-2"
                                    onClick={() => setCaseQuery({
                                        title: `${cluster.is_noise ? 'Hotspot' : 'Cluster'} · last ${cluster.period_days} days`,
                                        disease: cluster.disease,
                                        cities: cluster.cities.join(','),
                                        days: cluster.period_days,
                                    })}
                                />
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ── Row 1: Trends + Emerging ────────────────────────────────────── */}

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

                {/* Disease Trends Chart */}
                <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <SectionHeader
                        icon={<Activity className="h-5 w-5" />}
                        title="Disease Trends (90 Days)"
                        subtitle="7-day rolling average of daily cases"
                        info="Aggregates patient visit records from the last 90+7 days. Displays a 7-day smoothed rolling average to highlight underlying surge trends rather than daily noise. Missing days are filled with zeros automatically."
                    />
                    {trends.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={trends} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                                    tickFormatter={v => v.slice(5)}
                                />
                                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                                />
                                <Legend wrapperStyle={{ fontSize: '11px' }} />
                                {diseases.map((d, i) => (
                                    <Line
                                        key={d}
                                        type="monotone"
                                        dataKey={d}
                                        stroke={DISEASE_COLORS[i % DISEASE_COLORS.length]}
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 5 }}
                                        name={dName(d)}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[300px] flex items-center justify-center text-slate-400">
                            {loading ? 'Loading trends...' : 'No trend data available for the selected period'}
                        </div>
                    )}
                </div>

                {/* Emerging Threats Panel */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <SectionHeader
                        icon={<TrendingUp className="h-5 w-5" />}
                        title="Emerging Threats"
                        subtitle="Month-over-month growth rate"
                        info="Compares cases in the most recent month vs. the same period 3 months ago. Growth rate = (recent − prior) / prior × 100. Alert levels: Low < 10%, Medium 10–25%, High 25–50%, Critical > 50%. Powered by the /api/forecast/emerging endpoint."
                    />
                    <div className="space-y-3">
                        {emerging.length > 0 ? emerging.slice(0, 6).map((t, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-bold text-slate-700 truncate" style={{ fontFamily: 'serif' }}>
                                        {dName(t.disease)}
                                    </p>
                                    <p className="text-[10px] text-slate-400 italic">{dNameIast(t.disease)}</p>
                                    <p className="text-xs text-slate-400">{t.current_cases} recent cases</p>
                                    <ViewCasesButton
                                        onClick={() => setCaseQuery({
                                            title: 'Emerging threat · recent 3-month window',
                                            disease: t.disease,
                                            startDate: t.window_start,
                                            endDate: t.window_end,
                                        })}
                                    />
                                </div>
                                <div className="flex items-center gap-2 ml-2">
                                    {t.growth_rate > 0
                                        ? <TrendingUp className="h-3 w-3 text-red-500" />
                                        : <TrendingDown className="h-3 w-3 text-green-500" />}
                                    <span className={`text-xs font-bold ${t.growth_rate > 0 ? 'text-red-600' : 'text-green-600'}`}>
                                        {t.growth_rate > 0 ? '+' : ''}{t.growth_rate.toFixed(0)}%
                                    </span>
                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${SEVERITY_STYLES[t.alert_level] ?? 'bg-slate-200 text-slate-700'}`}>
                                        {t.alert_level}
                                    </span>
                                </div>
                            </div>
                        )) : (
                            <p className="text-slate-400 text-sm text-center py-8">
                                {loading ? 'Loading trends...' : 'No emerging threats detected'}
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Row 2: Hotspots + Spread Prediction ─────────────────────────── */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

                {/* Geospatial Hotspots */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <SectionHeader
                        icon={<MapPin className="h-5 w-5" />}
                        title="Disease Hotspots"
                        subtitle="City-level case concentration"
                        info="Counts all patient visits per city joined to their diagnosis. Displays the top 8 city-disease pairs by case volume. Filter the dropdown to focus on a specific disease. Data comes directly from the patients + medical_records tables."
                    />
                    <div className="mb-4">
                        <select
                            value={selectedDisease}
                            onChange={e => setSelectedDisease(e.target.value)}
                            className="w-full text-sm border border-slate-200 rounded-xl px-3 py-2 text-slate-700 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-amber-400"
                        >
                            <option value="">All Diseases</option>
                            {uniqueDiseaseList.map(d => (
                                <option key={d} value={d}>{dName(d)}</option>
                            ))}
                        </select>
                    </div>
                    <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                        {topHotspots.length > 0 ? topHotspots.map((h, i) => (
                            <div key={i} className="flex items-center justify-between p-3 rounded-xl hover:bg-red-50 transition-colors border border-transparent hover:border-red-100">
                                <div className="flex items-center gap-3">
                                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ${i < 3 ? 'bg-red-500' : 'bg-orange-400'}`}>
                                        {i + 1}
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold text-slate-800" style={{ fontFamily: 'serif' }}>
                                            {dName(h.diagnosis, h.devanagari)}
                                        </p>
                                        <p className="text-[10px] text-slate-400 italic mb-1">{h.iast || dNameIast(h.diagnosis)}</p>
                                        <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded w-fit">
                                            <MapPin className="h-3 w-3 text-slate-400" />
                                            <span className="capitalize">{h.city}</span>
                                        </div>
                                        <ViewCasesButton
                                            className="mt-1"
                                            onClick={() => setCaseQuery({
                                                title: `Hotspot · ${h.city}`,
                                                disease: h.diagnosis,
                                                cities: h.city,
                                            })}
                                        />
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-lg font-bold text-slate-800">{h.count}</p>
                                    <p className="text-[10px] text-slate-400">cases</p>
                                </div>
                            </div>
                        )) : (
                            <p className="text-slate-400 text-sm text-center py-8">
                                {loading ? 'Loading hotspots...' : 'No hotspot data found'}
                            </p>
                        )}
                    </div>
                </div>

                {/* 7-Day Spread Prediction */}
                <div className="bg-white rounded-2xl shadow-sm border border-blue-100 p-6">
                    <SectionHeader
                        icon={<Brain className="h-5 w-5 text-blue-600" />}
                        title="7-Day Regional Spread Forecast"
                        subtitle="Graph diffusion model · city-level predictions"
                        info="Builds a geographic graph: each city is a node, edges connect cities within 300 km (weighted by proximity). Disease cases diffuse along edges using a 0.25 transmission rate per step. Each 'day' is one diffusion step. The model simulates how today's case load would spread if not contained. Not a trained GNN — it is a deterministic graph diffusion (Phase 1). A real ST-GNN is planned for Phase 2 after 6+ months of live data."
                    />
                    {spread.length > 0 ? (
                        <>
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart
                                    data={spread
                                        .filter((_, i) => i < 12)
                                        .map(s => ({
                                            name: `${s.city} D+${s.day_offset}`,
                                            cases: s.predicted_cases,
                                            risk: s.risk_level,
                                        }))}
                                    margin={{ top: 5, right: 5, bottom: 30, left: 0 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                    <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94a3b8' }} angle={-40} textAnchor="end" />
                                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                    <Tooltip contentStyle={{ borderRadius: '12px', fontSize: '12px' }} />
                                    <Bar dataKey="cases" name="Predicted Cases" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                            <div className="mt-4 grid grid-cols-2 gap-2">
                                {spread.slice(0, 4).map((p, i) => (
                                    <div key={i} className="flex items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-100">
                                        <div>
                                            <p className="text-xs font-semibold text-slate-700">{p.city}</p>
                                            <p className="text-[10px] text-slate-400">Day +{p.day_offset}</p>
                                        </div>
                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${SEVERITY_STYLES[p.risk_level] ?? 'bg-slate-200 text-slate-700'}`}>
                                            {p.risk_level}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <div className="h-[200px] flex items-center justify-center text-slate-400">
                            {loading ? 'Running spread simulation...' : 'Insufficient location data for spread prediction'}
                        </div>
                    )}
                </div>
            </div>

            {/* ── Row 3: Forecast + Disease Radar ─────────────────────────────── */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

                {/* 3-Month Disease Forecast */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <SectionHeader
                        icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
                        title="3-Month Disease Forecast"
                        subtitle="Predicted case counts for the next 3 months per disease"
                        info="Uses a RandomForest model trained on 13 months of patient records. Ayurvedic Ritu (season) flags are used as features — Vasanta (spring), Grishma (summer), Varsha (monsoon), Sharad (autumn), Hemanta (pre-winter), Shishira (winter). Values shown are predicted total cases per disease per month. 🌿 = Ritu Sandhi (seasonal transition — highest risk window)."
                    />
                    {Object.keys(forecastByDisease).length > 0 ? (
                        <>
                            <div className="flex items-center gap-3 mb-4">
                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${SEVERITY_STYLES[forecast?.risk_level ?? ''] ?? 'bg-slate-200 text-slate-700'}`}>
                                    {forecast?.risk_level ?? 'low'} risk
                                </span>
                                <span className="text-xs text-slate-500 capitalize">
                                    {forecast?.trend === 'increasing' ? '↑ Rising trend' : forecast?.trend === 'decreasing' ? '↓ Declining' : '→ Stable'}
                                </span>
                            </div>

                            {/* Month header row */}
                            {(() => {
                                const firstDisease = Object.values(forecastByDisease)[0] ?? [];
                                const months = firstDisease.map(m => m.month_name);
                                const diseases = Object.entries(forecastByDisease).slice(0, 6);
                                return (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-xs">
                                            <thead>
                                                <tr className="border-b border-slate-100">
                                                    <th className="text-left py-2 pr-3 text-slate-500 font-medium w-36">Disease (रोग)</th>
                                                    {months.map((m, i) => (
                                                        <th key={i} className="text-center py-2 px-2 text-slate-500 font-medium">{m}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {diseases.map(([dis, months_data], di) => (
                                                    <tr key={di} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                                                        <td className="py-2.5 pr-3 font-medium text-slate-700">
                                                            <p className="font-bold text-slate-800" style={{ fontFamily: 'serif' }}>
                                                                {dName(dis, nameMap[dis]?.devanagari)}
                                                            </p>
                                                            <p className="text-[10px] text-slate-400 italic">{nameMap[dis]?.iast ?? ''}</p>
                                                        </td>
                                                        {months_data.map((m_entry, mi) => (
                                                            <td key={mi} className="text-center py-2.5 px-2">
                                                                <p className="text-base font-bold text-purple-700">{m_entry.predicted_cases}</p>
                                                                <p className="text-[10px] text-slate-400">
                                                                    {RITU_EMOJI[m_entry.season] ?? '🌿'} {m_entry.season || '—'}
                                                                    {m_entry.ritu_sandhi ? ' 🌿' : ''}
                                                                </p>
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        <p className="text-[10px] text-slate-400 mt-3 italic">
                                            Values = predicted cases. 🌿 Ritu Sandhi = seasonal transition (high-risk window).
                                            Model: RandomForest trained on Jan 2025 – Feb 2026 Ayurvedic clinical data.
                                        </p>
                                    </div>
                                );
                            })()}
                        </>
                    ) : forecast?.forecast_data && forecast.forecast_data.length > 0 ? (
                        // Fallback: old bar chart if by_disease is missing
                        <ResponsiveContainer width="100%" height={200}>
                            <BarChart data={forecast.forecast_data.slice(0, 9)} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                                <XAxis dataKey="month_name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                                <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                                <Bar dataKey="predicted_cases" name="Predicted Cases" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[200px] flex items-center justify-center text-slate-400 text-sm">
                            {loading ? 'Generating forecast...' : 'No forecast data available'}
                        </div>
                    )}
                </div>


            </div>

            {/* Disease Radar + Top Cities */}
            <div className="space-y-6">
                {/* Top Diseases Radar */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <SectionHeader
                        icon={<BarChart2 className="h-5 w-5" />}
                        title="Disease Load Distribution"
                        subtitle="Top 6 diseases by case volume"
                        info="Radar chart of the top 6 diseases by total case count across all time. Each axis represents a disease. The larger the polygon area, the higher the overall burden relative to others. Data source: analytics/dashboard top_diseases summary."
                    />
                    {radarData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={160}>
                            <RadarChart data={radarData}>
                                <PolarGrid stroke="#f1f5f9" />
                                <PolarAngleAxis dataKey="disease" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                <PolarRadiusAxis tick={{ fontSize: 8 }} />
                                <Radar name="Cases" dataKey="count" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
                            </RadarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-[160px] flex items-center justify-center text-slate-400 text-sm">
                            {loading ? 'Loading...' : 'No summary data'}
                        </div>
                    )}
                </div>

                {/* Top Cities */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                    <SectionHeader
                        icon={<MapPin className="h-5 w-5" />}
                        title="Top Cities by Patient Load"
                        info="Ranks cities by total patient visits across all time. Bar width shows relative proportion compared to the highest-volume city. Source: patients table city field."
                    />
                    <div className="space-y-2">
                        {summary?.top_cities.slice(0, 4).map((c, i) => {
                            const max = summary.top_cities[0]?.count ?? 1;
                            const pct = Math.round((c.count / max) * 100);
                            return (
                                <div key={i} className="flex items-center gap-3">
                                    <span className="text-xs font-medium text-slate-500 w-20 truncate">{c.city}</span>
                                    <div className="flex-1 bg-slate-100 rounded-full h-2">
                                        <div
                                            className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-500 transition-all"
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                    <span className="text-xs font-bold text-slate-700 w-8 text-right">{c.count}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            <CaseDetailsModal query={caseQuery} onClose={() => setCaseQuery(null)} />
        </div>
    );
}
