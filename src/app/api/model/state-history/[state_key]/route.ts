import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(
    _request: NextRequest,
    { params }: { params: Promise<{ state_key: string }> }
) {
    try {
        const { state_key } = await params;

        const response = await fetch(
            `${PYTHON_BACKEND_URL}/api/model/state-history/${encodeURIComponent(state_key)}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'State history service error' }));
            return NextResponse.json(
                { error: errorData.detail || 'Failed to get state history' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('API Error (state-history):', error);
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                { error: 'ML service is currently unavailable.', details: 'Run: cd backend && uvicorn main:app --reload --port 8000' },
                { status: 503 }
            );
        }
        return NextResponse.json({ error: 'Failed to process request' }, { status: 500 });
    }
}
