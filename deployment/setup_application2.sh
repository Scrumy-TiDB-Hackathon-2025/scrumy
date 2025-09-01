#!/bin/bash

# Application Setup Script for ScrumBot
# Run after basic EC2 setup is complete

set -e

echo "🔧 Setting up ScrumBot application..."

# Navigate to project directory
cd ~/scrumy

# Setup AI Processing
echo "🤖 Setting up AI processing..."
cd ai_processing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Verify key dependencies
python -c "import fastapi, websockets; print('Dependencies OK')"



# Build Whisper.cpp
echo "🎤 Building Whisper.cpp..."
chmod +x build_whisper2.sh
./build_whisper.sh

# Verify Whisper build
if [ -f "whisper.cpp/build/bin/whisper-cli" ]; then
    echo "✅ Whisper.cpp built successfully"
else
    echo "❌ Whisper.cpp build failed"
    exit 1
fi

# Setup Integration System
echo "🔗 Setting up integration system..."
cd ../integration
npm install

# Verify integration dependencies
if [ -d "node_modules" ]; then
    echo "✅ Integration dependencies installed"
else
    echo "❌ Integration npm install failed"
    exit 1
fi

# Setup environment files
echo "📝 Setting up environment files..."
cd ../shared

echo ""
echo "🔧 MANUAL CONFIGURATION REQUIRED:"
echo "1. Copy environment template: cp .env.example .tidb.env"
echo "2. Edit .tidb.env with your credentials:"
echo "   - TIDB_CONNECTION_STRING"
echo "   - GROQ_API_KEY"
echo "   - NOTION_TOKEN (optional)"
echo "   - CLICKUP_TOKEN (optional)"
echo "   - SLACK_BOT_TOKEN (optional)"
echo ""
echo "3. Setup Groq API key in ai_processing:"
echo "   cd ~/scrumy/ai_processing && ./setup_groq_key.sh"
echo ""
echo "4. Run PM2 setup: ./setup_pm2.sh"