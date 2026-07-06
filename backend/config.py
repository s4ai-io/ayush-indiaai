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
LLM_REQUEST_TIMEOUT = 300.0  # vLLM HTTP request timeout
ASR_REQUEST_TIMEOUT = 180.0  # Modal ASR (transcription) HTTP timeout
TRANSLATE_REQUEST_TIMEOUT = 120.0  # Modal IndicTrans2 (translation) HTTP timeout
GEMMA_REQUEST_TIMEOUT = 240.0  # Modal Gemma-4-12B voice pipeline HTTP timeout (long audio is chunked server-side)

# ── Server ─────────────────────────────────────────────────────────────────────
DEFAULT_BACKEND_HOST = "0.0.0.0"
DEFAULT_BACKEND_PORT = 8000

# ── LLM Defaults ──────────────────────────────────────────────────────────────
DEFAULT_LLM_MODEL = "microsoft/phi-4"
DEFAULT_VLLM_API_HOST = "http://localhost:8000/v1"
DEFAULT_VLLM_API_KEY = "dummy-key"
LLM_TEMPERATURE = 0

# ── Modal ASR / Translation ────────────────────────────────────────────────────
MODAL_SCALEDOWN_WINDOW = 1800  # 30 minutes — keep warm after last request

# ── CORS Defaults ──────────────────────────────────────────────────────────────
DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"

# ── Auth ───────────────────────────────────────────────────────────────────────
# JWT signing key (SECRET_KEY) lives in .env; these are the non-secret defaults.
AUTH_COOKIE_NAME = "ayush_token"
DEFAULT_ACCESS_TOKEN_EXPIRE_HOURS = 12  # one clinic shift
