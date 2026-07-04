"use client"

import { useState, useEffect, useCallback } from "react"
import { DiseaseSearchDropdown } from "@/components/ui/DiseaseSearchDropdown"
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
    LineChart, Line, CartesianGrid, Legend, ReferenceLine,
} from "recharts"

// ── Types ────────────────────────────────────────────────────────────────────

interface QAction {
    name: string
    q_value: number
    is_learned: boolean
}

interface QTableState {
    state_key: string
    actions: QAction[]
    total_prescriptions: number
}

interface StateEvent {
    visit_number: number
    date: string
    original_herbs: string[]
    added_herbs: string[]
    removed_herbs: string[]
    doctor_rating: string
    q_updates: Record<string, { before: number; after: number; reward: number }>
}

interface StateHistory {
    state_key: string
    events: StateEvent[]
}

const NAMC_OPTIONS = [
    { value: "SP60 (EF-2.4.4)", label: "SP60 — Diabetes / Madhumeha" },
    { value: "SP64 (EF-3)",      label: "SP64 — Obesity / Sthoulya" },
    { value: "SM34(AAC-12.4)",   label: "SM34 — Constipation / Vibandha" },
    { value: "EC-3.19",          label: "EC-3.19 — Fever / Jwara" },
]

const DOSHA_OPTIONS = [
    "Vata_Vata", "Vata_Pitta", "Vata_Kapha",
    "Pitta_Vata", "Pitta_Pitta", "Pitta_Kapha",
    "Kapha_Vata", "Kapha_Pitta", "Kapha_Kapha",
]

const DOSHA_LABEL: Record<string, string> = {
    Vata_Vata: "Vata / Vata", Vata_Pitta: "Vata / Pitta", Vata_Kapha: "Vata / Kapha",
    Pitta_Vata: "Pitta / Vata", Pitta_Pitta: "Pitta / Pitta", Pitta_Kapha: "Pitta / Kapha",
    Kapha_Vata: "Kapha / Vata", Kapha_Pitta: "Kapha / Pitta", Kapha_Kapha: "Kapha / Kapha",
}

function barColor(q: number, name?: string) {
    if (name?.startsWith("yoga:"))      return q > 0 ? "#3b82f6" : "#d1d5db"
    if (name?.startsWith("diet:"))      return q > 0 ? "#f59e0b" : "#d1d5db"
    if (name?.startsWith("lifestyle:")) return q > 0 ? "#8b5cf6" : "#d1d5db"
    if (q > 0) return "#22c55e"
    if (q < 0) return "#ef4444"
    return "#d1d5db"
}

function actionLabel(name: string) {
    if (name.startsWith("yoga:"))      return name.replace("yoga:", "🧘 ")
    if (name.startsWith("diet:"))      return name.replace("diet:", "🥗 ")
    if (name.startsWith("lifestyle:")) return name.replace("lifestyle:", "🌿 ")
    return name
}

// ── State picker helper ───────────────────────────────────────────────────────

function StatePicker({
    namc, setNamc, dosha, setDosha, label,
}: {
    namc: string; setNamc: (v: string) => void
    dosha: string; setDosha: (v: string) => void
    label?: string
}) {
    return (
        <div className="flex flex-col gap-2">
            {label && <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>}
            <select
                value={namc}
                onChange={e => setNamc(e.target.value)}
                className="border rounded px-3 py-1.5 text-sm bg-white"
            >
                {NAMC_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                ))}
            </select>
            <select
                value={dosha}
                onChange={e => setDosha(e.target.value)}
                className="border rounded px-3 py-1.5 text-sm bg-white"
            >
                {DOSHA_OPTIONS.map(d => (
                    <option key={d} value={d}>{DOSHA_LABEL[d]}</option>
                ))}
            </select>
        </div>
    )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

type Tab = "demo" | "history" | "compare" | "cohort" | "outcomes"

