#!/bin/bash
# VoidView 依赖安装脚本 (Linux/Mac)

set -e  # 遇到错误立即退出

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Installing VoidView dependencies..."

echo ""
echo "[1/3] Installing shared package..."
(cd shared && pip install -e .)

echo ""
echo "[2/3] Installing server package..."
(cd server && pip install -e .)

echo ""
echo "[3/3] Installing client package..."
(cd client && pip install -e .)

echo ""
echo "========================================"
echo "Done! All dependencies installed."
echo "========================================"
echo ""
echo "To start server: python run_server.py"
echo "To start client: python run_client.py"
