#!/bin/bash
# Quick start script for Claude Code Server

set -e

echo "🚀 Claude Code Server - Quick Start"
echo "===================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $PYTHON_VERSION"

# Check for API key
if [ -z "$CLAUDE_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: CLAUDE_API_KEY or ANTHROPIC_API_KEY not set"
    echo "   Set it with: export CLAUDE_API_KEY='your-key-here'"
    echo ""
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  1. Set your API key: export CLAUDE_API_KEY='your-key-here'"
echo "  2. Run: python -m claude_code_server.server"
echo ""
echo "Or use Docker:"
echo "  1. Copy .env.example to .env and fill in your API key"
echo "  2. Run: docker-compose up"
echo ""
echo "Test the server:"
echo "  curl http://localhost:8000/health"
echo ""
echo "Run example client:"
echo "  python example_client.py"
echo ""
