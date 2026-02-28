"""
Central application configuration.

All non-secret, git-safe constants live here. Secrets (API keys, DB passwords)
stay in .env and are loaded via os.getenv() where needed.

Import as:
    from config import cfg
"""

# ── Timeouts (seconds) ─────────────────────────────────────────────────────────
# These are kept in sync across backend agents, LLM clients, and the frontend.

AGENT_TIMEOUT = 300          # AG-UI workflow timeout (all agents)
LLM_REQUEST_TIMEOUT = 300.0  # OpenAI/vLLM HTTP request timeout
ASR_REQUEST_TIMEOUT = 180.0  # Modal ASR (transcription) HTTP timeout
TRANSLATE_REQUEST_TIMEOUT = 120.0  # Modal IndicTrans2 (translation) HTTP timeout

# ── Server ─────────────────────────────────────────────────────────────────────
DEFAULT_BACKEND_HOST = "0.0.0.0"
DEFAULT_BACKEND_PORT = 8000

# ── LLM Defaults ──────────────────────────────────────────────────────────────
DEFAULT_LLM_BINDING = "vllm"          # "openai" | "vllm"
DEFAULT_LLM_MODEL = "microsoft/phi-4"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_VLLM_API_HOST = "http://localhost:8000/v1"
DEFAULT_VLLM_API_KEY = "dummy-key"
LLM_TEMPERATURE = 0

# ── Modal ASR / Translation ────────────────────────────────────────────────────
MODAL_SCALEDOWN_WINDOW = 1800  # 30 minutes — keep warm after last request

# ── CORS Defaults ──────────────────────────────────────────────────────────────
DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
