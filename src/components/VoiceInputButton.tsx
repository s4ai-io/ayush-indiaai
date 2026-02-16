"use client";

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';

interface VoiceInputButtonProps {
    onTranscript: (text: string) => void;
    onError?: (error: string) => void;
    onStateChange?: (isListening: boolean) => void;
    language?: string;
}

export function VoiceInputButton({ onTranscript, onError, onStateChange, language = 'en-US' }: VoiceInputButtonProps) {
    const [isListening, setIsListening] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const [permissionState, setPermissionState] = useState<PermissionState | 'unknown'>('unknown');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null);
    const transcriptRef = useRef<string>('');
    const isRecognitionActiveRef = useRef<boolean>(false);

    useEffect(() => {
        if (onStateChange) {
            onStateChange(isListening);
        }
    }, [isListening, onStateChange]);

    useEffect(() => {
        // Update language on the fly if recognition is inactive, 
        // or just let the next startListening pick it up.
        if (recognitionRef.current) {
            recognitionRef.current.lang = language;
        }
    }, [language]);

    // Use refs to keep latest callbacks without triggering re-effects
    const onTranscriptRef = useRef(onTranscript);
    const onErrorRef = useRef(onError);

    useEffect(() => {
        onTranscriptRef.current = onTranscript;
        onErrorRef.current = onError;
    }, [onTranscript, onError]);

    useEffect(() => {
        // Check if browser supports Speech Recognition
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

        if (SpeechRecognition) {
            setIsSupported(true);

            // Initialize speech recognition
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = language;

            recognition.onstart = () => {
                console.log('Speech recognition started');
                isRecognitionActiveRef.current = true;
                setIsListening(true);
            };

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            recognition.onresult = (event: any) => {
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    }
                }

                // Update the accumulated transcript
                if (finalTranscript) {
                    transcriptRef.current += finalTranscript;
                    // Send immediately for better responsiveness
                    if (onTranscriptRef.current) {
                        onTranscriptRef.current(finalTranscript);
                    }
                }
            };

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            recognition.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);

                let errorMessage = 'Voice input error occurred';

                switch (event.error) {
                    case 'not-allowed':
                    case 'permission-denied':
                        errorMessage = 'Microphone permission denied. Please allow access in settings.';
                        setPermissionState('denied');
                        break;
                    case 'no-speech':
                        return; // Ignore no-speech errors to keep listening
                    case 'network':
                        errorMessage = 'Network error. Check connection.';
                        break;
                    case 'aborted':
                        isRecognitionActiveRef.current = false;
                        return;
                }

                if (onErrorRef.current) onErrorRef.current(errorMessage);
                if (event.error !== 'no-speech') {
                    try { recognition.stop(); } catch (e) { /* ignore */ }
                }
            };

            recognition.onend = () => {
                console.log('Speech recognition ended');
                isRecognitionActiveRef.current = false;
                setIsListening(false);
            };

            recognitionRef.current = recognition;
        } else {
            setIsSupported(false);
        }

        // Check permission status if API is available
        if (navigator.permissions && navigator.permissions.query) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            navigator.permissions.query({ name: 'microphone' as any }).then((permissionStatus) => {
                setPermissionState(permissionStatus.state);
                permissionStatus.onchange = () => {
                    setPermissionState(permissionStatus.state);
                };
            });
        }

        return () => {
            if (recognitionRef.current) {
                try { recognitionRef.current.stop(); } catch (e) { /* ignore */ }
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty dependency array to init once!

    const requestMicrophoneAccess = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Close immediately
            return true;
        } catch (err) {
            console.error("Microphone access denied:", err);
            if (onError) onError("Microphone access is required to use voice input.");
            return false;
        }
    };

    const startListening = async () => {
        // Explicit permission check/request
        if (permissionState === 'denied') {
            if (onError) onError("Microphone permission is blocked. Please enable it in browser settings.");
            return;
        }

        if (permissionState === 'prompt' || permissionState === 'unknown') {
            const granted = await requestMicrophoneAccess();
            if (!granted) return;
        }

        try {
            transcriptRef.current = '';
            // Ensure language is set before starting
            if (recognitionRef.current) {
                recognitionRef.current.lang = language;
            }
            recognitionRef.current.start();
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (e: any) {
            console.error('Error starting recognition:', e);
        }
    };

    const stopListening = () => {
        try {
            recognitionRef.current.stop();
        } catch (e) {
            console.error('Error stopping recognition:', e);
        }
    };

    const toggleListening = async () => {
        if (!recognitionRef.current) return;

        if (isListening) {
            stopListening();
        } else {
            await startListening();
        }
    };

    if (!isSupported) return null;

    return (
        <button
            onClick={toggleListening}
            className={`
        relative z-[100] flex items-center justify-center
        w-12 h-12 rounded-full shadow-lg transition-all duration-300
        ${isListening
                    ? 'bg-red-500 text-white animate-pulse shadow-red-500/50'
                    : 'bg-[#00A9B4] text-white hover:bg-[#008f99] shadow-[#00A9B4]/30 hover:scale-105'
                }
      `}
            title={isListening ? 'Stop recording' : 'Start voice input'}
            type="button"
        >
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>
    );
}
