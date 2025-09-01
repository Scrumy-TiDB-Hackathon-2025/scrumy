# ScrumBot EC2 Setup Guide

## Quick Setup (5 minutes)

### 1. Launch EC2 Instance
```bash
# Recommended: t3.small (2 vCPU, 2GB RAM)
# OS: Ubuntu 22.04 LTS
# Security Group: Allow ports 22, 3000, 8000, 8001
```

### 2. Connect and Run Setup
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone repository
git clone https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy.git
cd scrumy

# Run automated setup
chmod +x deployment/*.sh
./deployment/setup_ec2_instance.sh
./deployment/setup_application.sh
```

### 3. Configure Environment
```bash
# Copy and edit environment file
cp shared/.env.example shared/.tidb.env
nano shared/.tidb.env

# Required settings:
TIDB_CONNECTION_STRING="mysql://user:pass@gateway.tidbcloud.com:4000/test"
GROQ_API_KEY="your_groq_key"
DEBUG_LOGGING=false
```

### 4. Start Services
```bash
# Setup PM2 processes
./deployment/setup_pm2.sh

# Setup ngrok tunnels (for Chrome extension HTTPS)
./deployment/setup_ngrok.sh

# Check status
pm2 status
pm2 logs
```

## What Gets Installed

### System Components
- **Node.js 20** - Frontend and PM2
- **Python 3.10** - Backend services
- **PM2** - Process management
- **ngrok** - HTTPS tunnels
- **Build tools** - For Whisper compilation

### Application Services
- **Backend API** (port 3000) - Main FastAPI server
- **WebSocket Server** (port 8001) - Chrome extension audio
- **Integration Bridge** (port 8000) - Task creation service
- **Whisper CLI** - Audio transcription (no server)

### PM2 Process Architecture
```
┌─────────────────┬──────┬─────────┬──────────┐
│ App name        │ id   │ mode    │ pid      │
├─────────────────┼──────┼─────────┼──────────┤
│ scrumbot-backend│ 0    │ fork    │ 12345    │
│ scrumbot-ws     │ 1    │ fork    │ 12346    │
│ scrumbot-bridge │ 2    │ fork    │ 12347    │
└─────────────────┴──────┴─────────┴──────────┘
```

## Verification Steps

### 1. Check Services
```bash
# All services running
pm2 status

# Check logs for errors
pm2 logs --lines 20

# Test endpoints
curl http://localhost:3000/health
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 2. Test Whisper CLI
```bash
# Verify whisper-cli works
cd ai_processing
source venv/bin/activate
echo "test" | ./whisper.cpp/whisper-cli --model base
```

### 3. Check ngrok Tunnels
```bash
# View tunnel URLs
curl http://localhost:4040/api/tunnels

# Should show HTTPS URLs for ports 8000 and 8001
```

## Chrome Extension Setup

1. **Get ngrok URLs** from tunnel status
2. **Update extension** with HTTPS WebSocket URL
3. **Test on Google Meet/Zoom**

## Troubleshooting

### Service Won't Start
```bash
# Check logs
pm2 logs scrumbot-backend
pm2 logs scrumbot-ws
pm2 logs scrumbot-bridge

# Restart service
pm2 restart scrumbot-backend
```

### Whisper Issues
```bash
# Rebuild CLI only
cd ai_processing
./build_whisper_cli_only.sh

# Test manually
echo "hello" | ./whisper.cpp/whisper-cli --model base
```

### Memory Issues
```bash
# Check usage
free -h
pm2 monit

# Restart if needed
pm2 restart all
```

## Production Checklist

- [ ] Environment variables configured
- [ ] All PM2 services running
- [ ] ngrok tunnels active
- [ ] Whisper CLI executable
- [ ] TiDB connection working
- [ ] Chrome extension updated with HTTPS URLs
- [ ] Test recording from video call

## Quick Commands

```bash
# Start everything
pm2 start ecosystem.config.js

# Stop everything  
pm2 stop all

# View logs
pm2 logs --lines 50

# Restart after changes
pm2 restart all

# Monitor resources
pm2 monit
```