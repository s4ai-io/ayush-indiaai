/**
 * Types for the on-device (client-side) Gemma-4-E2B voice pipeline.
 * This is an opt-in alternative to the cloud STT+translate+Phi-4 pipeline —
 * see src/services/voiceModel/.
 */

export type VoicePipelineMode = 'cloud' | 'local';

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
}

export type LoadingStatus =
  | 'idle'
  | 'checking_webgpu'
  | 'no_webgpu'
  | 'loading_tokenizer'
  | 'downloading'
  | 'compiling'
  | 'ready'
  | 'error';

export interface ModelProgress {
  file: string;
  progress: number; // 0 to 100
  loaded: number; // bytes
  total: number; // bytes
}

export interface ModelState {
  status: LoadingStatus;
  progress: number; // overall progress 0-100
  activeFile: string | null;
  downloadedBytes: number;
  totalBytes: number;
  errorMsg: string | null;
  files: Record<string, ModelProgress>;
}

export interface GPUInfo {
  supported: boolean;
  adapterName: string | null;
  vendor?: string;
  architecture?: string;
}

export interface GeneratorParams {
  temperature: number;
  top_p: number;
  top_k: number;
  max_new_tokens: number;
}

export interface PerformanceStats {
  promptTokens: number;
  generatedTokens: number;
  latencyMs: number;
  inferenceTimeMs: number;
  tokensPerSec: number;
  memoryUsage?: number; // MB, if performance.memory is available
  memoryLimit?: number; // MB
}

/** Structured extraction result parsed from a fenced ```json block in the model's reply. */
export interface ExtractionResult<T = Record<string, unknown>> {
  reply: string; // natural-language text shown in the chat panel (JSON block stripped out)
  extracted: T | null; // parsed JSON, or null if no/invalid JSON block was found
  stats: PerformanceStats;
}
