"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Activity, UserPlus, Stethoscope, Menu, X, Users, ShieldAlert } from "lucide-react";

export function AppSidebar() {
    const pathname = usePathname();
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <>
            {/* Hamburger Menu Button (Visible when collapsed) */}
            {!isExpanded && (
                <div className="fixed top-4 left-4 z-50">
                    <Button
                        variant="outline"
                        size="icon"
                        className="bg-white shadow-md border-slate-200 text-slate-700 hover:bg-slate-100 p-2"
                        onClick={() => setIsExpanded(true)}
                    >
                        <Menu className="h-6 w-6" />
                        <span className="sr-only">Toggle Menu</span>
                    </Button>
                </div>
            )}

            {/* Sidebar Overlay (Mobile) */}
            {isExpanded && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={() => setIsExpanded(false)}
                />
            )}

            {/* Sidebar Panel */}
            <div
                className={cn(
                    "fixed top-0 left-0 h-full bg-primary text-primary-foreground z-50 transition-transform duration-300 ease-in-out shadow-2xl flex flex-col w-72",
                    isExpanded ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Header with Close Button */}
                <div className="flex items-center justify-between p-6">
                    <div>
                        <h1 className="text-2xl font-bold">Ayush AI</h1>
                        <p className="text-sm opacity-80">Intelligent Health System</p>
                    </div>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-white hover:bg-white/20 hover:text-white"
                        onClick={() => setIsExpanded(false)}
                    >
                        <X className="h-6 w-6" />
                        <span className="sr-only">Close Menu</span>
                    </Button>
                </div>

                {/* Navigation Links */}
                <nav className="flex-1 space-y-8 overflow-y-auto px-4 pb-8">
                    {/* Reception */}
                    <div className="space-y-2">
                        <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Reception</h2>
                        <Link
                            href="/registration"
                            onClick={() => setIsExpanded(false)}
                            className={cn("flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-colors text-sm font-medium", pathname === "/registration" ? "bg-white/20 text-white shadow-sm" : "text-white/80 hover:bg-white/10 hover:text-white")}
                        >
                            <UserPlus className="h-5 w-5" />
                            <span>New Registration</span>
                        </Link>
                        <Link
                            href="/patients"
                            onClick={() => setIsExpanded(false)}
                            className={cn("flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-colors text-sm font-medium", pathname === "/patients" ? "bg-white/20 text-white shadow-sm" : "text-white/80 hover:bg-white/10 hover:text-white")}
                        >
                            <Users className="h-5 w-5" />
                            <span>Patient Directory</span>
                        </Link>
                    </div>

                    {/* Clinical */}
                    <div className="space-y-2">
                        <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Clinical</h2>
                        <Link
                            href="/doctor"
                            onClick={() => setIsExpanded(false)}
                            className={cn("flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-colors text-sm font-medium", pathname === "/doctor" ? "bg-white/20 text-white shadow-sm" : "text-white/80 hover:bg-white/10 hover:text-white")}
                        >
                            <Stethoscope className="h-5 w-5" />
                            <span>Doctor Dashboard</span>
                        </Link>
                    </div>

                    {/* Public Health */}
                    <div className="space-y-2">
                        <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Public Health</h2>
                        <Link
                            href="/public-health/dashboard"
                            onClick={() => setIsExpanded(false)}
                            className={cn("flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-colors text-sm font-medium", pathname.includes("/public-health") ? "bg-white/20 text-white shadow-sm" : "text-white/80 hover:bg-white/10 hover:text-white")}
                        >
                            <ShieldAlert className="h-5 w-5" />
                            <span>Dashboard</span>
                        </Link>
                    </div>

                    {/* Admin */}
                    <div className="space-y-2">
                        <h2 className="px-4 text-xs font-semibold text-white/50 uppercase tracking-wider mb-2">Admin</h2>
                        <Link
                            href="/admin/accuracy"
                            onClick={() => setIsExpanded(false)}
                            className={cn("flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-colors text-sm font-medium", pathname === "/admin/accuracy" ? "bg-white/20 text-white shadow-sm" : "text-white/80 hover:bg-white/10 hover:text-white")}
                        >
                            <LayoutDashboard className="h-5 w-5" />
                            <span>Accuracy Evaluator</span>
                        </Link>
                    </div>
                </nav>

                {/* Footer */}
                <div className="p-6 mt-auto">
                    <div className="bg-white/10 rounded-xl p-4 text-center">
                        <p className="text-xs text-white/70 font-medium">© 2026 Ministry of AYUSH POC</p>
                    </div>
                </div>
            </div>
        </>
    );
}
