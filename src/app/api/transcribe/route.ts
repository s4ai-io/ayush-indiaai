import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
    try {
        const formData = await req.formData();
        const audioFile = formData.get('audio') as File | null;
        const language = formData.get('language') as string | null;

        if (!audioFile) {
            return NextResponse.json({ error: 'No audio file provided' }, { status: 400 });
        }

        const modalUrl = process.env.NEXT_PUBLIC_MODAL_ASR_URL || process.env.MODAL_ASR_URL;

        if (!modalUrl) {
            console.error('MODAL_ASR_URL is not defined in environment variables');
            return NextResponse.json(
                { error: 'ASR Service is not configured properly.' },
                { status: 500 }
            );
        }

        // Forward the audio file to the Modal.com backend
        const backendFormData = new FormData();
        backendFormData.append('audio', audioFile, audioFile.name || 'audio.webm');

        if (language) {
            backendFormData.append('language', language);
        }

        const response = await fetch(modalUrl, {
            method: 'POST',
            body: backendFormData,
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Modal API Error:', errorText);
            return NextResponse.json(
                { error: `Modal API Error: ${response.statusText}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error('Error in /api/transcribe:', error);
        return NextResponse.json(
            { error: 'Internal server error processing audio' },
            { status: 500 }
        );
    }
}
