# ScrumBot Frontend Startup Guide

## 🚀 Quick Start for Frontend Developers

This guide will help you set up the complete ScrumBot development environment locally.

## 📋 Prerequisites

- **Node.js 18+** (for frontend)
- **Python 3.10+** (for backend)
- **Chrome Browser** (for extension testing)
- **Git** (for version control)

## 🛠️ Initial Setup

### 1. Clone and Setup Repository
```bash
git clone https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy.git
cd scrumy
```

### 2. Backend Setup (AI Processing)
```bash
cd ai_processing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build Whisper (required for transcription)
chmod +x build_whisper.sh
./build_whisper.sh

# Make scripts executable
chmod +x start_backend.py
chmod +x start_websocket_server.py
```

### 3. Frontend Setup
```bash
cd ../frontend_dashboard

# Install dependencies
npm install

# Make script executable
chmod +x scripts/set-urls.sh
```

## 🚦 Starting the Development Environment

**IMPORTANT**: Start servers in this exact order:

### Step 1: Start Backend API Server
```bash
# Terminal 1 - In ai_processing directory
cd ai_processing
source venv/bin/activate
python3 start_backend.py
```
✅ **Expected**: Server starts on `http://localhost:5167`

### Step 2: Start WebSocket Server
```bash
# Terminal 2 - In ai_processing directory  
cd ai_processing
source venv/bin/activate
python3 start_websocket_server.py
```
✅ **Expected**: WebSocket server starts on `ws://localhost:8080`

### Step 3: Start Frontend Dashboard
```bash
# Terminal 3 - In frontend_dashboard directory
cd frontend_dashboard
./scripts/set-urls.sh dev
```

**When prompted:**
- API URL: Press Enter (uses default: `http://localhost:5167`)
- WebSocket URL: Press Enter (uses default: `ws://localhost:8080`)

✅ **Expected**: Frontend starts on `http://localhost:3000`

### Step 4: Load Chrome Extension
1. Open Chrome browser
2. Go to `chrome://extensions/`
3. Enable **Developer mode** (toggle in top right)
4. Click **Load unpacked**
5. Navigate to and select the `chrome_extension` folder
6. Extension should appear with ScrumBot icon

## 🔧 Troubleshooting

### Port Conflicts

If you get "port already in use" errors:

**Clear Port 5167 (Backend API):**
```bash
lsof -ti:5167 | xargs kill -9 2>/dev/null
```

**Clear Port 8080 (WebSocket):**
```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null
```

**Clear Port 3000 (Frontend):**
```bash
lsof -ti:3000 | xargs kill -9 2>/dev/null
```

**Clear All Ports at Once:**
```bash
lsof -ti:5167,8080,3000 | xargs kill -9 2>/dev/null
```

### Common Issues

**1. Permission Denied on Scripts:**
```bash
chmod +x ai_processing/start_backend.py
chmod +x ai_processing/start_websocket_server.py  
chmod +x frontend_dashboard/scripts/set-urls.sh
```

**2. Python Virtual Environment Issues:**
```bash
cd ai_processing
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Node.js Dependencies Issues:**
```bash
cd frontend_dashboard
rm -rf node_modules package-lock.json
npm install
```

**4. Whisper Build Issues:**
```bash
cd ai_processing
chmod +x build_whisper.sh
./build_whisper.sh
```

## 🧪 Testing the Setup

### 1. Verify Backend API
Open: `http://localhost:5167/health`
Expected: `{"status": "healthy"}`

### 2. Verify WebSocket
Open: `http://localhost:8080/health`  
Expected: `{"status": "healthy"}`

### 3. Verify Frontend
Open: `http://localhost:3000`
Expected: ScrumBot dashboard loads

### 4. Test Chrome Extension
1. Go to `https://meet.google.com`
2. Click ScrumBot extension icon
3. Should show recording controls

## 📁 Project Structure

