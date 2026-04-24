#!/usr/bin/env bash
# SentinelLine quick-start
set -e
cd "$(dirname "$0")"

echo "=== SentinelLine - Manufacturing Anomaly Detection ==="

# Install deps (skip gracefully if locked down)
if command -v pip3 &>/dev/null; then
    echo "[*] Installing Python dependencies..."
    pip3 install -r requirements.txt 2>/dev/null || echo "[!] Some deps failed -- core may still work"
fi

echo "[*] Launching server on port ${PORT:-8080}..."
python3 run.py
