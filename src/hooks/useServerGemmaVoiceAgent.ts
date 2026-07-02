"use client";

import { useCallback, useRef, useState } from "react";
import type {
  GemmaAgentStatus,
  GemmaMessage,
  GemmaTurnResponse,
  VoiceFlow,
} from "@/types/voiceModel";

interface UseServerGemmaVoiceAgentOptions {
  /** Called after every turn that yields a non-null structured JSON block. */
  onExtracted?: (extracted: Record<string, unknown>) => void;
}

/**
 * Records mic audio (same MediaRecorder/webm approach as VoiceInputButton —
 * the Modal service decodes whatever format the browser produces) or sends a
 * typed message, and posts each turn to POST /api/gemma4-turn, which proxies
 * to the Modal-hosted Gemma-4-12B service. That service understands audio
 * directly (chunking internally for recordings over Gemma's ~30s per-clip
 * cap) and returns an acknowledgement + structured JSON extraction — no
 * AG-UI/tool-calling involved, mirroring how the on-device Gemma-4-E2B
 * pipeline (a separate, WebGPU-based prototype) proved the JSON-block
 * convention works without it, and supports both audio and text turns the
 * same way that prototype's ChatEngine.generate() did.
 *
 * Cross-turn memory is text-only (assistant acknowledgements), matching that
 * same prototype — raw audio is never replayed across turns, only the
 * current turn's recording is sent.
 */
export function useServerGemmaVoiceAgent(flow: VoiceFlow, options?: UseServerGemmaVoiceAgentOptions) {
  const [status, setStatus] = useState<GemmaAgentStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<GemmaMessage[]>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const onExtractedRef = useRef(options?.onExtracted);
  onExtractedRef.current = options?.onExtracted;
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const sendTurn = useCallback(
    async (input: { audioBlob?: Blob; text?: string }) => {
      setStatus("processing");
      setError(null);

      const userLabel = input.text?.trim() || "🎤 Voice message";
      setMessages((prev) => [
        ...prev,
        { id: `user-${Date.now()}`, role: "user", content: userLabel, timestamp: Date.now() },
      ]);

      try {
        const formData = new FormData();
        if (input.audioBlob) formData.append("audio", input.audioBlob, "recording.webm");
        if (input.text?.trim()) formData.append("user_text_prompt", input.text.trim());
        formData.append("flow", flow);
        // Text-only history — no raw audio replay across turns.
        formData.append(
          "conversation_history",
          JSON.stringify(messagesRef.current.map((m) => ({ role: m.role, content: m.content })))
        );

        const res = await fetch("/api/gemma4-turn", { method: "POST", body: formData });
        if (!res.ok) {
          const detail = await res.text().catch(() => res.statusText);
          throw new Error(`Gemma-4 request failed: ${detail.slice(0, 200)}`);
        }

        const data: GemmaTurnResponse = await res.json();

        setMessages((prev) => [
          ...prev,
          { id: `assistant-${Date.now()}`, role: "assistant", content: data.reply, timestamp: Date.now() },
        ]);

        if (data.extracted && onExtractedRef.current) {
          onExtractedRef.current(data.extracted);
        }

        setStatus("idle");
        return data;
      } catch (err: any) {
        setStatus("error");
        setError(err.message || "Failed to process voice input.");
        throw err;
      }
    },
    [flow]
  );

  const sendTextTurn = useCallback((text: string) => sendTurn({ text }), [sendTurn]);

  const startRecording = useCallback(async () => {
    setError(null);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunksRef.current.push(event.data);
    };

    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
      sendTurn({ audioBlob }).catch(() => {});
    };

    mediaRecorder.start();
    setStatus("recording");
  }, [sendTurn]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && status === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, [status]);

  const reset = useCallback(() => {
    setMessages([]);
    setError(null);
    setStatus("idle");
  }, []);

  return {
    status,
    error,
    messages,
    setMessages,
    isRecording: status === "recording",
    startRecording,
    stopRecording,
    sendTextTurn,
    reset,
  };
}
