"use client";

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';

interface VoiceInputButtonProps {
    onTranscript: (text: string) => void;
    onError?: (error: string) => void;
    onStateChange?: (isListening: boolean) => void;
}

export function VoiceInputButton({ onTranscript, onError, onStateChange }: VoiceInputButtonProps) {
    const [isListening, setIsListening] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const [permissionState, setPermissionState] = useState<PermissionState | 'unknown'>('unknown');
    const recognitionRef = useRef<any>(null);
    const transcriptRef = useRef<string>('');
    const isRecognitionActiveRef = useRef<boolean>(false);

    useEffect(() => {
        if (onStateChange) {
            onStateChange(isListening);
        }
    }, [isListening, onStateChange]);

    useEffect(() => {
        // Check if browser supports Speech Recognition
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

        if (SpeechRecognition) {
            setIsSupported(true);

            // Initialize speech recognition
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                console.log('Speech recognition started');
                isRecognitionActiveRef.current = true;
                setIsListening(true);
            };

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
                    onTranscript(finalTranscript);
                }
            };

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

                if (onError) onError(errorMessage);
                if (event.error !== 'no-speech') {
                    stopListening();
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
            navigator.permissions.query({ name: 'microphone' as any }).then((permissionStatus) => {
                setPermissionState(permissionStatus.state);
                permissionStatus.onchange = () => {
                    setPermissionState(permissionStatus.state);
                };
            });
        }

        return () => {
            if (recognitionRef.current) {
                try { recognitionRef.current.stop(); } catch (e) { }
            }
        };
    }, [onTranscript, onError]);

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
            recognitionRef.current.start();
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
