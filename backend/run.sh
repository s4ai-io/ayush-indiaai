#!/bin/bash
# ============================================================
#  AYUSH India AI — Backend Server Runner
#  Usage: ./run.sh [--port PORT] [--reload]
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
    echo "⚠️  No venv found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# ── 2. Check PostgreSQL ───────────────────────────────
echo "🔍 Checking PostgreSQL..."
if ! command -v psql &>/dev/null; then
    echo "❌ PostgreSQL not found. Install with: brew install postgresql@16"
    exit 1
fi

if ! pg_isready -q 2>/dev/null; then
    echo "⚠️  PostgreSQL not running. Starting..."
    brew services start postgresql@16 2>/dev/null || brew services start postgresql 2>/dev/null || {
        echo "❌ Could not start PostgreSQL. Start it manually."
        exit 1
    }
    sleep 2
fi

# ── 3. Check database exists ─────────────────────────
DB_NAME="ayush_db"
if ! psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "📂 Creating database '$DB_NAME'..."
    createdb "$DB_NAME" 2>/dev/null || {
        echo "❌ Could not create database. Run: createdb $DB_NAME"
        exit 1
    }
fi

# ── 4. Initialize tables if needed ───────────────────
echo "🗄️  Ensuring database tables exist..."
python3 -c "
from database import engine, Base
import models_db
Base.metadata.create_all(bind=engine)
print('  ✓ Tables ready')
"

# ── 5. Kill existing process on port ─────────────────
if lsof -ti:$PORT &>/dev/null; then
    echo "🔄 Killing existing process on port $PORT..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# ── 6. Start server ─────────────────────────────────
echo ""
echo "============================================================"
echo "  🚀 Starting AYUSH Backend on http://localhost:$PORT"
echo "============================================================"
echo ""
python3 main.py
