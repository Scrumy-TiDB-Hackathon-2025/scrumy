#!/bin/bash

# Restart PM2 processes with environment variables
# Use this after updating .env file

set -e

echo "🔄 Restarting PM2 processes with environment..."

# Navigate to project root first
cd ~/scrumy

# Load .env file if it exists (check both locations)
if [ -f "ai_processing/.env" ]; then
    echo "📝 Loading environment variables from ai_processing/.env..."
    export $(grep -v '^#' ai_processing/.env | xargs)
    echo "✅ Environment variables loaded from ai_processing/.env"
elif [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
    
    # Show masked GROQ key if present
    if [ -n "$GROQ_API_KEY" ]; then
        masked_key="${GROQ_API_KEY:0:8}...${GROQ_API_KEY: -4}"
        echo "   GROQ_API_KEY: $masked_key"
    fi
else
    echo "⚠️  No .env file found - using system environment"
fi

# Stop existing processes
echo "⏹️  Stopping existing processes..."
pm2 stop scrumbot-backend scrumbot-websocket 2>/dev/null || true

# Navigate to ai_processing for PM2 commands
cd ~/scrumy/ai_processing

# Start processes with updated environment
echo "🚀 Starting processes with updated environment..."
pm2 start --name scrumbot-backend --interpreter venv/bin/python start_backend.py --update-env
pm2 start --name scrumbot-websocket --interpreter venv/bin/python start_websocket_server.py --update-env

# Save configuration
pm2 save

echo "✅ PM2 processes restarted with environment!"
echo ""
echo "📊 Check status:"
echo "  pm2 status"
echo "  pm2 logs scrumbot-websocket --lines 10"