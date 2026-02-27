"use client";

import { useState, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface VoiceInputButtonProps {
    onTranscript: (text: string) => void;
    onError?: (error: string) => void;
    language?: string;
}

// Maps browser locale / ISO-639-1 codes → IndicTrans2 src_lang codes
// Used to check if translation is needed (i.e. language is not English)
const INDIC_LANG_CODES = new Set([
    "hi", "gu", "mr", "ta", "te", "bn", "pa", "kn", "ml", "ur",
    "as", "or", "ne", "sa", "sd", "mai", "kok", "doi", "brx", "ks", "mni", "sat",
]);

function needsTranslation(language: string): boolean {
    const base = language.split("-")[0].toLowerCase();
    return INDIC_LANG_CODES.has(base);
}

export function VoiceInputButton({ onTranscript, onError, language = 'hi' }: VoiceInputButtonProps) {
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [statusLabel, setStatusLabel] = useState<string | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<BlobPart[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                setIsProcessing(true);
                // Stop all tracks to release the microphone
                stream.getTracks().forEach(track => track.stop());

                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

                try {
                    // ─── Step 1: Transcribe ───────────────────────────────────────
                    setStatusLabel('Transcribing...');
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.webm');
                    if (language) {
                        formData.append('language', language);
                    }

                    const transcribeRes = await fetch('/api/transcribe', {
                        method: 'POST',
                        body: formData,
                    });

                    if (!transcribeRes.ok) {
                        throw new Error(`Transcription error: ${transcribeRes.statusText}`);
                    }

                    const transcribeData = await transcribeRes.json();
                    if (!transcribeData?.text) {
                        throw new Error('No transcription received');
                    }

                    const transcript: string = transcribeData.text;

                    // ─── Step 2: Translate (only if not English) ──────────────────
                    if (language && needsTranslation(language)) {
                        setStatusLabel('Translating...');
                        const translateRes = await fetch('/api/translate', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ text: transcript, src_lang: language }),
                        });

                        if (!translateRes.ok) {
                            // Translation failed — fall back to raw transcript so the user isn't blocked
                            console.warn('Translation failed, falling back to raw transcript');
                            onTranscript(transcript);
                            return;
                        }

                        const translateData = await translateRes.json();
                        const englishText: string = translateData?.translated_text || transcript;
                        onTranscript(englishText);
                    } else {
                        // English audio — no translation needed
                        onTranscript(transcript);
                    }

                } catch (error: any) {
                    console.error('Voice pipeline error:', error);
                    if (onError) {
                        onError(error.message || 'Failed to process voice input.');
                    }
                } finally {
                    setIsProcessing(false);
                    setStatusLabel(null);
                }
            };

            mediaRecorder.start();
            setIsListening(true);
        } catch (error: any) {
            console.error('Microphone access denied or error:', error);
            if (onError) {
                onError('Microphone access denied. Please allow microphone permissions.');
            }
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isListening) {
            mediaRecorderRef.current.stop();
            setIsListening(false);
        }
    };

    const toggleListening = () => {
        if (isProcessing) return;
        if (isListening) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    return (
        <div className="relative flex flex-col items-center">
            <button
                onClick={toggleListening}
                disabled={isProcessing}
                className={`
          voice-input-button
          flex items-center justify-center
          w-10 h-10 rounded-full
          transition-all duration-300
          ${isListening
                        ? 'bg-red-500/20 border-2 border-red-500 text-red-500 voice-input-recording'
                        : isProcessing
                            ? 'bg-yellow-500/20 border-2 border-yellow-500 text-yellow-500 cursor-not-allowed opacity-70'
                            : 'bg-neon-purple/20 border-2 border-neon-purple/50 text-neon-purple hover:bg-neon-purple/30 hover:border-neon-purple'
                    }
          active:scale-95
        `}
                title={isListening ? 'Stop recording' : isProcessing ? (statusLabel ?? 'Processing...') : 'Start voice input'}
                type="button"
            >
                {isProcessing ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                ) : isListening ? (
                    <MicOff className="w-5 h-5 animate-pulse" />
                ) : (
                    <Mic className="w-5 h-5" />
                )}
            </button>

            {/* Status label shown under the button while processing */}
            {isProcessing && statusLabel && (
                <span className="absolute -bottom-5 text-[10px] font-medium text-yellow-600 whitespace-nowrap">
                    {statusLabel}
                </span>
            )}
        </div>
    );
}
