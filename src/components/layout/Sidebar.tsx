"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, TrendingUp, Activity, HeartPulse } from "lucide-react";

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
            <nav className="flex-1 space-y-2">
                {navItems.map((item) => {
                    const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                                isActive ? "bg-white/20 font-medium" : "hover:bg-white/10"
                            )}
                        >
                            <item.icon className="h-5 w-5" />
                            <span>{item.name}</span>
                        </Link>
                    );
                })}
            </nav>
            <div className="p-4 bg-white/10 rounded-lg mt-auto">
                <p className="text-xs text-center opacity-70">© 2026 Ministry of AYUSH POC</p>
            </div>
        </div>
    );
}
