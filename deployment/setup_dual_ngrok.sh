#!/bin/bash

# Dual ngrok Setup - Two accounts for REST API and WebSocket
# Bypasses free account 1-tunnel limitation

set -e

echo "🌐 Setting up dual ngrok tunnels with two accounts..."

# Config files for two accounts
NGROK_CONFIG_1="$HOME/.config/ngrok/ngrok-account1.yml"
NGROK_CONFIG_2="$HOME/.config/ngrok/ngrok-account2.yml"

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
web_addr: localhost:404$([[ "$account_name" == "Account 1" ]] && echo "0" || echo "1")
EOF
        
        echo "✅ Created config for $account_name"
    else
        echo "✅ Config exists for $account_name"
    fi
}

# Setup configs for both accounts
setup_ngrok_config "$NGROK_CONFIG_1" "Account 1 (REST API)" "NGROK_TOKEN_1"
setup_ngrok_config "$NGROK_CONFIG_2" "Account 2 (WebSocket)" "NGROK_TOKEN_2"

echo ""
echo "🚀 Starting dual ngrok tunnels..."

# Start ngrok for REST API (Account 1)
echo "Starting REST API tunnel (Account 1)..."
ngrok http 5167 --config "$NGROK_CONFIG_1" --log stdout > /tmp/ngrok-api.log 2>&1 &
NGROK_PID_1=$!

# Start ngrok for WebSocket (Account 2) 
echo "Starting WebSocket tunnel (Account 2)..."
ngrok http 8080 --config "$NGROK_CONFIG_2" --log stdout > /tmp/ngrok-ws.log 2>&1 &
NGROK_PID_2=$!

# Wait for tunnels to start
sleep 8

# Extract URLs from different web interfaces
echo "📋 Extracting tunnel URLs..."
API_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")
WS_URL=$(curl -s http://localhost:4041/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "")

# Fallback: extract from logs if API fails
if [ -z "$API_URL" ]; then
    API_URL=$(grep -o 'https://[^[:space:]]*\.ngrok-free\.app' /tmp/ngrok-api.log | head -1)
fi

if [ -z "$WS_URL" ]; then
    WS_URL=$(grep -o 'https://[^[:space:]]*\.ngrok-free\.app' /tmp/ngrok-ws.log | head -1)
fi

echo "✅ Dual ngrok tunnels active!"
echo ""
echo "🔗 Tunnel URLs:"
echo "  REST API: $API_URL"
echo "  WebSocket: $WS_URL"
echo ""
echo "📝 Update Chrome extension config.js:"
echo "  BACKEND_URL: '$API_URL'"
echo "  WEBSOCKET_URL: '$WS_URL'"
echo ""
echo "🧪 Test endpoints:"
echo "  curl $API_URL/health              # Backend API"
echo "  curl $WS_URL/health               # WebSocket health"
echo ""
echo "🌐 Web interfaces:"
echo "  Account 1: http://localhost:4040  # REST API tunnel"
echo "  Account 2: http://localhost:4041  # WebSocket tunnel"
echo ""
echo "🛑 To stop tunnels:"
echo "  kill $NGROK_PID_1 $NGROK_PID_2"
echo ""
echo "📊 Monitor logs:"
echo "  tail -f /tmp/ngrok-api.log        # REST API logs"
echo "  tail -f /tmp/ngrok-ws.log         # WebSocket logs"
echo ""

# Save PIDs for cleanup
echo "$NGROK_PID_1 $NGROK_PID_2" > /tmp/ngrok-pids.txt

echo "✅ Both tunnels running in background"
echo "💡 Tip: Save your tokens as environment variables:"
echo "   export NGROK_TOKEN_1='your_first_token'"
echo "   export NGROK_TOKEN_2='your_second_token'"