#!/bin/bash

# AYUSH ML Pipeline Integration - Setup Script
# This script sets up both the Python backend and Next.js frontend

set -e  # Exit on error

echo "=========================================="
echo "AYUSH ML Pipeline Integration - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Step 1: Setup Python Backend
echo -e "${YELLOW}Step 1: Setting up Python backend...${NC}"
cd backend

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if models exist
if [ ! -f "models/outcome_model.pkl" ]; then
    echo -e "${YELLOW}Warning: ML models not found in backend/models/${NC}"
    echo "You need to train the models first. Options:"
    echo "  1. Run: python ayush_ml_pipeline.py (from backend directory)"
    echo "  2. Or copy from ayush_calude: cp ../ayush_calude/*.pkl models/"
    echo ""
    read -p "Do you want to copy models from ayush_calude now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "../ayush_calude/outcome_model.pkl" ]; then
            echo "Copying models..."
            cp ../ayush_calude/*.pkl models/ 2>/dev/null || echo "Some model files not found"
            echo -e "${GREEN}✓ Models copied${NC}"
        else
            echo -e "${YELLOW}Models not found in ayush_calude. You'll need to train them.${NC}"
        fi
    fi
fi

# Check if data exists
if [ ! -f "data/public_health_trends.csv" ]; then
    echo "Copying trend data..."
    if [ -f "../ayush_calude/public_health_trends.csv" ]; then
        cp ../ayush_calude/public_health_trends.csv data/
        echo -e "${GREEN}✓ Trend data copied${NC}"
    else
        echo -e "${YELLOW}Warning: Trend data not found. Forecast features may not work.${NC}"
    fi
fi

cd ..
echo -e "${GREEN}✓ Python backend setup complete${NC}"
echo ""

# Step 2: Setup Next.js Frontend
echo -e "${YELLOW}Step 2: Setting up Next.js frontend...${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

echo -e "${GREEN}✓ Next.js frontend setup complete${NC}"
echo ""

# Step 3: Environment Variables
echo -e "${YELLOW}Step 3: Checking environment variables...${NC}"

if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file..."
    cat > .env.local << EOF
# Python Backend URL
PYTHON_BACKEND_URL=http://localhost:8000

# Next.js Public API URL (for client-side requests)
NEXT_PUBLIC_API_URL=http://localhost:3000
EOF
    echo -e "${GREEN}✓ Created .env.local${NC}"
else
    echo -e "${GREEN}✓ .env.local already exists${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "To start the application:"
echo ""
echo -e "${YELLOW}Terminal 1 - Python Backend:${NC}"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload --port 8000"
echo ""
echo -e "${YELLOW}Terminal 2 - Next.js Frontend:${NC}"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
