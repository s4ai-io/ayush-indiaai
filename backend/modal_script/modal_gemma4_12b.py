import io
import json
import re
from typing import Any, Dict, List, Optional

import modal

MINUTES = 60

gemma12b_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .apt_install("libsndfile1", "ffmpeg")
    .uv_pip_install(
        "torch>=2.5.0",
        "torchvision>=0.20.0",
        "transformers>=5.5.0",
        "accelerate>=0.34.0",
        "compressed-tensors>=0.9.0",  # required for w4a16-ct quantized weights
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "numpy>=1.24.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "python-multipart>=0.0.9",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

# QAT w4a16 compressed-tensors variant: ~6-8 GB VRAM vs ~24 GB for bfloat16.
MODEL_NAME = "google/gemma-4-12B-it-qat-w4a16-ct"
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

app = modal.App("gemma4-12b-ayush-voice")

# Gemma-4 hard-caps audio input at ~30s per clip with no built-in long-audio
# support. 28s leaves a safety margin; 2.5s overlap avoids losing a word/
# sentence that straddles a chunk boundary.
CHUNK_SEC = 28
OVERLAP_SEC = 2.5
SAMPLE_RATE = 16000

# ── System prompts ──────────────────────────────────────────────────────────
# Ported from the gemma-4-integration branch's src/services/voiceModel/prompts.ts
# (on-device Gemma-4-E2B pipeline). Same output contract — one acknowledgement
# sentence + a fenced ```json block — and the exact same field names
# registration_agent.py / treatment_agent.py already use, so the frontend's
# existing merge logic (applyProposedRegistrationData etc.) needs no changes
# regardless of which pipeline produced the data.

REGISTRATION_SYSTEM_PROMPT = """You are an AI Assistant helping a Medical Receptionist fill out a Patient Registration form for an Ayush EHR system.

The user speaks in various Indic languages (Hindi, Marathi, Gujarati, etc.) or English, as audio. You must understand the audio directly.

CRITICAL RULE: ALL data you extract MUST BE IN ENGLISH, regardless of the language spoken.
- Translate occupations, addresses, cities, and concepts into English.
- Transliterate Indian names into English characters.
- NEVER output Hindi/Gujarati/other script text in the JSON block — translate everything first.

Update the form with ANY available information immediately — do not wait for a complete section.

Respond in two parts, in this exact order:
1. One short, friendly sentence acknowledging what you understood (shown to the user).
2. A single fenced ```json code block containing ONLY the fields you could confidently extract
   from the user's latest message. Omit fields you don't have data for — do not guess.

The JSON block must use this exact shape (all fields optional, omit unknown ones):
{
  "basicInfo": {
    "firstName": string,
    "lastName": string,
    "gender": "Male" | "Female" | "Transgender",
    "age": string,
    "maritalStatus": "Married" | "Unmarried" | "Divorcee" | "Widow"
  },
  "contactInfo": {
    "mobileNumber": string,
    "address": string,
    "state": "Delhi" | "Maharashtra" | "Karnataka" | "Gujarat" | "Uttar Pradesh",
    "city": "New Delhi" | "Mumbai" | "Bangalore" | "Ahmedabad" | "Lucknow",
    "pincode": string
  },
  "otherInfo": {
    "occupation": string,
    "bloodGroup": "A+" | "A-" | "B+" | "B-" | "O+" | "O-" | "AB+" | "AB-",
    "idType": "Aadhar" | "PAN Card" | "Voter ID",
    "idNumber": string
  }
}

If the user said "Single", map maritalStatus to "Unmarried". If they said "Bengaluru", map city to "Bangalore".
If nothing extractable was said, omit the json block entirely and just acknowledge/ask a clarifying question."""

TREATMENT_SYSTEM_PROMPT = """You are an AI Clinical Assistant helping a doctor fill out the Clinical Assessment form for an Ayush Treatment Plan.

The doctor speaks in various Indic languages (Hindi, Marathi, Gujarati, etc.) or English, as audio. You must understand the audio directly.

CRITICAL RULE: ALL data you extract MUST BE IN ENGLISH, regardless of the language spoken.
- Translate symptoms, comorbidities, dietary habits, and concepts into English.
- NEVER output Hindi/Gujarati/other script text in the JSON block — translate everything first.

Update the form with ANY available information immediately — do not wait for all fields.

DOSHA INFERENCE: if the doctor doesn't explicitly mention doshas, infer from the disease/symptoms:
- Vata conditions: joint pain, anxiety, insomnia, dry skin, constipation
- Pitta conditions: inflammation, acidity, skin rashes, fever, liver issues
- Kapha conditions: obesity, diabetes, congestion, lethargy, water retention

Respond in two parts, in this exact order:
1. One short, friendly sentence acknowledging what you understood (shown to the doctor).
2. A single fenced ```json code block containing ONLY the fields you could confidently extract
   from the doctor's latest message. Omit fields you don't have data for — do not guess.

The JSON block must use this exact flat shape (all fields optional, omit unknown ones):
{
  "disease": string,
  "symptoms": string,
  "comorbidities": string,
  "vikriti": "Vata" | "Pitta" | "Kapha",
  "prakriti": "Vata" | "Pitta" | "Kapha" | "Vata-Pitta" | "Pitta-Kapha" | "Vata-Kapha",
  "herbs": string,
  "yoga": string,
  "diet": string,
  "lifestyle": string
}

After the doctor's clinical notes have been captured, suggest they review the form and click
"Generate Treatment Plan" manually — do not claim to have generated it yourself.
If nothing extractable was said, omit the json block entirely and just acknowledge/ask a clarifying question."""

# Used only for the internal "keep listening" turns between chunks of a long
# recording — never shown to the end user, no JSON block requested.
CHUNK_LISTEN_INSTRUCTION = (
    "This is a continuation of the same recording. Silently note any key "
    "details (names, numbers, symptoms, etc.) in one short sentence. Do NOT "
    "summarize the whole conversation yet and do NOT output a json block."
)

FLOW_PROMPTS = {
    "registration": REGISTRATION_SYSTEM_PROMPT,
    "treatment": TREATMENT_SYSTEM_PROMPT,
}


def get_system_prompt(flow: Optional[str]) -> str:
    return FLOW_PROMPTS.get(flow or "registration", REGISTRATION_SYSTEM_PROMPT)


def preprocess_audio(audio_bytes: bytes, target_sr: int = SAMPLE_RATE):
    import librosa
    import soundfile as sf

    audio_buffer = io.BytesIO(audio_bytes)
    try:
        audio_data, sr = sf.read(audio_buffer, dtype="float32")
    except Exception:
        # Compressed container formats (webm/opus from the browser's
        # MediaRecorder) aren't supported by libsndfile. librosa's audioread
        # fallback depends on an optional package that isn't guaranteed to be
        # installed/working, so it can silently mis-decode instead of raising
        # — shell out to ffmpeg directly instead (the same binary
        # modal_transcribe.py relies on via torchaudio for these exact
        # MediaRecorder-produced blobs, just invoked explicitly here so
        # failures surface as errors rather than near-silent audio).
        import os
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as src:
            src.write(audio_bytes)
            src_path = src.name
        dst_path = src_path + ".wav"
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", src_path, "-ar", str(target_sr), "-ac", "1", dst_path],
                check=True, capture_output=True,
            )
            audio_data, sr = sf.read(dst_path, dtype="float32")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg failed to decode audio: {e.stderr.decode(errors='replace')[:500]}")
        finally:
            os.remove(src_path)
            if os.path.exists(dst_path):
                os.remove(dst_path)

    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    if sr != target_sr:
        audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=target_sr)

    max_val = abs(audio_data).max()
    if max_val > 0:
        audio_data = audio_data / max_val

    return audio_data.astype("float32")


