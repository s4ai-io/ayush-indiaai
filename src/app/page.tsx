'use client';

import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { UserPlus, Stethoscope, ArrowRight, ShieldAlert, type LucideIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/layout/AuthProvider";
import type { Role } from "@/lib/auth/roles";

interface RoleCard {
    title: string;
    description: string;
    body: string;
    href: string;
    cta: string;
    icon: LucideIcon;
    accent: { border: string; iconBg: string; iconText: string; button: string };
    roles: Role[];
}

const ROLE_CARDS: RoleCard[] = [
    {
        title: "Reception Desk",
        description: "Patient Registration & Triage",
        body: "Register new patients using voice-enabled forms and manage the daily patient queue.",
        href: "/registration",
        cta: "Enter Reception",
        icon: UserPlus,
        accent: {
            border: "border-t-blue-500",
            iconBg: "bg-blue-100",
            iconText: "text-blue-600",
            button: "bg-blue-600 hover:bg-blue-700",
        },
        roles: ["receptionist", "admin"],
    },
    {
        title: "Doctor's Cabin",
        description: "Clinical Diagnosis & Treatment",
        body: "Diagnose patients, generate AI-driven Ayurvedic treatment plans, and provide feedback.",
        href: "/doctor",
        cta: "Start Consultation",
        icon: Stethoscope,
        accent: {
            border: "border-t-purple-500",
            iconBg: "bg-purple-100",
            iconText: "text-purple-600",
            button: "bg-purple-600 hover:bg-purple-700",
        },
        roles: ["doctor", "admin"],
    },
    {
        title: "Command Center",
        description: "Public Health Intelligence",
        body: "Monitor disease outbreaks, risk forecasts, and epidemiological trends in real-time.",
        href: "/public-health/dashboard",
        cta: "View Analytics",
        icon: ShieldAlert,
        accent: {
            border: "border-t-amber-500",
            iconBg: "bg-amber-100",
            iconText: "text-amber-600",
            button: "bg-amber-600 hover:bg-amber-700",
        },
        roles: ["admin"],
    },
];

export default function LandingPage() {
    const { user } = useAuth();
    const cards = ROLE_CARDS.filter((card) => user && card.roles.includes(user.role));

    return (
        <div className="space-y-8 max-w-5xl mx-auto py-12">
            <div className="text-center space-y-4 mb-12">
                <h1 className="text-4xl font-bold tracking-tight text-slate-900">
                    Welcome{user ? `, ${user.name}` : ""} to Ayush AI
                </h1>
                <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                    Intelligent Healthcare System integrating Traditional Knowledge with Modern AI throughout the patient journey.
                </p>
            </div>

            <div className={`grid gap-8 ${cards.length >= 3 ? "md:grid-cols-3" : cards.length === 2 ? "md:grid-cols-2 max-w-3xl mx-auto" : "max-w-md mx-auto"}`}>
                {cards.map(({ title, description, body, href, cta, icon: Icon, accent }) => (
                    <Card key={href} className={`hover:shadow-lg transition-shadow border-t-4 ${accent.border}`}>
                        <CardHeader>
                            <div className={`w-12 h-12 ${accent.iconBg} rounded-lg flex items-center justify-center mb-4 ${accent.iconText}`}>
                                <Icon className="h-6 w-6" />
                            </div>
                            <CardTitle className="text-xl">{title}</CardTitle>
                            <CardDescription>{description}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-sm text-slate-500 min-h-[60px]">{body}</p>
                            <Link href={href} className="block">
                                <Button className={`w-full ${accent.button}`}>
                                    {cta}
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="mt-16 text-center text-sm text-slate-400">
                <p>Workflows shown match your access level{user ? ` (${user.role})` : ""}.</p>
            </div>
        </div>
    );
}
