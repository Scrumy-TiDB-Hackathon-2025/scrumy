#!/bin/bash

# Fixed PM2 Restart Script with Reliable Environment Loading
# Ensures Groq API key is properly loaded on EC2

set -e

echo "🔄 Restarting PM2 processes with environment (FIXED VERSION)..."

# Get the correct project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_PROCESSING_DIR="$PROJECT_DIR/ai_processing"

echo "📁 Project directory: $PROJECT_DIR"
echo "📁 AI processing directory: $AI_PROCESSING_DIR"

# Function to find .env file
find_env_file() {
    local env_file=""

    # Check multiple possible locations
    if [ -f "$AI_PROCESSING_DIR/.env" ]; then
        env_file="$AI_PROCESSING_DIR/.env"
    elif [ -f "$PROJECT_DIR/.env" ]; then
        env_file="$PROJECT_DIR/.env"
    elif [ -f "$PROJECT_DIR/shared/.env" ]; then
        env_file="$PROJECT_DIR/shared/.env"
    elif [ -f "$AI_PROCESSING_DIR/.env.prod" ]; then
        env_file="$AI_PROCESSING_DIR/.env.prod"
    fi

    echo "$env_file"
}

# Find and validate .env file
ENV_FILE=$(find_env_file)

if [ -z "$ENV_FILE" ] || [ ! -f "$ENV_FILE" ]; then
    echo "❌ No .env file found! Checked locations:"
    echo "   - $AI_PROCESSING_DIR/.env"
    echo "   - $PROJECT_DIR/.env"
    echo "   - $PROJECT_DIR/shared/.env"
    echo "   - $AI_PROCESSING_DIR/.env.prod"
    echo ""
    echo "🔧 Create .env file with: ./ai_processing/setup_groq_key.sh"
    exit 1
fi

echo "📝 Found .env file: $ENV_FILE"

# Load and validate environment variables
echo "🔍 Loading environment variables..."

# Method 1: Source the file (for current shell)
set -a
source "$ENV_FILE"
set +a

# Method 2: Export specific variables (more reliable)
while IFS= read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    # Extract key=value pairs
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"

        # Remove quotes if present
        value=$(echo "$value" | sed 's/^["\x27]\|["\x27]$//g')

        # Export the variable
        export "$key"="$value"

        # Show masked values for sensitive keys
        if [[ "$key" == "GROQ_API_KEY" ]]; then
            if [ -n "$value" ]; then
                masked_key="${value:0:10}...${value: -4}"
                echo "   ✅ $key: $masked_key"
            else
                echo "   ❌ $key: EMPTY"
            fi
        elif [[ "$key" =~ (TOKEN|KEY|SECRET|PASSWORD) ]]; then
            echo "   ✅ $key: ***masked***"
        else
            echo "   ✅ $key: $value"
        fi
    fi
done < "$ENV_FILE"

# Validate critical environment variables
echo ""
echo "🔍 Validating critical environment variables..."

if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ GROQ_API_KEY is not set!"
    echo "🔧 Run: ./ai_processing/setup_groq_key.sh"
    exit 1
fi

if [[ ! "$GROQ_API_KEY" =~ ^gsk_ ]]; then
    echo "⚠️ GROQ_API_KEY doesn't start with 'gsk_' - may be invalid"
fi

echo "✅ Environment validation passed"

# Stop existing processes (with better error handling)
echo ""
echo "⏹️ Stopping existing PM2 processes..."

# Stop processes individually to avoid errors if they don't exist
for process in scrumbot-backend scrumbot-websocket; do
    if pm2 list | grep -q "$process"; then
        echo "   Stopping $process..."
        pm2 stop "$process" 2>/dev/null || true
        pm2 delete "$process" 2>/dev/null || true
    else
        echo "   $process not running"
    fi
done

# Navigate to ai_processing directory
cd "$AI_PROCESSING_DIR"

# Create temporary ecosystem file with actual environment values
ECOSYSTEM_FILE="/tmp/scrumbot-ecosystem-$(date +%s).js"
echo "📝 Creating PM2 ecosystem config: $ECOSYSTEM_FILE"

