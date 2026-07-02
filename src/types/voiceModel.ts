/**
 * Types for the server-hosted Gemma-4-12B voice pipeline (Modal-hosted,
 * see backend/modal_script/modal_gemma4_12b.py + POST /api/gemma4-turn).
 * This is an opt-in alternative to the Cloud pipeline (Modal ASR +
 * IndicTrans2 + Phi-4 via AG-UI tool-calling) — see src/hooks/useServerGemmaVoiceAgent.ts.
 * Gemma-4 doesn't use AG-UI/tool-calling: the model replies with one
 * acknowledgement sentence + a fenced ```json block, parsed server-side.
 */

export type VoicePipelineMode = "cloud" | "gemma4";

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
