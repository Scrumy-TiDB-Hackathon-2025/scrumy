#!/bin/bash

# Dual Tunnel Setup - ngrok for REST API, LocalTunnel for WebSocket
# Bypasses ngrok free account 1-tunnel limitation

set -e

echo "🌐 Setting up dual tunnels..."

# Install LocalTunnel for WebSocket
if ! command -v lt &> /dev/null; then
    echo "📦 Installing LocalTunnel..."
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    sudo npm install -g localtunnel
fi

# Check ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok not installed. Install with: sudo apt install ngrok"
    exit 1
fi

if [ ! -f ~/.config/ngrok/ngrok.yml ]; then
    echo "❌ Ngrok not configured. Run: ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

echo "🚀 Starting REST API tunnel (ngrok)..."
ngrok http 5167 --log stdout > /tmp/ngrok-api.log 2>&1 &
NGROK_PID=$!

echo "🚀 Starting WebSocket tunnel (LocalTunnel)..."
nohup lt --port 8080 --subdomain scrumbot-ws-$(date +%s) > /tmp/localtunnel-ws.log 2>&1 &
LT_PID=$!
disown $LT_PID

# Wait for tunnels
sleep 5

# Extract URLs
echo "📋 Extracting tunnel URLs..."
API_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
WS_URL=$(grep -o 'https://.*\.loca\.lt' /tmp/localtunnel-ws.log | head -1)

echo "✅ Dual tunnels active!"
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
echo "⚠️  IMPORTANT: Visit $WS_URL in browser first and click 'Continue'"
echo "     This bypasses LocalTunnel's verification page"
echo ""
echo "🛑 To stop tunnels:"
echo "  kill $NGROK_PID $LT_PID"
echo ""
echo "Press Ctrl+C to stop all tunnels"

echo "✅ Both tunnels running in background"
echo "📊 Monitor logs:"
echo "  tail -f /tmp/ngrok-api.log         # ngrok logs"
echo "  tail -f /tmp/localtunnel-ws.log   # LocalTunnel logs"
echo "  pm2 logs                          # Service logs"