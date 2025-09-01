#!/bin/bash

# PM2 Setup Script for ScrumBot
# Configures PM2 processes for production deployment

set -e

echo "⚙️  Setting up PM2 processes..."

# Navigate to project root
cd ~/scrumy

# Create PM2 ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'scrumbot-backend',
      script: 'start_backend.py',
      cwd: '/home/ubuntu/scrumy/ai_processing',
      interpreter: '/home/ubuntu/scrumy/ai_processing/venv/bin/python',
      env: { PORT: 5167, DEBUG_LOGGING: 'false' },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    },
    {
      name: 'scrumbot-websocket',
      script: 'start_websocket_server.py',
      cwd: '/home/ubuntu/scrumy/ai_processing',
      interpreter: '/home/ubuntu/scrumy/ai_processing/venv/bin/python',
      env: { PORT: 8080, DEBUG_LOGGING: 'false' },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M'
    },
    {
      name: 'scrumbot-integration',
      script: 'npm',
      args: 'start',
      cwd: '/home/ubuntu/scrumy/integration',
      env: { PORT: 3003 },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    }
  ]
};
EOF

# Create logs directory
mkdir -p logs

# Start PM2 processes
echo "🚀 Starting PM2 processes..."
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
sudo pm2 startup systemd -u $USER --hp $HOME

echo "✅ PM2 setup complete!"
echo ""
echo "📊 PM2 Commands:"
echo "  pm2 status          - View process status"
echo "  pm2 logs            - View all logs"
echo "  pm2 restart all     - Restart all processes"
echo "  pm2 stop all        - Stop all processes"
echo ""
echo "🌐 Next step: Setup ngrok tunnels with ./setup_ngrok.sh"