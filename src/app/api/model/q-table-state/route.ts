import { NextRequest, NextResponse } from 'next/server';
import { authHeaders } from '@/lib/server/backend';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const params = new URLSearchParams();

        const namc_code = searchParams.get('namc_code');
        const prakriti = searchParams.get('prakriti');
        const vikriti = searchParams.get('vikriti');
        const demo_session = searchParams.get('demo_session');

        if (namc_code) params.append('namc_code', namc_code);
        if (prakriti) params.append('prakriti', prakriti);
        if (vikriti) params.append('vikriti', vikriti);
        if (demo_session) params.append('demo_session', demo_session);

        const response = await fetch(
            `${PYTHON_BACKEND_URL}/api/model/q-table-state?${params.toString()}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Q-table state service error' }));
            return NextResponse.json(
                { error: errorData.detail || 'Failed to get Q-table state' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('API Error (q-table-state):', error);
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                { error: 'ML service is currently unavailable.', details: 'Run: cd backend && uvicorn main:app --reload --port 8000' },
                { status: 503 }
            );
        }
        return NextResponse.json({ error: 'Failed to process request' }, { status: 500 });
    }
}
