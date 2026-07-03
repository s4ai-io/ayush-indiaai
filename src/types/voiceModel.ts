/**
 * Types for the assistant panel's two interchangeable backends:
 *  - "gemma4": Gemma-4-12B, Modal-hosted (POST /api/gemma4-turn). Understands
 *    audio directly.
 *  - "phi4": Phi-4, vLLM-hosted (POST /api/phi4-turn). Text-only — audio must
 *    be transcribed first (see VoiceInputButton).
 * Both reply with one acknowledgement sentence + a fenced ```json block,
 * parsed server-side — no AG-UI/tool-calling involved.
 */

export type VoiceModel = "gemma4" | "phi4";

export type VoiceFlow = "registration" | "treatment";

export type MessageRole = "user" | "assistant";

export interface GemmaMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
}

export type GemmaAgentStatus = "idle" | "recording" | "processing" | "error";

export interface GemmaTurnResponse {
  reply: string;
  extracted: Record<string, unknown> | null;
  tokens_generated: number;
  chunks_processed: number;
  audio_duration_seconds: number;
}
