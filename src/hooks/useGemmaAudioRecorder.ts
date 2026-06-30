import { useState, useRef, useCallback, useEffect } from 'react';

const TARGET_SAMPLE_RATE = 16000;

interface AudioRecorderState {
  isRecording: boolean;
  error: string | null;
}

interface AudioRecorderOptions {
  onRecordingComplete?: (audio: Float32Array) => void;
}

/**
 * Hook for recording microphone audio and producing a 16kHz mono Float32Array
 * suitable for Gemma-4's audio input. Used only by the Local (on-device) voice
 * pipeline mode — the Cloud mode keeps using MediaRecorder/webm in VoiceInputButton.
 */
export function useGemmaAudioRecorder(options?: AudioRecorderOptions) {
  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    error: null,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);

  const onRecordingCompleteRef = useRef(options?.onRecordingComplete);
  useEffect(() => {
    onRecordingCompleteRef.current = options?.onRecordingComplete;
  }, [options?.onRecordingComplete]);

  /**
   * Start recording from the microphone.
   * Returns a Promise that resolves when recording has successfully started.
   */
  const startRecording = useCallback((): Promise<void> => {
    return new Promise(async (resolve, reject) => {
      try {
        setState({ isRecording: true, error: null });

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: TARGET_SAMPLE_RATE,
          },
        });
        streamRef.current = stream;

        const audioContext = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
        audioContextRef.current = audioContext;

        await audioContext.audioWorklet.addModule('/audio-processor.js');

        const source = audioContext.createMediaStreamSource(stream);
        const workletNode = new AudioWorkletNode(audioContext, 'audio-capture-processor');
        workletNodeRef.current = workletNode;

        workletNode.port.onmessage = (event) => {
          if (event.data.type === 'complete') {
            const audio = event.data.audio as Float32Array;

            // Clean up here, AFTER receiving audio, so the context stays alive
            // long enough for the worklet's postMessage to be delivered.
            if (streamRef.current) {
              streamRef.current.getTracks().forEach((track) => track.stop());
              streamRef.current = null;
            }
            if (audioContextRef.current) {
              audioContextRef.current.close().catch(() => {});
              audioContextRef.current = null;
            }
            workletNodeRef.current = null;

            if (onRecordingCompleteRef.current) {
              onRecordingCompleteRef.current(audio);
            }
          }
        };

        source.connect(workletNode);
        // Don't connect to destination — we don't want playback of mic input

        resolve();
      } catch (err: any) {
        const errorMsg = err.name === 'NotAllowedError'
          ? 'Microphone access denied. Please allow microphone permissions.'
          : err.message || 'Failed to start recording.';
        setState({ isRecording: false, error: errorMsg });
        reject(new Error(errorMsg));
      }
    });
  }, []);

  /**
   * Stop recording and trigger the worklet to flush accumulated audio data.
   * Actual cleanup of the stream and AudioContext happens in the onmessage
   * handler once the 'complete' payload arrives, so the context stays alive
   * long enough to deliver that message.
   */
  const stopRecording = useCallback(() => {
    if (workletNodeRef.current) {
      // Signal the worklet; cleanup runs in onmessage after audio arrives.
      workletNodeRef.current.port.postMessage('stop');
    } else {
      // No worklet — tear down whatever is left directly.
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
    }
    setState({ isRecording: false, error: null });
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return {
    isRecording: state.isRecording,
    error: state.error,
    startRecording,
    stopRecording,
    clearError,
  };
}
