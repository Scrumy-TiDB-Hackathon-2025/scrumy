# EC2 Deployment Guide

## 🚀 **Quick Deployment**

### 1. Launch EC2 Instance
- **Instance Type**: t3.small (2GB RAM, 2 vCPU)
- **AMI**: Ubuntu 22.04 LTS
- **Security Group**: Allow ports 22, 80, 443, 5167, 8080, 3003

### 2. Run Setup Scripts
```bash
# 1. Basic system setup
wget https://raw.githubusercontent.com/Scrumy-TiDB-Hackathon-2025/scrumy/feature/ai-processing-integration/deployment/setup_ec2_instance.sh
chmod +x setup_ec2_instance.sh
./setup_ec2_instance.sh
```

### 3. Manual Configuration Steps

#### Configure Ngrok
```bash
# Get auth token from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_NGROK_TOKEN_HERE
```

#### Clone Repository
```bash
git clone https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy.git
cd scrumy
git checkout feature/ai-processing-integration
```

#### Setup Application
```bash
./deployment/setup_application.sh
```

#### Configure Environment
```bash
cd shared
cp .env.example .tidb.env
# Edit .tidb.env with your credentials:
nano .tidb.env
```

**Required Environment Variables:**
```bash
TIDB_CONNECTION_STRING=mysql://username:password@gateway.tidbcloud.com:4000/database
GROQ_API_KEY=gsk_your_groq_api_key_here
DEBUG_LOGGING=false
```

#### Setup Groq API Key
```bash
cd ai_processing
./setup_groq_key.sh
# Enter your Groq API key when prompted
```

### 4. Start Services
```bash
# Setup and start PM2 processes
./deployment/setup_pm2.sh

# Setup ngrok tunnels
./deployment/setup_ngrok.sh
```

### 5. Verify Deployment
```bash
# Check PM2 status
pm2 status

# Check ngrok tunnels
curl http://localhost:4040/api/tunnels

# Test backend health
curl http://localhost:5167/health

# Test WebSocket
curl http://localhost:8080/health
```

## 📊 **Monitoring**

### PM2 Commands
```bash
pm2 status              # View all processes
pm2 logs                # View all logs
pm2 logs scrumbot-backend    # View specific service logs
pm2 restart all         # Restart all services
pm2 stop all           # Stop all services
pm2 delete all         # Delete all processes
```

### Log Files
```bash
tail -f logs/backend-combined.log     # Backend logs
tail -f logs/websocket-combined.log   # WebSocket logs
tail -f logs/integration-combined.log # Integration logs
tail -f logs/ngrok.log                # Ngrok logs
```

## 🔧 **Troubleshooting**

### Common Issues

#### Services Won't Start
```bash
# Check Python virtual environment
cd ai_processing && source venv/bin/activate && python --version

# Check dependencies
pip list | grep -E "(fastapi|websockets|groq)"

# Check Whisper build
ls -la whisper.cpp/build/bin/whisper-cli
```

#### Ngrok Connection Issues
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels

# Restart ngrok
pkill ngrok
./deployment/setup_ngrok.sh
```

#### Memory Issues (t3.small)
```bash
# Check memory usage
free -h
pm2 monit

# Restart services if memory high
pm2 restart all
```

## 🎯 **Chrome Extension Testing**

### Update Extension Configuration
1. Get WebSocket URL from ngrok dashboard
2. Update Chrome extension manifest with new URL
3. Reload extension in Chrome
4. Test with provided test script

### Expected URLs
- **Backend**: `https://random-string.ngrok.io` (port 5167)
- **WebSocket**: `wss://random-string.ngrok.io` (port 8080)
- **Integration**: `https://random-string.ngrok.io` (port 3003)

## 💰 **Cost Estimation**
- **t3.small**: ~$15/month
- **Ngrok**: Free tier (1 tunnel) or $8/month (multiple tunnels)
- **Total**: ~$15-23/month