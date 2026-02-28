import modal
import io
import os
from pathlib import Path

# Portable path to .env (works on any dev machine)
_ENV_PATH = str(Path(__file__).resolve().parent.parent / ".env")

# Define the image with necessary dependencies
# Use CUDA-enabled base to ensure CUDAExecutionProvider is available in onnxruntime-gpu
image = (
    modal.Image.from_registry("nvcr.io/nvidia/cuda:12.4.0-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("ffmpeg", "python3-pip") # Required for audio processing
    .pip_install(
        "torch",
        "torchaudio",
        "torchcodec",
        "transformers>=4.40.0",
        "accelerate",
        "soundfile",
        "librosa",
        "fastapi[standard]",
        "onnxruntime-gpu==1.20.1",
        "onnx==1.20.1",
    )
)

app = modal.App("ai4bharat-asr-multilingual", image=image)

# Define the model to download
ASR_MODEL_ID = "ai4bharat/indic-conformer-600m-multilingual"

# Cache the weights so we don't download them on every cold start
@app.cls(
    gpu="A100",
    scaledown_window=1800,  # 30 minutes
    secrets=[modal.Secret.from_dotenv(path=_ENV_PATH)]
)
class ASRModel:
    @modal.enter()
    def setup(self):
        """Loads the model and processor into memory on container startup."""
        import torch
        from transformers import AutoModel
        
        print(f"Loading custom model from {ASR_MODEL_ID}...")
        
        # Determine the device to run on
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        self.model = AutoModel.from_pretrained(ASR_MODEL_ID, trust_remote_code=True)
        # We don't need to explicitly move to device here; the custom implementation handles ONNX sessions internally
        print("Model loaded successfully.")

    @modal.method()
    def transcribe(self, audio_bytes: bytes, target_language: str = None):
        """Processes audio bytes and returns the transcription.
        
        Args:
            audio_bytes: the raw audio file bytes (e.g., from a webm or wav file)
            target_language: The ISO-639-1 language code (e.g. 'hi')
        """
        import torch
        import torchaudio

        # The AI4Bharat model only supports 22 Indian languages
        # Map browser locale codes to valid AI4Bharat language codes
        SUPPORTED_LANGUAGES = {
            "as", "bn", "brx", "doi", "gu", "hi", "kn", "kok",
            "ks", "mai", "ml", "mni", "mr", "ne", "or",
            "pa", "sa", "sat", "sd", "ta", "te", "ur"
        }

        # Normalize language: strip region codes (e.g. 'hi-IN' -> 'hi'), default to 'hi'
        if target_language:
            lang_base = target_language.split("-")[0].lower()
            target_language = lang_base if lang_base in SUPPORTED_LANGUAGES else "hi"
        else:
            target_language = "hi"

        import tempfile
        import os

        # Save to a temporary file to guarantee torchaudio/ffmpeg can probe the container formats (webm, mp3, etc)
        tmp_path = "/tmp/audio.webm"
        with open(tmp_path, "wb") as f:
            f.write(audio_bytes)

        wav, sr = torchaudio.load(tmp_path)
        os.remove(tmp_path)

        # The model expects a single channel (mono) waveform [1, length]
        wav = torch.mean(wav, dim=0, keepdim=True)
        
        target_sample_rate = 16000
        if sr != target_sample_rate:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sample_rate)
            wav = resampler(wav)
            
        print(f"Running inference on audio of shape {wav.shape} for language '{target_language}'...")
        # ai4bharat/indic-conformer-600m-multilingual works best on ≤20 s chunks.
        # Strategy: split into 20 s chunks with 0.5 s overlap, try RNNT first,
        # fall back to CTC per-chunk if RNNT returns empty.
        try:
            CHUNK_SEC     = 20
            OVERLAP_SEC   = 0.5
            SR            = 16000
            CHUNK_SAMPLES = CHUNK_SEC * SR
            OVERLAP       = int(OVERLAP_SEC * SR)
            STEP          = CHUNK_SAMPLES - OVERLAP
            audio_len     = wav.shape[-1]

            def _decode_chunk(chunk_wav):
                """Try RNNT; if empty fall back to CTC."""
                result = self.model(chunk_wav, target_language, "rnnt")
                if isinstance(result, list):
                    result = result[0]
                result = (result or "").strip()
                if not result:
                    # RNNT returned empty — use CTC as fallback
                    result = self.model(chunk_wav, target_language, "ctc")
                    if isinstance(result, list):
                        result = result[0]
                    result = (result or "").strip()
                return result

            parts = []
            start = 0
            while start < audio_len:
                end   = min(start + CHUNK_SAMPLES, audio_len)
                chunk = wav[:, start:end]
                part  = _decode_chunk(chunk)
                if part:
                    parts.append(part)
                print(f"  chunk [{start//SR:.1f}s–{end//SR:.1f}s]: {repr(part[:60])}")
                start += STEP

            transcription = " ".join(parts)

            if not transcription.strip():
                raise RuntimeError(
                    f"Model returned empty transcription for {audio_len/SR:.1f} s "
                    f"of {target_language} audio — check audio quality or language setting."
                )

            print(f"Transcription complete ({len(parts)} chunks): {transcription[:120]}")
            return str(transcription)
        except RuntimeError:
            raise
        except Exception as e:
            print(f"Error during inference: {e}")
            raise e

# Since we need to accept generic HTTP form-data (a file from the browser), 
# ASGI wrapper is more robust for FastAPI than the basic @web_endpoint
@app.function(image=image, secrets=[modal.Secret.from_dotenv(path=_ENV_PATH)])
@modal.asgi_app()
def asgi_app():
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    
    web_app = FastAPI()
    
    # Allow all CORS for ease of development (the proxy will actually be the only caller soon)
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @web_app.post("/transcribe")
    async def transcribe_endpoint(
        audio: UploadFile = File(...),
        language: str = Form(None)
    ):
        if not audio:
            raise HTTPException(status_code=400, detail="No audio file provided")
            
        audio_bytes = await audio.read()
        
        # Call the remote method
        try:
            model = ASRModel()
            result = await model.transcribe.remote.aio(audio_bytes, language)
            return {"text": result, "language": language}
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
            
    return web_app
