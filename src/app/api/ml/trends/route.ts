import { NextRequest, NextResponse } from 'next/server';
import { authHeaders } from '@/lib/server/backend';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        // Forward request to Python backend
        const response = await fetch(`${PYTHON_BACKEND_URL}/api/trends`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(await authHeaders()),
            },
        });

        // Handle backend errors
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                detail: 'Trends service error',
            }));

            return NextResponse.json(
                { error: errorData.detail || 'Failed to get trends' },
                { status: response.status }
            );
        }

        // Return successful response
        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('API Error (trends):', error);

        // Check if backend is unreachable
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                {
                    error: 'Trends service is currently unavailable. Please ensure the Python backend is running.',
                    details: 'Run: cd backend && uvicorn main:app --reload --port 8000'
                },
                { status: 503 }
            );
        }

        return NextResponse.json(
            { error: 'Failed to process request' },
            { status: 500 }
        );
    }
}
