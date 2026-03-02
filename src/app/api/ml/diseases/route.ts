import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const q = searchParams.get('q') || '';

        const url = q
            ? `${PYTHON_BACKEND_URL}/api/diseases?q=${encodeURIComponent(q)}`
            : `${PYTHON_BACKEND_URL}/api/diseases`;

        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Failed to fetch diseases' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('API Error (diseases):', error);

        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                { error: 'ML service unavailable', diseases: [] },
                { status: 503 }
            );
        }

        return NextResponse.json(
            { error: 'Failed to fetch diseases', diseases: [] },
            { status: 500 }
        );
    }
}
