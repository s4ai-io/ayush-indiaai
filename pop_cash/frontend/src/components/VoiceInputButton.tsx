"use client";

import { useState, useRef } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
  language?: string;
}

export function VoiceInputButton({ onTranscript, onError, language = 'hi' }: VoiceInputButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
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
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          if (language) {
            formData.append('language', language);
          }

          const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
          }

          const data = await response.json();
          if (data && data.text) {
            onTranscript(data.text);
          } else {
            throw new Error('No transcription received');
          }
        } catch (error: any) {
          console.error('Transcription error:', error);
          if (onError) {
            onError(error.message || 'Failed to transcribe audio.');
          }
        } finally {
          setIsProcessing(false);
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
    if (isProcessing) return; // Don't allow toggling while processing

    if (isListening) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
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
      title={isListening ? 'Stop recording' : isProcessing ? 'Processing...' : 'Start voice input'}
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
  );
}
