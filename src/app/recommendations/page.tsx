import { ConsultationForm } from "@/components/forms/ConsultationForm";

export default function RecommendationsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Personalized Consultation</h2>
                <p className="text-muted-foreground">AI-driven holistic health recommendations based on AYUSH principles.</p>
            </div>

            <ConsultationForm />
        </div>
    );
}