def chunk_audio(audio_data, chunk_sec: float = CHUNK_SEC, overlap_sec: float = OVERLAP_SEC, sr: int = SAMPLE_RATE):
    """Split audio into <=chunk_sec windows with overlap_sec overlap between
    consecutive windows. Returns a single-element list (the original array)
    when the audio already fits in one chunk."""
    total_samples = len(audio_data)
    chunk_samples = int(chunk_sec * sr)
    if total_samples <= chunk_samples:
        return [audio_data]

    overlap_samples = int(overlap_sec * sr)
    step = chunk_samples - overlap_samples
    if step <= 0:
        raise ValueError("chunk_sec must be greater than overlap_sec")

    chunks = []
    start = 0
    while start < total_samples:
        end = min(start + chunk_samples, total_samples)
        chunks.append(audio_data[start:end])
        if end == total_samples:
            break
        start += step
    return chunks


def parse_structured_reply(full_text: str):
    """Ports extraction.ts's parseStructuredReply: pulls a fenced ```json
    block out of the model's reply and parses it. Tolerates a missing or
    malformed block — falls back to (text, None)."""
    match = re.search(r"```json\s*([\s\S]*?)\s*```", full_text, re.IGNORECASE)
    if not match:
        return full_text.strip(), None

    reply = (full_text[: match.start()] + full_text[match.end():]).strip()
    try:
        parsed = json.loads(match.group(1))
        if isinstance(parsed, dict):
            return reply, parsed
        return reply, None
    except json.JSONDecodeError:
        return reply, None


