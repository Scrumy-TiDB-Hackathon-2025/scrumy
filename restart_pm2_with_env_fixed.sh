#!/bin/bash

# Fixed PM2 Restart Script - Uses Direct PM2 Commands Like setup_pm2.sh
# Ensures proper environment loading and individual process creation

set -e

echo "🔄 Restarting PM2 processes with environment..."

# Get the correct project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_PROCESSING_DIR="$PROJECT_DIR/ai_processing"

echo "📁 Project directory: $PROJECT_DIR"
echo "📁 AI processing directory: $AI_PROCESSING_DIR"

# Find and validate .env file
ENV_FILE=""
if [ -f "$AI_PROCESSING_DIR/.env" ]; then
    ENV_FILE="$AI_PROCESSING_DIR/.env"
elif [ -f "$PROJECT_DIR/.env" ]; then
    ENV_FILE="$PROJECT_DIR/.env"
else
    echo "❌ No .env file found!"
    echo "   Checked: $AI_PROCESSING_DIR/.env"
    echo "   Checked: $PROJECT_DIR/.env"
    echo "🔧 Create .env file with: ./ai_processing/setup_groq_key_fixed.sh"
    exit 1
fi

echo "📝 Loading environment variables from $ENV_FILE..."

# Load environment variables (method that works with PM2)
set -a
source "$ENV_FILE"
set +a

# Show masked GROQ key if present
if [ -n "$GROQ_API_KEY" ]; then
    masked_key="${GROQ_API_KEY:0:8}...${GROQ_API_KEY: -4}"
    echo "   ✅ GROQ_API_KEY: $masked_key"
else
    echo "❌ GROQ_API_KEY not found in environment!"
    exit 1
fi

echo "✅ Environment variables loaded"

# Stop existing processes
echo ""
echo "⏹️ Stopping existing processes..."
pm2 stop scrumbot-backend scrumbot-websocket scrumbot-chatbot 2>/dev/null || true
pm2 delete scrumbot-backend scrumbot-websocket scrumbot-chatbot 2>/dev/null || true

# Navigate to ai_processing directory
cd "$AI_PROCESSING_DIR"

# Start processes using direct PM2 commands (same as setup_pm2.sh)
echo ""
echo "🚀 Starting PM2 processes..."
pm2 start --name scrumbot-backend --interpreter venv/bin/python start_backend.py --update-env
pm2 start --name scrumbot-websocket --interpreter venv/bin/python start_websocket_server.py --update-env

# Start AI Chatbot
echo "🤖 Starting AI Chatbot..."
cd ../ai_chatbot
pm2 start --name scrumbot-chatbot --interpreter python run_server.py --update-env
cd ../ai_processing

# Save PM2 configuration
echo ""
echo "💾 Saving PM2 configuration..."
pm2 save

# Wait for processes to start
sleep 3

# Verify processes are running
echo ""
echo "🔍 Verifying process startup..."
if pm2 list | grep -q "scrumbot-backend.*online"; then
    echo "   ✅ scrumbot-backend: ONLINE"
else
    echo "   ❌ scrumbot-backend: FAILED"
fi

if pm2 list | grep -q "scrumbot-websocket.*online"; then
    echo "   ✅ scrumbot-websocket: ONLINE"
else
    echo "   ❌ scrumbot-websocket: FAILED"
fi

if pm2 list | grep -q "scrumbot-chatbot.*online"; then
    echo "   ✅ scrumbot-chatbot: ONLINE"
else
    echo "   ❌ scrumbot-chatbot: FAILED"
fi

echo ""
echo "✅ PM2 processes restarted with environment!"
echo ""
echo "📊 Quick Status Check:"
pm2 status

echo ""
echo "🧪 Test endpoints:"
echo "   Backend:   curl http://localhost:5167/health"
echo "   WebSocket: curl http://localhost:8080/health"
echo "   Chatbot:   curl http://localhost:8001/health"
echo ""
echo "📋 Monitor commands:"
echo "   pm2 status                            # Process status"
echo "   pm2 logs scrumbot-backend --lines 5   # Backend logs"
echo "   pm2 logs scrumbot-websocket --lines 5 # WebSocket logs"
echo "   pm2 logs scrumbot-chatbot --lines 5   # Chatbot logs"
echo "   pm2 monit                             # Real-time monitoring"
echo ""
echo "🔧 If issues persist:"
echo "   1. Check logs: pm2 logs --lines 20"
echo "   2. Restart individual: pm2 restart scrumbot-websocket"
echo "   3. Manual test: cd $AI_PROCESSING_DIR && python start_websocket_server.py"