cat > "$ECOSYSTEM_FILE" << EOF
module.exports = {
  apps: [
    {
      name: 'scrumbot-backend',
      script: 'start_backend.py',
      interpreter: './venv/bin/python',
      cwd: '$AI_PROCESSING_DIR',
      env: {
        GROQ_API_KEY: '$GROQ_API_KEY',
        TIDB_CONNECTION_STRING: '$TIDB_CONNECTION_STRING',
        NOTION_TOKEN: '$NOTION_TOKEN',
        NOTION_DATABASE_ID: '$NOTION_DATABASE_ID',
        SLACK_BOT_TOKEN: '$SLACK_BOT_TOKEN',
        CLICKUP_TOKEN: '$CLICKUP_TOKEN',
        HOST: '${HOST:-0.0.0.0}',
        PORT: '${PORT:-5167}',
        ENVIRONMENT: '${ENVIRONMENT:-production}',
        DEBUG: '${DEBUG:-false}'
      },
      error_file: '$AI_PROCESSING_DIR/logs/backend-error.log',
      out_file: '$AI_PROCESSING_DIR/logs/backend-out.log',
      log_file: '$AI_PROCESSING_DIR/logs/backend-combined.log',
      time: true,
      max_restarts: 5,
      min_uptime: '10s',
      restart_delay: 5000
    },
    {
      name: 'scrumbot-websocket',
      script: 'start_websocket_server.py',
      interpreter: './venv/bin/python',
      cwd: '$AI_PROCESSING_DIR',
      env: {
        GROQ_API_KEY: '$GROQ_API_KEY',
        TIDB_CONNECTION_STRING: '$TIDB_CONNECTION_STRING',
        NOTION_TOKEN: '$NOTION_TOKEN',
        NOTION_DATABASE_ID: '$NOTION_DATABASE_ID',
        SLACK_BOT_TOKEN: '$SLACK_BOT_TOKEN',
        CLICKUP_TOKEN: '$CLICKUP_TOKEN',
        HOST: '${HOST:-0.0.0.0}',
        PORT: '${PORT:-8080}',
        ENVIRONMENT: '${ENVIRONMENT:-production}',
        DEBUG: '${DEBUG:-false}'
      },
      error_file: '$AI_PROCESSING_DIR/logs/websocket-error.log',
      out_file: '$AI_PROCESSING_DIR/logs/websocket-out.log',
      log_file: '$AI_PROCESSING_DIR/logs/websocket-combined.log',
      time: true,
      max_restarts: 5,
      min_uptime: '10s',
      restart_delay: 5000
    }
  ]
};
EOF

# Ensure log directory exists
mkdir -p "$AI_PROCESSING_DIR/logs"

# Start processes using ecosystem file
echo ""
echo "🚀 Starting PM2 processes with ecosystem config..."
pm2 start "$ECOSYSTEM_FILE"

# Wait for processes to start
sleep 3

# Verify processes are running
echo ""
echo "🔍 Verifying process startup..."
if pm2 list | grep -q "scrumbot-backend.*online"; then
    echo "   ✅ scrumbot-backend: ONLINE"
else
    echo "   ❌ scrumbot-backend: FAILED"
    echo "   📋 Logs: pm2 logs scrumbot-backend --lines 10"
fi

if pm2 list | grep -q "scrumbot-websocket.*online"; then
    echo "   ✅ scrumbot-websocket: ONLINE"
else
    echo "   ❌ scrumbot-websocket: FAILED"
    echo "   📋 Logs: pm2 logs scrumbot-websocket --lines 10"
fi

# Save PM2 configuration
echo ""
echo "💾 Saving PM2 configuration..."
pm2 save

# Clean up temporary ecosystem file
rm -f "$ECOSYSTEM_FILE"

echo ""
echo "✅ PM2 processes restarted with environment!"
echo ""
echo "📊 Quick Status Check:"
pm2 status

echo ""
echo "🧪 Test endpoints:"
echo "   Backend:   curl http://localhost:5167/health"
echo "   WebSocket: curl http://localhost:8080/health"
echo ""
echo "📋 Monitor commands:"
echo "   pm2 status                           # Process status"
echo "   pm2 logs scrumbot-backend --lines 5  # Backend logs"
echo "   pm2 logs scrumbot-websocket --lines 5 # WebSocket logs"
echo "   pm2 monit                            # Real-time monitoring"
echo ""
echo "🔧 If issues persist:"
echo "   1. Check logs: pm2 logs --lines 20"
echo "   2. Restart individual: pm2 restart scrumbot-websocket"
echo "   3. Manual test: cd $AI_PROCESSING_DIR && source $ENV_FILE && python start_websocket_server.py"
