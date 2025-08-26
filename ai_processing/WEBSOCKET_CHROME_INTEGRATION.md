# WebSocket Chrome Extension Integration Guide

## Overview

This document describes the WebSocket integration between the AI processing backend and the Chrome extension for real-time meeting transcription and participant identification.

## Architecture

The integration consists of two main communication channels:

1. **WebSocket Connection** - Real-time audio streaming and transcription
2. **REST API Endpoints** - Meeting management and AI processing tools

```
Chrome Extension → WebSocket → AI Processing Backend
                ↓
            Real-time transcription with speaker identification
                ↓
            Database storage (SQLite/TiDB)
```

## WebSocket Endpoints

### Primary WebSocket Endpoint
- **URL**: `ws://localhost:8001/ws`
- **Production**: `wss://your-domain.com/ws`

### Alternative WebSocket Endpoint
- **URL**: `ws://localhost:8001/ws/audio-stream`
- **Production**: `wss://your-domain.com/ws/audio-stream`

## WebSocket Message Protocol

### 1. Handshake Messages

#### Client → Server (HANDSHAKE)
```json
{
  "type": "HANDSHAKE",
  "clientType": "chrome-extension",
  "version": "1.0",
  "capabilities": ["audio-capture", "meeting-detection"]
}
```

#### Server → Client (HANDSHAKE_ACK)
```json
{
  "type": "HANDSHAKE_ACK",
  "serverVersion": "1.0",
  "status": "ready",
  "supportedFeatures": [
    "audio-transcription",
    "speaker-identification",
    "real-time-processing"
  ],
  "timestamp": "2025-01-08T15:30:00.000Z"
}
```

### 2. Audio Processing Messages

#### Client → Server (AUDIO_CHUNK)
```json
{
  "type": "AUDIO_CHUNK",
  "data": "base64-encoded-audio-data",
  "timestamp": 1641645000000,
  "metadata": {
    "platform": "meet.google.com",
    "meetingUrl": "https://meet.google.com/abc-defg-hij",
    "chunkSize": 4096,
    "sampleRate": 16000,
    "channels": 1,
    "sampleWidth": 2
  }
}
```

#### Server → Client (TRANSCRIPTION_RESULT)
```json
{
  "type": "TRANSCRIPTION_RESULT",
  "data": {
    "text": "Hello everyone, welcome to today's meeting.",
    "confidence": 0.95,
    "timestamp": "2025-01-08T15:30:15.000Z",
    "speakers": [
      {
        "id": "speaker_1",
        "name": "John Smith",
        "segments": ["Hello everyone, welcome to today's meeting."],
        "confidence": 0.92
      }
    ],
    "meetingId": "meet_123456",
    "chunkId": 1
  }
}
```

### 3. Meeting Event Messages

#### Client → Server (MEETING_EVENT)
```json
{
  "type": "MEETING_EVENT",
  "eventType": "meeting_started",
  "timestamp": 1641645000000,
  "data": {
    "meetingTitle": "Team Standup",
    "platform": "meet.google.com",
    "participants": ["John Smith", "Jane Doe"]
  }
}
```

#### Server → Client (MEETING_UPDATE)
```json
{
  "type": "MEETING_UPDATE",
  "data": {
    "meetingId": "meet_123456",
    "participants": ["John Smith", "Jane Doe", "Bob Wilson"],
    "latestTranscript": "We need to finalize the project timeline.",
    "timestamp": "2025-01-08T15:30:20.000Z"
  }
}
```

### 4. Error Messages

#### Server → Client (ERROR)
```json
{
  "type": "ERROR",
  "error": "Audio processing failed: Invalid audio format"
}
```

## REST API Endpoints

All endpoints are compatible with the Chrome extension's expected format.

### Core Endpoints

#### Health Check
- **GET** `/health`
- **Response**: `{"status": "healthy"}`

#### Model Configuration
- **GET** `/get-model-config`
- **Response**:
```json
{
  "model": "whisper-cpp",
  "language": "en",
  "sample_rate": 16000,
  "chunk_length": 30
}
```