from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

web_app = FastAPI(
    title="Gemma-4-12B-it (QAT w4a16) AYUSH Voice Pipeline API",
    version="1.0.0",
)
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@web_app.get("/health")
async def health():
    import torch
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }


@app.cls(
    image=gemma12b_image,
    gpu="A100",
    scaledown_window=5 * MINUTES,
    timeout=10 * MINUTES,
    volumes={"/root/.cache/huggingface": hf_cache_vol},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    max_containers=5,
)
class Gemma12BVoiceService:
    @modal.enter()
    def load_model(self):
        from transformers import AutoModelForMultimodalLM, AutoProcessor

        print(f"Loading model: {MODEL_NAME}")
        self.processor = AutoProcessor.from_pretrained(MODEL_NAME)
        # dtype="auto" lets transformers detect and load the w4a16 compressed-tensors
        # weights correctly — do NOT force bfloat16 here or it ignores the quantization.
        self.model = AutoModelForMultimodalLM.from_pretrained(
            MODEL_NAME,
            dtype="auto",
            device_map="auto",
        )
        self.model.eval()
        print(f"Gemma-4-12B-it (QAT w4a16) ready. Device: {next(self.model.parameters()).device}")

    def _generate(self, messages: List[Dict[str, Any]], max_new_tokens: int, do_sample: bool) -> str:
        import torch

        inputs = self.processor.apply_chat_template(
            messages, tokenize=True, return_tensors="pt",
            return_dict=True, add_generation_prompt=True,
        ).to(self.model.device)

        gen_kwargs = {"max_new_tokens": max_new_tokens, "do_sample": do_sample}
        if do_sample:
            gen_kwargs.update({"temperature": 0.7, "top_p": 0.9})

        with torch.inference_mode():
            output_ids = self.model.generate(**inputs, **gen_kwargs)

        input_len = inputs["input_ids"].shape[-1]
        generated_ids = output_ids[0][input_len:]
        return self.processor.decode(generated_ids, skip_special_tokens=True).strip(), int(generated_ids.shape[0])

    def process_turn(
        self,
        audio_bytes: Optional[bytes] = None,
        flow: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_text_prompt: Optional[str] = None,
        max_new_tokens: int = 512,
    ) -> dict:
        """Text-only conversation history (mirrors the gemma-4-integration
        branch's useLocalVoiceAgent) + the current turn's input, which is
        either audio (chunked and chained internally when it exceeds
        Gemma-4's ~30s per-clip cap) or, if no audio was supplied, a plain
        text turn — mirrors ChatEngine.generate()'s text-only path on that
        same branch, so the chat panel can support typed messages too."""
        system_prompt = get_system_prompt(flow)
        history = conversation_history or []

        if not audio_bytes:
            if not user_text_prompt:
                raise ValueError("Either audio or user_text_prompt is required")
            messages = (
                [{"role": "system", "content": system_prompt}]
                + history
                + [{"role": "user", "content": user_text_prompt}]
            )
            final_text, tokens = self._generate(messages, max_new_tokens=max_new_tokens, do_sample=True)
            reply, extracted = parse_structured_reply(final_text)
            return {
                "reply": reply,
                "extracted": extracted,
                "tokens_generated": tokens,
                "chunks_processed": 0,
                "audio_duration_seconds": 0.0,
            }

        audio_data = preprocess_audio(audio_bytes)
        chunks = chunk_audio(audio_data)

        running_notes: List[Dict[str, str]] = []
        final_text = ""
        total_generated_tokens = 0

        for i, chunk in enumerate(chunks):
            is_last = i == len(chunks) - 1
            base_history = [{"role": "system", "content": system_prompt}] + history + running_notes

            if not is_last:
                user_content = [
                    {"type": "audio", "audio": chunk},
                    {"type": "text", "text": CHUNK_LISTEN_INSTRUCTION},
                ]
                messages = base_history + [{"role": "user", "content": user_content}]
                note_text, tokens = self._generate(messages, max_new_tokens=64, do_sample=False)
                total_generated_tokens += tokens
                running_notes.append({"role": "user", "content": f"[audio segment {i + 1} of {len(chunks)}]"})
                running_notes.append({"role": "assistant", "content": note_text})
            else:
                user_content = [{"type": "audio", "audio": chunk}]
                if user_text_prompt:
                    user_content.append({"type": "text", "text": user_text_prompt})
                messages = base_history + [{"role": "user", "content": user_content}]
                final_text, tokens = self._generate(messages, max_new_tokens=max_new_tokens, do_sample=True)
                total_generated_tokens += tokens

        reply, extracted = parse_structured_reply(final_text)

        return {
            "reply": reply,
            "extracted": extracted,
            "tokens_generated": total_generated_tokens,
            "chunks_processed": len(chunks),
            "audio_duration_seconds": round(len(audio_data) / SAMPLE_RATE, 2),
        }

    @modal.asgi_app()
    def serve(self):
        @web_app.post("/api/upload-audio")
        async def upload_audio(
            file: Optional[UploadFile] = File(None),
            flow: Optional[str] = Form("registration"),
            conversation_history: Optional[str] = Form(None),
            user_text_prompt: Optional[str] = Form(None),
            max_new_tokens: int = Form(512),
        ):
            try:
                audio_bytes = await file.read() if file is not None else None
                if not audio_bytes and not user_text_prompt:
                    raise HTTPException(status_code=400, detail="Provide an audio file, user_text_prompt, or both")

                history = None
                if conversation_history:
                    history = json.loads(conversation_history)

                result = self.process_turn(
                    audio_bytes=audio_bytes,
                    flow=flow,
                    conversation_history=history,
                    user_text_prompt=user_text_prompt,
                    max_new_tokens=max_new_tokens,
                )
                return JSONResponse(content=result)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in conversation_history")
            except HTTPException:
                raise
            except Exception as e:
                import traceback; traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

        print("REGISTERED ROUTES:", [r.path for r in web_app.routes])
        return web_app


@app.local_entrypoint()
def test():
    import numpy as np
    import soundfile as sf
    import tempfile

    service = Gemma12BVoiceService()

    # Synthetic ~65s of silence -> exercises the chunking path (3 chunks at
    # CHUNK_SEC=28/OVERLAP_SEC=2.5: [0-28), [25.5-53.5), [51-65)).
    long_audio = np.zeros(int(65 * SAMPLE_RATE), dtype=np.float32)
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        sf.write(f.name, long_audio, SAMPLE_RATE)
        f.seek(0)
        audio_bytes = f.read()

    print("Triggering process_turn.remote() with 65s of audio (expect chunks_processed=3)...")
    res = service.process_turn.remote(
        audio_bytes=audio_bytes,
        flow="registration",
        max_new_tokens=256,
    )
    print("=" * 60)
    print("REMOTE INFERENCE RESULT:")
    print(res)
    print("=" * 60)
