#!/bin/bash

# Tunnel Setup Script for ScrumBot (Free Alternatives to ngrok)
# Uses LocalTunnel (completely free) or Cloudflare Tunnel

set -e

echo "🌐 Setting up free tunnel alternatives..."

# Function to setup LocalTunnel (completely free, no signup)
setup_localtunnel() {
    echo "📦 Installing LocalTunnel..."
    
    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install localtunnel globally
    sudo npm install -g localtunnel
    
    echo "🚀 Starting LocalTunnel on port 3000..."
    lt --port 3000 --subdomain scrumbot-$(date +%s) > /tmp/localtunnel.log 2>&1 &
    LT_PID=$!
    
    # Wait for tunnel to start
    sleep 3
    
    # Extract URL from logs
    TUNNEL_URL=$(grep -o 'https://.*\.loca\.lt' /tmp/localtunnel.log | head -1)
    
    if [ -z "$TUNNEL_URL" ]; then
        echo "❌ Failed to get LocalTunnel URL. Check logs:"
        cat /tmp/localtunnel.log
        exit 1
    fi
    
    echo "✅ LocalTunnel active!"
    echo "🔗 Tunnel URL: $TUNNEL_URL"
    echo "🛑 To stop: kill $LT_PID"
    
    return 0
}

# Function to setup Cloudflare Tunnel (free, requires signup)
setup_cloudflare() {
    echo "📦 Installing Cloudflare Tunnel..."
    
    # Download cloudflared
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
    
    echo "🚀 Starting Cloudflare Tunnel on port 3000..."
    cloudflared tunnel --url http://localhost:3000 > /tmp/cloudflare.log 2>&1 &
    CF_PID=$!
    
    # Wait for tunnel to start
    sleep 5
    
    # Extract URL from logs
    TUNNEL_URL=$(grep -o 'https://.*\.trycloudflare\.com' /tmp/cloudflare.log | head -1)
    
    if [ -z "$TUNNEL_URL" ]; then
        echo "❌ Failed to get Cloudflare URL. Check logs:"
        cat /tmp/cloudflare.log
        exit 1
    fi
    
    echo "✅ Cloudflare Tunnel active!"
    echo "🔗 Tunnel URL: $TUNNEL_URL"
    echo "🛑 To stop: kill $CF_PID"
    
    return 0
}

# Setup nginx proxy (same as before)
setup_nginx() {
    if ! command -v nginx &> /dev/null; then
        echo "📦 Installing nginx..."
        sudo apt update
        sudo apt install nginx -y
    fi
    
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
        
        sudo ln -sf /etc/nginx/sites-available/scrumbot /etc/nginx/sites-enabled/
        sudo nginx -t
        sudo systemctl reload nginx
        echo "✅ Nginx proxy configured"
    fi
}

# Main execution
setup_nginx

echo ""
echo "Choose tunnel service:"
echo "1) LocalTunnel (completely free, no signup)"
echo "2) Cloudflare Tunnel (free, no signup for temp tunnels)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        setup_localtunnel
        ;;
    2)
        setup_cloudflare
        ;;
    *)
        echo "❌ Invalid choice. Defaulting to LocalTunnel..."
        setup_localtunnel
        ;;
esac

echo ""
echo "📝 Update Chrome extension config.js:"
echo "  BACKEND_URL: '$TUNNEL_URL'"
echo "  WEBSOCKET_URL: '$TUNNEL_URL'"
echo ""
echo "🧪 Test endpoints:"
echo "  curl $TUNNEL_URL/health           # Backend API"
echo "  curl $TUNNEL_URL/ws/health        # WebSocket health"
echo ""
echo "Press Ctrl+C to stop tunnel"

# Keep script running
wait