"use client";
import logo from "./s4ailogo.png";
import Image from "next/image";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    LayoutDashboard, UserPlus, Stethoscope, Menu, X, Users, ShieldAlert,
    ChevronLeft, ChevronRight, type LucideIcon, BarChart2, BrainCircuit,
    UserCog, LogOut,
} from "lucide-react";
import { useAuth } from "@/components/layout/AuthProvider";
import { ALL_ROLES, type Role } from "@/lib/auth/roles";

interface NavItem {
    href: string;
    label: string;
    icon: LucideIcon;
    isActive: (pathname: string) => boolean;
    roles: Role[];
}

const NAV_SECTIONS: { label: string; items: NavItem[] }[] = [
    {
        label: "Overview",
        items: [
            { href: "/", label: "Dashboard", icon: LayoutDashboard, isActive: (p) => p === "/", roles: ALL_ROLES },
            { href: "/public-health/dashboard", label: "Analytics", icon: BarChart2, isActive: (p) => p.includes("/public-health"), roles: ["admin"] },
        ],
    },
    {
        label: "Reception",
        items: [
            { href: "/registration", label: "New Registration", icon: UserPlus, isActive: (p) => p === "/registration", roles: ["receptionist", "admin"] },
            { href: "/patients", label: "Patient Directory", icon: Users, isActive: (p) => p === "/patients", roles: ALL_ROLES },
        ],
    },
    {
        label: "Clinical",
        items: [
            { href: "/doctor", label: "Doctor Dashboard", icon: Stethoscope, isActive: (p) => p === "/doctor", roles: ["doctor", "admin"] },
        ],
    },
    {
        label: "Admin",
        items: [
            { href: "/admin/staff", label: "Staff Management", icon: UserCog, isActive: (p) => p === "/admin/staff", roles: ["admin"] },
            { href: "/admin/accuracy", label: "Accuracy Evaluator", icon: ShieldAlert, isActive: (p) => p === "/admin/accuracy", roles: ["admin"] },
            { href: "/admin/model-dashboard", label: "Model Intelligence", icon: BrainCircuit, isActive: (p) => p === "/admin/model-dashboard", roles: ["admin"] },
            { href: "/admin/analytics-models", label: "Analytics Models", icon: BarChart2, isActive: (p) => p === "/admin/analytics-models", roles: ["admin"] },
        ],
    },
];

