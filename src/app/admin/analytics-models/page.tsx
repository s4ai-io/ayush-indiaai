"use client"

import { useState, useEffect } from "react"
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
    CartesianGrid, Legend,
} from "recharts"

// ── Types ────────────────────────────────────────────────────────────────────

interface DBSCANCluster {
    cluster_id: number
    disease: string
    cities: string[]
    total_cases: number
    radius_km: number
    is_noise: boolean
    centroid_lat?: number
    centroid_lon?: number
}

interface DBSCANData {
    name: string
    type: string
    algorithm: string
    params: { eps_km: number; min_samples: number; distance_metric: string; max_cities_per_cluster: number; period_days: number }
    stats: { total_clusters: number; total_hotspots: number; diseases_tracked: number }
    clusters: DBSCANCluster[]
    error?: string
}

interface DiseaseScore {
    disease: string
    z_score: number
    severity: string
    cusum_value: number
    triggered_by: string
    pct_increase: number
    surge_month: string
}

interface AnomalyData {
    name: string
    type: string
    algorithms: string[]
    params: {
        z_threshold: number
        cusum_k_factor: number
        min_recent_cases: number
        baseline_window: string
        severity_thresholds: Record<string, string>
    }
    stats: { total_alerts: number; by_severity: Record<string, number> }
    disease_scores: DiseaseScore[]
    error?: string
}

interface HubCity { city: string; connectivity: number; current_cases: number }

interface GNNData {
    name: string
    type: string
    phase_note: string
    params: { transmission_rate: number; adjacency_threshold_km: number; forecast_days: number; edge_weight_formula: string; distance_metric: string }
    stats: { graph_nodes: number; graph_edges: number; top_hubs: HubCity[] }
    error?: string
}

interface FeatureImportance { feature: string; importance: number }

interface ForecasterData {
    name: string
    type: string
    params: { n_estimators: number; max_depth: number; random_state: number; n_jobs: number; retrain_interval: string; forecast_horizon: string; feature_count: number; features: string[] }
    ritu_map: Record<string, { months: string; label: string; emoji: string }>
    sandhi_months: number[]
    stats: { trained: boolean; diseases_tracked: number; training_samples: number; months_of_data: number; model_age_hours: number | null }
    feature_importance: FeatureImportance[]
    error?: string
}

