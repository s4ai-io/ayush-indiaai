import { riskForecastData } from "@/lib/mockData";
import { cn } from "@/lib/utils";
import { AlertTriangle, ShieldCheck, ThermometerSun, CloudRain, Wind } from "lucide-react";

export function RiskMap() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {riskForecastData.map((zone) => {
                let colorClass = "bg-green-50 border-green-200 text-green-900";
                let icon = <ShieldCheck className="h-6 w-6 text-green-600" />;

                // Dynamic Icon Logic based on Threat
                if (zone.threat.includes("Heat")) icon = <ThermometerSun className="h-6 w-6 text-orange-600" />;
                if (zone.threat.includes("Monsoon") || zone.threat.includes("Malaria")) icon = <CloudRain className="h-6 w-6 text-blue-600" />;
                if (zone.threat.includes("Respiratory")) icon = <Wind className="h-6 w-6 text-gray-600" />;

                if (zone.riskLevel === 'High') {
                    colorClass = "bg-red-50 border-red-200 text-red-900";
                    if (!icon.props.className.includes("text-")) icon = <AlertTriangle className="h-6 w-6 text-red-600" />;
                } else if (zone.riskLevel === 'Moderate') {
                    colorClass = "bg-amber-50 border-amber-200 text-amber-900";
                }

                return (
                    <div key={zone.region} className={cn("border rounded-lg p-5 flex flex-col gap-3 shadow-sm hover:shadow-md transition-shadow", colorClass)}>
                        <div className="flex items-center justify-between">
                            <h3 className="font-bold text-lg">{zone.region}</h3>
                            {icon}
                        </div>

                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="font-semibold">{zone.threat}</span>
                                <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium",
                                    zone.riskLevel === 'High' ? 'bg-red-200 text-red-800' :
                                        zone.riskLevel === 'Moderate' ? 'bg-amber-200 text-amber-800' : 'bg-green-200 text-green-800'
                                )}>
                                    {zone.riskLevel} Risk
                                </span>
                            </div>
                            <p className="text-xs opacity-80 leading-relaxed min-h-[40px]">{zone.details}</p>
                        </div>

                        <div className="space-y-1">
                            <div className="flex justify-between text-xs opacity-70">
                                <span>Risk Probability</span>
                                <span>{zone.probability}%</span>
                            </div>
                            <div className="w-full bg-white/60 h-2 rounded-full overflow-hidden">
                                <div
                                    className={cn("h-full transition-all duration-1000",
                                        zone.riskLevel === 'High' ? "bg-red-500" :
                                            zone.riskLevel === 'Moderate' ? "bg-amber-500" : "bg-green-500"
                                    )}
                                    style={{ width: `${zone.probability}%` }}
                                />
                            </div>
                        </div>
                    </div>
                )
            })}
        </div>
    );
}
