<div align="center" style="border-bottom: none">
    <h1>
        🤖 ScrumBot
        <br>
        AI-Powered Meeting Assistant with TiDB & MCP Integration
    </h1>
    <br>
    <a href="https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy"><img src="https://img.shields.io/badge/TiDB_Hackathon-2025-orange" alt="TiDB Hackathon 2025"></a>
    <a href="https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy"><img src="https://img.shields.io/badge/License-MIT-blue" alt="License"></a>
    <a href="https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy"><img src="https://img.shields.io/badge/Built_on-Meetily-green" alt="Built on Meetily"></a>
    <a href="https://tidbcloud.com/"><img src="https://img.shields.io/badge/Database-TiDB_Serverless-red" alt="TiDB Serverless"></a>
    <br>
    <br>
    <h3>
    Extending Meetily with TiDB, Chrome Extension, and MCP Integration
    </h3>
    <p align="center">
    <strong>Built for TiDB Hackathon 2025</strong><br>
    An enhanced meeting assistant that captures audio from video calls, processes it with AI, stores data in TiDB Serverless, and automatically creates tasks in Notion and Slack using Model Context Protocol (MCP).
    </p>

<p align="center">
    <img src="assets/demo_small.gif" width="650" alt="ScrumBot Demo" />
    <br>
    <em>Powered by Meetily's robust foundation</em>
</p>

</div>