interface ModelInfo {
    dbscan: DBSCANData
    anomaly: AnomalyData
    gnn: GNNData
    forecaster: ForecasterData
    generated_at: string
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const SEVERITY_COLOR: Record<string, string> = {
    Critical: "#ef4444",
    High:     "#f97316",
    Medium:   "#eab308",
    Low:      "#22c55e",
}

const SEVERITY_BG: Record<string, string> = {
    Critical: "bg-red-100 text-red-800 border-red-200",
    High:     "bg-orange-100 text-orange-800 border-orange-200",
    Medium:   "bg-yellow-100 text-yellow-800 border-yellow-200",
    Low:      "bg-green-100 text-green-800 border-green-200",
}

function ParamChip({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="inline-flex flex-col items-center bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 min-w-[80px]">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
            <span className="text-sm font-bold text-slate-800 mt-0.5">{value}</span>
        </div>
    )
}

function StatCard({ label, value, sub, color = "teal" }: { label: string; value: string | number; sub?: string; color?: string }) {
    const colors: Record<string, string> = {
        teal:   "border-t-teal-500",
        blue:   "border-t-blue-500",
        orange: "border-t-orange-500",
        red:    "border-t-red-500",
        purple: "border-t-purple-500",
        green:  "border-t-green-500",
    }
    return (
        <div className={`bg-white rounded-xl border border-slate-200 border-t-2 ${colors[color] ?? colors.teal} p-4`}>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">{label}</p>
            <p className="text-2xl font-extrabold text-slate-900 mt-1">{value}</p>
            {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
        </div>
    )
}

function ModelHeader({ name, type, badge }: { name: string; type: string; badge?: string }) {
    return (
        <div className="flex items-start gap-4 bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                    <h2 className="text-lg font-extrabold text-slate-900">{name}</h2>
                    <span className="text-xs bg-teal-100 text-teal-800 border border-teal-200 font-semibold px-2.5 py-0.5 rounded-full">{type}</span>
                    {badge && <span className="text-xs bg-amber-100 text-amber-800 border border-amber-200 font-semibold px-2.5 py-0.5 rounded-full">{badge}</span>}
                </div>
            </div>
        </div>
    )
}

// ── Tab: DBSCAN ───────────────────────────────────────────────────────────────

function DBSCANTab({ data }: { data: DBSCANData }) {
    if (data.error) return <ErrorCard msg={data.error} />

    const chartData = data.clusters
        .slice(0, 12)
        .map(c => ({ name: c.disease.length > 22 ? c.disease.slice(0, 20) + "…" : c.disease, cases: c.total_cases, type: c.is_noise ? "Hotspot" : "Cluster" }))

    return (
        <div className="space-y-5">
            <ModelHeader name={data.name} type={data.type} />

            {/* Params */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Algorithm Parameters</p>
                <div className="flex flex-wrap gap-3">
                    <ParamChip label="ε (epsilon)" value={`${data.params.eps_km} km`} />
                    <ParamChip label="min_samples" value={data.params.min_samples} />
                    <ParamChip label="Distance" value="Haversine" />
                    <ParamChip label="Max Cities" value={data.params.max_cities_per_cluster} />
                    <ParamChip label="Window" value={`${data.params.period_days} days`} />
                </div>
                <p className="text-xs text-slate-400 mt-3 leading-relaxed">
                    Each (city, disease) pair is treated as a weighted point. Cities within <strong>{data.params.eps_km} km</strong> of each other that share disease burden form a cluster.
                    Points with fewer than <strong>{data.params.min_samples}</strong> neighbours remain as isolated hotspots (noise label = −1).
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <StatCard label="Clusters Found" value={data.stats.total_clusters} sub="Multi-city disease zones" color="teal" />
                <StatCard label="Isolated Hotspots" value={data.stats.total_hotspots} sub="Noise points (label −1)" color="orange" />
                <StatCard label="Diseases Tracked" value={data.stats.diseases_tracked} sub={`Last ${data.params.period_days} days`} color="blue" />
            </div>

            {/* Chart */}
            {chartData.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Disease Burden by Cluster Type</p>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 60 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" interval={0} />
                            <YAxis tick={{ fontSize: 11 }} />
                            <Tooltip formatter={(v) => [`${v} cases`, "Total cases"]} />
                            <Bar dataKey="cases" radius={[4, 4, 0, 0]}>
                                {chartData.map((c, i) => (
                                    <Cell key={i} fill={c.type === "Cluster" ? "#0d9488" : "#f97316"} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="flex gap-4 mt-2 text-xs text-slate-500">
                        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-teal-600 inline-block" /> Multi-city cluster</span>
                        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-orange-500 inline-block" /> Isolated hotspot</span>
                    </div>
                </div>
            )}

            {/* Cluster table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-100">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Cluster Detail</p>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
                            <tr>
                                <th className="px-4 py-2 text-left">Disease</th>
                                <th className="px-4 py-2 text-left">Type</th>
                                <th className="px-4 py-2 text-left">Cities</th>
                                <th className="px-4 py-2 text-right">Cases</th>
                                <th className="px-4 py-2 text-right">Radius km</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.clusters.map((c, i) => (
                                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                                    <td className="px-4 py-2 font-medium text-slate-800">{c.disease}</td>
                                    <td className="px-4 py-2">
                                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${c.is_noise ? "bg-orange-100 text-orange-800 border-orange-200" : "bg-teal-100 text-teal-800 border-teal-200"}`}>
                                            {c.is_noise ? "Hotspot" : "Cluster"}
                                        </span>
                                    </td>
                                    <td className="px-4 py-2 text-slate-600 text-xs">{c.cities.slice(0, 4).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(", ")}{c.cities.length > 4 ? ` +${c.cities.length - 4}` : ""}</td>
                                    <td className="px-4 py-2 text-right font-semibold text-slate-800">{c.total_cases}</td>
                                    <td className="px-4 py-2 text-right text-slate-500">{c.radius_km != null ? Math.round(c.radius_km) : "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

// ── Tab: Anomaly Detection ────────────────────────────────────────────────────

function AnomalyTab({ data }: { data: AnomalyData }) {
    if (data.error) return <ErrorCard msg={data.error} />

    const chartData = data.disease_scores.map(d => ({
        name: d.disease.length > 22 ? d.disease.slice(0, 20) + "…" : d.disease,
        z_score: d.z_score,
        severity: d.severity,
    }))

    const sev = data.stats.by_severity

    return (
        <div className="space-y-5">
            <ModelHeader name={data.name} type={data.type} />

            {/* Params */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Algorithm Parameters</p>
                <div className="flex flex-wrap gap-3 mb-4">
                    <ParamChip label="Z-Threshold" value={data.params.z_threshold} />
                    <ParamChip label="CUSUM k" value={data.params.cusum_k_factor} />
                    <ParamChip label="Min Cases" value={data.params.min_recent_cases} />
                    <ParamChip label="Baseline" value={data.params.baseline_window} />
                </div>

                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Severity Thresholds</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {Object.entries(data.params.severity_thresholds).map(([level, desc]) => (
                        <div key={level} className={`rounded-lg border px-3 py-2 text-xs ${SEVERITY_BG[level] ?? ""}`}>
                            <span className="font-bold block">{level}</span>
                            <span className="opacity-80">{desc}</span>
                        </div>
                    ))}
                </div>

                <p className="text-xs text-slate-400 mt-3 leading-relaxed">
                    <strong>Z-Score</strong> (leave-one-out): scores each month against all <em>other</em> months for that disease — detects sharp, isolated spikes.&nbsp;
                    <strong>CUSUM</strong> accumulates deviations over time — fires on slow-building drift that Z-Score alone would miss. Both run per-disease on every reload.
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatCard label="Total Alerts" value={data.stats.total_alerts} color="orange" />
                <StatCard label="Critical" value={sev.Critical ?? 0} sub="Z ≥ 3.5" color="red" />
                <StatCard label="High" value={sev.High ?? 0} sub="Z ≥ 2.5" color="orange" />
                <StatCard label="Medium / Low" value={(sev.Medium ?? 0) + (sev.Low ?? 0)} sub="Z ≥ 1.5" color="green" />
            </div>

            {/* Z-score bar chart */}
            {chartData.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Per-Disease Z-Score (most anomalous month)</p>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 40, left: 130, bottom: 4 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                            <XAxis type="number" tick={{ fontSize: 11 }} domain={[0, "auto"]} />
                            <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={125} />
                            <Tooltip formatter={(v) => [`Z = ${v}`, "Z-Score"]} />
                            <Bar dataKey="z_score" radius={[0, 4, 4, 0]}>
                                {chartData.map((d, i) => (
                                    <Cell key={i} fill={SEVERITY_COLOR[d.severity] ?? "#94a3b8"} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="flex flex-wrap gap-3 mt-2 text-xs text-slate-500">
                        {Object.entries(SEVERITY_COLOR).map(([k, v]) => (
                            <span key={k} className="flex items-center gap-1.5">
                                <span className="w-3 h-3 rounded inline-block" style={{ background: v }} /> {k}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Alert table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-100">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Alert Detail</p>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
                            <tr>
                                <th className="px-4 py-2 text-left">Disease</th>
                                <th className="px-4 py-2 text-left">Severity</th>
                                <th className="px-4 py-2 text-right">Z-Score</th>
                                <th className="px-4 py-2 text-right">CUSUM</th>
                                <th className="px-4 py-2 text-right">% Change</th>
                                <th className="px-4 py-2 text-left">Triggered By</th>
                                <th className="px-4 py-2 text-left">Month</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.disease_scores.map((d, i) => (
                                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                                    <td className="px-4 py-2 font-medium text-slate-800">{d.disease}</td>
                                    <td className="px-4 py-2">
                                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${SEVERITY_BG[d.severity] ?? ""}`}>{d.severity}</span>
                                    </td>
                                    <td className="px-4 py-2 text-right font-mono text-slate-700">{d.z_score.toFixed(2)}</td>
                                    <td className="px-4 py-2 text-right font-mono text-slate-500">{d.cusum_value.toFixed(1)}</td>
                                    <td className="px-4 py-2 text-right font-semibold text-orange-600">+{d.pct_increase.toFixed(0)}%</td>
                                    <td className="px-4 py-2 text-xs text-slate-500">{d.triggered_by}</td>
                                    <td className="px-4 py-2 text-xs text-slate-400">{d.surge_month}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

// ── Tab: GNN Diffusion ────────────────────────────────────────────────────────

function GNNTab({ data }: { data: GNNData }) {
    if (data.error) return <ErrorCard msg={data.error} />

    const hubs = data.stats.top_hubs ?? []
    const hubChart = hubs.map(h => ({ name: h.city.charAt(0).toUpperCase() + h.city.slice(1), connectivity: h.connectivity, cases: h.current_cases }))

    return (
        <div className="space-y-5">
            <ModelHeader name={data.name} type={data.type} badge="Phase 1" />

            {/* Params */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Algorithm Parameters</p>
                <div className="flex flex-wrap gap-3 mb-4">
                    <ParamChip label="Transmission Rate" value={data.params.transmission_rate} />
                    <ParamChip label="Adjacency Threshold" value={`${data.params.adjacency_threshold_km} km`} />
                    <ParamChip label="Forecast Days" value={data.params.forecast_days} />
                    <ParamChip label="Distance" value={data.params.distance_metric} />
                </div>

                <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 font-mono text-xs text-slate-700 leading-relaxed">
                    <span className="text-slate-400">// Diffusion step per city per day:</span><br />
                    <span className="text-teal-700">load<sub>t+1</sub>(city)</span> = load<sub>t</sub>(city) +{" "}
                    <span className="text-blue-700">Σ</span> ( weight<sub>edge</sub> × load<sub>t</sub>(neighbour) × {data.params.transmission_rate} )<br />
                    <span className="text-slate-400">// edge weight = 1 − (distance_km / {data.params.adjacency_threshold_km})</span>
                </div>

                <p className="text-xs text-slate-400 mt-3 leading-relaxed">
                    A dynamic graph is built from real patient location data on every request. Nodes = cities with recent cases.
                    Edges connect cities within <strong>{data.params.adjacency_threshold_km} km</strong> — closer cities carry higher weight.
                    Diffusion runs for <strong>{data.params.forecast_days} days</strong>. {data.phase_note}.
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
                <StatCard label="Graph Nodes" value={data.stats.graph_nodes} sub="Cities with active cases" color="teal" />
                <StatCard label="Graph Edges" value={data.stats.graph_edges} sub={`< ${data.params.adjacency_threshold_km} km connections`} color="blue" />
                <StatCard label="Top Hubs" value={hubs.length} sub="By degree centrality" color="purple" />
            </div>

            {/* Hub chart */}
            {hubChart.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Hub Cities — Degree Centrality (transmission risk)</p>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={hubChart} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                            <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                            <Tooltip formatter={(v) => [typeof v === "number" ? v.toFixed(3) : v, "Centrality"]} />
                            <Bar dataKey="connectivity" fill="#7c3aed" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Hub table */}
            {hubs.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                    <div className="px-5 py-3 border-b border-slate-100">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Hub City Detail</p>
                    </div>
                    <table className="w-full text-sm">
                        <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
                            <tr>
                                <th className="px-4 py-2 text-left">Rank</th>
                                <th className="px-4 py-2 text-left">City</th>
                                <th className="px-4 py-2 text-right">Degree Centrality</th>
                                <th className="px-4 py-2 text-right">Current Cases</th>
                            </tr>
                        </thead>
                        <tbody>
                            {hubs.map((h, i) => (
                                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                                    <td className="px-4 py-2 text-slate-400 font-mono">#{i + 1}</td>
                                    <td className="px-4 py-2 font-semibold text-slate-800">{h.city.charAt(0).toUpperCase() + h.city.slice(1)}</td>
                                    <td className="px-4 py-2 text-right font-mono text-purple-700">{h.connectivity.toFixed(3)}</td>
                                    <td className="px-4 py-2 text-right text-slate-700">{h.current_cases}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}

// ── Tab: Disease Forecaster ───────────────────────────────────────────────────

function ForecasterTab({ data }: { data: ForecasterData }) {
    if (data.error) return <ErrorCard msg={data.error} />

    const featureLabels: Record<string, string> = {
        disease_enc:  "Disease (encoded)",
        category_enc: "Category (encoded)",
        season_enc:   "Season (encoded)",
        month_num:    "Month number",
        ritu_sandhi:  "Ritu Sandhi (transition)",
        cases_lag1:   "Cases lag-1 (1 mo ago)",
        cases_lag2:   "Cases lag-2 (2 mo ago)",
        cases_lag3:   "Cases lag-3 (3 mo ago)",
        avg_severity: "Average severity",
    }

    const impData = data.feature_importance.map(f => ({
        name: featureLabels[f.feature] ?? f.feature,
        importance: f.importance,
        pct: Math.round(f.importance * 100),
    }))

    const s = data.stats
    const modelAgeLabel = s.model_age_hours == null ? "Unknown"
        : s.model_age_hours < 1 ? "< 1 hour ago"
        : `${s.model_age_hours.toFixed(1)}h ago`

    return (
        <div className="space-y-5">
            <ModelHeader name={data.name} type={data.type} badge={s.trained ? "Trained" : "Not Trained"} />

            {/* Params */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Model Parameters</p>
                <div className="flex flex-wrap gap-3 mb-4">
                    <ParamChip label="n_estimators" value={data.params.n_estimators} />
                    <ParamChip label="max_depth" value={data.params.max_depth} />
                    <ParamChip label="random_state" value={data.params.random_state} />
                    <ParamChip label="Features" value={data.params.feature_count} />
                    <ParamChip label="Horizon" value={data.params.forecast_horizon} />
                    <ParamChip label="Retrain" value={data.params.retrain_interval} />
                </div>

                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Features</p>
                <div className="flex flex-wrap gap-2">
                    {data.params.features.map(f => (
                        <span key={f} className="bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono px-2.5 py-1 rounded-md">
                            {f}
                        </span>
                    ))}
                </div>

                <p className="text-xs text-slate-400 mt-3 leading-relaxed">
                    Lag features (cases_lag1/2/3) give the model a 3-month memory.
                    <strong> ritu_sandhi</strong> = 1 for seasonal transition months ({data.sandhi_months.join(", ")}), where Ayurvedic theory predicts peak vulnerability.
                    Model is persisted to disk and retrained at most once per {data.params.retrain_interval}.
                </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatCard label="Diseases Tracked" value={s.diseases_tracked} color="teal" />
                <StatCard label="Training Samples" value={s.training_samples.toLocaleString()} sub="Monthly disease rows" color="blue" />
                <StatCard label="Months of Data" value={s.months_of_data} sub="Training history" color="purple" />
                <StatCard label="Model Age" value={modelAgeLabel} sub="Last retrain" color={s.model_age_hours != null && s.model_age_hours > 20 ? "orange" : "green"} />
            </div>

            {/* Feature importance chart */}
            {impData.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 p-5">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">Feature Importance (from trained RandomForest)</p>
                    <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={impData} layout="vertical" margin={{ top: 4, right: 60, left: 160, bottom: 4 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                            <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                            <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={155} />
                            <Tooltip formatter={(v) => [typeof v === "number" ? `${(v * 100).toFixed(1)}%` : v, "Importance"]} />
                            <Bar dataKey="importance" fill="#2563eb" radius={[0, 4, 4, 0]}>
                                {impData.map((_, i) => (
                                    <Cell key={i} fill={`hsl(${220 - i * 18}, 80%, ${55 + i * 3}%)`} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Ritu map */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="px-5 py-3 border-b border-slate-100">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Ayurvedic Ritu (Season) Feature Encoding</p>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-0">
                    {Object.entries(data.ritu_map).map(([ritu, info], i) => (
                        <div key={ritu} className={`px-5 py-3 flex items-center gap-3 ${i % 2 === 0 ? "bg-white" : "bg-slate-50"} border-b border-slate-100`}>
                            <span className="text-xl">{info.emoji}</span>
                            <div>
                                <p className="text-sm font-bold text-slate-800">{ritu}</p>
                                <p className="text-xs text-slate-500">{info.months} — {info.label}</p>
                                {data.sandhi_months.includes(
                                    info.months.startsWith("Jan") ? 1 :
                                    info.months.startsWith("Mar") ? 3 :
                                    info.months.startsWith("May") ? 5 :
                                    info.months.startsWith("Jul") ? 7 :
                                    info.months.startsWith("Sep") ? 9 : 11
                                ) && (
                                    <span className="text-[10px] bg-amber-100 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-semibold mt-0.5 inline-block">Sandhi transition</span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

// ── Error card ────────────────────────────────────────────────────────────────

function ErrorCard({ msg }: { msg: string }) {
    return (
        <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-sm text-red-700">
            <strong>Error loading model data:</strong> {msg}
        </div>
    )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

type Tab = "dbscan" | "anomaly" | "gnn" | "forecaster"

const TAB_LABELS: Record<Tab, string> = {
    dbscan:     "DBSCAN Clustering",
    anomaly:    "Anomaly Detection",
    gnn:        "GNN Spread",
    forecaster: "Disease Forecaster",
}

export default function AnalyticsModelsPage() {
    const [activeTab, setActiveTab] = useState<Tab>("dbscan")
    const [data, setData] = useState<ModelInfo | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch("/api/analytics/model-info")
            .then(r => r.json())
            .then(setData)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false))
    }, [])

    return (
        <div className="min-h-screen bg-slate-50 p-6">
            <div className="max-w-6xl mx-auto space-y-6">

                {/* Header */}
                <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Analytics Model Intelligence</h1>
                        <p className="text-sm text-slate-500 mt-0.5">
                            Live parameters, training stats &amp; real-data diagnostics for all 4 analytics models
                        </p>
                    </div>
                    {data && (
                        <span className="text-xs text-slate-400 bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-mono">
                            Loaded: {new Date(data.generated_at).toLocaleTimeString()}
                        </span>
                    )}
                </div>

                {/* Tabs */}
                <div className="flex gap-1 border-b border-slate-200 overflow-x-auto">
                    {(["dbscan", "anomaly", "gnn", "forecaster"] as Tab[]).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${
                                activeTab === tab
                                    ? "border-teal-600 text-teal-700"
                                    : "border-transparent text-slate-500 hover:text-slate-700"
                            }`}
                        >
                            {TAB_LABELS[tab]}
                        </button>
                    ))}
                </div>

                {/* Content */}
                {loading && (
                    <div className="flex items-center justify-center py-20 text-slate-400 text-sm">
                        Loading model data…
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-sm text-red-700">
                        Failed to load: {error}
                    </div>
                )}

                {data && !loading && (
                    <>
                        {activeTab === "dbscan"     && <DBSCANTab data={data.dbscan} />}
                        {activeTab === "anomaly"    && <AnomalyTab data={data.anomaly} />}
                        {activeTab === "gnn"        && <GNNTab data={data.gnn} />}
                        {activeTab === "forecaster" && <ForecasterTab data={data.forecaster} />}
                    </>
                )}
            </div>
        </div>
    )
}
