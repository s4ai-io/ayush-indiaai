import { RiskMap } from "@/components/charts/RiskMap";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ForecastingPage() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Public Health Forecast</h2>
                <p className="text-muted-foreground">Predictive analytics for emerging health risks.</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Regional Risk Assessment</CardTitle>
                </CardHeader>
                <CardContent>
                    <RiskMap />
                </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader><CardTitle>AI Insights</CardTitle></CardHeader>
                    <CardContent className="space-y-2">
                        <div className="p-3 bg-red-50 text-red-900 border border-red-100 rounded text-sm">
                            <strong>Alert:</strong> High probability of Heat Stroke in West Zone due to rising temperatures. Advisory: Hydration campaigns recommended.
                        </div>
                        <div className="p-3 bg-amber-50 text-amber-900 border border-amber-100 rounded text-sm">
                            <strong>Notice:</strong> Dengue mosquito breeding expected to peak in South Zone. Advisory: Vector control implementation.
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle>Data Sources</CardTitle></CardHeader>
                    <CardContent>
                        <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
                            <li>Historical Hospital Admissions (State Registry)</li>
                            <li>Meteorological Data (IMD API)</li>
                            <li>Vector Surveillance Reports</li>
                            <li>Social Media Sentiment Analysis</li>
                        </ul>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
