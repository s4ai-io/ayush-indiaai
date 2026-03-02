#!/bin/bash
# ============================================================
#  AYUSH India AI — Backend Server Runner
#  Usage: ./run.sh [--port PORT] [--no-reload]
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT=8000
RELOAD="--reload"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)   PORT="$2"; shift 2 ;;
        --no-reload) RELOAD=""; shift ;;
        --help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT    Port to run on (default: 8000)"
            echo "  --no-reload    Disable auto-reload"
            echo "  --help         Show this help"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── 1. Check Python venv ──────────────────────────────
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No venv found. Run ./setup.sh first."
    exit 1
fi

# ── 2. Check data files ──────────────────────────────
echo "📁 Checking data files..."
for f in "data/patients.csv" "data/ISHAAyushAI_Dataset.csv"; do
    if [ -f "$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ⚠️  Missing: $f (some features may not work)"
    fi
done

# ── 3. Kill existing process on port ─────────────────
if lsof -ti:$PORT &>/dev/null; then
    echo "🔄 Killing existing process on port $PORT..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# ── 4. Start server ─────────────────────────────────
echo ""
echo "============================================================"
echo "  🚀 Starting AYUSH Backend on http://localhost:$PORT"
echo "============================================================"
echo ""
python3 main.py
