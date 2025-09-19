#!/bin/bash

echo "🔍 Extracting ngrok URLs..."

# Get ngrok tunnels info
NGROK_INFO=$(curl -s http://localhost:4040/api/tunnels)

# Extract REST API URL (port 8000)
REST_URL=$(echo "$NGROK_INFO" | jq -r '.tunnels[] | select(.config.addr | contains("8000")) | .public_url')

# Extract WebSocket URL (port 8080) and convert to wss://
WS_URL=$(echo "$NGROK_INFO" | jq -r '.tunnels[] | select(.config.addr | contains("8080")) | .public_url' | sed 's/https:/wss:/')

echo "📡 REST API URL: $REST_URL"
echo "🔌 WebSocket URL: $WS_URL/ws"

# Update Chrome extension config
echo "
🔧 Update Chrome extension config.js:
BACKEND_URL: '$REST_URL'
WEBSOCKET_URL: '$WS_URL/ws'
"