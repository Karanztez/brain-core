#!/usr/bin/env bash
# Script to install Alibaba Open Code Review (ocr) on Ubuntu/Debian Linux VPS

set -e

echo "🚀 Installing Alibaba Open Code Review (ocr) on Linux VPS..."

# 1. Ensure curl and ca-certificates are installed
if ! command -v curl &> /dev/null; then
    echo "📦 Installing curl..."
    sudo apt-get update && sudo apt-get install -y curl ca-certificates
fi

# 2. Install Node.js LTS (v20) if npm is missing
if ! command -v npm &> /dev/null; then
    echo "📦 Installing Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# 3. Install Alibaba Open Code Review CLI globally
echo "🧠 Installing @alibaba-group/open-code-review CLI globally..."
sudo npm install -g @alibaba-group/open-code-review

# 4. Verify installation
if command -v ocr &> /dev/null; then
    echo "✅ Alibaba Open Code Review (ocr) installed successfully!"
    ocr --version
else
    echo "⚠️ Installation completed, please restart your shell or check PATH."
fi
