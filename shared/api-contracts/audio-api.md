# Audio API Contract

## WebSocket Audio Streaming

### Connection
```
ws://localhost:8000/ws/audio
```

### Message Format

#### Basic Audio Chunk
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_audio_data",
  "timestamp": "2025-01-08T10:00:00Z",
  "metadata": {
    "platform": "google-meet|zoom|teams",
    "meetingUrl": "https://meet.google.com/abc-def-ghi",
    "chunkSize": 1024,
    "sampleRate": 16000
  }
}
```

#### Enhanced Audio Chunk (with participant data)
```json
{
  "type": "AUDIO_CHUNK_ENHANCED",
  "data": "base64_encoded_audio_data",
  "timestamp": "2025-01-08T10:00:00Z",
  "platform": "google-meet|zoom|teams",
  "meetingUrl": "https://meet.google.com/abc-def-ghi",
  "participants": [
    {
      "id": "participant_1",
      "name": "Christian Onyisi",
      "platform_id": "google_meet_user_123",
      "status": "active",
      "is_host": false,
      "join_time": "2025-01-08T10:00:00Z"
    },
    {
      "id": "participant_2", 
      "name": "John Smith",
      "platform_id": "google_meet_user_456",
      "status": "active",
      "is_host": true,
      "join_time": "2025-01-08T09:58:30Z"
    }
  ],
  "participant_count": 2,
  "metadata": {
    "chunk_size": 1024,
    "sample_rate": 16000,
    "channels": 1,
    "format": "webm"
  }
}
```

### Response Format

#### Basic Transcription Result
```json
{
  "type": "transcription_result",
  "data": {
    "text": "Transcribed text",
    "confidence": 0.95,
    "timestamp": "2025-01-08T10:00:00Z",
    "speaker": "Speaker 1"
  }
}
```

#### Enhanced Transcription Result (with speaker attribution)
```json
{
  "type": "TRANSCRIPTION_RESULT",
  "data": {
    "text": "Transcribed text",
    "confidence": 0.95,
    "timestamp": "2025-01-08T10:00:00Z",
    "speaker": "Christian Onyisi",
    "speaker_id": "participant_1",
    "speaker_confidence": 0.89,
    "meetingId": "meeting_123",
    "chunkId": 15,
    "speakers": [
      {
        "id": "participant_1",
        "name": "Christian Onyisi",
        "segments": ["This part of the conversation"],
        "confidence": 0.89
      }
    ]
  }
}
```

### Meeting Event Messages
```json
{
  "type": "MEETING_EVENT", 
  "eventType": "participant_joined|participant_left|meeting_started|meeting_ended",
  "timestamp": "2025-01-08T10:00:00Z",
  "data": {
    "meetingId": "meeting_123",
    "participant": {
      "id": "participant_3",
      "name": "Sarah Johnson", 
      "platform_id": "google_meet_user_789",
      "status": "active",
      "is_host": false,
      "join_time": "2025-01-08T10:05:00Z"
    },
    "total_participants": 3
  }
}
```

### Message Type Support
The WebSocket endpoint supports both message types:
- `audio_chunk` - Basic format for backward compatibility
- `AUDIO_CHUNK_ENHANCED` - Enhanced format with participant data
- `MEETING_EVENT` - Meeting state changes

## REST API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy"}
```

### Process Transcript
```
POST /process-transcript
Body: {
  "text": "Meeting transcript text",
  "meeting_id": "meeting_123",
  "model": "ollama",
  "model_name": "llama3.2:1b"
}
Response: {
  "process_id": "process_456",
  "status": "processing"
}
```

### Process Transcript with Tools (NEW)
```
POST /process-transcript-with-tools
Body: {
  "text": "Meeting transcript text",
  "meeting_id": "meeting_123",
  "timestamp": "2025-01-08T10:00:00Z",
  "platform": "google-meet",
  "participants": [
    {
      "id": "participant_1",
      "name": "Christian Onyisi",
      "status": "active",
      "is_host": false
    }
  ],
  "participant_count": 2
}
Response: {
  "status": "success",
  "meeting_id": "meeting_123",
  "analysis": "AI analysis of the meeting",
  "speakers": [
    {
      "id": "participant_1", 
      "name": "Christian Onyisi",
      "segments": ["Discussed project timeline"],
      "total_words": 25,
      "confidence": 0.92
    }
  ],
  "actions_taken": [
    {
      "tool": "create_notion_task",
      "arguments": {...},
      "result": {...}
    }
  ],
  "tools_used": 3,
  "processed_at": "2025-01-08T10:05:00Z"
}
```

### Get Available Tools (NEW)
```
GET /available-tools
Response: {
  "tools": [...],
  "tool_names": ["create_notion_task", "send_slack_notification"],
  "count": 2
}
```

### Get Summary
```
GET /get-summary/{meeting_id}
Response: {
  "status": "completed|processing|error",
  "data": {
    "speakers": {
      "speakers": [
        {
          "id": "participant_1",
          "name": "Christian Onyisi",
          "segments": ["Meeting content segments"],
          "total_words": 150,
          "characteristics": "Clear speaking style, technical contributor"
        }
      ],
      "confidence": 0.91,
      "total_speakers": 2,
      "identification_method": "ai_inference"
    },
    "summary": {...},
    "tasks": {...},
    "participants": {
      "participants": [
        {
          "name": "Christian Onyisi",
          "role": "Developer",
          "participation_level": "high",
          "key_contributions": ["Technical insights", "Problem solving"]
        }
      ],
      "total_participants": 2,
      "participation_balance": "balanced"
    }
  }
}
```