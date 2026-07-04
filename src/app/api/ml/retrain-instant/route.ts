import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        const response = await fetch(`${PYTHON_BACKEND_URL}/api/ml/retrain-instant`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Retrain service error' }));
            return NextResponse.json(
                { error: errorData.detail || 'Failed to retrain' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('API Error (retrain-instant):', error);
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                { error: 'ML service is currently unavailable.', details: 'Run: cd backend && uvicorn main:app --reload --port 8000' },
                { status: 503 }
            );
        }
        return NextResponse.json({ error: 'Failed to process request' }, { status: 500 });
    }
}
