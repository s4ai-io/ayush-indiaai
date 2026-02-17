"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, TrendingUp, Activity, HeartPulse, UserPlus, Stethoscope, Users } from "lucide-react";

const navItems = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Disease Trends", href: "/trends", icon: TrendingUp },
    { name: "Risk Forecast", href: "/forecasting", icon: Activity },
    { name: "Consultation", href: "/recommendations", icon: HeartPulse },
];

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();

    return (
        <div className={cn("flex flex-col h-full w-64 bg-primary text-primary-foreground p-4", className)}>
            <div className="mb-8 p-2">
                <h1 className="text-2xl font-bold">Ayush AI</h1>
                <p className="text-sm opacity-80">Intelligent Health System</p>
            </div>
            <nav className="flex-1 space-y-6 overflow-y-auto">
                {/* Reception */}
                <div className="space-y-1">
                    <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider">Reception</h2>
                    <Link href="/registration" className={cn("flex items-center gap-3 px-4 py-2 mx-2 rounded-lg transition-colors text-sm", pathname === "/registration" ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10")}>
                        <UserPlus className="h-4 w-4" />
                        <span>New Registration</span>
                    </Link>
                </div>

                {/* Clinical */}
                <div className="space-y-1">
                    <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider">Clinical</h2>
                    <Link href="/doctor" className={cn("flex items-center gap-3 px-4 py-2 mx-2 rounded-lg transition-colors text-sm", pathname === "/doctor" ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10")}>
                        <Stethoscope className="h-4 w-4" />
                        <span>Doctor Dashboard</span>
                    </Link>
                </div>

                {/* Intelligence */}
                <div className="space-y-1">
                    <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider">Public Health</h2>
                    <Link href="/public-health/dashboard" className={cn("flex items-center gap-3 px-4 py-2 mx-2 rounded-lg transition-colors text-sm", pathname.includes("/public-health") ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10")}>
                        <Activity className="h-4 w-4" />
                        <span>Outbreak Monitor</span>
                    </Link>
                    <Link href="/trends" className={cn("flex items-center gap-3 px-4 py-2 mx-2 rounded-lg transition-colors text-sm", pathname === "/trends" ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10")}>
                        <TrendingUp className="h-4 w-4" />
                        <span>Disease Trends</span>
                    </Link>
                    <Link href="/forecasting" className={cn("flex items-center gap-3 px-4 py-2 mx-2 rounded-lg transition-colors text-sm", pathname === "/forecasting" ? "bg-white/20 text-white" : "text-white/80 hover:bg-white/10")}>
                        <LayoutDashboard className="h-4 w-4" />
                        <span>Risk Forecast</span>
                    </Link>
                </div>
            </nav>
            <div className="p-4 bg-white/10 rounded-lg mt-auto">
                <p className="text-xs text-center opacity-70">© 2026 Ministry of AYUSH POC</p>
            </div>
        </div>
    );
}
