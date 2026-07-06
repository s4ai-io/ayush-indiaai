import { NextRequest, NextResponse } from 'next/server';
import { authHeaders } from '@/lib/server/backend';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const response = await fetch(`${PYTHON_BACKEND_URL}/api/ml/demo-submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
            body: JSON.stringify(body),
        });
        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error) {
        console.error('demo-submit error:', error);
        return NextResponse.json({ error: 'Failed to submit demo prescription' }, { status: 500 });
    }
}
