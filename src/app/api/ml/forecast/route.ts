import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        // Get query parameters
        const searchParams = request.nextUrl.searchParams;
        const disease = searchParams.get('disease');
        const months = searchParams.get('months') || '3';

        // Build query string
        const params = new URLSearchParams();
        if (disease) params.append('disease', disease);
        params.append('months', months);

        // Forward request to Python backend
        const response = await fetch(
            `${PYTHON_BACKEND_URL}/api/forecast?${params.toString()}`,
            {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        );

        // Handle backend errors
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                detail: 'Forecast service error',
            }));

            return NextResponse.json(
                { error: errorData.detail || 'Failed to get forecast' },
                { status: response.status }
            );
        }

        // Return successful response
        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('API Error (forecast):', error);

        // Check if backend is unreachable
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return NextResponse.json(
                {
                    error: 'Forecast service is currently unavailable. Please ensure the Python backend is running.',
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
