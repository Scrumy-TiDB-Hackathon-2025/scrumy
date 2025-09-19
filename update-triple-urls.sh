#!/bin/bash

# Update Chrome Extension URLs after triple ngrok setup
# Extracts URLs from ngrok and updates config.js

set -e

echo "🔗 Updating Chrome extension URLs from triple ngrok..."

# Extract URLs from ngrok web interfaces
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

# Convert WebSocket URL to WSS
WS_URL_WSS=$(echo "$WS_URL" | sed 's/https:/wss:/')/ws

echo "📋 Extracted URLs:"
echo "  REST API: $API_URL"
echo "  WebSocket: $WS_URL_WSS"
echo "  AI Chatbot: $CHATBOT_URL"

# Update Chrome extension config.js
CONFIG_FILE="chrome_extension/config.js"

if [ -f "$CONFIG_FILE" ]; then
    echo "📝 Updating $CONFIG_FILE..."
    
    # Create backup
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    
    # Update URLs in prod config
    sed -i.tmp "s|BACKEND_URL: 'https://[^']*'|BACKEND_URL: '$API_URL'|g" "$CONFIG_FILE"
    sed -i.tmp "s|WEBSOCKET_URL: 'wss://[^']*'|WEBSOCKET_URL: '$WS_URL_WSS'|g" "$CONFIG_FILE"
    sed -i.tmp "s|CHATBOT_URL: 'https://[^']*'|CHATBOT_URL: '$CHATBOT_URL'|g" "$CONFIG_FILE"
    
    # Clean up temp file
    rm -f "$CONFIG_FILE.tmp"
    
    echo "✅ Updated Chrome extension config"
else
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Update frontend environment if it exists
FRONTEND_ENV="frontend_dashboard/.env.local"
if [ -f "$FRONTEND_ENV" ]; then
    echo "📝 Updating frontend environment..."
    
    # Create backup
    cp "$FRONTEND_ENV" "$FRONTEND_ENV.backup"
    
    # Update or add environment variables
    if grep -q "NEXT_PUBLIC_API_URL" "$FRONTEND_ENV"; then
        sed -i.tmp "s|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=$API_URL|g" "$FRONTEND_ENV"
    else
        echo "NEXT_PUBLIC_API_URL=$API_URL" >> "$FRONTEND_ENV"
    fi
    
    if grep -q "NEXT_PUBLIC_WS_URL" "$FRONTEND_ENV"; then
        sed -i.tmp "s|NEXT_PUBLIC_WS_URL=.*|NEXT_PUBLIC_WS_URL=$WS_URL_WSS|g" "$FRONTEND_ENV"
    else
        echo "NEXT_PUBLIC_WS_URL=$WS_URL_WSS" >> "$FRONTEND_ENV"
    fi
    
    if grep -q "NEXT_PUBLIC_CHATBOT_URL" "$FRONTEND_ENV"; then
        sed -i.tmp "s|NEXT_PUBLIC_CHATBOT_URL=.*|NEXT_PUBLIC_CHATBOT_URL=$CHATBOT_URL|g" "$FRONTEND_ENV"
    else
        echo "NEXT_PUBLIC_CHATBOT_URL=$CHATBOT_URL" >> "$FRONTEND_ENV"
    fi
    
    # Clean up temp file
    rm -f "$FRONTEND_ENV.tmp"
    
    echo "✅ Updated frontend environment"
fi

echo ""
echo "🧪 Test the updated URLs:"
echo "  curl $API_URL/health              # Backend API"
echo "  curl $WS_URL/health               # WebSocket health"
echo "  curl $CHATBOT_URL/health          # AI Chatbot health"
echo ""
echo "🔄 Reload Chrome extension to use new URLs"
echo "💡 Backup files created with .backup extension"