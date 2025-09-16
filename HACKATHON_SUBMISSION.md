# TiDB Hackathon 2025 Submission - ScrumBot

## Project Information
- **Project Name**: ScrumBot - AI-Powered Meeting Assistant with TiDB & MCP Integration
- **Repository**: https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy
- **TiDB Cloud Account Email**: [TO BE PROVIDED]

## Data Flow and Integrations

### Architecture Overview
```
Chrome Extension → WebSocket Server → AI Processing → TiDB Serverless → Integration Platforms
     ↓                    ↓                ↓              ↓                    ↓
Audio Capture → Real-time Transcription → Task Extraction → Data Storage → Notion/Slack/ClickUp
```

### TiDB Integration Points
1. **Meeting Data Storage**: All meetings, transcripts, and metadata stored in TiDB Serverless
2. **Task Management**: AI-extracted tasks stored with full context and relationships
3. **Vector Store**: AI Chatbot uses TiDB for knowledge base and meeting history
4. **Real-time Analytics**: Meeting patterns, task completion rates, team productivity

### Data Flow
1. **Audio Capture**: Chrome extension captures meeting audio from Google Meet/Zoom/Teams
2. **Real-time Processing**: WebSocket streams audio to Whisper for transcription
3. **AI Analysis**: Groq LLM extracts tasks, identifies speakers, generates summaries
4. **TiDB Storage**: All data persisted in TiDB Serverless with optimized schema
5. **Integration Sync**: Tasks automatically created in Notion, Slack notifications sent
6. **Chatbot Access**: AI assistant queries TiDB for meeting insights and task status

## Key Features
- **Chrome Extension**: Direct audio capture from video calls
- **TiDB Serverless**: Scalable cloud database with MySQL compatibility
- **AI Processing**: Whisper transcription + Groq LLM for task extraction
- **MCP Integration**: Automated task creation in Notion and Slack
- **Real-time Analytics**: Meeting insights and team productivity metrics
- **AI Chatbot**: Query meeting data and get intelligent responses

## Technology Stack
- **Database**: TiDB Serverless (primary data store)
- **Backend**: FastAPI with WebSocket support
- **AI/ML**: Whisper.cpp (local), Groq API (cloud)
- **Frontend**: Next.js dashboard + Chrome extension
- **Integrations**: Model Context Protocol (MCP) for Notion/Slack
- **Deployment**: PM2 + ngrok for development, Docker ready for production