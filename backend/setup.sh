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
echo "Step 1/5: Setting up Python environment..."
if [ -d "venv" ]; then
    echo "  ✓ venv already exists"
else
    python3 -m venv venv
    echo "  ✓ Created venv"
fi
source venv/bin/activate

# ── 2. Install dependencies ──────────────────────────
echo ""
echo "Step 2/5: Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  ✓ All dependencies installed"

# ── 3. Check PostgreSQL ──────────────────────────────
echo ""
echo "Step 3/5: Checking PostgreSQL..."
if ! command -v psql &>/dev/null; then
    echo "  ❌ PostgreSQL not found!"
    echo "  Install with: brew install postgresql@16"
    echo "  Then run: brew services start postgresql@16"
    exit 1
fi

if ! pg_isready -q 2>/dev/null; then
    echo "  ⚠️  PostgreSQL not running. Starting..."
    brew services start postgresql@16 2>/dev/null || brew services start postgresql 2>/dev/null || {
        echo "  ❌ Could not start PostgreSQL."
        exit 1
    }
    sleep 2
fi
echo "  ✓ PostgreSQL running"

# ── 4. Create database ──────────────────────────────
echo ""
echo "Step 4/5: Setting up database..."
DB_NAME="ayush_db"
if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "  ✓ Database '$DB_NAME' already exists"
else
    createdb "$DB_NAME"
    echo "  ✓ Created database '$DB_NAME'"
fi

# ── 5. Create tables ─────────────────────────────────
echo ""
echo "Step 5/5: Creating database tables..."
python3 -c "
from database import engine, Base
import models_db
Base.metadata.create_all(bind=engine)
print('  ✓ All tables created')
"

# ── Summary ──────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ✅ Setup Complete!"
echo "============================================================"
echo ""
echo "  Next steps:"
echo "    1. Migrate data:    ./migrate.sh"
echo "    2. Generate data:   ./migrate.sh --generate"
echo "    3. Run server:      ./run.sh"
echo ""
