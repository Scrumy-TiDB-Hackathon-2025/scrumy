#!/bin/bash

# Restart PM2 processes with environment variables
# Use this after updating .env file

set -e

echo "🔄 Restarting PM2 processes with environment..."

# Get the correct project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_PROCESSING_DIR="$PROJECT_DIR/ai_processing"

echo "📁 Project directory: $PROJECT_DIR"
echo "📁 AI processing directory: $AI_PROCESSING_DIR"

# Load .env file from ai_processing directory
if [ -f "$AI_PROCESSING_DIR/.env" ]; then
    echo "📝 Loading environment variables from $AI_PROCESSING_DIR/.env..."
    set -a  # automatically export all variables
    source "$AI_PROCESSING_DIR/.env"
    set +a  # stop automatically exporting
    echo "✅ Environment variables loaded"
    
    # Show masked GROQ key if present
    if [ -n "$GROQ_API_KEY" ]; then
        masked_key="${GROQ_API_KEY:0:8}...${GROQ_API_KEY: -4}"
        echo "   GROQ_API_KEY: $masked_key"
    else
        echo "❌ GROQ_API_KEY not found in environment!"
    fi
else
    echo "❌ No .env file found at $AI_PROCESSING_DIR/.env"
    echo "   Run: cd ai_processing && ./setup_groq_key.sh"
    exit 1
fi

# Stop existing processes
echo "⏹️  Stopping existing processes..."
pm2 stop scrumbot-backend scrumbot-websocket 2>/dev/null || true
pm2 delete scrumbot-backend scrumbot-websocket 2>/dev/null || true

# Navigate to ai_processing directory
cd "$AI_PROCESSING_DIR"

# Start processes with environment variables
echo "🚀 Starting processes with environment variables..."
GROQ_API_KEY="$GROQ_API_KEY" pm2 start --name scrumbot-backend --interpreter ./venv/bin/python start_backend.py
GROQ_API_KEY="$GROQ_API_KEY" pm2 start --name scrumbot-websocket --interpreter ./venv/bin/python start_websocket_server.py

# Save configuration
pm2 save

echo "✅ PM2 processes restarted with environment!"
echo ""
echo "📊 Check status:"
echo "  pm2 status"
echo "  pm2 logs scrumbot-backend --lines 5"
echo "  pm2 logs scrumbot-websocket --lines 5"