import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Activity, Users, UserPlus, Stethoscope, ArrowRight, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
    return (
        <div className="space-y-8 max-w-5xl mx-auto py-12">
            <div className="text-center space-y-4 mb-12">
                <h1 className="text-4xl font-bold tracking-tight text-slate-900">Welcome to Ayush AI</h1>
                <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                    Intelligent Healthcare System integrating Traditional Knowledge with Modern AI throughout the patient journey.
                </p>
            </div>

            <div className="grid gap-8 md:grid-cols-3">
                {/* Reception Role */}
                <Card className="hover:shadow-lg transition-shadow border-t-4 border-t-blue-500">
                    <CardHeader>
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 text-blue-600">
                            <UserPlus className="h-6 w-6" />
                        </div>
                        <CardTitle className="text-xl">Reception Desk</CardTitle>
                        <CardDescription>Patient Registration & Triage</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-slate-500 min-h-[60px]">
                            Register new patients using voice-enabled forms and manage the daily patient queue.
                        </p>
                        <Link href="/consultation" className="block">
                            <Button className="w-full bg-blue-600 hover:bg-blue-700">
                                Enter Reception
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>

                {/* Clinical Role */}
                <Card className="hover:shadow-lg transition-shadow border-t-4 border-t-purple-500">
                    <CardHeader>
                        <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 text-purple-600">
                            <Stethoscope className="h-6 w-6" />
                        </div>
                        <CardTitle className="text-xl">Doctor's Cabin</CardTitle>
                        <CardDescription>Clinical Diagnosis & Treatment</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-slate-500 min-h-[60px]">
                            Diagnose patients, generate AI-driven Ayurvedic treatment plans, and provide feedback.
                        </p>
                        <Link href="/doctor" className="block">
                            <Button className="w-full bg-purple-600 hover:bg-purple-700">
                                Start Consultation
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>

                {/* Public Health Role */}
                <Card className="hover:shadow-lg transition-shadow border-t-4 border-t-amber-500">
                    <CardHeader>
                        <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center mb-4 text-amber-600">
                            <ShieldAlert className="h-6 w-6" />
                        </div>
                        <CardTitle className="text-xl">Command Center</CardTitle>
                        <CardDescription>Public Health Intelligence</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-slate-500 min-h-[60px]">
                            Monitor disease outbreaks, risk forecasts, and epidemiological trends in real-time.
                        </p>
                        <Link href="/public-health/dashboard" className="block">
                            <Button className="w-full bg-amber-600 hover:bg-amber-700">
                                View Analytics
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>

            <div className="mt-16 text-center text-sm text-slate-400">
                <p>Select your role to access specific workflows.</p>
            </div>
        </div >
    );
}
