import modal
from pathlib import Path

# Portable path to .env (works on any dev machine)
_ENV_PATH = str(Path(__file__).resolve().parent.parent / ".env")

# Use a clean image with build tools required for IndicTransToolkit
image = (
    modal.Image.from_registry("nvcr.io/nvidia/cuda:12.4.0-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("git", "build-essential", "cmake", "clang")
    .pip_install(
        "torch",
        "transformers==4.38.2",
        "accelerate",
        "fastapi[standard]",
        "sentencepiece",
        "sacremoses",
        "mosestokenizer",
        "bitsandbytes",
        "IndicTransToolkit @ git+https://github.com/VarunGumma/IndicTransToolkit.git",
    )
)

app = modal.App("ai4bharat-translate-indic-en", image=image)

# Maps browser language codes → IndicTrans2 BCP-47 script codes
LANG_CODE_MAP = {
    "hi": "hin_Deva",
    "gu": "guj_Gujr",
    "mr": "mar_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "bn": "ben_Beng",
    "pa": "pan_Guru",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "ur": "urd_Arab",
    "as": "asm_Beng",
    "or": "ory_Orya",
    "ne": "npi_Deva",
    "sa": "san_Deva",
    "sd": "snd_Arab",
    "mai": "mai_Deva",
    "kok": "kok_Deva",
    "doi": "doi_Deva",
    "brx": "brx_Deva",
    "ks": "kas_Arab",
    "mni": "mni_Mtei",
    "sat": "sat_Olck",
}

TRANSLATION_MODEL_ID = "ai4bharat/indictrans2-indic-en-1B"
TGT_LANG = "eng_Latn"


@app.cls(
    gpu="A100",
    scaledown_window=1800,  # 30 minutes
    secrets=[modal.Secret.from_dotenv(path=_ENV_PATH)]
)
class TranslationModel:
    @modal.enter()
    def setup(self):
        """Load IndicTrans2 indic→en model into GPU memory on container startup."""
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from IndicTransToolkit.processor import IndicProcessor

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading translation model {TRANSLATION_MODEL_ID} on {self.device}...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            TRANSLATION_MODEL_ID,
            trust_remote_code=True,
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            TRANSLATION_MODEL_ID,
            trust_remote_code=True,
            torch_dtype=torch.float16,
        ).to(self.device)
        self.model.eval()

        self.ip = IndicProcessor(inference=True)
        print("Translation model loaded successfully.")

    @modal.method()
    def translate(self, text: str, src_lang_code: str) -> str:
        """Translate text from any supported Indian language to English."""
        import torch

        # Normalise: strip region suffix ('hi-IN' → 'hi')
        base_code = src_lang_code.split("-")[0].lower()
        src_lang = LANG_CODE_MAP.get(base_code)

        if not src_lang:
            print(f"Unknown language code '{src_lang_code}', returning original text.")
            return text

        print(f"Translating from {src_lang} → {TGT_LANG}: {text[:80]}...")

        batch = self.ip.preprocess_batch([text], src_lang=src_lang, tgt_lang=TGT_LANG)

        inputs = self.tokenizer(
            batch,
            truncation=True,
            padding="longest",
            return_tensors="pt",
            return_attention_mask=True,
        ).to(self.device)

        with torch.no_grad():
            generated_tokens = self.model.generate(
                **inputs,
                use_cache=True,
                min_length=0,
                max_length=2048,
                num_beams=5,
                num_return_sequences=1,
            )

        decoded = self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )

        translations = self.ip.postprocess_batch(decoded, lang=TGT_LANG)
        result = translations[0] if translations else text
        print(f"Translation result: {result}")
        return result


@app.function(image=image, secrets=[modal.Secret.from_dotenv(path=_ENV_PATH)])
@modal.asgi_app()
def asgi_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    
    web_app = FastAPI()
    
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class TranslateRequest(BaseModel):
        text: str
        src_lang: str  

    @web_app.post("/translate")
    async def translate_endpoint(req: TranslateRequest):
        if not req.text or not req.text.strip():
            raise HTTPException(status_code=400, detail="No text provided for translation")
        try:
            model = TranslationModel()
            result = await model.translate.remote.aio(req.text, req.src_lang)
            return {"translated_text": result, "src_lang": req.src_lang, "tgt_lang": "eng_Latn"}
        except Exception as e:
            print(f"Error during translation: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
        
    return web_app
