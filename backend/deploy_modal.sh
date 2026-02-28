#!/usr/bin/env bash
# ============================================================
# deploy_modal.sh
# Deploy all Modal.com models for the AYUSH backend.
#
# Usage:
#   ./deploy_modal.sh            # deploy all three models
#   ./deploy_modal.sh asr        # deploy ASR only
#   ./deploy_modal.sh translate  # deploy Translate only
#   ./deploy_modal.sh vllm       # deploy vLLM phi-4 only
# ============================================================

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODAL_DIR="$SCRIPT_DIR/modal_asr"
VENV="$SCRIPT_DIR/venv/bin/activate"

# ── Colour helpers ───────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${CYAN}[deploy]${NC} $*"; }
success() { echo -e "${GREEN}[  OK  ]${NC} $*"; }
warn()    { echo -e "${YELLOW}[ WARN ]${NC} $*"; }
error()   { echo -e "${RED}[ERROR ]${NC} $*"; exit 1; }

# ── Activate venv ────────────────────────────────────────────
if [[ -f "$VENV" ]]; then
    # shellcheck source=/dev/null
    source "$VENV"
    info "Activated virtualenv: $VENV"
else
    warn "No venv found at $VENV — using system Python"
fi

# ── Check modal CLI ──────────────────────────────────────────
if ! command -v modal &>/dev/null; then
    error "'modal' CLI not found. Run: pip install modal"
fi

# ── Validate HF_TOKEN in backend/.env ───────────────────────
ENV_FILE="$SCRIPT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    error "backend/.env not found at $ENV_FILE"
fi

HF_TOKEN_VAL=$(grep -E "^HF_TOKEN=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs)
if [[ -z "$HF_TOKEN_VAL" || "$HF_TOKEN_VAL" == "your_hf_token_here" ]]; then
    echo ""
    error "HF_TOKEN is missing or still a placeholder in backend/.env
       1. Go to https://huggingface.co/settings/tokens
       2. Create a token with 'Read' access
       3. Set it in backend/.env:  HF_TOKEN=hf_xxxxxxxxxxxx"
fi
info "HF_TOKEN found in .env ✓"

# ── Update a key in .env ─────────────────────────────────────
update_env() {
    local key="$1"
    local value="$2"
    if grep -qE "^${key}=" "$ENV_FILE"; then
        sed -i '' "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    else
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
    info "  .env updated: ${key}=${value}"
}

# ── Deploy function ──────────────────────────────────────────
# Args: <label> <file> <env_key> <url_suffix>
#   env_key    — variable in .env to update (e.g. MODAL_ASR_URL)
#   url_suffix — path appended to the base URL (e.g. /transcribe, /v1)
deploy_app() {
    local label="$1"
    local file="$2"
    local env_key="${3:-}"
    local url_suffix="${4:-}"

    echo ""
    info "Deploying ${label}  →  $(basename "$file")"
    echo "────────────────────────────────────────────"

    # Capture output to parse the URL, but also stream it to terminal
    local output
    if ! output=$(modal deploy "$file" 2>&1); then
        echo "$output"
        error "${label} deployment FAILED — see output above"
    fi
    echo "$output"

    success "${label} deployed successfully"

    # Modal prints the endpoint URL on a line like:
    #   "=> https://<user>--<app>-<fn>.modal.run"
    if [[ -n "$env_key" ]]; then
        local base_url
        base_url=$(echo "$output" \
            | grep -oE 'https://[a-zA-Z0-9._-]+--[a-zA-Z0-9._-]+\.modal\.run' \
            | head -1)
        if [[ -n "$base_url" ]]; then
            update_env "$env_key" "${base_url}${url_suffix}"
        else
            warn "Could not parse URL from deploy output — ${env_key} not updated"
        fi
    fi
}

# ── Select which apps to deploy ──────────────────────────────
TARGET="${1:-all}"

echo ""
echo "════════════════════════════════════════════"
echo "  AYUSH Modal Deployment  —  target: ${TARGET}"
echo "════════════════════════════════════════════"

case "$TARGET" in
    asr)
        deploy_app "ASR  (ai4bharat indic-conformer)"   "$MODAL_DIR/app.py"           "MODAL_ASR_URL"       "/transcribe"
        ;;
    translate)
        deploy_app "Translate  (ai4bharat IndicTrans2)"  "$MODAL_DIR/app_translate.py" "MODAL_TRANSLATE_URL"  "/translate"
        ;;
    vllm)
        deploy_app "vLLM phi-4  (microsoft/phi-4)"       "$MODAL_DIR/modal_vllm_phi4.py" "VLLM_API_HOST"    "/v1"
        ;;
    all)
        deploy_app "ASR  (ai4bharat indic-conformer)"   "$MODAL_DIR/app.py"            "MODAL_ASR_URL"       "/transcribe"
        deploy_app "Translate  (ai4bharat IndicTrans2)"  "$MODAL_DIR/app_translate.py"  "MODAL_TRANSLATE_URL" "/translate"
        deploy_app "vLLM phi-4  (microsoft/phi-4)"       "$MODAL_DIR/modal_vllm_phi4.py" "VLLM_API_HOST"    "/v1"
        ;;
    *)
        echo "Unknown target: $TARGET"
        echo "Usage: $0 [asr|translate|vllm|all]"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════"
success "All deployments complete!"
echo "════════════════════════════════════════════"
echo ""
