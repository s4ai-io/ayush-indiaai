import { TextStreamer } from '@huggingface/transformers';
import { ModelManager } from './ModelManager';
import { GeneratorParams, PerformanceStats, Message } from '@/types/voiceModel';

export class ChatEngine {
  private static instance: ChatEngine | null = null;
  private modelManager: ModelManager;

  private constructor() {
    this.modelManager = ModelManager.getInstance();
  }

  public static getInstance(): ChatEngine {
    if (!ChatEngine.instance) {
      ChatEngine.instance = new ChatEngine();
    }
    return ChatEngine.instance;
  }

  /**
   * Generates a streaming response for the given conversation history.
   * Supports both text-only and audio-input modes via the low-level
   * AutoProcessor + Gemma4ForConditionalGeneration API.
   *
   * @param audioData - Optional Float32Array of 16kHz mono audio for voice input
   */
  public async generate(
    chatHistory: Message[],
    params: GeneratorParams,
    onToken: (token: string) => void,
    controlObj: { aborted: boolean },
    audioData?: Float32Array
  ): Promise<PerformanceStats> {
    const processor = this.modelManager.getProcessor();
    const model = this.modelManager.getModel();
    if (!processor || !model) {
      throw new Error('Model is not loaded. Call ModelManager.loadModel() first.');
    }

    // Build chat messages in multimodal content format.
    // For audio messages, the last user message includes an audio content part.
    const formattedMessages = chatHistory.map((msg, idx) => {
      const isLastUserMsg = msg.role === 'user' && idx === chatHistory.length - 1;

      if (isLastUserMsg && audioData) {
        // Multimodal: audio + text prompt
        const contentParts: any[] = [{ type: 'audio' }];
        if (msg.content) {
          contentParts.push({ type: 'text', text: msg.content });
        } else {
          contentParts.push({ type: 'text', text: 'Respond to this audio.' });
        }
        return { role: msg.role, content: contentParts };
      }

      // Text-only message
      return { role: msg.role, content: msg.content };
    });

    // Apply chat template to get the prompt text
    const prompt = processor.apply_chat_template(formattedMessages, {
      tokenize: false,
      add_generation_prompt: true,
    });

    // Process inputs through the processor (handles tokenization + audio features)
    // The signature of Gemma4Processor in Transformers.js is: processor(text, images, audio, options)
    const inputs = await processor(prompt, null, audioData || null);

    // Estimate prompt token count
    const promptTokenCount = inputs.input_ids?.dims?.[1] ?? inputs.input_ids?.length ?? 0;

    const startTime = performance.now();
    let firstTokenTime: number | null = null;
    let generatedTokenCount = 0;

    // TextStreamer drives token-by-token UI updates.
    const streamer = new TextStreamer(processor.tokenizer, {
      skip_prompt: true,
      skip_special_tokens: true,
      callback_function: (text: string) => {
        if (controlObj.aborted) return;
        if (firstTokenTime === null) firstTokenTime = performance.now();
        onToken(text);
      },
      token_callback_function: (_tokens: bigint[]) => {
        generatedTokenCount += _tokens.length;
      },
    });

    await model.generate({
      ...inputs,
      max_new_tokens: params.max_new_tokens,
      temperature: params.temperature > 0 ? params.temperature : 0.01,
      top_p: params.top_p,
      top_k: params.top_k,
      do_sample: params.temperature > 0,
      streamer,
    });

    const endTime = performance.now();
    const totalDurationMs = endTime - startTime;
    const inferenceTimeMs = firstTokenTime ? endTime - firstTokenTime : totalDurationMs;
    const timeToFirstTokenMs = firstTokenTime ? firstTokenTime - startTime : 0;
    const tokensPerSec = inferenceTimeMs > 0 ? generatedTokenCount / (inferenceTimeMs / 1000) : 0;

    let memoryUsage: number | undefined;
    let memoryLimit: number | undefined;
    const perf = window.performance as any;
    if (perf?.memory) {
      memoryUsage = Math.round(perf.memory.usedJSHeapSize / (1024 * 1024));
      memoryLimit = Math.round(perf.memory.jsHeapLimit / (1024 * 1024));
    }

    return {
      promptTokens: promptTokenCount,
      generatedTokens: generatedTokenCount,
      latencyMs: Math.round(timeToFirstTokenMs),
      inferenceTimeMs: Math.round(inferenceTimeMs),
      tokensPerSec: parseFloat(tokensPerSec.toFixed(2)),
      memoryUsage,
      memoryLimit,
    };
  }
}
