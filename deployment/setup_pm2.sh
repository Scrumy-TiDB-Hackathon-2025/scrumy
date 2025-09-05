#!/bin/bash

# PM2 Setup Script for ScrumBot
# Configures PM2 processes for production deployment

set -e

echo "⚙️  Setting up PM2 processes..."

# Navigate to ai_processing directory
cd ~/scrumy/ai_processing

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found - using system environment"
fi

# Start PM2 processes using direct commands (proven to work)
echo "🚀 Starting PM2 processes..."
pm2 start --name scrumbot-backend --interpreter venv/bin/python start_backend.py --update-env
pm2 start --name scrumbot-websocket --interpreter venv/bin/python start_websocket_server.py --update-env

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
sudo pm2 startup systemd -u $USER --hp $HOME

echo "✅ PM2 setup complete!"
echo ""
echo "🧪 Test services before ngrok:"
echo "  curl http://localhost:5167/health  # Backend API"
echo "  curl http://localhost:8080/health  # WebSocket server"
echo "  netstat -tlnp | grep :5167        # Check backend port"
echo "  netstat -tlnp | grep :8080        # Check websocket port"
echo ""
echo "📊 PM2 Commands:"
echo "  pm2 status          - View process status"
echo "  pm2 logs            - View all logs"
echo "  pm2 restart all     - Restart all processes"
echo "  pm2 stop all        - Stop all processes"
echo ""
echo "🌐 Next step: Setup free tunnel with ./setup_tunnel.sh"