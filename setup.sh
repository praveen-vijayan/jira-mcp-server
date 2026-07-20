#!/bin/bash
# Setup script for Jira MCP Server

echo "🚀 Setting up Jira MCP Server..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Jira credentials!"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Jira credentials"
echo "2. Activate the virtual environment: source .venv/bin/activate"
echo "3. Run the server:"
echo "   - Stdio mode: python server.py"
echo "   - SSE mode: python server.py --transport sse"
echo ""
echo "For MCP Inspector, connect to: http://localhost:8000/mcp"

# Made with Bob
