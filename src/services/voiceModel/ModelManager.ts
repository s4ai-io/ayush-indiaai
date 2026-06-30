import { AutoProcessor, Gemma4ForConditionalGeneration, GraniteSpeechForConditionalGeneration, env } from '@huggingface/transformers';
import { ModelState, ModelProgress } from '@/types/voiceModel';

// Configure transformers.js environments
env.allowLocalModels = false; // Force Hugging Face Hub download and browser cache storage
// By default, transformers.js caches files in browser Cache Storage or IndexedDB.

export class ModelManager {
  private static instance: ModelManager | null = null;
  private processor: any = null;
  private model: any = null;
  private modelId = 'onnx-community/gemma-4-E2B-it-ONNX';

  private onStateChangeCallback: ((state: ModelState) => void) | null = null;

  private state: ModelState = {
    status: 'idle',
    progress: 0,
    activeFile: null,
    downloadedBytes: 0,
    totalBytes: 0,
    errorMsg: null,
    files: {},
  };

  private constructor() {}

  public static getInstance(): ModelManager {
    if (!ModelManager.instance) {
      ModelManager.instance = new ModelManager();
    }
    return ModelManager.instance;
  }

  public registerStateListener(callback: (state: ModelState) => void) {
    this.onStateChangeCallback = callback;
    // Push initial state
    callback(this.state);
  }

  private updateState(newState: Partial<ModelState>) {
    this.state = { ...this.state, ...newState };
    if (this.onStateChangeCallback) {
      this.onStateChangeCallback(this.state);
    }
  }

  public getModelState(): ModelState {
    return this.state;
  }

  public getProcessor(): any {
    return this.processor;
  }

  public getModel(): any {
    return this.model;
  }

  /**
   * Initializes the model with WebGPU support using low-level
   * AutoProcessor + Gemma4ForConditionalGeneration (instead of pipeline)
   * to enable multimodal audio input.
   */
  public async loadModel(): Promise<void> {
    if (this.processor && this.model) {
      this.updateState({ status: 'ready', progress: 100 });
      return;
    }

    try {
      this.updateState({
        status: 'checking_webgpu',
        progress: 5,
        errorMsg: null,
        files: {},
      });

      // Detect WebGPU availability
      if (!navigator.gpu) {
        throw new Error('WebGPU is not supported by your browser. Please use Chrome/Edge 113+ or Opera.');
      }

      const adapter = await navigator.gpu.requestAdapter();
      if (!adapter) {
        throw new Error('WebGPU adapter not found. WebGPU might be disabled or unsupported on your GPU.');
      }

      this.updateState({ status: 'loading_tokenizer', progress: 15 });

      // Load processor (handles tokenization, chat templates, and audio preprocessing)
      const processorPromise = AutoProcessor.from_pretrained(this.modelId, {
        progress_callback: (data: any) => this.handleProgress(data),
      });

      // Load model with WebGPU and quantized weights
      // We load it using GraniteSpeechForConditionalGeneration (which maps to AudioTextToText)
      // to skip loading the vision encoder component, and then re-assign the prototype.
      const modelPromise = GraniteSpeechForConditionalGeneration.from_pretrained(this.modelId, {
        dtype: 'q4f16',
        device: 'webgpu',
        progress_callback: (data: any) => this.handleProgress(data),
      }).then((model: any) => {
        // Change prototype to make it behave like Gemma4ForConditionalGeneration
        Object.setPrototypeOf(model, Gemma4ForConditionalGeneration.prototype);

        // Assign Gemma4ForConditionalGeneration instance fields
        model.forward_params = [
          'input_ids',
          'attention_mask',
          'inputs_embeds',
          'per_layer_inputs',
          'position_ids',
          'pixel_values',
          'image_position_ids',
          'input_features',
          'input_features_mask',
          'past_key_values',
        ];
        return model;
      });

      // Load both in parallel
      const [proc, mod] = await Promise.all([processorPromise, modelPromise]);

      this.processor = proc;
      this.model = mod;

      this.updateState({
        status: 'ready',
        progress: 100,
        activeFile: null,
      });
    } catch (error: any) {
      console.error('ModelManager failed to load:', error);
      const isWebGpuError = error.message?.includes('WebGPU') || error.message?.includes('gpu');
      this.updateState({
        status: isWebGpuError ? 'no_webgpu' : 'error',
        progress: 0,
        errorMsg: error.message || 'An unknown error occurred during model loading.',
      });
      throw error;
    }
  }

  /**
   * Handles downloading progress events from Transformers.js
   */
  private handleProgress(data: any) {
    const { status, file, name, progress, loaded, total } = data;

    // Create copy of files record
    const files = { ...this.state.files };

    const fileName = file || name || 'unknown_file';

    if (status === 'initiate') {
      files[fileName] = {
        file: fileName,
        progress: 0,
        loaded: 0,
        total: 0,
      };
      this.updateState({
        status: 'downloading',
        activeFile: fileName,
        files,
      });
    } else if (status === 'progress') {
      files[fileName] = {
        file: fileName,
        progress: progress || 0,
        loaded: loaded || 0,
        total: total || 0,
      };

      // Calculate overall progress across all tracked files
      let totalLoaded = 0;
      let totalSize = 0;
      let filesCount = 0;
      let completedProgressSum = 0;

      Object.values(files).forEach((f: ModelProgress) => {
        filesCount++;
        if (f.total > 0) {
          totalLoaded += f.loaded;
          totalSize += f.total;
        }
        completedProgressSum += f.progress;
      });

      const overallProgress = filesCount > 0 ? Math.round(completedProgressSum / filesCount) : 0;

      this.updateState({
        activeFile: fileName,
        downloadedBytes: totalLoaded,
        totalBytes: totalSize,
        progress: Math.min(95, Math.max(20, overallProgress)), // clamp progress before compilation
        files,
      });
    } else if (status === 'done') {
      if (files[fileName]) {
        files[fileName].progress = 100;
        if (files[fileName].total > 0) {
          files[fileName].loaded = files[fileName].total;
        }
      }
      this.updateState({
        activeFile: `Finished loading ${fileName}`,
        files,
      });
    } else if (status === 'ready') {
      // Transformers.js reports ready when model sessions compile
      this.updateState({
        status: 'compiling',
        progress: 98,
        activeFile: 'Compiling shaders & initializing WebGPU context...',
      });
    }
  }

  /**
   * Unloads the model and clears references to free up memory.
   */
  public async unloadModel() {
    if (this.model) {
      try {
        if (typeof this.model.dispose === 'function') {
          await this.model.dispose();
        }
      } catch (err) {
        console.warn('Failed to call model.dispose() explicitly:', err);
      }

      this.model = null;
      this.processor = null;
      this.updateState({
        status: 'idle',
        progress: 0,
        activeFile: null,
        downloadedBytes: 0,
        totalBytes: 0,
        errorMsg: null,
        files: {},
      });
    }
  }
}
