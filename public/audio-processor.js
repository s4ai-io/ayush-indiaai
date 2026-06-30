/**
 * AudioWorklet processor that captures raw PCM samples from the microphone
 * and posts them to the main thread.
 */
class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._chunks = [];
    this._stopped = false;

    this.port.onmessage = (event) => {
      if (event.data === 'stop') {
        // Concatenate all chunks and send back
        const totalLength = this._chunks.reduce((sum, c) => sum + c.length, 0);
        const result = new Float32Array(totalLength);
        let offset = 0;
        for (const chunk of this._chunks) {
          result.set(chunk, offset);
          offset += chunk.length;
        }
        this.port.postMessage({ type: 'complete', audio: result }, [result.buffer]);
        this._chunks = [];
        this._stopped = true;
      }
    };
  }

  process(inputs) {
    if (this._stopped) return false;

    const input = inputs[0];
    if (input && input.length > 0 && input[0].length > 0) {
      // Copy the first channel's data
      this._chunks.push(new Float32Array(input[0]));
    }
    return true;
  }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor);