export function AppSidebar() {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const [isCollapsed, setIsCollapsed] = useState(false);

    const toggleCollapsed = () => setIsCollapsed((prev) => !prev);

    // No session (or still loading) → no sidebar. This also hides it on /login.
    if (!user) return null;

    const visibleSections = NAV_SECTIONS
        .map((section) => ({
            ...section,
            items: section.items.filter((item) => item.roles.includes(user.role)),
        }))
        .filter((section) => section.items.length > 0);

    return (
        <>
            {/* Hamburger Menu Button — mobile/tablet only; desktop keeps the sidebar persistently visible */}
            <div
                className={cn(
                    "fixed top-4 left-4 z-50 md:hidden transition-all duration-200 ease-out",
                    isMobileOpen ? "opacity-0 scale-90 pointer-events-none" : "opacity-100 scale-100"
                )}
            >
                <Button
                    variant="outline"
                    size="icon"
                    className="bg-white shadow-md border-slate-200 text-slate-700 hover:bg-slate-100 hover:scale-105 active:scale-95 p-2 transition-transform duration-150"
                    onClick={() => setIsMobileOpen(true)}
                >
                    <Menu className="h-6 w-6" />
                    <span className="sr-only">Toggle Menu</span>
                </Button>
            </div>

            {/* Sidebar Overlay (Mobile) */}
            <div
                className={cn(
                    "fixed inset-0 bg-black/50 backdrop-blur-[2px] z-40 md:hidden transition-opacity duration-300 ease-in-out",
                    isMobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
                )}
                onClick={() => setIsMobileOpen(false)}
                aria-hidden="true"
            />

            {/* Sidebar Panel — fixed slide-in drawer on mobile, persistent collapsible column on desktop */}
            <div
                className={cn(
                    "fixed top-0 left-0 h-full bg-primary text-primary-foreground z-50 transition-[transform,width] duration-300 ease-in-out shadow-2xl flex flex-col w-72 shrink-0",
                    isMobileOpen ? "translate-x-0" : "-translate-x-full",
                    "md:sticky md:top-0 md:h-screen md:translate-x-0 md:z-30 md:shadow-none md:border-r md:border-white/10",
                    isCollapsed ? "md:w-20" : "md:w-72"
                )}
            >
                {/* Desktop collapse toggle */}
                <button
                    type="button"
                    onClick={toggleCollapsed}
                    title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    className="hidden md:flex absolute -right-3 top-8 w-6 h-6 rounded-full bg-primary border border-white/20 text-white items-center justify-center shadow-md hover:bg-primary/90 hover:scale-110 active:scale-95 transition-all duration-150 z-10"
                >
                    {isCollapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
                </button>

                {/* Header with Close Button */}
                <div className={cn("flex items-center p-6", isCollapsed ? "md:justify-center md:px-3" : "justify-between")}>

                    {/* Left side */}
                    <div className="flex items-center gap-3 min-w-0">

                        {/* Logo */}
                        <div className="w-10 h-10 relative shrink-0">
                            <Image
                                src={logo}
                                alt="S4AI"
                                fill
                                className="object-contain"
                            />
                        </div>

                        {/* Text */}
                        <div className={cn("min-w-0", isCollapsed && "md:hidden")}>
                            <h1 className="text-lg font-bold text-white truncate">ISHA Ayush</h1>
                            <p className="text-xs text-white/70 truncate">
                                S4AI Technologies LLP
                            </p>
                        </div>

                    </div>

                    {/* Close button — mobile drawer only */}
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-white hover:bg-white/20 md:hidden shrink-0"
                        onClick={() => setIsMobileOpen(false)}
                    >
                        <X className="h-6 w-6" />
                    </Button>

                </div>


                {/* Navigation Links */}
                <nav className="flex-1 space-y-8 overflow-y-auto overflow-x-hidden px-4 pb-8">
                    {visibleSections.map((section) => (
                        <div key={section.label} className="space-y-2">
                            <h2 className={cn(
                                "px-4 text-xs font-semibold text-white/50 uppercase tracking-wider mb-2 transition-opacity duration-150",
                                isCollapsed && "md:hidden"
                            )}>
                                {section.label}
                            </h2>
                            {section.items.map(({ href, label, icon: Icon, isActive }) => (
                                <Link
                                    key={href}
                                    href={href}
                                    onClick={() => setIsMobileOpen(false)}
                                    title={isCollapsed ? label : undefined}
                                    className={cn(
                                        "flex items-center gap-3 px-4 py-3 mx-2 rounded-xl transition-all duration-200 ease-out text-sm font-medium hover:translate-x-1",
                                        isCollapsed && "md:justify-center md:mx-0 md:px-0 md:hover:translate-x-0",
                                        isActive(pathname) ? "bg-white/20 text-white shadow-sm" : "text-white/80 hover:bg-white/10 hover:text-white"
                                    )}
                                >
                                    <Icon className="h-5 w-5 shrink-0" />
                                    <span className={cn(isCollapsed && "md:hidden")}>{label}</span>
                                </Link>
                            ))}
                        </div>
                    ))}
                </nav>

                {/* Footer — signed-in user + logout */}
                <div className={cn("p-6 mt-auto space-y-3", isCollapsed && "md:px-3")}>
                    <div className={cn(
                        "bg-white/10 rounded-xl flex items-center gap-3",
                        isCollapsed ? "md:p-2 md:justify-center p-3" : "p-3"
                    )}>
                        <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold shrink-0 uppercase">
                            {user.name.charAt(0)}
                        </div>
                        <div className={cn("min-w-0 flex-1", isCollapsed && "md:hidden")}>
                            <p className="text-sm font-medium text-white truncate">{user.name}</p>
                            <p className="text-[11px] text-white/60 capitalize truncate">{user.role}</p>
                        </div>
                        <button
                            type="button"
                            onClick={logout}
                            title="Sign out"
                            className={cn(
                                "text-white/60 hover:text-white hover:bg-white/10 rounded-lg p-1.5 transition-colors shrink-0",
                                isCollapsed && "md:hidden"
                            )}
                        >
                            <LogOut className="h-4 w-4" />
                            <span className="sr-only">Sign out</span>
                        </button>
                    </div>
                    <div className={cn("text-center", isCollapsed && "md:hidden")}>
                        <p className="text-[10px] text-white/50 font-medium">© 2026 Ministry of AYUSH POC</p>
                    </div>
                </div>
            </div>
        </>
    );
}
