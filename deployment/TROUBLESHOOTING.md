# EC2 Deployment Troubleshooting

## 🔧 **Whisper.cpp Build Issues**

### **Error: whisper-server compilation fails**
```
error: 'timestamp_to_sample' was not declared in this scope
error: 'to_timestamp' was not declared in this scope
error: '::read_wav' has not been declared
```

**Solution**: Use CLI-only build (we don't need the server)
```bash
cd ~/scrumy/ai_processing
./build_whisper_cli_only.sh
```

**Alternative**: Modify setup script to disable server build
```bash
# In setup_application.sh, replace whisper build with:
cd whisper.cpp
mkdir -p build && cd build
cmake .. -DWHISPER_BUILD_EXAMPLES=ON -DWHISPER_BUILD_SERVER=OFF
make -j$(nproc) whisper-cli
```

### **Error: cmake not found**
```bash
sudo apt install -y cmake build-essential
```

### **Error: insufficient memory during build**
```bash
# Use single thread build on t3.micro
make whisper-cli  # instead of make -j$(nproc)
```

## 🐍 **Python Environment Issues**

### **Error: venv creation fails**
```bash
sudo apt install -y python3.10-venv python3-pip
```

### **Error: pip install fails**
```bash
# Upgrade pip first
pip install --upgrade pip
# Then install requirements
pip install -r requirements.txt
```

### **Error: FastAPI import fails**
```bash
# Activate venv and reinstall
source venv/bin/activate
pip install fastapi uvicorn websockets
```

## 🌐 **Ngrok Issues**

### **Error: ngrok auth token not configured**
```bash
# Get token from https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_TOKEN_HERE
```

### **Error: ngrok tunnels not starting**
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels

# Restart ngrok
pkill ngrok
./deployment/setup_ngrok.sh
```

### **Error: tunnel limit exceeded (free tier)**
```bash
# Free tier allows 1 tunnel, modify ngrok.yml to use only one:
tunnels:
  backend:
    proto: http
    addr: 5167
```

## ⚙️  **PM2 Issues**

### **Error: PM2 processes won't start**
```bash
# Check PM2 status
pm2 status

# View logs
pm2 logs

# Restart all
pm2 restart all
```

### **Error: Python interpreter not found**
```bash
# Fix interpreter path in ecosystem.config.js
interpreter: '/home/ubuntu/scrumy/ai_processing/venv/bin/python'
```

### **Error: memory limit exceeded**
```bash
# Increase memory limits in ecosystem.config.js
max_memory_restart: '800M'  # for t3.micro
```

## 💾 **Memory Issues (t3.micro)**

### **Error: out of memory during build**
```bash
# Add swap space
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Build with single thread
make whisper-cli  # instead of make -j$(nproc)
```

### **Error: application crashes due to memory**
```bash
# Monitor memory usage
free -h
pm2 monit

# Restart services
pm2 restart all
```

## 🔗 **Integration Issues**

### **Error: TiDB connection fails**
```bash
# Check environment variables
cat shared/.tidb.env | grep TIDB

# Test connection
mysql -h gateway.tidbcloud.com -P 4000 -u username -p
```

### **Error: Groq API key invalid**
```bash
# Verify API key
cd ai_processing
./setup_groq_key.sh

# Test API
curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
```

## 🌐 **Chrome Extension Issues**

### **Error: WebSocket connection refused**
```bash
# Check WebSocket server
curl http://localhost:8080/health

# Check ngrok tunnel
curl http://localhost:4040/api/tunnels

# Update extension with correct WSS URL
```

### **Error: HTTPS required for extension**
```bash
# Ensure using WSS (not WS) in extension
wss://your-ngrok-url.ngrok.io

# Check ngrok HTTPS tunnel is active
```

## 📊 **Quick Diagnostics**

### **Check all services**
```bash
# PM2 status
pm2 status

# Port usage
sudo netstat -tlnp | grep -E ':(5167|8080|3003)'

# Memory usage
free -h

# Disk space
df -h

# Ngrok tunnels
curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        print(f'{tunnel[\"name\"]}: {tunnel[\"public_url\"]}')
except:
    print('Ngrok not running or no tunnels')
"
```

### **Restart everything**
```bash
# Stop all services
pm2 stop all
pkill ngrok

# Restart services
pm2 start ecosystem.config.js
./deployment/setup_ngrok.sh
```

## 🆘 **Emergency Recovery**

### **Complete reset**
```bash
# Stop everything
pm2 delete all
pkill -f python
pkill ngrok

# Clean build
cd ~/scrumy/ai_processing
rm -rf whisper.cpp/build
./build_whisper_cli_only.sh

# Restart setup
./deployment/setup_pm2.sh
./deployment/setup_ngrok.sh
```