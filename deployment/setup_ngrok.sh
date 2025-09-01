#!/bin/bash

# Ngrok Setup Script for ScrumBot
# Configures ngrok tunnels for Chrome extension access

set -e

echo "🌐 Setting up ngrok tunnels..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok not installed!"
    echo "Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install ngrok
fi

# Check if ngrok auth token is configured
if ! ngrok config check 2>/dev/null; then
    echo "❌ Ngrok not configured!"
    echo ""
    echo "🔧 MANUAL STEP REQUIRED:"
    echo "1. Get your ngrok auth token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. Run: ngrok config add-authtoken YOUR_TOKEN_HERE"
    echo "3. Then run this script again"
    exit 1
fi

# Create ngrok configuration for multiple tunnels
cat > ngrok.yml << 'EOF'
version: "2"

tunnels:
  websocket:
    proto: http
    addr: 8080
    
  integration:
    proto: http
    addr: 3003
EOF

echo "✅ Ngrok configuration created!"
echo ""
echo "🚀 Starting ngrok tunnels..."

# Ensure logs directory exists
mkdir -p logs

# Start ngrok in background for Chrome extension services
nohup ngrok start --all --config ngrok.yml > logs/ngrok.log 2>&1 &

# Wait for ngrok to start
sleep 5

# Get tunnel URLs
echo "🌐 Ngrok tunnel URLs:"
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        print(f\"  {tunnel['name']}: {tunnel['public_url']}\")
except:
    print('  Could not retrieve tunnel URLs. Check ngrok status manually.')
"

echo ""
echo ""
echo "📋 NEXT STEPS:"
echo "1. Copy the WebSocket HTTPS URL above"
echo "2. Update Chrome extension manifest.json with the WebSocket URL"
echo "3. Update integration service URL if needed"
echo "4. Test Chrome extension on Google Meet/Zoom"
echo ""
echo "🔍 Monitor:"
echo "  Ngrok dashboard: http://localhost:4040"
echo "  Ngrok logs: tail -f logs/ngrok.log"
echo "  PM2 status: pm2 status"