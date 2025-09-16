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

# Find and load .env file from ai_processing directory
ENV_FILE=""
if [ -f "$AI_PROCESSING_DIR/.env" ]; then
    ENV_FILE="$AI_PROCESSING_DIR/.env"
elif [ -f "$AI_PROCESSING_DIR/.env/.env" ]; then
    ENV_FILE="$AI_PROCESSING_DIR/.env/.env"
fi

if [ -n "$ENV_FILE" ]; then
    echo "📝 Loading environment variables from $ENV_FILE..."
    set -a  # automatically export all variables
    source "$ENV_FILE"
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
    echo "❌ No .env file found in $AI_PROCESSING_DIR"
    echo "   Available .env files:"
    find "$AI_PROCESSING_DIR" -name ".env" -type f 2>/dev/null || echo "   None found"
    exit 1
fi

# Stop existing processes
echo "⏹️  Stopping existing processes..."
pm2 stop scrumbot-backend scrumbot-websocket scrumbot-chatbot 2>/dev/null || true
pm2 delete scrumbot-backend scrumbot-websocket scrumbot-chatbot 2>/dev/null || true

# Navigate to ai_processing directory
cd "$AI_PROCESSING_DIR"

# Create PM2 ecosystem file with environment variables
echo "📝 Creating PM2 ecosystem config..."
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'scrumbot-backend',
      script: 'start_backend.py',
      interpreter: './venv/bin/python',
      env: {
        GROQ_API_KEY: '$GROQ_API_KEY'
      }
    },
    {
      name: 'scrumbot-websocket', 
      script: 'start_websocket_server.py',
      interpreter: './venv/bin/python',
      env: {
        GROQ_API_KEY: '$GROQ_API_KEY'
      }
    },
    {
      name: 'scrumbot-chatbot',
      script: 'run_server.py',
      interpreter: 'python',
      cwd: '../ai_chatbot',
      env: {
        GROQ_API_KEY: '$GROQ_API_KEY'
      }
    }
  ]
};
EOF

# Start processes using ecosystem file
echo "🚀 Starting processes with ecosystem config..."
pm2 start ecosystem.config.js

# Save configuration
pm2 save

echo "✅ PM2 processes restarted with environment!"
echo ""
echo "📊 Check status:"
echo "  pm2 status"
echo "  pm2 logs scrumbot-backend --lines 5"
echo "  pm2 logs scrumbot-websocket --lines 5"
echo "  pm2 logs scrumbot-chatbot --lines 5"