#### Available Tools
- **GET** `/available-tools`
- **Response**:
```json
{
  "tools": [
    {
      "name": "identify_speakers",
      "description": "Identify speakers in meeting transcript",
      "parameters": ["text", "context"]
    },
    {
      "name": "extract_tasks",
      "description": "Extract action items and tasks",
      "parameters": ["transcript", "meeting_context"]
    },
    {
      "name": "generate_summary",
      "description": "Generate comprehensive meeting summary",
      "parameters": ["transcript", "meeting_title"]
    }
  ],
  "tool_names": ["identify_speakers", "extract_tasks", "generate_summary"],
  "count": 3
}
```

### AI Processing Endpoints

#### Speaker Identification
- **POST** `/identify-speakers`
- **Request**:
```json
{
  "text": "Hello, this is John. How are you doing today, Sarah?",
  "context": "Meeting transcript with multiple speakers"
}
```
- **Response**:
```json
{
  "status": "success",
  "data": {
    "speakers": [
      {
        "id": "speaker_1",
        "name": "John",
        "segments": ["Hello, this is John."],
        "total_words": 4,
        "characteristics": "John - active participant, clear communication"
      },
      {
        "id": "speaker_2",
        "name": "Sarah",
        "segments": ["Response from Sarah"],
        "total_words": 3,
        "characteristics": "Sarah - active participant"
      }
    ],
    "confidence": 0.85,
    "total_speakers": 2,
    "identification_method": "ai_inference",
    "processing_time": 1.5
  }
}
```

#### Meeting Summary Generation
- **POST** `/generate-summary`
- **Request**:
```json
{
  "transcript": "Meeting transcript content...",
  "meeting_id": "meeting_123",
  "meeting_title": "Team Standup"
}
```
- **Response**:
```json
{
  "status": "success",
  "data": {
    "meeting_title": "Team Standup",
    "executive_summary": {
      "overview": "Team discussed project progress and next steps",
      "key_outcomes": ["Updated project timeline", "Assigned new tasks"],
      "business_impact": "Improved team coordination",
      "urgency_level": "medium",
      "follow_up_required": true
    },
    "key_decisions": {
      "decisions": [
        {
          "decision": "Move deadline to next Friday",
          "rationale": "Need more time for testing",
          "impact": "Allows for better quality assurance"
        }
      ],
      "total_decisions": 1,
      "consensus_level": "unanimous"
    },
    "participants": {
      "participants": [
        {
          "name": "John Smith",
          "role": "Team Lead",
          "participation_level": "high",
          "key_contributions": ["Project planning", "Task assignment"]
        }
      ],
      "meeting_leader": "John Smith",
      "total_participants": 3,
      "participation_balance": "balanced"
    },
    "summary_generated_at": "2025-01-08T15:45:00.000Z"
  }
}
```