```
scrumy/
├── ai_processing/           # Backend API & WebSocket servers
│   ├── app/                # FastAPI application
│   ├── start_backend.py    # API server starter
│   ├── start_websocket_server.py # WebSocket server starter
│   └── requirements.txt    # Python dependencies
├── frontend_dashboard/      # Next.js admin dashboard
│   ├── scripts/set-urls.sh # Environment setup script
│   ├── package.json        # Node.js dependencies
│   └── app/                # Next.js pages
├── chrome_extension/        # Chrome extension
│   ├── manifest.json       # Extension configuration
│   ├── config.js          # API endpoints configuration
│   └── *.js               # Extension scripts
└── DEVELOPMENT_GUIDE.md    # This file
```

## 🔄 Development Workflow

### Making Changes

**Backend Changes:**
1. Edit files in `ai_processing/app/`
2. Restart backend server (Ctrl+C, then `python3 start_backend.py`)

**Frontend Changes:**
1. Edit files in `frontend_dashboard/`
2. Changes auto-reload (Next.js hot reload)

**Extension Changes:**
1. Edit files in `chrome_extension/`
2. Go to `chrome://extensions/`
3. Click refresh icon on ScrumBot extension

### Environment Configuration

**Development URLs (default):**
- Backend API: `http://localhost:5167`
- WebSocket: `ws://localhost:8080`
- Frontend: `http://localhost:3000`

**Production URLs:**
Use `./scripts/set-urls.sh prod` and provide production URLs.

## 🐛 Debugging

### Backend Logs
Check terminal running `start_backend.py` for API logs.

### WebSocket Logs  
Check terminal running `start_websocket_server.py` for WebSocket logs.

### Frontend Logs
Check browser console and terminal running frontend.

### Extension Logs
1. Go to `chrome://extensions/`
2. Click "Details" on ScrumBot extension
3. Click "Inspect views: service worker"
4. Check console for logs

## 📝 Environment Variables

### Backend Environment (.env)
Create `.env` file in `ai_processing/` directory:
```bash
# Required for AI processing
GROQ_API_KEY=your_groq_api_key_here

# Optional integrations
NOTION_TOKEN=your_notion_token
SLACK_BOT_TOKEN=your_slack_token
```

### Integration Environment (.env.integration)
The integration environment file is already configured in `integration/.env.integration`.

**⚠️ IMPORTANT**: This file contains real API credentials and should NOT be committed to version control.

If you need to modify integration settings:
```bash
# Edit integration/.env.integration with your API keys:
# - NOTION_TOKEN and NOTION_DATABASE_ID  
# - CLICKUP_TOKEN and CLICKUP_LIST_ID
# - Other integration credentials
```

**For production**: Create your own `.env.integration` file with your credentials.

## 🎯 Testing Features

### 1. Meeting Transcription
1. Start all servers
2. Load Chrome extension
3. Go to Google Meet
4. Click extension icon → Start Recording
5. Speak into microphone
6. Check frontend dashboard for transcripts

### 2. Task Extraction
1. Complete meeting transcription
2. Click "Stop Recording" in extension
3. Check dashboard for extracted tasks
4. Verify tasks appear in Notion/Slack (if configured)

## 🆘 Getting Help

**Common Commands:**
```bash
# Kill all servers
pkill -f "start_backend.py|start_websocket_server.py|next"

# Check what's running on ports
lsof -i:5167,8080,3000

# Restart all servers manually:
# 1. Kill all: pkill -f "start_backend.py|start_websocket_server.py|next"
# 2. Follow startup sequence above
```

**Log Locations:**
- Backend: Terminal output
- WebSocket: Terminal output  
- Frontend: Browser console + terminal
- Extension: Chrome DevTools

---

## 🎉 Success Indicators

When everything is working correctly:

✅ Backend API responds at `http://localhost:5167/health`  
✅ WebSocket server responds at `http://localhost:8080/health`  
✅ Frontend loads at `http://localhost:3000`  
✅ Chrome extension shows in browser toolbar  
✅ Extension can connect to WebSocket server  
✅ Meeting transcription works end-to-end  

**Happy coding! 🚀**