# ScrumBot - Run Instructions for Judges

## Quick Demo Setup (5 minutes)

### Prerequisites
- Node.js 18+
- Python 3.10+
- Chrome browser
- TiDB Serverless account (free at [tidbcloud.com](https://tidbcloud.com))

### 1. Clone and Setup
```bash
git clone https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy.git
cd scrumy

# Setup AI processing backend
cd ai_processing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Build Whisper (required for transcription)
chmod +x build_whisper.sh
./build_whisper.sh
```

### 2. Configure TiDB Connection
```bash
# Copy environment template
cp shared/.env.example shared/.tidb.env

# Edit shared/.tidb.env with your TiDB connection:
TIDB_CONNECTION_STRING="mysql://username:password@gateway01.us-west-2.prod.aws.tidbcloud.com:4000/test"
GROQ_API_KEY="your_groq_api_key"  # Free at console.groq.com
```

### 3. Start All Services
```bash
# Start all services with PM2
./deployment/setup_pm2.sh

# Verify services are running
curl http://localhost:5167/health  # Backend API
curl http://localhost:8080/health  # WebSocket server  
curl http://localhost:8001/health  # AI Chatbot
```

### 4. Setup Public Tunnels (for Chrome extension)
```bash
# Setup triple ngrok tunnels
./deployment/setup_triple_ngrok.sh

# Update Chrome extension URLs automatically
./update-triple-urls.sh
```

### 5. Install Chrome Extension
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → select `chrome_extension` folder
4. Extension ready to use!

## Demo Flow

### 1. Start a Meeting Recording
1. Join any Google Meet/Zoom/Teams call
2. Click ScrumBot extension icon
3. Click "Start Recording"
4. Speak some action items: "John, please finish the API documentation by Friday"

### 2. View Real-time Processing
- Watch live transcription in browser console
- See WebSocket messages in real-time
- Monitor PM2 logs: `pm2 logs --lines 20`

### 3. Check Task Creation
```bash
# Query TiDB directly to see stored data
mysql -h gateway01.us-west-2.prod.aws.tidbcloud.com -P 4000 -u username -p
USE test;
SELECT * FROM meetings ORDER BY created_at DESC LIMIT 5;
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5;
```

### 4. Test AI Chatbot
```bash
# Query meeting data via chatbot
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tasks were created in recent meetings?"}'
```

## Troubleshooting

### Services Not Starting
```bash
# Check PM2 status
pm2 status

# Restart if needed
./restart_pm2_with_env_fixed.sh

# Check logs
pm2 logs --lines 20
```

### Chrome Extension Issues
```bash
# Verify ngrok tunnels are active
curl -s http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url'
curl -s http://localhost:4042/api/tunnels | jq '.tunnels[0].public_url'  
curl -s http://localhost:4044/api/tunnels | jq '.tunnels[0].public_url'

# Update extension config if URLs changed
./update-triple-urls.sh
```

### Database Connection Issues
```bash
# Test TiDB connection
cd ai_processing
python -c "
import os
from dotenv import load_dotenv
load_dotenv('../shared/.tidb.env')
print('TiDB URL:', os.getenv('TIDB_CONNECTION_STRING'))
"
```

## Key Demo Points
1. **Real-time Audio Capture**: Show Chrome extension capturing meeting audio
2. **Live Transcription**: Demonstrate Whisper processing in real-time
3. **AI Task Extraction**: Show Groq LLM identifying action items
4. **TiDB Storage**: Query database to show stored meeting data
5. **Integration Sync**: Show tasks created in Notion/Slack
6. **AI Chatbot**: Ask questions about meeting history and get intelligent responses

## Architecture Highlights
- **TiDB Serverless**: Primary database for all meeting data and analytics
- **Chrome Extension**: Direct integration with video conferencing platforms
- **WebSocket Streaming**: Real-time audio processing pipeline
- **MCP Protocol**: Automated task management across platforms
- **AI Processing**: Local Whisper + Cloud Groq for optimal performance