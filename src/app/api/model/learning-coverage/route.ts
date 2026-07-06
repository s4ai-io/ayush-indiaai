import { NextResponse } from 'next/server';
import { authHeaders } from '@/lib/server/backend';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET() {
    try {
        const response = await fetch(
            `${PYTHON_BACKEND_URL}/api/model/learning-coverage`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Learning coverage service error' }));
            return NextResponse.json(
                { error: errorData.detail || 'Failed to get learning coverage' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('API Error (learning-coverage):', error);
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                { error: 'ML service is currently unavailable.', details: 'Run: cd backend && uvicorn main:app --reload --port 8000' },
                { status: 503 }
            );
        }
        return NextResponse.json({ error: 'Failed to process request' }, { status: 500 });
    }
}
