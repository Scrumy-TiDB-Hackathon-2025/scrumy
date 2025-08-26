# AI Processing Application Core

This directory contains the core application logic for the ScrumBot AI Processing backend, responsible for audio transcription, meeting analysis, and data processing.

## 📁 Directory Overview

The `app/` directory contains the main Python modules that power the AI processing backend:

```
app/
├── main.py                    # FastAPI application entry point
├── websocket_server.py        # WebSocket server for real-time communication
├── integrated_processor.py    # Main processing orchestrator
├── ai_processor.py           # Core AI processing logic
├── transcript_processor.py   # Transcript analysis and processing
├── meeting_summarizer.py     # Meeting summary generation
├── speaker_identifier.py     # Speaker identification logic
├── task_extractor.py         # Task extraction from meetings
├── tools_endpoints.py        # External tools integration endpoints
├── integration_adapter.py    # Integration layer for external services
├── database_interface.py     # Database abstraction layer
├── database_config.py        # Database configuration management
├── sqlite_database.py        # SQLite database implementation
├── tidb_database.py          # TiDB database implementation
├── db.py                     # Legacy database utilities
└── mock_data/                # Mock data for testing and development
```

## 🚀 Core Components

### 1. Application Entry Point

**`main.py`** - FastAPI application setup
- Configures FastAPI server with CORS
- Sets up all API endpoints
- Handles health checks and status monitoring
- Manages application lifecycle

### 2. WebSocket Server

**`websocket_server.py`** - Real-time communication
- Handles WebSocket connections from Chrome extension
- Processes real-time audio streams
- Manages connection lifecycle
- Sends transcription updates to clients

### 3. Processing Pipeline

**`integrated_processor.py`** - Main processing orchestrator
- Coordinates all AI processing tasks
- Manages workflow between different processors
- Handles error recovery and retries
- Provides unified processing interface

**`ai_processor.py`** - Core AI processing
- Interfaces with Whisper for transcription
- Handles audio preprocessing
- Manages AI model interactions
- Provides transcription quality checks

### 4. Analysis Components

**`transcript_processor.py`** - Transcript analysis
- Processes raw transcriptions
- Applies text cleaning and formatting
- Handles speaker attribution
- Generates structured transcript data

**`meeting_summarizer.py`** - Summary generation
- Creates concise meeting summaries
- Identifies key discussion points
- Generates action items
- Produces executive summaries

**`speaker_identifier.py`** - Speaker identification
- Analyzes audio patterns for speaker detection
- Manages speaker profiles
- Handles speaker attribution in transcripts
- Provides speaker statistics

**`task_extractor.py`** - Task extraction
- Identifies action items from discussions
- Extracts deadlines and assignments
- Creates structured task data
- Integrates with project management tools

### 5. Integration Layer

**`tools_endpoints.py`** - External tools integration
- Provides endpoints for external tool integration
- Handles webhook management
- Manages tool authentication
- Processes tool-specific data formats

**`integration_adapter.py`** - Integration abstraction
- Provides unified interface for external services
- Handles service authentication
- Manages data transformation between systems
- Provides error handling for integration failures

### 6. Database Layer

**`database_interface.py`** - Database abstraction
- Defines database interface contracts
- Provides database-agnostic operations
- Handles connection management
- Manages transaction lifecycle

**`database_config.py`** - Database configuration
- Manages database connection settings
- Handles environment-specific configurations
- Provides database switching capabilities
- Manages connection pooling

**`sqlite_database.py`** - SQLite implementation
- SQLite-specific database operations
- Local development database support
- Lightweight data persistence
- Testing and development utilities

**`tidb_database.py`** - TiDB implementation
- TiDB Cloud integration
- Production-ready database operations
- Distributed database support
- Advanced querying capabilities

## 🔧 Key Workflows

### 1. Audio Processing Workflow
```
Audio Input → WebSocket → AI Processor → Whisper → Transcript Processor → Database
```

### 2. Meeting Analysis Workflow
```
Transcript → Meeting Summarizer → Task Extractor → Speaker Identifier → Structured Data
```

### 3. Real-time Processing
```
Chrome Extension → WebSocket Server → Integrated Processor → Live Updates
```

## 🛠️ Development Guidelines

### Adding New Processors
1. Create new processor in appropriate module
2. Implement standardized interface
3. Add to `integrated_processor.py` orchestration
4. Update API endpoints in `main.py`
5. Add tests in `/tests` directory

### Database Operations
- Use `database_interface.py` for all database operations
- Don't directly import database implementations
- Use configuration switching for different environments
- Always handle database connection errors

### WebSocket Integration
- Follow existing WebSocket patterns in `websocket_server.py`
- Handle connection lifecycle properly
- Implement proper error handling and reconnection
- Send structured JSON messages

## 📊 Data Flow

### Input Data
- Audio streams from Chrome extension
- WebSocket messages with meeting metadata
- Configuration parameters

### Processing Steps
1. **Audio Reception**: WebSocket server receives audio chunks
2. **Transcription**: AI processor sends audio to Whisper
3. **Analysis**: Transcript processor analyzes content
4. **Enhancement**: Various processors add metadata
5. **Storage**: Database interface persists results
6. **Output**: Structured data sent to frontend

### Output Data
- Real-time transcription updates
- Meeting summaries and insights
- Extracted tasks and action items
- Speaker identification results

## 🔍 Testing

### Unit Tests
```bash
# Run specific app tests
pytest tests/ -v

# Test individual components
pytest tests/test_endpoints.py -v
```

### Integration Tests
```bash
# Test full processing pipeline
python test_core_functionality_integration.py

# Test WebSocket integration
python test_websocket_integration.py
```

## 🚨 Common Issues

### Whisper Integration
- Ensure Whisper server is running on correct port
- Check audio format compatibility
- Verify model loading and initialization

### Database Connectivity
- Check database configuration in environment
- Verify connection credentials
- Test database switching functionality

### WebSocket Problems
- Check CORS configuration
- Verify WebSocket endpoint URLs
- Test connection lifecycle handling

## 📝 Configuration

### Environment Variables
- `DATABASE_TYPE`: Choose between 'sqlite' or 'tidb'
- `TIDB_HOST`: TiDB connection host
- `WHISPER_SERVER_URL`: Whisper server endpoint
- `DEBUG_MODE`: Enable debug logging

### Development Setup
1. Set up virtual environment
2. Install requirements: `pip install -r requirements.txt`
3. Configure database settings
4. Start Whisper server
5. Run FastAPI server: `python server.py`

## 📚 Related Documentation

- [API Documentation](../API_DOCUMENTATION.md)
- [AI Integration Guide](../AI_INTEGRATION_GUIDE.md)
- [WebSocket Integration](../WEBSOCKET_CHROME_INTEGRATION.md)
- [Testing Guide](../tests/README.md)

---

**Maintainer**: ScrumBot AI Team  
**Last Updated**: August 2025  
**Version**: 1.0.0