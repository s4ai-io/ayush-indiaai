import { ConsultationForm } from "@/components/forms/ConsultationForm";

type Props = {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export default async function RecommendationsPage(props: Props) {
    const searchParams = await props.searchParams;
    const condition = typeof searchParams.condition === 'string' ? searchParams.condition : undefined;

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Personalized Consultation</h2>
                <p className="text-muted-foreground">AI-driven holistic health recommendations based on AYUSH principles.</p>
            </div>

            <ConsultationForm initialCondition={decodeURIComponent(condition || '') || undefined} />
        </div>
    );
}
