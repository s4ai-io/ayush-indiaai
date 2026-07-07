"use client";

import { useCallback, useRef, useState } from "react";
import type {
  GemmaAgentStatus,
  GemmaMessage,
  GemmaTurnResponse,
  VoiceFlow,
  VoiceModel,
} from "@/types/voiceModel";

interface UseServerGemmaVoiceAgentOptions {
  /** Called after every turn that yields a non-null structured JSON block. */
  onExtracted?: (extracted: Record<string, unknown>) => void;
}

const MODEL_ENDPOINTS: Record<VoiceModel, string> = {
  gemma4: "/api/gemma4-turn",
  phi4: "/api/phi4-turn",
};

// Last N messages (user + assistant combined) sent as conversation_history.
const MAX_HISTORY_MESSAGES = 12;

/**
 * Records mic audio (same MediaRecorder/webm approach as VoiceInputButton —
 * the Modal service decodes whatever format the browser produces) or sends a
 * typed message, and posts each turn to either POST /api/gemma4-turn
 * (Modal-hosted Gemma-4-12B, understands audio directly) or POST
 * /api/phi4-turn (vLLM-hosted Phi-4, text-only — audio must already be
 * transcribed). Both return an acknowledgement + structured JSON extraction
 * in the same shape — no AG-UI/tool-calling involved — so the caller can
 * switch models turn-to-turn without changing how results are consumed.
 *
 * Cross-turn memory is text-only (assistant acknowledgements) — raw audio is
 * never replayed across turns, only the current turn's recording is sent.
 */
export function useServerGemmaVoiceAgent(flow: VoiceFlow, options?: UseServerGemmaVoiceAgentOptions) {
  const [status, setStatus] = useState<GemmaAgentStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<GemmaMessage[]>([]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);
  const onExtractedRef = useRef(options?.onExtracted);
  onExtractedRef.current = options?.onExtracted;
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  const sendTurn = useCallback(
    async (input: { audioBlob?: Blob; text?: string; model: VoiceModel }) => {
      setStatus("processing");
      setError(null);

      const userLabel = input.text?.trim() || "🎤 Voice message";
      setMessages((prev) => [
        ...prev,
        { id: `user-${Date.now()}`, role: "user", content: userLabel, timestamp: Date.now() },
      ]);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      try {
        const formData = new FormData();
        if (input.audioBlob) formData.append("audio", input.audioBlob, "recording.webm");
        if (input.text?.trim()) formData.append("user_text_prompt", input.text.trim());
        formData.append("flow", flow);
        // Text-only history — no raw audio replay across turns. Capped to the
        // last MAX_HISTORY_MESSAGES so a single bad/hallucinated turn can't
        // keep poisoning every later turn for the rest of a long session.
        formData.append(
          "conversation_history",
          JSON.stringify(
            messagesRef.current
              .slice(-MAX_HISTORY_MESSAGES)
              .map((m) => ({ role: m.role, content: m.content }))
          )
        );

        const res = await fetch(MODEL_ENDPOINTS[input.model], {
          method: "POST",
          body: formData,
          signal: controller.signal,
        });
        if (!res.ok) {
          const detail = await res.text().catch(() => res.statusText);
          throw new Error(`${input.model === "gemma4" ? "Gemma-4" : "Phi-4"} request failed: ${detail.slice(0, 200)}`);
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
        if (err.name === "AbortError") {
          setStatus("idle");
          return;
        }
        setStatus("error");
        setError(err.message || "Failed to process voice input.");
        throw err;
      } finally {
        abortControllerRef.current = null;
      }
    },
    [flow]
  );

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  const sendTextTurn = useCallback((text: string, model: VoiceModel = "gemma4") => sendTurn({ text, model }), [sendTurn]);

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
      // Gemma-4 only — Phi-4 has no direct audio understanding.
      sendTurn({ audioBlob, model: "gemma4" }).catch(() => {});
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
    stopGeneration,
    reset,
  };
}
