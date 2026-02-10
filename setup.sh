#!/bin/bash
# setup.sh - Quick setup script for Agri-Mind

set -e

echo "🌾 Agri-Mind - Setup Script"
echo "============================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate || source venv/Scripts/activate  # Windows compatibility
echo "✓ Virtual environment created"

# Upgrade pip
echo ""
echo "🔧 Upgrading pip..."
pip install --upgrade pip wheel setuptools
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "✓ All dependencies installed"

# Create .env file
echo ""
echo "⚙️ Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env file created from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your credentials:"
    echo "   SENTINELHUB_CLIENT_ID=your_client_id"
    echo "   SENTINELHUB_CLIENT_SECRET=your_client_secret"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Create demo_data directory
echo ""
echo "📁 Setting up demo data directory..."
mkdir -p demo_data
mkdir -p logs
echo "✓ Directories created"

# Test imports
echo ""
echo "🧪 Testing imports..."
python3 -c "from utils.satellite import *; from utils.indices import *; from utils.arabic_nlg import *" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All imports successful"
else
    echo "⚠️  Some imports failed - check dependencies"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the dashboard:"
echo "   source venv/bin/activate  (or venv\\Scripts\\activate on Windows)"
echo "   streamlit run app.py"
echo ""
echo "📖 For more info, see README.md"
echo ""