# Table of Contents
- [About ScrumBot](#about-scrumbot)
- [What's New in ScrumBot](#whats-new-in-scrumbot)
- [TiDB Integration](#tidb-integration)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Chrome Extension](#chrome-extension)
- [MCP Integration](#mcp-integration)
- [Development Setup](#development-setup)
- [Built on Meetily](#built-on-meetily)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

# About ScrumBot

ScrumBot is an enhanced AI-powered meeting assistant built for the **TiDB Hackathon 2025**. It extends the excellent [Meetily](https://github.com/Zackriya-Solutions/meeting-minutes) project with new capabilities including TiDB Serverless integration, Chrome extension support, and Model Context Protocol (MCP) integration for seamless task management.

## What's New in ScrumBot

### 🚀 **Chrome Extension Integration**
- Capture audio directly from Google Meet, Zoom, and Microsoft Teams
- Real-time WebSocket streaming to backend
- No desktop app installation required

### 🗄️ **TiDB Serverless Database**
- Scalable cloud database replacing SQLite
- Real-time analytics and insights
- Meeting data, transcripts, and tasks stored in TiDB
- Optimized for distributed teams and high availability

### 🔗 **Model Context Protocol (MCP) Integration**
- Automatic task creation in Notion databases
- Real-time Slack notifications for action items
- Cross-platform task synchronization
- Seamless workflow automation

### 🤖 **Enhanced AI Processing**
- Speaker identification and diarization
- Intelligent meeting summarization
- Automatic action item extraction
- Support for multiple AI providers (Ollama, Groq, OpenAI)

## TiDB Integration

ScrumBot leverages **TiDB Serverless** as its primary database, providing:

- **Scalability**: Handle multiple concurrent meetings and users
- **Real-time Analytics**: Query meeting patterns, task completion rates, team productivity
- **Global Distribution**: Support for worldwide distributed teams
- **Cost-Effective**: Serverless pricing model with generous free tier
- **MySQL Compatibility**: Easy migration from existing systems

### Database Schema
```sql
-- Meetings with metadata
CREATE TABLE meetings (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    platform VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- AI-processed summaries with JSON support
CREATE TABLE ai_summaries (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    summary_type ENUM('speakers', 'summary', 'tasks') NOT NULL,
    content JSON NOT NULL,
    model_used VARCHAR(100),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks for MCP integration
CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    assignee VARCHAR(255),
    due_date DATE,
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
    notion_page_id VARCHAR(255),
    slack_message_ts VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Architecture

ScrumBot extends Meetily's proven architecture with new components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Chrome         │    │   ScrumBot       │    │   TiDB          │
│  Extension      │───▶│   Backend        │───▶│   Serverless    │
│                 │    │   (FastAPI)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   MCP Servers    │
                       │                  │
                       │  ┌─────────────┐ │    ┌─────────────────┐
                       │  │   Notion    │─┼───▶│     Notion      │
                       │  │    MCP      │ │    │   Database      │
                       │  └─────────────┘ │    └─────────────────┘
                       │                  │
                       │  ┌─────────────┐ │    ┌─────────────────┐
                       │  │   Slack     │─┼───▶│     Slack       │
                       │  │    MCP      │ │    │   Workspace     │
                       │  └─────────────┘ │    └─────────────────┘
                       └──────────────────┘
```

## Features

### ✅ **Core Features (Inherited from Meetily)**
- Modern, responsive UI with real-time updates
- Real-time audio capture (microphone + system audio)
- Live transcription using locally-running Whisper
- Local processing for privacy
- Multiple AI provider support (Ollama, Groq, OpenAI, Claude)
- Rich text editor for notes

### 🆕 **New ScrumBot Features**
- **Chrome Extension**: Direct audio capture from video calls
- **TiDB Integration**: Scalable cloud database with analytics
- **MCP Protocol**: Automated task creation and notifications
- **Speaker Identification**: AI-powered speaker diarization
- **Cross-Platform Sync**: Tasks synchronized across Notion, Slack, and ScrumBot
- **Real-time Analytics**: Meeting insights and team productivity metrics

### 🚧 **In Development**
- Advanced meeting analytics dashboard
- Team productivity insights
- Multi-language support
- Mobile companion app


## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- TiDB Serverless account (free at [tidbcloud.com](https://tidbcloud.com))
- Chrome browser for extension

### 1. Clone and Setup
```bash
git clone https://github.com/Scrumy-TiDB-Hackathon-2025/scrumy.git
cd scrumy

# Setup backend
cd ai_processing
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Build Whisper
chmod +x build_whisper.sh
./build_whisper.sh
```

### 2. Configure Environment
```bash
# Copy environment template
cp shared/.env.example shared/.tidb.env

# Edit shared/.tidb.env with your credentials:
# - TiDB connection string (required)
# - Integration platform tokens (optional)
# - AI provider API keys (optional)
```

**Required Configuration:**
```bash
# TiDB Serverless (Required)
TIDB_CONNECTION_STRING="mysql://username:password@gateway01.us-west-2.prod.aws.tidbcloud.com:4000/test"

# AI Provider (Choose one)
GROQ_API_KEY="your_groq_api_key"  # Free tier recommended
```

**Optional Integrations:**
```bash
# Task Management Platforms
NOTION_TOKEN="secret_your_notion_integration_token"
NOTION_DATABASE_ID="your_database_id_here"
CLICKUP_TOKEN="pk_your_clickup_api_token"
CLICKUP_LIST_ID="your_list_id_here"

# Communication
SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
```

### 3. Start Services
```bash
# Start backend
./clean_start_backend.sh

# In another terminal, start frontend
cd frontend_dashboard
npm install
npm run dev
```

### 4. Install Chrome Extension
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `chrome_extension` folder
4. The ScrumBot extension will appear in your browser

## Chrome Extension

The ScrumBot Chrome extension captures audio directly from video conferencing platforms:

### Supported Platforms
- **Google Meet** (`meet.google.com`)
- **Zoom** (`zoom.us`)
- **Microsoft Teams** (`teams.microsoft.com`)

### Features
- **One-Click Recording**: Start/stop recording with extension popup
- **Real-time Streaming**: Audio sent via WebSocket to ScrumBot backend
- **Meeting Detection**: Automatically detects when you're in a video call
- **Privacy Focused**: Audio processed locally, not sent to external services

### Usage
1. Join a video call on supported platforms
2. Click the ScrumBot extension icon
3. Click "Start Recording" when ready
4. View real-time transcription in the ScrumBot dashboard
5. Click "Stop Recording" to end and process the meeting

## MCP Integration

ScrumBot implements the Model Context Protocol for seamless task management:

### Notion Integration
- **Automatic Task Creation**: Action items from meetings become Notion pages
- **Rich Properties**: Tasks include assignee, due date, priority, and meeting context
- **Database Sync**: All tasks stored in both TiDB and Notion for redundancy

### Slack Integration
- **Real-time Notifications**: Team members get notified of new tasks
- **Rich Formatting**: Tasks displayed with context and meeting information
- **Channel Routing**: Tasks sent to appropriate channels based on team/project

### Setup MCP Integration
```bash
# Notion Setup
1. Create integration at https://developers.notion.com
2. Create a tasks database in Notion
3. Set NOTION_TOKEN and NOTION_DATABASE_ID environment variables

# Slack Setup
1. Create app at https://api.slack.com/apps
2. Add bot token scopes: chat:write, chat:write.public
3. Install app to workspace
4. Set SLACK_BOT_TOKEN environment variable
```

## Development Setup

ScrumBot is built on Meetily's solid foundation. For detailed setup instructions, refer to the sections below or the original [Meetily documentation](https://github.com/Zackriya-Solutions/meeting-minutes).

### Environment Variables
```bash
# TiDB Configuration (Required)
TIDB_CONNECTION_STRING="mysql://username:password@gateway01.us-west-2.prod.aws.tidbcloud.com:4000/test"

# MCP Integration (Optional)
NOTION_TOKEN="secret_your_notion_integration_token"
NOTION_DATABASE_ID="your_database_id_here"
SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"

# AI Providers (Choose one or more)
GROQ_API_KEY="your_groq_api_key"  # Free tier: 100 requests/day
OPENAI_API_KEY="your_openai_key"  # Optional
ANTHROPIC_API_KEY="your_claude_key"  # Optional
```

### Project Structure
```
scrumy/
├── backend/                 # FastAPI backend (from Meetily)
│   ├── app/                # Core application logic
│   ├── whisper.cpp/        # Whisper transcription engine
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend (from Meetily)
│   ├── src/               # React components and pages
│   └── package.json       # Node.js dependencies
├── nextjs-frontend/        # Standalone web dashboard (ScrumBot)
├── scrumbot-extension/     # Chrome extension (New)
│   ├── manifest.json      # Extension configuration
│   ├── content.js         # Meeting detection and audio capture
│   └── popup.html         # Extension UI
└── docs/                  # Documentation and assets
```

### Development Workflow
1. **Backend Development**: Modify FastAPI endpoints in `backend/app/`
2. **Frontend Development**: Update React components in `frontend/src/`
3. **Extension Development**: Modify Chrome extension in `scrumbot-extension/`
4. **Database Changes**: Update TiDB schema and migrations
5. **MCP Integration**: Enhance Notion/Slack integrations

## Built on Meetily

ScrumBot is built on the excellent foundation provided by [Meetily](https://github.com/Zackriya-Solutions/meeting-minutes) by [Zackriya Solutions](https://github.com/Zackriya-Solutions). We extend Meetily's core capabilities with:

### Inherited from Meetily ✅
- **Audio Capture**: Real-time microphone and system audio capture
- **Whisper Integration**: Local transcription using Whisper.cpp
- **Multi-AI Support**: Ollama, Groq, OpenAI, Claude integration
- **Modern UI**: Next.js frontend with real-time updates
- **Privacy First**: Local processing, no external dependencies
- **Cross-Platform**: macOS and Windows support

### Enhanced by ScrumBot 🆕
- **TiDB Serverless**: Scalable cloud database integration
- **Chrome Extension**: Direct video call audio capture
- **MCP Protocol**: Automated task management workflow
- **Advanced Analytics**: Meeting insights and team productivity
- **Cross-Platform Sync**: Notion and Slack integration

### Whisper Model Selection

ScrumBot inherits Meetily's flexible Whisper model support:

**Recommended for Development:**
- `tiny` or `base` - Fast, low memory usage
- `small` - Good balance of speed and accuracy
- `medium` - Higher accuracy for production use

**Advanced Models:**
- `large-v3` - Highest accuracy, requires more resources
- `small.en-tdrz` - With speaker diarization support

### AI Provider Configuration

Choose your preferred AI provider based on your needs:

| Provider | Cost | Speed | Quality | Setup |
|----------|------|-------|---------|-------|
| **Ollama** | Free | Medium | Good | Local install |
| **Groq** | Free tier | Very Fast | Excellent | API key |
| **OpenAI** | Paid | Fast | Excellent | API key |
| **Claude** | Paid | Medium | Excellent | API key |

## Contributing

We welcome contributions to ScrumBot! This project is built for the TiDB Hackathon 2025 and extends the excellent Meetily foundation.

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Areas
- **TiDB Integration**: Enhance database queries and analytics
- **Chrome Extension**: Improve audio capture and platform support
- **MCP Protocol**: Extend Notion/Slack integrations
- **AI Processing**: Add new AI providers or improve existing ones
- **Frontend**: Enhance UI/UX and add new features

## License

MIT License - Feel free to use this project for your own purposes.

This project builds upon [Meetily](https://github.com/Zackriya-Solutions/meeting-minutes) which is also MIT licensed.

## Acknowledgments

### Built on Meetily Foundation
**ScrumBot is built on the excellent [Meetily](https://github.com/Zackriya-Solutions/meeting-minutes) project by [Zackriya Solutions](https://github.com/Zackriya-Solutions).**

- **Original Authors**: [Zackriya Solutions](https://in.linkedin.com/company/zackriya-solutions)
- **Meetily Website**: [meetily.zackriya.com](https://meetily.zackriya.com)
- **Meetily Repository**: [github.com/Zackriya-Solutions/meeting-minutes](https://github.com/Zackriya-Solutions/meeting-minutes)

### Core Technologies
- **[Whisper.cpp](https://github.com/ggerganov/whisper.cpp)** - Local speech recognition
- **[TiDB](https://tidbcloud.com/)** - Distributed SQL database
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Next.js](https://nextjs.org/)** - React framework for production

### TiDB Hackathon 2025
This project was created for the **TiDB Hackathon 2025**, showcasing the power of TiDB Serverless for modern applications.

- **Event**: [TiDB Hackathon 2025](https://tidb-2025-hackathon.devpost.com/)
- **Database**: [TiDB Serverless](https://tidbcloud.com/)
- **Team**: Scrumy Team

### Special Thanks
- **Meetily Team** for providing the robust foundation
- **TiDB Team** for the excellent serverless database platform
- **Open Source Community** for the amazing tools and libraries

---

<div align="center">
<strong>🤖 ScrumBot - Extending Meetily with TiDB & MCP Integration</strong><br>
<em>Built for TiDB Hackathon 2025</em>
</div>
