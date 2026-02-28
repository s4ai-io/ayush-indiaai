#!/bin/bash

# AYUSH India AI — Full Stack Setup
# Sets up the Python backend (venv + deps) and Next.js frontend.
# Requires PostgreSQL for data persistence.

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "   AYUSH India AI — Full Stack Setup"
echo "=========================================="
echo ""

# Check execution directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory.${NC}"
    exit 1
fi

# ------------------------------------------------------------------
# Step 1: Python Backend
# ------------------------------------------------------------------
echo -e "${YELLOW}Step 1: Setting up Python Backend...${NC}"

cd backend

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3.10+ is required.${NC}"
    exit 1
fi

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate
echo "Virtual environment activated."

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

# Create .env if missing
if [ ! -f ".env" ]; then
    echo "Creating backend/.env from template..."
    cat > .env << 'EOF'
# ── LLM ───────────────────────────────────────────────────────────────
# Binding: "openai" | "vllm"
LLM_BINDING=vllm
LLM_MODEL=microsoft/phi-4

# vLLM endpoint (only used when LLM_BINDING=vllm)
VLLM_API_HOST=https://<your-modal-endpoint>/v1
VLLM_API_KEY=dummy-key

# OpenAI (used when LLM_BINDING=openai)
OPENAI_API_KEY=sk-...

# ── Server ─────────────────────────────────────────────────────────────
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# ── CORS ───────────────────────────────────────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
EOF
    echo -e "${GREEN}✓ Created backend/.env — update LLM keys before starting${NC}"
else
    echo -e "${GREEN}✓ backend/.env exists${NC}"
fi

# Setup Database
echo -e "${YELLOW}Step 1.5: Setup PostgreSQL Database...${NC}"
echo "Please ensure you have PostgreSQL installed and running locally."
echo "You must create a database named 'ayush_db'."
echo "Default connection string is: postgresql://user:password@localhost:5432/ayush_db"
echo "If your credentials differ, add DATABASE_URL to backend/.env."
echo ""
echo "Running data migration script to seed PostgreSQL from CSVs..."
python migrate_csv_postgres.py || echo -e "${YELLOW}⚠ Migration failed. Please check your PostgreSQL connection.${NC}"
echo ""

# Check required data files
echo "Checking data files..."
MISSING=0
for f in "data/patients.csv" "data/AyurGenixAI_Dataset.csv" "data/medical_records.csv"; do
    if [ -f "$f" ]; then
        echo -e "  ${GREEN}✓ $f${NC}"
    else
        echo -e "  ${YELLOW}⚠ Missing: $f (some features may not work)${NC}"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo -e "${YELLOW}  → Data files live in backend/data/. See README for details.${NC}"
fi

cd ..
echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

# ------------------------------------------------------------------
# Step 2: Next.js Frontend
# ------------------------------------------------------------------
echo -e "${YELLOW}Step 2: Setting up Next.js Frontend...${NC}"

# Check Node.js
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: Node.js/npm is required (v18+).${NC}"
    exit 1
fi

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Create .env.local if missing
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local from template..."
    cat > .env.local << 'EOF'
# Python FastAPI backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
PYTHON_BACKEND_URL=http://localhost:8000

# CopilotKit runtime (Next.js API route)
NEXT_PUBLIC_COPILOT_URL=/api/copilotkit

# Modal.run ASR & Translation endpoints
MODAL_ASR_URL=https://<your-modal-asr-endpoint>/transcribe
MODAL_TRANSLATE_URL=https://<your-modal-translate-endpoint>/translate
EOF
    echo -e "${GREEN}✓ Created .env.local — update Modal endpoint URLs before starting${NC}"
else
    echo -e "${GREEN}✓ .env.local exists${NC}"
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo "=========================================="
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Start the app with two terminals:"
echo ""
echo -e "${YELLOW}Terminal 1 — Backend:${NC}"
echo "  cd backend && ./run.sh"
echo "  → http://localhost:8000  (API docs at /docs)"
echo ""
echo -e "${YELLOW}Terminal 2 — Frontend:${NC}"
echo "  npm run dev"
echo "  → http://localhost:3000"
echo ""
