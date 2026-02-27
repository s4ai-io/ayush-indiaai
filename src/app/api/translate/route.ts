import { NextRequest, NextResponse } from 'next/server';
import { logInteractionToTxt } from '@/lib/logger';

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { text, src_lang } = body;

        if (!text || !text.trim()) {
            return NextResponse.json({ error: 'No text provided for translation' }, { status: 400 });
        }

        if (!src_lang) {
            return NextResponse.json({ error: 'No source language provided' }, { status: 400 });
        }

        const modalUrl = process.env.NEXT_PUBLIC_MODAL_TRANSLATE_URL || process.env.MODAL_TRANSLATE_URL;

        if (!modalUrl) {
            console.error('MODAL_TRANSLATE_URL is not defined in environment variables');
            return NextResponse.json(
                { error: 'Translation service is not configured properly.' },
                { status: 500 }
            );
        }

        // Forward to the Modal.com IndicTrans2 backend
        const response = await fetch(modalUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, src_lang }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Modal Translation API Error:', errorText);
            logInteractionToTxt(
                'Translation (Modal)',
                `Source: ${src_lang}\nText: ${text}`,
                undefined,
                `Modal API Error: ${response.statusText}\n${errorText}`
            );
            return NextResponse.json(
                { error: `Translation API Error: ${response.statusText}` },
                { status: response.status }
            );
        }

        const data = await response.json();
        logInteractionToTxt(
            'Translation (Modal)',
            `Source: ${src_lang}\nText: ${text}`,
            JSON.stringify(data, null, 2)
        );
        return NextResponse.json(data);

    } catch (error: any) {
        console.error('Error in /api/translate:', error);
        let inputSummary = "Translation Request";
        try {
            const body = await req.clone().json();
            inputSummary = `Source: ${body?.src_lang}\nText: ${body?.text}`;
        } catch (_) { }
        logInteractionToTxt(
            'Translation (Modal)',
            inputSummary,
            undefined,
            error.message || String(error)
        );
        return NextResponse.json(
            { error: 'Internal server error during translation' },
            { status: 500 }
        );
    }
}
