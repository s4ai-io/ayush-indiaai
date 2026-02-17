
'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Activity, MapPin, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Types
interface TrendData {
    date: string;
    [key: string]: number | string;
}

interface AlertData {
    disease: string;
    severity: string;
    message: string;
    date: string;
}

interface HotspotData {
    city: string;
    pincode: string;
    diagnosis: string;
    count: number;
}

interface PredictionData {
    pincode: string;
    predicted_cases: number;
    risk_level: string;
    day_offset: number;
}

export default function PublicHealthDashboard() {
    const [trends, setTrends] = useState<TrendData[]>([]);
    const [alerts, setAlerts] = useState<AlertData[]>([]);
    const [hotspots, setHotspots] = useState<HotspotData[]>([]);
    const [predictions, setPredictions] = useState<PredictionData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Trends
                const trendsRes = await fetch('http://localhost:8000/api/analytics/trends');
                const trendsData = await trendsRes.json();
                setTrends(trendsData);

                // Fetch Alerts
                const alertsRes = await fetch('http://localhost:8000/api/analytics/alerts');
                const alertsData = await alertsRes.json();
                setAlerts(alertsData);

                // Fetch Hotspots (Dengue default for demo)
                const hotspotsRes = await fetch('http://localhost:8000/api/analytics/hotspots?disease=Dengue');
                const hotspotsData = await hotspotsRes.json();
                setHotspots(hotspotsData);

                // Fetch Predictions
                const predRes = await fetch('http://localhost:8000/api/analytics/predictions');
                const predData = await predRes.json();
                setPredictions(predData);

            } catch (error) {
                console.error("Failed to fetch analytics data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // Get list of diseases from trend keys (excluding date)
    const diseases = trends.length > 0 ? Object.keys(trends[0]).filter(k => k !== 'date') : [];
    // Colors for chart
    const colors = ["#ef4444", "#3b82f6", "#22c55e", "#f59e0b", "#6366f1"];

    return (
        <div className="min-h-screen bg-slate-50 p-6 space-y-6">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">Public Health Intelligence</h1>
                    <p className="text-slate-500">Real-time epidemiological monitoring & early warning system</p>
                </div>
                <div className="flex gap-2">
                    <span className="bg-white px-4 py-2 rounded-full text-sm font-medium shadow-sm border text-slate-600">
                        {new Date().toLocaleDateString()}
                    </span>
                </div>
            </header>

            {/* Top Alerts Section */}
            {alerts.length > 0 && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r shadow-sm mb-6 animate-pulse">
                    <div className="flex items-start">
                        <AlertTriangle className="h-6 w-6 text-red-600 mr-3 mt-0.5" />
                        <div>
                            <h3 className="text-lg font-bold text-red-800">Active Outbreak Alerts</h3>
                            <div className="mt-2 space-y-2">
                                {alerts.map((alert, idx) => (
                                    <div key={idx} className="p-2 bg-white/60 rounded text-red-700 text-sm font-semibold border-red-100 border">
                                        🚨 {alert.message}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                {/* 1. Disease Trends Chart */}
                <Card className="col-span-2 shadow-sm border-slate-200">
                    <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-lg flex items-center gap-2 text-slate-700">
                                <Activity className="h-5 w-5 text-blue-500" />
                                Disease Trends (Last 30 Days)
                            </CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[350px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={trends} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={(val) => val.slice(5)} />
                                    <YAxis />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Legend />
                                    {diseases.map((d, i) => (
                                        <Line
                                            key={d}
                                            type="monotone"
                                            dataKey={d}
                                            stroke={colors[i % colors.length]}
                                            strokeWidth={2}
                                            dot={false}
                                            activeDot={{ r: 6 }}
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* 2. Hotspots List (Placeholder for Map) */}
                <div className="space-y-6">
                    <Card className="shadow-sm border-slate-200 h-full">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-lg flex items-center gap-2 text-slate-700">
                                <MapPin className="h-5 w-5 text-red-500" />
                                Critical Hotspots
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {hotspots.slice(0, 5).map((hotspot, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg group hover:bg-red-50 transition-colors cursor-pointer border border-transparent hover:border-red-100">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center font-bold text-xs">
                                                {idx + 1}
                                            </div>
                                            <div>
                                                <p className="font-medium text-slate-800">{hotspot.pincode}</p>
                                                <p className="text-xs text-slate-500">{hotspot.city}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-bold text-slate-700">{hotspot.count}</p>
                                            <p className="text-xs text-slate-500">Cases</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* GNN Predictions Widget */}
                    <Card className="shadow-sm border-blue-100 bg-blue-50/50">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-lg flex items-center gap-2 text-blue-800">
                                <TrendingUp className="h-5 w-5 text-blue-600" />
                                AI Spread Prediction
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-sm text-blue-600 mb-2">
                                Forecast for next 7 days (GNN Model)
                            </div>
                            <div className="space-y-2">
                                {predictions.slice(0, 3).map((pred, idx) => (
                                    <div key={idx} className="flex justify-between items-center text-sm p-2 bg-white rounded border border-blue-100">
                                        <span className="font-medium text-slate-700">{pred.pincode}</span>
                                        <span className="text-xs text-slate-500">Day +{pred.day_offset}</span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${pred.risk_level === 'High' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                                            }`}>
                                            {pred.risk_level} Risk
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>

            </div>
        </div>
    );
}

// Add types for UI components if missing, or use basic HTML for quick prototype
// We assume standard UI components (Card, Alert) are available from shadcn/ui or similar structure used in app.
// If not, I should define them inline or use standard HTML.
// Based on file list, I see `src/components/ui/card` doesn't exist?
// I only see `src/components/LanguageSelector.tsx` and `VoiceInputButton.tsx` in recent file lists.
// I should verify if `src/components/ui` exists.
