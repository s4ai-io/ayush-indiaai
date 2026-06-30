import { useCallback, useEffect, useRef, useState } from 'react';
import { ModelManager } from '@/services/voiceModel/ModelManager';
import { ChatEngine } from '@/services/voiceModel/ChatEngine';
import { parseStructuredReply } from '@/services/voiceModel/extraction';
import { getSystemPrompt, VoiceFlow } from '@/services/voiceModel/prompts';
import { useGemmaAudioRecorder } from './useGemmaAudioRecorder';
import { ExtractionResult, Message, ModelState } from '@/types/voiceModel';

const DEFAULT_PARAMS = {
  temperature: 0.2,
  top_p: 0.9,
  top_k: 40,
  max_new_tokens: 256,
};

export type LocalVoiceAgentStatus = 'idle' | 'loading_model' | 'ready' | 'recording' | 'generating' | 'error';

interface UseLocalVoiceAgentOptions {
  /** Called after every turn that yields a non-null structured JSON block. */
  onExtracted?: (extracted: Record<string, unknown>) => void;
}

/**
 * Combines ModelManager (Gemma-4-E2B load, cached singleton), the 16kHz audio
 * recorder, and ChatEngine into one hook for the Local (on-device) voice
 * pipeline mode. The model is only loaded when `ensureModelLoaded()` is
 * called — selecting "Cloud" mode never touches this hook's model download.
 */
export function useLocalVoiceAgent(flow: VoiceFlow, options?: UseLocalVoiceAgentOptions) {
  const onExtractedRef = useRef(options?.onExtracted);
  useEffect(() => {
    onExtractedRef.current = options?.onExtracted;
  }, [options?.onExtracted]);

  const [modelState, setModelState] = useState<ModelState | null>(null);
  const [status, setStatus] = useState<LocalVoiceAgentStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingReply, setStreamingReply] = useState('');

  const modelManagerRef = useRef(ModelManager.getInstance());
  const chatEngineRef = useRef(ChatEngine.getInstance());
  const controlRef = useRef({ aborted: false });

  useEffect(() => {
    modelManagerRef.current.registerStateListener(setModelState);
  }, []);

  const ensureModelLoaded = useCallback(async () => {
    const current = modelManagerRef.current.getModelState();
    if (current.status === 'ready') {
      setStatus('ready');
      return;
    }
    setStatus('loading_model');
    setError(null);
    try {
      await modelManagerRef.current.loadModel();
      setStatus('ready');
    } catch (err: any) {
      setStatus('error');
      setError(err.message || 'Failed to load the on-device model.');
      throw err;
    }
  }, []);

  const runTurn = useCallback(
    async (userText: string, audioData?: Float32Array): Promise<ExtractionResult> => {
      await ensureModelLoaded();

      const history: Message[] = [
        { id: 'system', role: 'system', content: getSystemPrompt(flow), timestamp: 0 },
        ...messages,
        { id: `user-${Date.now()}`, role: 'user', content: userText, timestamp: Date.now() },
      ];

      setStatus('generating');
      setStreamingReply('');
      controlRef.current = { aborted: false };

      let fullText = '';
      const stats = await chatEngineRef.current.generate(
        history,
        DEFAULT_PARAMS,
        (token) => {
          fullText += token;
          setStreamingReply(fullText);
        },
        controlRef.current,
        audioData
      );

      const { reply, extracted } = parseStructuredReply(fullText);

      setMessages((prev) => [
        ...prev,
        { id: `user-${Date.now()}`, role: 'user', content: userText || '🎤 Voice message', timestamp: Date.now() },
        { id: `assistant-${Date.now()}`, role: 'assistant', content: reply, timestamp: Date.now() },
      ]);
      setStreamingReply('');
      setStatus('ready');

      if (extracted && onExtractedRef.current) {
        onExtractedRef.current(extracted as Record<string, unknown>);
      }

      return { reply, extracted, stats };
    },
    [ensureModelLoaded, flow, messages]
  );

  const sendAudioTurn = useCallback(
    (audioData: Float32Array, textPrompt = '') => runTurn(textPrompt, audioData),
    [runTurn]
  );

  const sendTextTurn = useCallback(
    (text: string) => runTurn(text).catch((err) => {
      setError(err.message || 'Generation failed.');
      throw err;
    }),
    [runTurn]
  );

  const recorder = useGemmaAudioRecorder({
    onRecordingComplete: (audio) => {
      sendAudioTurn(audio).catch((err) => setError(err.message || 'Generation failed.'));
    },
  });

  const reset = useCallback(() => {
    setMessages([]);
    setStreamingReply('');
    setError(null);
  }, []);

  return {
    status,
    error,
    modelState,
    messages,
    setMessages,
    streamingReply,
    ensureModelLoaded,
    sendAudioTurn,
    sendTextTurn,
    isRecording: recorder.isRecording,
    recorderError: recorder.error,
    startRecording: recorder.startRecording,
    stopRecording: recorder.stopRecording,
    reset,
  };
}
