#!/bin/bash

# AYUSH India AI — Complete Setup Script
# Sets up Python backend, PostgreSQL database, and Next.js frontend.

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
# Step 1: Python Backend & Database
# ------------------------------------------------------------------
echo -e "${YELLOW}Step 1: Setting up Python Backend & Database...${NC}"

cd backend

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required.${NC}"
    exit 1
fi

# Create Venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate Venv
source venv/bin/activate
echo "Virtual environment activated."

# Install Dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

# Create .env if missing
if [ ! -f ".env" ]; then
    echo "Creating backend/.env file..."
    cat > .env << EOF
DATABASE_URL=postgresql://utsav:postgres@localhost/ayush_db
# OPENAI_API_KEY=your_key_here
EOF
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${GREEN}✓ backend/.env exists${NC}"
fi

# Check PostgreSQL
echo "Checking PostgreSQL connection..."
if pg_isready -q; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    
    # Check/Create Database
    if psql -lqt | cut -d \| -f 1 | grep -qw ayush_db; then
        echo -e "${GREEN}✓ Database 'ayush_db' exists${NC}"
    else
        echo "Creating database 'ayush_db'..."
        createdb ayush_db || echo "If creation failed, you might need to run 'createdb ayush_db' manually."
    fi

    # Run Migrations
    echo "Running Data Migration..."
    python migrate_data.py

else
    echo -e "${RED}⚠ PostgreSQL is NOT running. Please start it and run 'python migrate_data.py' manually.${NC}"
fi

# Check ML Models
if [ ! -f "models/outcome_model.pkl" ] && [ -f "ayush_ml_pipeline.py" ]; then
    echo "Training ML models (first run)..."
    python ayush_ml_pipeline.py
    echo -e "${GREEN}✓ Models trained${NC}"
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
    echo -e "${RED}Error: Node.js/npm is required.${NC}"
    exit 1
fi

# Install Deps
echo "Installing Node.js dependencies..."
npm install

# Create .env.local if missing
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
PYTHON_BACKEND_URL=http://localhost:8000
EOF
    echo -e "${GREEN}✓ Created .env.local${NC}"
fi

echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
echo "=========================================="
echo -e "${GREEN}SETUP PREPARATION COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "To start the application run these two commands in separate terminals:"
echo ""
echo -e "${YELLOW}1. Backend:${NC}"
echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo ""
echo -e "${YELLOW}2. Frontend:${NC}"
echo "   npm run dev"
echo ""
