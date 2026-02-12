"use client";

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';

interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;
  onError?: (error: string) => void;
}

export function VoiceInputButton({ onTranscript, onError }: VoiceInputButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<any>(null);
  const transcriptRef = useRef<string>('');
  const isRecognitionActiveRef = useRef<boolean>(false);

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
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }
        
        // Update the accumulated transcript
        if (finalTranscript) {
          transcriptRef.current += finalTranscript;
        }
      };
      
      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        
        let errorMessage = 'Voice input error occurred';
        
        switch (event.error) {
          case 'not-allowed':
          case 'permission-denied':
            errorMessage = 'Microphone permission denied. Please allow microphone access in your browser settings.';
            break;
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            break;
          case 'network':
            errorMessage = 'Network error occurred. Please check your connection.';
            break;
          case 'aborted':
            // User stopped recording, not an error
            isRecognitionActiveRef.current = false;
            return;
        }
        
        if (onError) {
          onError(errorMessage);
        }
        
        isRecognitionActiveRef.current = false;
        setIsListening(false);
        transcriptRef.current = '';
      };
      
      recognition.onend = () => {
        console.log('Speech recognition ended');
        isRecognitionActiveRef.current = false;
        
        // If we have accumulated transcript, send it
        if (transcriptRef.current.trim()) {
          onTranscript(transcriptRef.current.trim());
          transcriptRef.current = '';
        }
        setIsListening(false);
      };
      
      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
      console.warn('Speech Recognition API is not supported in this browser');
    }
    
    // Cleanup
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore errors during cleanup
        }
      }
    };
  }, [onTranscript, onError]);

  const toggleListening = async () => {
    if (!recognitionRef.current) return;
    
    if (isListening || isRecognitionActiveRef.current) {
      // Stop listening
      console.log('Stopping speech recognition...');
      try {
        recognitionRef.current.stop();
        // State will be updated in onend event
      } catch (e) {
        console.error('Error stopping recognition:', e);
        isRecognitionActiveRef.current = false;
        setIsListening(false);
      }
    } else {
      // Start listening
      console.log('Starting speech recognition...');
      try {
        transcriptRef.current = ''; // Reset transcript
        recognitionRef.current.start();
        // State will be updated in onstart event
      } catch (e: any) {
        console.error('Error starting recognition:', e);
        
        if (e.message && e.message.includes('already started')) {
          // Recognition is already running, stop it first
          console.log('Recognition already started, stopping first...');
          try {
            recognitionRef.current.stop();
          } catch (stopError) {
            console.error('Error stopping already-started recognition:', stopError);
          }
        } else {
          if (onError) {
            onError('Failed to start voice input. Please try again.');
          }
          isRecognitionActiveRef.current = false;
          setIsListening(false);
        }
      }
    }
  };

  // Don't render if not supported
  if (!isSupported) {
    return null;
  }

  return (
    <button
      onClick={toggleListening}
      className={`
        voice-input-button
        flex items-center justify-center
        w-10 h-10 rounded-full
        transition-all duration-300
        ${isListening 
          ? 'bg-red-500/20 border-2 border-red-500 text-red-500 voice-input-recording' 
          : 'bg-neon-purple/20 border-2 border-neon-purple/50 text-neon-purple hover:bg-neon-purple/30 hover:border-neon-purple'
        }
        active:scale-95
      `}
      title={isListening ? 'Stop recording' : 'Start voice input'}
      type="button"
    >
      {isListening ? (
        <MicOff className="w-5 h-5" />
      ) : (
        <Mic className="w-5 h-5" />
      )}
    </button>
  );
}
