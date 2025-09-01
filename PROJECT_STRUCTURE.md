# ScrumBot - Complete Project Structure

## 🏗️ **Root Directory**
```
scrumy-clean/
├── README.md                           # Main project documentation
├── .gitignore                          # Git ignore rules
├── LICENSE                             # MIT License
├── assets/                             # Project assets and media
│   └── demo_small.gif                  # Demo animation
├── shared/                             # Shared configuration
│   ├── .env.example                    # Environment template
│   └── .tidb.env                       # Actual environment (gitignored)
├── deployment/                         # EC2 deployment scripts
│   ├── README.md                       # Deployment guide
│   ├── setup_ec2_instance.sh          # System setup script
│   ├── setup_application.sh           # App dependencies
│   ├── setup_pm2.sh                   # Process management
│   └── setup_ngrok.sh                 # Tunnel configuration
├── ai_processing/                      # AI Processing Backend
├── integration/                        # Integration System
├── chrome_extension/                   # Chrome Extension
├── frontend_dashboard/                 # Next.js Frontend
└── docs/                              # Documentation
```

## 🤖 **AI Processing Backend** (`ai_processing/`)
```
ai_processing/
├── app/                                # Core application modules
│   ├── __init__.py
│   ├── ai_processor.py                 # Groq API integration
│   ├── debug_logger.py                 # Conditional debug logging
│   ├── integration_adapter.py          # External system adapter
│   ├── integration_bridge.py           # Task creation bridge
│   ├── meeting_buffer.py               # Optimized meeting buffer
│   ├── meeting_summarizer.py           # Meeting summarization
│   ├── pipeline_logger.py              # Pipeline logging system
│   ├── speaker_identifier.py           # Speaker identification
│   ├── task_extractor.py               # Task extraction from transcripts
│   └── websocket_server.py             # WebSocket server for Chrome extension
├── whisper.cpp/                        # Whisper transcription engine
│   ├── build/
│   │   └── bin/
│   │       └── whisper-cli             # Whisper executable
│   └── models/
│       └── ggml-base.en.bin           # Whisper model
├── tests/                              # Test files
│   └── data/
│       ├── meeting-test.wav            # Test audio file
│       ├── meeting-test.m4a            # Original recording
│       └── meeting-test.wav.txt        # Transcription reference
├── requirements.txt                    # Python dependencies
├── build_whisper.sh                   # Whisper build script
├── clean_start_backend.sh             # Backend startup script
├── setup_groq_key.sh                  # Groq API key setup
├── start_backend.py                   # Backend entry point
├── start_websocket_server.py          # WebSocket server entry
├── test_memory_profiling.py           # Memory analysis tool
├── test_chrome_extension_readiness.py # Readiness checker
├── MEMORY_ANALYSIS.md                 # Scalability analysis
├── .env                               # Local environment (gitignored)
└── venv/                              # Python virtual environment
```

## 🔗 **Integration System** (`integration/`)
```
integration/
├── app/                                # Integration modules
│   ├── __init__.py
│   ├── ai_agent.py                     # AI agent coordination
│   ├── integrations.py                 # Platform integrations
│   ├── notion_tools.py                 # Notion API tools
│   ├── slack_tools.py                  # Slack API tools
│   ├── clickup_tools.py                # ClickUp API tools
│   ├── tidb_manager.py                 # TiDB database manager
│   └── tools.py                        # Tool registry
├── package.json                        # Node.js dependencies
├── package-lock.json                   # Dependency lock file
├── server.js                          # Integration server entry
└── node_modules/                       # Node.js modules
```

## 🌐 **Chrome Extension** (`chrome_extension/`)
```
chrome_extension/
├── manifest.json                       # Extension manifest
├── popup.html                          # Extension popup UI
├── popup.js                           # Popup functionality
├── content.js                         # Content script for meeting pages
├── background.js                      # Background service worker
├── icons/                             # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── styles/
    └── popup.css                      # Popup styling
```

## 🎨 **Frontend Dashboard** (`frontend_dashboard/`)
```
frontend_dashboard/
├── src/                               # React source code
│   ├── components/                    # React components
│   ├── pages/                        # Next.js pages
│   ├── styles/                       # CSS styles
│   └── utils/                        # Utility functions
├── public/                           # Static assets
├── package.json                      # Frontend dependencies
├── next.config.js                    # Next.js configuration
└── node_modules/                     # Frontend modules
```

## 📚 **Documentation** (`docs/`)
```
docs/
├── API.md                            # API documentation
├── ARCHITECTURE.md                   # System architecture
├── DEPLOYMENT.md                     # Deployment guide
├── CHROME_EXTENSION.md               # Extension documentation
└── TROUBLESHOOTING.md                # Common issues
```

## 🔧 **Key Configuration Files**

### **Environment Configuration**
- `shared/.env.example` - Environment template
- `shared/.tidb.env` - Production environment
- `ai_processing/.env` - Local AI processing config

### **Deployment Configuration**
- `deployment/ecosystem.config.js` - PM2 process configuration
- `deployment/.ngrok2/ngrok.yml` - Ngrok tunnel configuration

### **Build Configuration**
- `ai_processing/requirements.txt` - Python dependencies
- `integration/package.json` - Node.js dependencies
- `chrome_extension/manifest.json` - Extension configuration

## 🚀 **Entry Points**

### **Development**
- `ai_processing/clean_start_backend.sh` - Start AI backend
- `ai_processing/start_websocket_server.py` - Start WebSocket server
- `integration/server.js` - Start integration server
- `frontend_dashboard/npm run dev` - Start frontend

### **Production (PM2)**
- `scrumbot-backend` - AI processing backend
- `scrumbot-websocket` - WebSocket server
- `scrumbot-integration` - Integration system

## 📊 **Key Features by Module**

### **AI Processing**
- Real-time audio transcription (Whisper.cpp)
- Speaker identification with Groq API
- Meeting summarization and task extraction
- Optimized batching (90% API call reduction)
- Memory-efficient meeting buffers

### **Integration System**
- Multi-platform task creation (Notion, ClickUp, Slack)
- TiDB Serverless database integration
- Two-layer task architecture
- Real-time notifications

### **Chrome Extension**
- Audio capture from Google Meet, Zoom, Teams
- WebSocket streaming to backend
- Real-time transcription display
- Meeting detection and management

### **Deployment**
- Automated EC2 setup scripts
- PM2 process management
- Ngrok tunnel configuration
- Scalable architecture (t3.micro to c5.xlarge)

## 💾 **Data Flow**
```
Chrome Extension → WebSocket → AI Processing → Integration → External APIs
     ↓               ↓            ↓              ↓           ↓
  Audio Capture → Transcription → Task Extract → Database → Notion/Slack/ClickUp
```

## 🔒 **Security & Configuration**
- Environment-based configuration
- API key management
- Conditional debug logging
- Production-safe defaults
- HTTPS/WSS for Chrome extension compatibility