"use client";

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';

interface VoiceInputButtonProps {
    onTranscript: (text: string) => void;
    onError?: (error: string) => void;
    onStateChange?: (isListening: boolean) => void;
    onInterimTranscript?: (text: string) => void;  // NEW: live preview callback
    language?: string;
    isActive?: boolean;
}

export function VoiceInputButton({ onTranscript, onError, onStateChange, onInterimTranscript, language = 'en-US', isActive = true }: VoiceInputButtonProps) {
    const [isListening, setIsListening] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const [permissionState, setPermissionState] = useState<PermissionState | 'unknown'>('unknown');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null);
    const accumulatedTranscriptRef = useRef<string>(''); // Buffer for full session
    const isRecognitionActiveRef = useRef<boolean>(false);

    useEffect(() => {
        if (onStateChange) {
            onStateChange(isListening);
        }
    }, [isListening, onStateChange]);

    useEffect(() => {
        if (recognitionRef.current) {
            recognitionRef.current.lang = language;
        }
    }, [language]);

    // Force stop if component becomes inactive while listening
    useEffect(() => {
        if (!isActive && isListening) {
            if (recognitionRef.current) {
                try {
                    recognitionRef.current.stop();
                } catch (e) {
                    console.error('Error stopping recognition on inactive:', e);
                }
            }
            setIsListening(false);
        }
    }, [isActive, isListening]);

    // Use refs to keep latest callbacks without triggering re-effects
    const onTranscriptRef = useRef(onTranscript);
    const onErrorRef = useRef(onError);
    const onInterimTranscriptRef = useRef(onInterimTranscript);

    useEffect(() => {
        onTranscriptRef.current = onTranscript;
        onErrorRef.current = onError;
        onInterimTranscriptRef.current = onInterimTranscript;
    }, [onTranscript, onError, onInterimTranscript]);

    useEffect(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

        if (SpeechRecognition) {
            setIsSupported(true);

            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = language;

            recognition.onstart = () => {
                console.log('Speech recognition started');
                accumulatedTranscriptRef.current = '';  // Reset buffer on new session
                isRecognitionActiveRef.current = true;
                setIsListening(true);
            };

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            recognition.onresult = (event: any) => {
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        // Accumulate final results — do NOT send yet
                        accumulatedTranscriptRef.current += transcript + ' ';
                    } else {
                        // Build interim for live preview
                        interimTranscript += transcript;
                    }
                }

                // Live preview: show accumulated + current interim in input box
                const liveText = accumulatedTranscriptRef.current + interimTranscript;
                if (onInterimTranscriptRef.current && liveText.trim()) {
                    onInterimTranscriptRef.current(liveText.trim());
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
                        return;
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

                // Only NOW send the complete accumulated transcript
                const fullTranscript = accumulatedTranscriptRef.current.trim();
                if (fullTranscript && onTranscriptRef.current) {
                    onTranscriptRef.current(fullTranscript);
                }
                accumulatedTranscriptRef.current = '';
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
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (err) {
            console.error("Microphone access denied:", err);
            if (onError) onError("Microphone access is required to use voice input.");
            return false;
        }
    };

    const startListening = async () => {
        if (permissionState === 'denied') {
            if (onError) onError("Microphone permission is blocked. Please enable it in browser settings.");
            return;
        }

        if (permissionState === 'prompt' || permissionState === 'unknown') {
            const granted = await requestMicrophoneAccess();
            if (!granted) return;
        }

        try {
            accumulatedTranscriptRef.current = '';
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
            // onend will fire and send the full transcript
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
                flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200
                ${isListening
                    ? 'bg-destructive text-destructive-foreground animate-pulse'
                    : 'bg-transparent text-muted-foreground hover:bg-primary/10 hover:text-primary'
                }
            `}
            title={isListening ? 'Stop recording — will send full transcript' : 'Start voice input'}
            type="button"
        >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
    );
}
