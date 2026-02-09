#!/bin/bash
# ============================================
# Backend Startup Script (Codespaces)
# Run from: /workspaces/Agentic_WorkFlow_Platform/apps/api
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Backend Setup - Agentic Workflow Platform"
echo "=========================================="

# 1. Create data directory for SQLite
echo "[1/5] Creating data directories..."
mkdir -p data/db

# 2. Create virtual environment if it doesn't exist
if [ ! -d "venv312" ]; then
    echo "[2/5] Creating virtual environment..."
    python3 -m venv venv312
else
    echo "[2/5] Virtual environment already exists."
fi

# 3. Activate virtual environment
echo "[3/5] Activating virtual environment..."
source venv312/bin/activate

# 4. Install dependencies
echo "[4/5] Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
# Install torch CPU (needed for Qwen3-Reranker and embeddings)
pip install torch --index-url https://download.pytorch.org/whl/cpu -q
pip install transformers -q

# 5. Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "[5/5] Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit apps/api/.env and set your API keys:"
    echo "    GOOGLE_API_KEY=\"your-gemini-key-here\""
    echo ""
else
    echo "[5/5] .env file already exists."
fi

echo ""
echo "=========================================="
echo "  Starting Backend Server on port 8000"
echo "=========================================="
echo ""

# Start uvicorn with PYTHONPATH set
PYTHONPATH=src python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
