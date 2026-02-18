#!/bin/bash
# ============================================================
#  AYUSH India AI — First-Time Backend Setup
#  Run this once to set up everything from scratch
#
#  Usage: ./setup.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "============================================================"
echo "  🏗️  AYUSH India AI — First-Time Setup"
echo "============================================================"
echo ""

# ── 1. Python Virtual Environment ────────────────────
echo "Step 1/3: Setting up Python environment..."
if [ -d "venv" ]; then
    echo "  ✓ venv already exists"
else
    python3 -m venv venv
    echo "  ✓ Created venv"
fi
source venv/bin/activate

# ── 2. Install dependencies ──────────────────────────
echo ""
echo "Step 2/3: Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  ✓ All dependencies installed"

# ── 3. Check data files ─────────────────────────────
echo ""
echo "Step 3/3: Checking data files..."
MISSING=0
for f in "data/patients.csv" "data/medical_records.csv" "data/ayush_treatments.csv" "data/AyurGenixAI_Dataset.csv"; do
    if [ -f "$f" ]; then
        ROWS=$(wc -l < "$f" | tr -d ' ')
        echo "  ✓ $f ($ROWS lines)"
    else
        echo "  ❌ Missing: $f"
        MISSING=1
    fi
done

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "  ⚠️  Some data files are missing. The app will still start"
    echo "     but some features may not work until data is available."
fi

# ── Summary ──────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ✅ Setup Complete!"
echo "============================================================"
echo ""
echo "  Next steps:"
echo "    1. Copy .env.example to .env and add your API keys"
echo "    2. Run server:  ./run.sh"
echo ""
