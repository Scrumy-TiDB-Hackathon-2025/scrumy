#!/bin/bash

# Triple ngrok Setup - Three accounts for REST API, WebSocket, and AI Chatbot
# Bypasses free account 1-tunnel limitation

set -e

echo "🌐 Setting up triple ngrok tunnels with three accounts..."

# Config files for three accounts
NGROK_CONFIG_1="$HOME/.config/ngrok/ngrok-account1.yml"
NGROK_CONFIG_2="$HOME/.config/ngrok/ngrok-account2.yml"
NGROK_CONFIG_3="$HOME/.config/ngrok/ngrok-account3.yml"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok not installed. Install with: sudo apt install ngrok"
    exit 1
fi

# Function to setup ngrok config
setup_ngrok_config() {
    local config_file=$1
    local account_name=$2
    local token_var=$3
    local web_port=$4
    
    if [ ! -f "$config_file" ]; then
        echo "⚙️  Setting up ngrok config for $account_name..."
        
        if [ -z "${!token_var}" ]; then
            echo ""
            echo "🔑 Enter ngrok auth token for $account_name:"
            echo "   Get token from: https://dashboard.ngrok.com/get-started/your-authtoken"
            read -p "Token: " token
            
            if [ -z "$token" ]; then
                echo "❌ Token required for $account_name"
                exit 1
            fi
        else
            token="${!token_var}"
        fi
        
        # Create config file
        mkdir -p "$(dirname "$config_file")"
        cat > "$config_file" << EOF
version: "2"
authtoken: $token
web_addr: localhost:$web_port
EOF
        
        echo "✅ Created config for $account_name"
    else
        echo "✅ Config exists for $account_name"
    fi
}

# Setup configs for all three accounts
setup_ngrok_config "$NGROK_CONFIG_1" "Account 1 (REST API)" "NGROK_TOKEN_1" "4040"
setup_ngrok_config "$NGROK_CONFIG_2" "Account 2 (WebSocket)" "NGROK_TOKEN_2" "4042"
setup_ngrok_config "$NGROK_CONFIG_3" "Account 3 (AI Chatbot)" "NGROK_TOKEN_3" "4044"

echo ""
echo "🚀 Starting triple ngrok tunnels..."

# Start ngrok for REST API (Account 1)
echo "Starting REST API tunnel (Account 1)..."
ngrok http 5167 --config "$NGROK_CONFIG_1" --log stdout > /tmp/ngrok-api.log 2>&1 &
NGROK_PID_1=$!

# Start ngrok for WebSocket (Account 2) 
echo "Starting WebSocket tunnel (Account 2)..."
ngrok http 8080 --config "$NGROK_CONFIG_2" --log stdout > /tmp/ngrok-ws.log 2>&1 &
NGROK_PID_2=$!

# Start ngrok for AI Chatbot (Account 3)
echo "Starting AI Chatbot tunnel (Account 3)..."
ngrok http 8001 --config "$NGROK_CONFIG_3" --log stdout > /tmp/ngrok-chatbot.log 2>&1 &
NGROK_PID_3=$!

# Wait for tunnels to start
sleep 10

# Extract URLs from different web interfaces
echo "📋 Extracting tunnel URLs..."
API_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")
WS_URL=$(curl -s http://localhost:4042/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")
CHATBOT_URL=$(curl -s http://localhost:4044/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")

# Fallback: extract from logs if API fails
if [ -z "$API_URL" ]; then
    API_URL=$(grep -o 'https://[^[:space:]]*\.ngrok-free\.app' /tmp/ngrok-api.log | head -1)
fi

if [ -z "$WS_URL" ]; then
    WS_URL=$(grep -o 'https://[^[:space:]]*\.ngrok-free\.app' /tmp/ngrok-ws.log | head -1)
fi

if [ -z "$CHATBOT_URL" ]; then
    CHATBOT_URL=$(grep -o 'https://[^[:space:]]*\.ngrok-free\.app' /tmp/ngrok-chatbot.log | head -1)
fi

echo "✅ Triple ngrok tunnels active!"
echo ""
echo "🔗 Tunnel URLs:"
echo "  REST API: $API_URL"
echo "  WebSocket: $WS_URL"
echo "  AI Chatbot: $CHATBOT_URL"
echo ""
echo "📝 Update Chrome extension config.js:"
echo "  BACKEND_URL: '$API_URL'"
echo "  WEBSOCKET_URL: '$WS_URL'"
echo "  CHATBOT_URL: '$CHATBOT_URL'"
echo ""
echo "🧪 Test endpoints:"
echo "  curl $API_URL/health              # Backend API"
echo "  curl $WS_URL/health               # WebSocket health"
echo "  curl $CHATBOT_URL/health          # AI Chatbot health"
echo ""
echo "🌐 Web interfaces:"
echo "  Account 1: http://localhost:4040  # REST API tunnel"
echo "  Account 2: http://localhost:4042  # WebSocket tunnel"
echo "  Account 3: http://localhost:4044  # AI Chatbot tunnel"
echo ""
echo "🛑 To stop tunnels:"
echo "  kill $NGROK_PID_1 $NGROK_PID_2 $NGROK_PID_3"
echo ""
echo "📊 Monitor logs:"
echo "  tail -f /tmp/ngrok-api.log        # REST API logs"
echo "  tail -f /tmp/ngrok-ws.log         # WebSocket logs"
echo "  tail -f /tmp/ngrok-chatbot.log    # AI Chatbot logs"
echo ""

# Save PIDs for cleanup
echo "$NGROK_PID_1 $NGROK_PID_2 $NGROK_PID_3" > /tmp/ngrok-pids.txt

echo "✅ All three tunnels running in background"
echo "💡 Tip: Save your tokens as environment variables:"
echo "   export NGROK_TOKEN_1='your_first_token'"
echo "   export NGROK_TOKEN_2='your_second_token'"
echo "   export NGROK_TOKEN_3='your_third_token'"