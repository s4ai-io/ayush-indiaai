import { TrendChart } from "@/components/charts/TrendChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function TrendsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Disease Trends Analysis</h2>
                <p className="text-muted-foreground">Historical records and emerging pattern detection.</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Case Frequency (2025-2026)</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-[400px] w-full">
                        <TrendChart />
                    </div>
                </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardHeader><CardTitle className="text-base">Dominant Strain</CardTitle></CardHeader>
                    <CardContent><p className="text-2xl font-bold text-amber-600">Flu (H3N2)</p></CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="text-base">Growth Rate</CardTitle></CardHeader>
                    <CardContent><p className="text-2xl font-bold text-emerald-600">-12%</p><p className="text-xs text-muted-foreground">Decreasing vs last month</p></CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="text-base">Predicted Peak</CardTitle></CardHeader>
                    <CardContent><p className="text-2xl font-bold text-red-600">July 15</p><p className="text-xs text-muted-foreground">Based on historical data</p></CardContent>
                </Card>
            </div>
        </div>
    );
}
