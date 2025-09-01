#!/bin/bash

# Ngrok Setup Script for ScrumBot (Free Account - Single Tunnel)
# Uses nginx proxy to route both services through one tunnel

set -e

echo "🌐 Setting up single ngrok tunnel with nginx proxy..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update
    sudo apt install ngrok
fi

# Check if ngrok is configured
if [ ! -f ~/.config/ngrok/ngrok.yml ]; then
    echo "⚠️  Ngrok not configured. Please run:"
    echo "   ngrok config add-authtoken YOUR_TOKEN"
    echo "   Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

# Ensure nginx is installed and configured
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing nginx..."
    sudo apt update
    sudo apt install nginx -y
fi

# Create nginx config if it doesn't exist
if [ ! -f /etc/nginx/sites-available/scrumbot ]; then
    echo "⚙️  Creating nginx proxy config..."
    sudo tee /etc/nginx/sites-available/scrumbot > /dev/null << 'EOF'
server {
    listen 3000;
    server_name localhost;

    # Backend API routes
    location / {
        proxy_pass http://localhost:5167;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket routes
    location /ws/ {
        proxy_pass http://localhost:8080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/scrumbot /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    echo "✅ Nginx proxy configured"
fi

echo "🚀 Starting ngrok tunnel on port 3000..."
ngrok http 3000 --log stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for tunnel to start
sleep 5

# Extract URL
echo "📋 Extracting tunnel URL..."
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

echo "✅ Ngrok tunnel active!"
echo ""
echo "🔗 Tunnel URL: $TUNNEL_URL"
echo ""
echo "📝 Update Chrome extension config.js:"
echo "  BACKEND_URL: '$TUNNEL_URL'"
echo "  WEBSOCKET_URL: '$TUNNEL_URL'"
echo ""
echo "🧪 Test endpoints:"
echo "  curl $TUNNEL_URL/health           # Backend API"
echo "  curl $TUNNEL_URL/ws/health        # WebSocket health"
echo ""
echo "🛑 To stop tunnel: kill $NGROK_PID or Ctrl+C"

# Keep script running
wait