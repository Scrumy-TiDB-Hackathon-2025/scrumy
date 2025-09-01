#!/bin/bash

# Cloudflare Tunnel for WebSocket (better than LocalTunnel)
# ngrok for REST API

set -e

echo "🌐 Setting up Cloudflare tunnel for WebSocket..."

# Install cloudflared if not present
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing Cloudflare Tunnel..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
fi

echo "🚀 Starting tunnels..."

# Start ngrok for REST API
ngrok http 5167 --log stdout > /tmp/ngrok-api.log 2>&1 &
NGROK_PID=$!

# Start Cloudflare for WebSocket
nohup cloudflared tunnel --url http://localhost:8080 > /tmp/cloudflare-ws.log 2>&1 &
CF_PID=$!
disown $CF_PID

# Wait for tunnels
sleep 5

# Extract URLs
API_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
WS_URL=$(grep -o 'https://.*\.trycloudflare\.com' /tmp/cloudflare-ws.log | head -1)

echo "✅ Tunnels active!"
echo ""
echo "🔗 URLs:"
echo "  REST API: $API_URL"
echo "  WebSocket: $WS_URL"
echo ""
echo "📝 Update Chrome extension config.js:"
echo "  BACKEND_URL: '$API_URL'"
echo "  WEBSOCKET_URL: '$WS_URL'"
echo ""
echo "🧪 Test:"
echo "  curl $API_URL/health"
echo "  curl $WS_URL/health"
echo ""
echo "🛑 To stop: kill $NGROK_PID $CF_PID"