export default function ModelDashboardPage() {
    const [activeTab, setActiveTab] = useState<Tab>("demo")
    const [demoMode, setDemoMode] = useState(true)

    return (
        <div className="min-h-screen bg-slate-50 p-6">
            <div className="max-w-7xl mx-auto space-y-6">

                {/* ── Header ── */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Model Intelligence Dashboard</h1>
                        <p className="text-sm text-slate-500 mt-0.5">Reinforcement learning Q-table visualiser & outcome tracker</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setDemoMode(v => !v)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border transition-all ${demoMode
                                ? "bg-amber-100 border-amber-300 text-amber-800"
                                : "bg-slate-100 border-slate-300 text-slate-700"
                                }`}
                        >
                            Demo Mode: <span className="font-bold">{demoMode ? "ON" : "OFF"}</span>
                        </button>
                        <ResetDemoButton />
                    </div>
                </div>

                {/* ── Tabs ── */}
                <div className="flex gap-1 border-b border-slate-200">
                    {(["demo", "history", "compare", "cohort", "outcomes"] as Tab[]).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2.5 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${activeTab === tab
                                ? "border-teal-600 text-teal-700"
                                : "border-transparent text-slate-500 hover:text-slate-700"
                                }`}
                        >
                            {tab === "demo" ? "Live Demo" :
                                tab === "history" ? "State History" :
                                    tab === "compare" ? "Compare States" :
                                        tab === "cohort" ? "Cohort Analytics" :
                                            "Outcomes"}
                        </button>
                    ))}
                </div>

                {/* ── Tab Content ── */}
                {activeTab === "demo" && <LiveDemoTab demoMode={demoMode} />}
                {activeTab === "history" && <StateHistoryTab />}
                {activeTab === "compare" && <CompareStatesTab />}
                {activeTab === "cohort" && <CohortTab />}
                {activeTab === "outcomes" && <OutcomesTab />}
            </div>
        </div>
    )
}

// ── Reset Demo Button ─────────────────────────────────────────────────────────

function ResetDemoButton() {
    const [resetting, setResetting] = useState(false)
    const handleReset = async () => {
        setResetting(true)
        try {
            await fetch("/api/ml/demo-reset", { method: "POST" })
            window.location.reload()
        } finally {
            setResetting(false)
        }
    }
    return (
        <button
            onClick={handleReset}
            disabled={resetting}
            className="px-4 py-2 bg-red-50 border border-red-200 text-red-700 text-sm font-medium rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50"
        >
            {resetting ? "Resetting..." : "Reset Demo"}
        </button>
    )
}

// ── Live Demo Tab ─────────────────────────────────────────────────────────────

