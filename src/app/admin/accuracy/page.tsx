"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
    Loader2,
    Play,
    CheckCircle2,
    XCircle,
    AlertCircle,
    Mic,
    FileText,
    Languages,
    Search,
    ShieldCheck
} from "lucide-react";
import { API_BASE } from '@/lib/config';

interface EvaluationResult {
    file: string;
    language: string;
    ground_truth: {
        disease: string;
        symptoms: string[];
        prakriti: string;
        doshas: string;
    };
    transcription: string;
    extraction: {
        disease: string;
        symptoms: string;
        prakriti: string;
        vikriti: string;
        error?: string;
    };
    score: number;
    is_match: boolean;
    status: string;
    error?: string;
}

interface EvaluationSummary {
    total: number;
    processed: number;
    avg_accuracy: number;
}

interface EvaluationReport {
    timestamp: string;
    model?: string;
    summary: EvaluationSummary;
    results: EvaluationResult[];
}

export default function AccuracyEvaluatorPage() {
    const [data, setData] = useState<EvaluationReport | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);
    const [processedCount, setProcessedCount] = useState(0);
    const [totalFiles, setTotalFiles] = useState(0);
    const [currentFile, setCurrentFile] = useState<string | null>(null);
    const [selectedModel, setSelectedModel] = useState<"phi4" | "gemma4">("phi4");

    const runEvaluation = async () => {
        setLoading(true);
        setError(null);
        setData(null);
        setProgress(0);
        setProcessedCount(0);
        setTotalFiles(0);
        setCurrentFile(null);

        try {
            const response = await fetch(`${API_BASE}/api/admin/evaluate-voice?model=${selectedModel}`);
            if (!response.ok) {
                throw new Error(`Evaluation failed with status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error("ReadableStream not supported");

            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const event = JSON.parse(line.replace("data: ", ""));
                            if (event.type === "progress") {
                                setTotalFiles(event.total);
                                setProcessedCount(event.current);
                                setProgress(event.percent);
                                setCurrentFile(event.file || null);
                            } else if (event.type === "complete") {
                                setData(event.report);
                                setProgress(100);
                            } else if (event.type === "error") {
                                setError(event.detail);
                            }
                        } catch (e) {
                            console.error("Error parsing stream event:", e);
                        }
                    }
                }
            }
        } catch (err: any) {
            console.error("Evaluation error:", err);
            setError(err.message || "Failed to run voice pipeline evaluation");
        } finally {
            setLoading(false);
        }
    };

    const getScoreBadge = (score: number) => {
        if (score >= 80) return <Badge className="bg-green-100 text-green-700 border-green-200 pointer-events-none text-[10px] px-2 py-0.5">{score}% Match</Badge>;
        if (score >= 50) return <Badge className="bg-amber-100 text-amber-700 border-amber-200 pointer-events-none text-[10px] px-2 py-0.5">{score}% Partial</Badge>;
        return <Badge variant="destructive" className="bg-red-100 text-red-700 border-red-200 pointer-events-none text-[10px] px-2 py-0.5">{score}% Mismatch</Badge>;
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto py-8 px-4">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <div className="p-2 bg-primary/10 rounded-lg">
                            <Mic className="w-6 h-6 text-primary" />
                        </div>
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Voice Pipeline Evaluator</h1>
                    </div>
                    <p className="text-slate-500">
                        Batch process {totalFiles || 10} audio files through ASR transcription & AI clinical extraction.
                    </p>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                    {/* Model selector segmented control */}
                    <div className="flex items-center bg-slate-100 p-1.5 rounded-xl border border-slate-200 shadow-sm self-start">
                        <button
                            type="button"
                            onClick={() => setSelectedModel("phi4")}
                            disabled={loading}
                            className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all duration-200 select-none ${
                                selectedModel === "phi4"
                                    ? "bg-white text-slate-900 shadow-md font-bold"
                                    : "text-slate-500 hover:text-slate-800"
                            } ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                        >
                            Microsoft Phi-4
                        </button>
                        <button
                            type="button"
                            onClick={() => setSelectedModel("gemma4")}
                            disabled={loading}
                            className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all duration-200 select-none ${
                                selectedModel === "gemma4"
                                    ? "bg-white text-slate-900 shadow-md font-bold"
                                    : "text-slate-500 hover:text-slate-800"
                            } ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                        >
                            Google Gemma-4
                        </button>
                    </div>

                    <Button
                        onClick={runEvaluation}
                        disabled={loading}
                        size="lg"
                        className="bg-primary hover:bg-primary/90 shadow-md transition-all active:scale-95 cursor-pointer font-semibold"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Evaluating Pipeline...
                            </>
                        ) : (
                            <>
                                <Play className="mr-2 h-5 w-5 fill-current" />
                                Run 10-File Evaluation
                            </>
                        )}
                    </Button>
                </div>
            </div>

            {loading && (
                <Card className="border-primary/20 bg-primary/5">
                    <CardContent className="py-6">
                        <div className="space-y-4">
                            <div className="flex justify-between items-center text-sm font-medium">
                                <span className="text-primary flex items-center gap-2">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    {processedCount > 0 ? `Processing file ${processedCount} of ${totalFiles}` : "Initializing Batch..."}
                                </span>
                                <span className="font-bold">{progress}%</span>
                            </div>
                            <Progress value={progress} className="h-2 transition-all duration-500" />
                            {currentFile && (
                                <p className="text-xs text-slate-500 flex items-center gap-1">
                                    <FileText className="h-3 w-3" />
                                    Current: <span className="font-mono font-semibold">{currentFile}</span>
                                </p>
                            )}
                            <p className="text-xs text-slate-400 text-center italic">
                                Seqeuntial processing in progress. Please wait...
                            </p>
                        </div>
                    </CardContent>
                </Card>
            )}

            {error && (
                <div className="p-4 bg-red-50 text-red-600 rounded-lg flex items-center border border-red-200">
                    <AlertCircle className="h-5 w-5 mr-3 shrink-0" />
                    <p className="text-sm font-medium">{error}</p>
                </div>
            )}

            {data && (
                <>
                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card className="border-l-4 border-l-slate-400 shadow-sm">
                            <CardHeader className="pb-2">
                                <div className="flex items-center gap-2">
                                    <FileText className="w-4 h-4 text-slate-500" />
                                    <CardTitle className="text-sm font-medium text-slate-500">Total Files</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold">{data.summary.total}</div>
                                <p className="text-xs text-slate-400 mt-1">Ground truth reference</p>
                            </CardContent>
                        </Card>
                        <Card className="border-l-4 border-l-amber-400 shadow-sm">
                            <CardHeader className="pb-2">
                                <div className="flex items-center gap-2">
                                    <Languages className="w-4 h-4 text-amber-500" />
                                    <CardTitle className="text-sm font-medium text-slate-500">Processed</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold">{data.summary.processed}</div>
                                <p className="text-xs text-slate-400 mt-1">Files successfully analyzed</p>
                            </CardContent>
                        </Card>
                        <Card className="border-l-4 border-l-blue-400 shadow-sm bg-blue-50/10">
                            <CardHeader className="pb-2">
                                <div className="flex items-center gap-2">
                                    <Search className="w-4 h-4 text-blue-500" />
                                    <CardTitle className="text-sm font-medium text-slate-500">Overall Accuracy</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold text-blue-600">{data.summary.avg_accuracy.toFixed(1)}%</div>
                                <p className="text-xs text-slate-400 mt-1">Weighted fuzzy match rate</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Results Table */}
                    <Card className="shadow-lg border-primary/10 overflow-hidden">
                        <CardHeader className="bg-slate-50/50 border-b">
                            <CardTitle>
                                Evaluation Pipeline Report ({data.model === "gemma4" ? "Google Gemma-4" : "Microsoft Phi-4"})
                            </CardTitle>
                            <CardDescription>
                                Detailed breakdown of transcription output and AI clinical extraction vs. ground truth.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left border-collapse">
                                    <thead className="text-xs text-slate-700 bg-slate-100/80 border-b uppercase sticky top-0 z-10">
                                        <tr>
                                            <th className="px-6 py-4 font-bold border-r">Score</th>
                                            <th className="px-6 py-4 font-bold border-r">Audio / Lang</th>
                                            <th className="px-6 py-4 font-bold border-r bg-blue-50/30">Original Data</th>
                                            <th className="px-6 py-4 font-bold border-r">Transcribed Audio</th>
                                            <th className="px-6 py-4 font-bold bg-amber-50/30">AI Extracted Data</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        {data.results.map((result, index) => (
                                            <tr key={index} className="bg-white hover:bg-slate-50/50 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap border-r align-top text-center">
                                                    {result.status === 'completed' ? getScoreBadge(result.score) : (
                                                        <Badge className="bg-amber-100 text-amber-700 border-amber-200 pointer-events-none">
                                                            <AlertCircle className="w-3 h-3 mr-1" /> Error
                                                        </Badge>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 border-r align-top">
                                                    <a
                                                        href={`${API_BASE}/api/admin/audio/${result.file}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="font-semibold text-primary hover:text-primary/80 hover:underline flex items-center gap-1.5 transition-colors group"
                                                        title="Click to play audio"
                                                    >
                                                        <Play className="w-3 h-3 fill-current opacity-0 group-hover:opacity-100 transition-opacity" />
                                                        <span className="text-xs">{result.file}</span>
                                                    </a>
                                                    <div className="text-[10px] text-slate-500 uppercase mt-1 flex items-center gap-1">
                                                        <Languages className="w-3 h-3" /> {result.language}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 border-r bg-blue-50/10 align-top">
                                                    <div className="space-y-1">
                                                        <div className="flex items-start gap-1">
                                                            <span className="text-[10px] font-bold text-blue-700 w-16 uppercase">Disease:</span>
                                                            <span className="font-semibold text-blue-900">{result.ground_truth?.disease || "-"}</span>
                                                        </div>
                                                        <div className="flex items-start gap-1">
                                                            <span className="text-[10px] font-bold text-blue-700 w-16 uppercase">Symptoms:</span>
                                                            <span className="text-slate-600 text-xs text-wrap">{result.ground_truth?.symptoms?.join(", ") || "None"}</span>
                                                        </div>
                                                        <div className="flex gap-4">
                                                            <div className="flex items-start gap-1 text-[10px]">
                                                                <span className="font-bold text-blue-700 w-16 uppercase">Doshas:</span>
                                                                <span className="text-slate-500 font-medium">{result.ground_truth?.doshas || "-"}</span>
                                                            </div>
                                                            <div className="flex items-start gap-1 text-[10px]">
                                                                <span className="font-bold text-blue-700 uppercase">Prakriti:</span>
                                                                <span className="text-slate-500">{result.ground_truth?.prakriti || "-"}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 border-r italic text-slate-600 leading-relaxed text-[11px] max-w-xs align-top">
                                                    "{result.transcription || result.error || "No data"}"
                                                </td>
                                                <td className="px-6 py-4 bg-amber-50/10 align-top">
                                                    {result.extraction?.error ? (
                                                        <div className="text-red-500 flex items-center text-xs">
                                                            <AlertCircle className="w-3 h-3 mr-1" /> {result.extraction.error}
                                                        </div>
                                                    ) : (
                                                        <div className="space-y-1">
                                                            <div className="flex items-start gap-1">
                                                                <span className="text-[10px] font-bold text-amber-700 w-14 uppercase">Disease:</span>
                                                                <span className={`font-semibold ${result.score >= 80 ? 'text-green-700' : 'text-amber-900'}`}>
                                                                    {result.extraction?.disease || "Not found"}
                                                                </span>
                                                            </div>
                                                            <div className="flex items-start gap-1">
                                                                <span className="text-[10px] font-bold text-amber-700 w-14 uppercase">Sympt:</span>
                                                                <span className="text-slate-600 text-xs text-wrap" title={result.extraction?.symptoms}>
                                                                    {result.extraction?.symptoms || "None extracted"}
                                                                </span>
                                                            </div>
                                                            <div className="flex gap-4">
                                                                <div className="flex items-start gap-1 text-[10px]">
                                                                    <span className="font-bold text-amber-700 uppercase">Doshas:</span>
                                                                    <span className="text-slate-500 font-medium">{result.extraction?.vikriti || "-"}</span>
                                                                </div>
                                                                <div className="flex items-start gap-1 text-[10px]">
                                                                    <span className="font-bold text-amber-700 uppercase">Prakriti:</span>
                                                                    <span className="text-slate-500">{result.extraction?.prakriti || "-"}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}

            {!data && !loading && !error && (
                <Card className="border-dashed bg-slate-50/50 shadow-inner">
                    <CardContent className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-6 shadow-sm">
                            <Mic className="h-8 w-8" />
                        </div>
                        <h3 className="text-xl font-bold text-slate-900 mb-2">Ready to Evaluate Pipeline</h3>
                        <p className="text-slate-500 max-w-md mb-8">
                            Click the button below to start the sequential processing of 10 ground truth audio files through the full voice-to-data pipeline using <strong>{selectedModel === "gemma4" ? "Google Gemma-4" : "Microsoft Phi-4"}</strong>.
                        </p>
                        <Button onClick={runEvaluation} size="lg" className="bg-primary hover:bg-primary/90 px-8 cursor-pointer">
                            Start Batch Process
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
