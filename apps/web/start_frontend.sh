#!/bin/bash
# ============================================
# Frontend Startup Script (Codespaces)
# Run from: /workspaces/Agentic_WorkFlow_Platform/apps/web
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Frontend Setup - Agentic Workflow Platform"
echo "=========================================="

# 1. Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "[1/3] Creating .env.local..."
    echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.local
else
    echo "[1/3] .env.local already exists."
fi

# 2. Install npm dependencies
echo "[2/3] Installing npm dependencies..."
npm install

# 3. Start the dev server
echo ""
echo "=========================================="
echo "  Starting Frontend Server on port 3000"
echo "=========================================="
echo ""

npm run dev