#### Task Extraction
- **POST** `/extract-tasks`
- **Request**:
```json
{
  "transcript": "Meeting transcript content...",
  "meeting_context": {
    "participants": ["John", "Sarah", "Bob"]
  }
}
```
- **Response**:
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "id": "task_1",
        "title": "Update project documentation",
        "description": "Update the API documentation with new endpoints",
        "assignee": "John Smith",
        "due_date": "2025-01-15",
        "priority": "high",
        "status": "pending",
        "category": "action_item",
        "dependencies": [],
        "business_impact": "high",
        "created_at": "2025-01-08T15:45:00.000Z"
      }
    ],
    "task_summary": {
      "total_tasks": 3,
      "high_priority": 1,
      "with_deadlines": 2,
      "assigned": 3
    },
    "extraction_metadata": {
      "explicit_tasks_found": 2,
      "implicit_tasks_found": 1,
      "extracted_at": "2025-01-08T15:45:00.000Z"
    }
  }
}
```

#### Complete Processing
- **POST** `/process-transcript-with-tools`
- **Request**:
```json
{
  "text": "Meeting transcript content...",
  "meeting_id": "meeting_123",
  "timestamp": "2025-01-08T15:30:00.000Z",
  "platform": "meet.google.com"
}
```
- **Response**:
```json
{
  "status": "success",
  "meeting_id": "meeting_123",
  "analysis": {
    "summary": "Comprehensive meeting analysis...",
    "key_points": ["Point 1", "Point 2"]
  },
  "actions_taken": [
    {
      "id": "task_1",
      "title": "Follow-up action",
      "assignee": "John Smith"
    }
  ],
  "speakers": [
    {
      "id": "speaker_1",
      "name": "John Smith",
      "segments": ["Opening remarks"]
    }
  ],
  "tools_used": 3,
  "processed_at": "2025-01-08T15:45:00.000Z"
}
```

## Audio Format Requirements

### Supported Audio Formats
- **Sample Rate**: 16000 Hz (16 kHz)
- **Channels**: 1 (mono)
- **Sample Width**: 2 bytes (16-bit)
- **Format**: PCM, WAV

### Audio Chunk Size
- **Recommended**: 1-2 second chunks
- **Maximum**: 30 seconds per chunk
- **Encoding**: Base64 for WebSocket transmission

## Error Handling

### WebSocket Errors
- **Connection Failed**: Retry with exponential backoff
- **Audio Processing Error**: Send error message to client
- **Invalid Message Format**: Send format error response

### REST API Errors
- **400 Bad Request**: Invalid request format
- **500 Internal Server Error**: Processing failed
- **503 Service Unavailable**: Server overloaded

## Testing

### WebSocket Testing
Use the provided test script:
```bash
python test_websocket_integration.py
```

### REST API Testing
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test speaker identification
curl -X POST http://localhost:8001/identify-speakers \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is John speaking.", "context": ""}'

# Test available tools
curl http://localhost:8001/available-tools
```

## Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python start_hackathon.py
```

### 3. Verify WebSocket Endpoints
- WebSocket: `ws://localhost:8001/ws`
- REST API: `http://localhost:8001`
- Swagger UI: `http://localhost:8001/docs`

## Production Deployment

### 1. Environment Variables
```bash
# Database configuration
DATABASE_TYPE=tidb  # or sqlite
TIDB_HOST=your-tidb-host
TIDB_USER=your-username
TIDB_PASSWORD=your-password

# Whisper configuration
WHISPER_MODEL_PATH=./models/ggml-base.bin
WHISPER_EXECUTABLE=./whisper.cpp/build/bin/main

# API Keys (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### 2. SSL/TLS Configuration
For production WebSocket connections (WSS), configure your reverse proxy:

#### Nginx Configuration
```nginx
location /ws {
    proxy_pass http://localhost:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Failed
1. Check if server is running on correct port
2. Verify firewall settings
3. Check CORS configuration

#### Audio Processing Errors
1. Verify Whisper model exists
2. Check audio format compatibility
3. Ensure sufficient disk space for temp files

#### Speaker Identification Not Working
1. Verify AI model availability
2. Check transcript quality
3. Ensure proper context is provided

### Debug Logging
Enable debug logging by setting:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

## Performance Optimization

### WebSocket Optimization
- Use connection pooling
- Implement message queuing
- Add rate limiting

### Audio Processing Optimization
- Use faster Whisper models for real-time processing
- Implement audio chunk caching
- Optimize temporary file handling

## Security Considerations

### Authentication (Future Enhancement)
- Implement JWT-based authentication
- Add API key validation
- Use secure WebSocket connections (WSS)

### Data Privacy
- Audio chunks are processed in memory when possible
- Temporary files are automatically cleaned up
- Meeting data is stored securely in database

## Chrome Extension Integration

This WebSocket implementation is specifically designed to work with the ScrumBot Chrome extension located in `../chrome_extension/`. The extension expects:

1. **WebSocket URL**: Configurable in `config.js`
2. **Message Format**: JSON with `type` field
3. **Audio Format**: Base64-encoded PCM data
4. **Real-time Response**: Immediate transcription results

For extension setup and testing, refer to the Chrome extension documentation.