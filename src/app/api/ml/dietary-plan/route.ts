import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const disease = searchParams.get('disease') || '';
        const prakriti = searchParams.get('prakriti') || '';

        if (!disease || !prakriti) {
            return NextResponse.json({ dietary_plan: null, disease_matched: null, prakriti });
        }

        const response = await fetch(
            `${PYTHON_BACKEND_URL}/api/dietary-plan?disease=${encodeURIComponent(disease)}&prakriti=${encodeURIComponent(prakriti)}`
        );

        if (!response.ok) {
            return NextResponse.json({ dietary_plan: null, disease_matched: null, prakriti }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('API Error (dietary-plan):', error);
        return NextResponse.json({ dietary_plan: null, disease_matched: null, prakriti: '' }, { status: 500 });
    }
}
