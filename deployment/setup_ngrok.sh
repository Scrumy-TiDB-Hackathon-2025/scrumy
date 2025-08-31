#!/bin/bash

# Ngrok Setup Script for ScrumBot
# Configures ngrok tunnels for Chrome extension access

set -e

echo "🌐 Setting up ngrok tunnels..."

# Check if ngrok auth token is configured
if ! ngrok config check 2>/dev/null | grep -q "valid"; then
    echo "❌ Ngrok not configured!"
    echo ""
    echo "🔧 MANUAL STEP REQUIRED:"
    echo "1. Get your ngrok auth token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. Run: ngrok config add-authtoken YOUR_TOKEN_HERE"
    echo "3. Then run this script again"
    exit 1
fi

# Create ngrok configuration directory
mkdir -p ~/.ngrok2

# Create ngrok configuration
cat > ~/.ngrok2/ngrok.yml << 'EOF'
version: "2"
authtoken: # This will be set by ngrok config add-authtoken

tunnels:
  backend:
    proto: http
    addr: 5167
    subdomain: # Optional: set custom subdomain
    
  websocket:
    proto: http
    addr: 8080
    subdomain: # Optional: set custom subdomain
    
  integration:
    proto: http
    addr: 3003
    subdomain: # Optional: set custom subdomain

  all:
    proto: http
    addr: 5167
    subdomain: # Optional: set custom subdomain for main backend
EOF

echo "✅ Ngrok configuration created!"
echo ""
echo "🚀 Starting ngrok tunnels..."

# Ensure logs directory exists
mkdir -p logs

# Start ngrok in background for all services
nohup ngrok start --all --config ~/.ngrok2/ngrok.yml > logs/ngrok.log 2>&1 &

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
echo "📋 Manual Configuration Required:"
echo "1. Update Chrome extension with WebSocket URL"
echo "2. Update any frontend configurations with backend URL"
echo "3. Test Chrome extension connection"
echo ""
echo "🔍 Monitor ngrok:"
echo "  Ngrok dashboard: http://localhost:4040"
echo "  Ngrok logs: tail -f logs/ngrok.log"