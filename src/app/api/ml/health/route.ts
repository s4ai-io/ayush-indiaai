import { NextRequest, NextResponse } from 'next/server';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
    try {
        // Forward request to Python backend
        const response = await fetch(`${PYTHON_BACKEND_URL}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Handle backend errors
        if (!response.ok) {
            return NextResponse.json(
                {
                    status: 'unhealthy',
                    models_loaded: false,
                    version: '1.0.0',
                    error: 'Backend health check failed'
                },
                { status: response.status }
            );
        }

        // Return successful response
        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('API Error (health):', error);

        // Backend is unreachable
        return NextResponse.json(
            {
                status: 'unhealthy',
                models_loaded: false,
                version: '1.0.0',
                error: 'Python backend is not running',
                details: 'Run: cd backend && uvicorn main:app --reload --port 8000'
            },
            { status: 503 }
        );
    }
}
