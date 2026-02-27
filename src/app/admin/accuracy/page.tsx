"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, RefreshCw, CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { API_BASE } from '@/lib/config';

interface EvaluationResult {
    expected: string;
    predicted: string;
    is_match: boolean;
    confidence: number;
    symptoms_used: string;
    error?: string;
}

interface EvaluationSummary {
    total: number;
    correct: number;
    accuracy: number;
}

interface EvaluationData {
    summary: EvaluationSummary;
    results: EvaluationResult[];
}

export default function AccuracyEvaluatorPage() {
    const [data, setData] = useState<EvaluationData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const runEvaluation = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/api/admin/evaluate`);
            if (!response.ok) {
                throw new Error(`Evaluation failed with status: ${response.status}`);
            }
            const result = await response.json();
            setData(result);
        } catch (err: any) {
            console.error("Evaluation error:", err);
            setError(err.message || "Failed to run evaluation");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 max-w-6xl mx-auto py-8">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">Translation Accuracy Evaluator</h1>
                    <p className="text-slate-500 mt-1">
                        Evaluate the ground truth translations against the AI recommendation model.
                    </p>
                </div>
                <Button
                    onClick={runEvaluation}
                    disabled={loading}
                    className="bg-primary hover:bg-primary/90"
                >
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                    Run Evaluation
                </Button>
            </div>

            {error && (
                <div className="p-4 bg-red-50 text-red-600 rounded-lg flex items-center border border-red-200">
                    <AlertCircle className="h-5 w-5 mr-2 shrink-0" />
                    <p>{error}</p>
                </div>
            )}

            {data && (
                <>
                    {/* Summary Cards */}
                    <div className="grid gap-4 md:grid-cols-3">
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-slate-500">Total Cases</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold">{data.summary.total}</div>
                                <p className="text-xs text-slate-400 mt-1">From ground_truth.json</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-slate-500">Correct Predictions</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold text-green-600">{data.summary.correct}</div>
                                <p className="text-xs text-slate-400 mt-1">Exact or fuzzy matches</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-slate-500">Overall Accuracy</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-3xl font-bold text-blue-600">{data.summary.accuracy}%</div>
                                <p className="text-xs text-slate-400 mt-1">Success rate</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Results Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Evaluation Results</CardTitle>
                            <CardDescription>Detailed breakdown of expected versus predicted diseases based on symptoms.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="border rounded-lg overflow-hidden">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm text-left">
                                        <thead className="text-xs text-slate-700 bg-slate-50 border-b">
                                            <tr>
                                                <th className="px-4 py-3 font-semibold">Status</th>
                                                <th className="px-4 py-3 font-semibold">Expected (Ground Truth)</th>
                                                <th className="px-4 py-3 font-semibold">Predicted (AI Model)</th>
                                                <th className="px-4 py-3 font-semibold">Confidence</th>
                                                <th className="px-4 py-3 font-semibold">Symptoms Used</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y">
                                            {data.results.map((result, index) => (
                                                <tr key={index} className="bg-white hover:bg-slate-50/50">
                                                    <td className="px-4 py-3 whitespace-nowrap">
                                                        {result.is_match ? (
                                                            <Badge className="bg-green-100 text-green-700 hover:bg-green-200 border-none">
                                                                <CheckCircle2 className="w-3 h-3 mr-1" /> Match
                                                            </Badge>
                                                        ) : (
                                                            <Badge variant="destructive" className="bg-red-100 text-red-700 hover:bg-red-200 border-none">
                                                                <XCircle className="w-3 h-3 mr-1" /> Mismatch
                                                            </Badge>
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-3 font-medium">{result.expected}</td>
                                                    <td className="px-4 py-3 text-slate-600">
                                                        {result.error ? (
                                                            <span className="text-red-500 flex items-center text-xs">
                                                                <AlertCircle className="w-3 h-3 mr-1" /> Error finding match
                                                            </span>
                                                        ) : (
                                                            result.predicted
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-3 text-slate-600">
                                                        {result.confidence > 0 ? `${(result.confidence * 100).toFixed(0)}%` : "-"}
                                                    </td>
                                                    <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate" title={result.symptoms_used}>
                                                        {result.symptoms_used}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}

            {!data && !loading && !error && (
                <Card className="border-dashed bg-slate-50/50">
                    <CardContent className="flex flex-col items-center justify-center h-64 text-center">
                        <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-4">
                            <RefreshCw className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900 mb-1">No Evaluation Data</h3>
                        <p className="text-slate-500 max-w-sm mb-6">
                            Click the button above to run the evaluation pipeline against the ground truth dataset.
                        </p>
                        <Button onClick={runEvaluation} className="bg-primary hover:bg-primary/90">
                            Run Evaluation Now
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