function LiveDemoTab({ demoMode }: { demoMode: boolean }) {
    const [disease, setDisease] = useState("Madhumeha")
    const [prakriti, setPrakriti] = useState("Vata")
    const [vikriti, setVikriti] = useState("Pitta")

    const [qtable, setQtable] = useState<QTableState | null>(null)
    const [currentPlan, setCurrentPlan] = useState<any>(null)
    const [addedHerb, setAddedHerb] = useState("")
    const [addedYoga, setAddedYoga] = useState("")
    const [selectedRating, setSelectedRating] = useState<"Accurate" | "Needs Changes" | null>(null)
    const [submitting, setSubmitting] = useState(false)
    const [submitted, setSubmitted] = useState(false)
    const [notification, setNotification] = useState<string | null>(null)
    const [loadingNext, setLoadingNext] = useState(false)
    const [loadingRec, setLoadingRec] = useState(false)

    // Fetch recommendation on load (Q-table is fetched inline after namc_code resolves)
    useEffect(() => {
        fetchRecommendation()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const fetchQTable = useCallback(async (namc_code?: string) => {
        try {
            const code = namc_code || currentPlan?.namc_code
            if (!code) return
            const params = new URLSearchParams({
                namc_code: code,
                prakriti,
                vikriti,
                demo_session: String(demoMode),
            })
            const res = await fetch(`/api/model/q-table-state?${params}`)
            if (res.ok) setQtable(await res.json())
        } catch { }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [prakriti, vikriti, demoMode, currentPlan?.namc_code])

    const fetchRecommendation = useCallback(async () => {
        setLoadingRec(true)
        try {
            const res = await fetch("/api/ml/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ disease, prakriti, vikriti, demo_session: demoMode }),
            })
            if (res.ok) {
                const plan = await res.json()
                setCurrentPlan(plan)
                // Immediately fetch Q-table for the resolved namc_code
                if (plan?.namc_code) {
                    const params = new URLSearchParams({
                        namc_code: plan.namc_code,
                        prakriti,
                        vikriti,
                        demo_session: String(demoMode),
                    })
                    const qtRes = await fetch(`/api/model/q-table-state?${params}`)
                    if (qtRes.ok) setQtable(await qtRes.json())
                }
            }
        } catch { }
        finally { setLoadingRec(false) }
    }, [disease, prakriti, vikriti, demoMode])

    const handleSubmit = async () => {
        if (!currentPlan) return
        setSubmitting(true)
        try {
            const planToSend = {
                ...currentPlan,
                herbs: addedHerb.trim()
                    ? [
                        { name: addedHerb.trim(), dosage: "As prescribed", benefits: "Added during demo" },
                        ...(currentPlan.herbs || []),
                    ]
                    : (currentPlan.herbs || []),
                yoga: addedYoga.trim()
                    ? [
                        { practice: addedYoga.trim(), duration: "20 mins daily", benefits: "Added during demo" },
                        ...(currentPlan.yoga || []),
                    ]
                    : (currentPlan.yoga || []),
            }

            // 1. Save feedback row via demo-submit (no real patient needed)
            const prescribeRes = await fetch("/api/ml/demo-submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    disease,
                    namc_code: currentPlan.namc_code || "",
                    state_key: currentPlan.state_key || "",
                    prakriti,
                    vikriti,
                    original_plan: currentPlan,
                    final_plan: planToSend,
                    rating: selectedRating,
                    demo_session: demoMode,
                }),
            })
            const prescribeData = prescribeRes.ok ? await prescribeRes.json() : {}
            const feedbackId = prescribeData.feedback_id

            // 2. Retrain instant
            if (feedbackId) {
                const retrainRes = await fetch("/api/ml/retrain-instant", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ feedback_id: feedbackId, demo_session: demoMode }),
                })
                if (retrainRes.ok) {
                    const retrainData = await retrainRes.json()
                    const updatedQ: Record<string, number> = retrainData.updated_q_values || {}

                    // Update Q-table bars with new values
                    if (qtable) {
                        const updated: QTableState = {
                            ...qtable,
                            actions: qtable.actions.map(a => ({
                                ...a,
                                q_value: updatedQ[a.name] ?? a.q_value,
                            })),
                        }
                        setQtable(updated)
                        const learnedHerb = Object.entries(updatedQ).find(([, v]) => v > 0)?.[0]
                        if (learnedHerb) {
                            setNotification(`✦ ${learnedHerb} learned`)
                            setTimeout(() => setNotification(null), 4000)
                        }
                    }
                }
            } else {
                // No feedback_id — just refresh Q-table
                await fetchQTable()
            }

            setSubmitted(true)
        } finally {
            setSubmitting(false)
        }
    }

    const handleNextPatient = async () => {
        setLoadingNext(true)
        setSubmitted(false)
        setAddedHerb("")
        setAddedYoga("")
        setSelectedRating(null)
        try {
            await fetchRecommendation() // also fetches Q-table inline after resolving namc_code
        } finally {
            setLoadingNext(false)
        }
    }

    const chartData = (qtable?.actions || []).map(a => {
        const label = actionLabel(a.name)
        return {
            name: label.length > 16 ? label.slice(0, 16) + "…" : label,
            fullName: a.name,
            q_value: a.q_value,
            is_learned: a.is_learned,
        }
    })

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* ── Left: Prescription Form ── */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
                <h2 className="text-lg font-bold text-slate-800">Prescription Form</h2>

                <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-500 uppercase">Disease</label>
                    <DiseaseSearchDropdown
                        value={disease}
                        onChange={setDisease}
                        placeholder="Search disease..."
                    />
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">Prakriti</label>
                        <select value={prakriti} onChange={e => setPrakriti(e.target.value)}
                            className="border rounded-lg px-3 py-2 text-sm w-full bg-white">
                            <option value="Vata">Vata</option>
                            <option value="Pitta">Pitta</option>
                            <option value="Kapha">Kapha</option>
                        </select>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">Vikriti</label>
                        <select value={vikriti} onChange={e => setVikriti(e.target.value)}
                            className="border rounded-lg px-3 py-2 text-sm w-full bg-white">
                            <option value="Vata">Vata</option>
                            <option value="Pitta">Pitta</option>
                            <option value="Kapha">Kapha</option>
                        </select>
                    </div>
                </div>

                {/* Get Recommendation button */}
                <button
                    onClick={fetchRecommendation}
                    disabled={!disease.trim() || loadingRec}
                    className="w-full py-2 rounded-lg text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 transition-colors"
                >
                    {loadingRec ? "Fetching…" : "Get AI Recommendation"}
                </button>

                {/* Herb list */}
                {currentPlan?.herbs && (
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">AI Recommended Herbs</label>
                        <ul className="space-y-1">
                            {currentPlan.herbs.map((h: any, i: number) => (
                                <li key={i} className="flex items-center gap-2 text-sm text-slate-700 bg-slate-50 px-3 py-1.5 rounded-lg">
                                    <span className="text-emerald-500">•</span> {h.name}
                                    {(h.ai_learned || (h.source && h.source.includes("RL"))) && (
                                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                                            ✦ AI-learned
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Yoga list */}
                {currentPlan?.yoga?.length > 0 && (
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">AI Recommended Yoga</label>
                        <ul className="space-y-1">
                            {currentPlan.yoga.map((y: any, i: number) => (
                                <li key={i} className="flex items-center gap-2 text-sm text-slate-700 bg-blue-50 px-3 py-1.5 rounded-lg">
                                    <span className="text-blue-500">◦</span> {y.practice || y}
                                    {y.ai_learned && (
                                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                                            ✦ AI-learned
                                        </span>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Add herb + yoga */}
                <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">+ Add Herb</label>
                        <input
                            className="border rounded-lg px-3 py-2 text-sm w-full"
                            placeholder="e.g. Guchi Powder"
                            value={addedHerb}
                            onChange={e => setAddedHerb(e.target.value)}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-semibold text-slate-500 uppercase">+ Add Yoga</label>
                        <input
                            className="border rounded-lg px-3 py-2 text-sm w-full"
                            placeholder="e.g. Surya Namaskar"
                            value={addedYoga}
                            onChange={e => setAddedYoga(e.target.value)}
                        />
                    </div>
                </div>

                {/* Rating */}
                <div className="flex gap-3">
                    <button
                        onClick={() => setSelectedRating(r => r === "Accurate" ? null : "Accurate")}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${selectedRating === "Accurate"
                            ? "bg-emerald-500 border-emerald-600 text-white"
                            : "bg-white border-slate-200 text-slate-700 hover:bg-emerald-50"
                            }`}
                    >
                        Accurate
                    </button>
                    <button
                        onClick={() => setSelectedRating(r => r === "Needs Changes" ? null : "Needs Changes")}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium border transition-all ${selectedRating === "Needs Changes"
                            ? "bg-red-500 border-red-600 text-white"
                            : "bg-white border-slate-200 text-slate-700 hover:bg-red-50"
                            }`}
                    >
                        Needs Changes
                    </button>
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="w-full py-3 bg-teal-600 text-white rounded-xl font-bold text-sm hover:bg-teal-700 transition-colors disabled:opacity-50"
                >
                    {submitting ? "Submitting..." : "Submit Prescription"}
                </button>

                {submitted && (
                    <button
                        onClick={handleNextPatient}
                        disabled={loadingNext}
                        className="w-full py-2.5 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-xl font-medium text-sm hover:bg-indigo-100 transition-colors"
                    >
                        {loadingNext ? "Loading..." : "Next Patient — Same Profile"}
                    </button>
                )}

                {notification && (
                    <div className="text-center text-amber-700 font-semibold text-sm bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 animate-pulse">
                        {notification}
                    </div>
                )}
            </div>

            {/* ── Right: Live Q-table ── */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-bold text-slate-800">Live Q-Table</h2>
                        {qtable && (
                            <p className="text-xs text-slate-500 mt-0.5">
                                State: <span className="font-mono font-semibold">{qtable.state_key}</span>
                            </p>
                        )}
                    </div>
                    {qtable && (
                        <span className="text-xs bg-slate-100 text-slate-600 px-3 py-1 rounded-full font-medium">
                            {qtable.total_prescriptions} prescription{qtable.total_prescriptions !== 1 ? "s" : ""} in memory
                        </span>
                    )}
                </div>

                {/* Legend */}
                <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-[#22c55e] inline-block"/><span>Herb</span></span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-[#3b82f6] inline-block"/>Yoga</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-[#f59e0b] inline-block"/>Diet</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-[#8b5cf6] inline-block"/>Lifestyle</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-[#ef4444] inline-block"/>Negative</span>
                </div>

                {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 64 }}>
                            <XAxis
                                dataKey="name"
                                tick={{ fontSize: 11 }}
                                angle={-40}
                                textAnchor="end"
                                interval={0}
                            />
                            <YAxis tick={{ fontSize: 11 }} />
                            <Tooltip
                                formatter={(value: number | undefined) => [(value ?? 0).toFixed(4), "Q-value"]}
                                labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName || ""}
                            />
                            <Bar
                                dataKey="q_value"
                                isAnimationActive={true}
                                animationDuration={800}
                                label={false as unknown as undefined}
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={barColor(entry.q_value, entry.fullName)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
                        Loading Q-table data...
                    </div>
                )}

                <div className="flex gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-green-500 inline-block" /> Q &gt; 0 (positive)</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-red-400 inline-block" /> Q &lt; 0 (negative)</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-gray-300 inline-block" /> Q = 0 (neutral)</span>
                </div>
            </div>
        </div>
    )
}

// ── State History Tab ─────────────────────────────────────────────────────────

function StateHistoryTab() {
    const [namc, setNamc] = useState("SP60 (EF-2.4.4)")
    const [dosha, setDosha] = useState("Vata_Pitta")
    const [history, setHistory] = useState<StateHistory | null>(null)
    const [loading, setLoading] = useState(false)
    const [selectedHerb, setSelectedHerb] = useState("")

    const stateKey = `${namc}_${dosha}`

    const loadHistory = async () => {
        setLoading(true)
        try {
            const res = await fetch(`/api/model/state-history/${encodeURIComponent(stateKey)}`)
            if (res.ok) setHistory(await res.json())
        } finally {
            setLoading(false)
        }
    }

    const allHerbs = history
        ? Array.from(new Set(history.events.flatMap(e => Object.keys(e.q_updates || {}))))
        : []

    const lineData = history?.events.map(e => ({
        visit: e.visit_number,
        q: selectedHerb ? (e.q_updates?.[selectedHerb]?.after ?? null) : null,
    })) || []

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <div className="flex flex-wrap items-end gap-4">
                    <StatePicker namc={namc} setNamc={setNamc} dosha={dosha} setDosha={setDosha} label="Select State" />
                    <button
                        onClick={loadHistory}
                        disabled={loading}
                        className="px-5 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50"
                    >
                        {loading ? "Loading..." : "Load History"}
                    </button>
                </div>
                {history && (
                    <p className="mt-3 text-xs text-slate-500 font-mono">State: {history.state_key}</p>
                )}
            </div>

            {history && (
                <>
                    {/* Event table */}
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-slate-50 border-b border-slate-200">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Visit #</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Date</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Added Herbs</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Removed Herbs</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Rating</th>
                                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Q Updates</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {history.events.map((ev, i) => (
                                        <tr key={i} className="hover:bg-slate-50">
                                            <td className="px-4 py-3 font-medium">{ev.visit_number}</td>
                                            <td className="px-4 py-3 text-slate-500">{ev.date}</td>
                                            <td className="px-4 py-3">
                                                {(ev.added_herbs || []).map((h, j) => (
                                                    <span key={j} className="inline-block bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full mr-1">{h}</span>
                                                ))}
                                            </td>
                                            <td className="px-4 py-3">
                                                {(ev.removed_herbs || []).map((h, j) => (
                                                    <span key={j} className="inline-block bg-red-100 text-red-800 text-xs px-2 py-0.5 rounded-full mr-1">{h}</span>
                                                ))}
                                            </td>
                                            <td className="px-4 py-3 text-slate-600">{ev.doctor_rating}</td>
                                            <td className="px-4 py-3 text-xs text-slate-500 font-mono max-w-xs truncate">
                                                {Object.entries(ev.q_updates || {}).map(([herb, u]) => (
                                                    <div key={herb}>{herb}: {u.before.toFixed(3)} → {u.after.toFixed(3)}</div>
                                                ))}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Line chart */}
                    {allHerbs.length > 0 && (
                        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                            <div className="flex items-center gap-3">
                                <h3 className="text-sm font-semibold text-slate-700">Q-value over visits</h3>
                                <select
                                    value={selectedHerb}
                                    onChange={e => setSelectedHerb(e.target.value)}
                                    className="border rounded-lg px-3 py-1.5 text-sm bg-white"
                                >
                                    <option value="">Select herb</option>
                                    {allHerbs.map(h => <option key={h} value={h}>{h}</option>)}
                                </select>
                            </div>
                            {selectedHerb && (
                                <ResponsiveContainer width="100%" height={260}>
                                    <LineChart data={lineData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="visit" label={{ value: "Visit #", position: "insideBottom", offset: -4 }} />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" label="Threshold" />
                                        <Line
                                            type="monotone"
                                            dataKey="q"
                                            name={selectedHerb}
                                            stroke="#14b8a6"
                                            strokeWidth={2}
                                            dot={{ r: 3 }}
                                            connectNulls
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

// ── Compare States Tab ────────────────────────────────────────────────────────

function CompareStatesTab() {
    const [namc1, setNamc1] = useState("SP60 (EF-2.4.4)")
    const [dosha1, setDosha1] = useState("Vata_Pitta")
    const [namc2, setNamc2] = useState("SP64 (EF-3)")
    const [dosha2, setDosha2] = useState("Pitta_Kapha")
    const [state1, setState1] = useState<QTableState | null>(null)
    const [state2, setState2] = useState<QTableState | null>(null)
    const [loading, setLoading] = useState(false)

    const loadBoth = async () => {
        setLoading(true)
        try {
            const [r1, r2] = await Promise.all([
                fetch(`/api/model/q-table-state?namc_code=${namc1}&prakriti=${dosha1.split("_")[0]}&vikriti=${dosha1.split("_")[1]}&demo_session=true`),
                fetch(`/api/model/q-table-state?namc_code=${namc2}&prakriti=${dosha2.split("_")[0]}&vikriti=${dosha2.split("_")[1]}&demo_session=true`),
            ])
            if (r1.ok) setState1(await r1.json())
            if (r2.ok) setState2(await r2.json())
        } finally {
            setLoading(false)
        }
    }

    const makeChartData = (s: QTableState | null) =>
        (s?.actions || []).map(a => ({
            name: a.name.length > 12 ? a.name.slice(0, 12) + "…" : a.name,
            q_value: a.q_value,
        }))

    return (
        <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h2 className="text-base font-bold text-slate-700 mb-4">
                    Same disease, different response by constitution
                </h2>
                <div className="flex flex-wrap items-end gap-6">
                    <StatePicker namc={namc1} setNamc={setNamc1} dosha={dosha1} setDosha={setDosha1} label="State A" />
                    <StatePicker namc={namc2} setNamc={setNamc2} dosha={dosha2} setDosha={setDosha2} label="State B" />
                    <button
                        onClick={loadBoth}
                        disabled={loading}
                        className="px-5 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50"
                    >
                        {loading ? "Loading..." : "Compare"}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {[state1, state2].map((s, i) => (
                    <div key={i} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-3">
                        <h3 className="text-sm font-semibold text-slate-700">
                            {s ? <span className="font-mono">{s.state_key}</span> : `State ${i === 0 ? "A" : "B"}`}
                        </h3>
                        {s && makeChartData(s).length > 0 ? (
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={makeChartData(s)} margin={{ top: 8, right: 8, left: 0, bottom: 60 }}>
                                    <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" interval={0} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip formatter={(v: number | undefined) => [(v ?? 0).toFixed(4), "Q-value"]} />
                                    <Bar dataKey="q_value" isAnimationActive={true}>
                                        {makeChartData(s).map((entry, idx) => (
                                            <Cell key={idx} fill={barColor(entry.q_value)} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-48 flex items-center justify-center text-slate-400 text-sm border-2 border-dashed border-slate-200 rounded-xl">
                                {loading ? "Loading..." : "Click Compare to load"}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

// ── Cohort Analytics Tab ──────────────────────────────────────────────────────

function CohortTab() {
    return (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-10 text-center space-y-3">
            <h2 className="text-xl font-bold text-slate-700">Cohort Analytics — Coming Soon</h2>
            <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
                K-Means clustering results will appear here once the clustering analytics pipeline is connected.
            </p>
        </div>
    )
}

// ── Outcomes Tab ──────────────────────────────────────────────────────────────

interface OutcomeRow {
    id: string
    patient: string
    disease: string
    prescribed_date: string
    target_vital: string
    baseline: string
    followup_value: string
    saved: boolean
    result?: { percentage_change?: number }
}

function OutcomesTab() {
    const [totalStates, setTotalStates] = useState<number | null>(null)
    const [rows, setRows] = useState<OutcomeRow[]>([])

    useEffect(() => {
        fetch("/api/model/q-table-state")
            .then(r => r.json())
            .then(d => { if (d.total_prescriptions !== undefined) setTotalStates(d.total_prescriptions) })
            .catch(() => { })
    }, [])

    const handleFollowupChange = (id: string, value: string) => {
        setRows(prev => prev.map(r => r.id === id ? { ...r, followup_value: value } : r))
    }

    const handleSave = async (row: OutcomeRow) => {
        if (!row.followup_value) return
        try {
            const res = await fetch("/api/outcomes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    medical_record_id: row.id,
                    followup_value: parseFloat(row.followup_value),
                }),
            })
            if (res.ok) {
                const data = await res.json()
                setRows(prev => prev.map(r =>
                    r.id === row.id ? { ...r, saved: true, result: data } : r
                ))
            }
        } catch { }
    }

    return (
        <div className="space-y-6">
            {/* Health metric */}
            {totalStates !== null && (
                <div className="bg-teal-50 border border-teal-200 rounded-xl px-5 py-3 text-sm text-teal-800 flex items-center gap-2">
                    <span className="font-semibold">Model health:</span>
                    <span>{totalStates} total prescriptions tracked across Q-states</span>
                </div>
            )}

            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200">
                    <h2 className="text-base font-bold text-slate-800">Pending Follow-ups</h2>
                </div>

                {rows.length === 0 ? (
                    <div className="px-6 py-10 text-center text-slate-400 text-sm space-y-2">
                        <p>No pending follow-ups fetched yet.</p>
                        <p className="text-xs text-slate-400">
                            {/* TODO: Backend endpoint GET /api/outcomes/pending needed. */}
                            Backend endpoint <code className="bg-slate-100 px-1 rounded">GET /api/outcomes/pending</code> needed.
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Patient</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Disease</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Prescribed Date</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Target Vital</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Baseline</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Follow-up Value</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {rows.map(row => (
                                    <tr key={row.id} className="hover:bg-slate-50">
                                        <td className="px-4 py-3">{row.patient}</td>
                                        <td className="px-4 py-3 text-slate-600">{row.disease}</td>
                                        <td className="px-4 py-3 text-slate-500">{row.prescribed_date}</td>
                                        <td className="px-4 py-3">{row.target_vital}</td>
                                        <td className="px-4 py-3 text-slate-500">{row.baseline}</td>
                                        <td className="px-4 py-3">
                                            {row.saved ? (
                                                <span className="text-green-600 font-medium">
                                                    Saved {row.result?.percentage_change !== undefined
                                                        ? `(${row.result.percentage_change.toFixed(1)}%)`
                                                        : ""}
                                                </span>
                                            ) : (
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={row.followup_value}
                                                    onChange={e => handleFollowupChange(row.id, e.target.value)}
                                                    className="border rounded px-2 py-1 w-24 text-sm"
                                                />
                                            )}
                                        </td>
                                        <td className="px-4 py-3">
                                            {!row.saved && (
                                                <button
                                                    onClick={() => handleSave(row)}
                                                    className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700"
                                                >
                                                    Save
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
