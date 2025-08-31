#!/bin/bash

# EC2 Instance Setup Script for ScrumBot
# Run this script on a fresh Ubuntu 22.04 EC2 instance

set -e

echo "🚀 Setting up ScrumBot on EC2 instance..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
echo "📦 Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node.js installation
node --version
npm --version

# Install Python 3.10 and pip
echo "🐍 Installing Python 3.10..."
sudo apt install -y python3.10 python3.10-venv python3-pip build-essential cmake

# Verify Python installation
python3 --version
pip3 --version

# Install PM2 globally
echo "⚙️  Installing PM2..."
sudo npm install -g pm2

# Verify PM2 installation
pm2 --version

# Install ngrok
echo "🌐 Installing ngrok..."
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install -y ngrok

# Verify ngrok installation
ngrok version

echo "✅ Basic setup complete!"
echo ""
echo "🔧 Manual steps required:"
echo "1. Configure ngrok auth token: ngrok config add-authtoken YOUR_TOKEN"
echo "2. Clone repository: git clone https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy.git"
echo "3. Run application setup: ./setup_application.sh"