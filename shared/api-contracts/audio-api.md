# Audio API Contract

## WebSocket Audio Streaming

### Connection
```
ws://localhost:8000/ws/audio
```

### Message Format
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

### Response Format
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
  "platform": "google-meet"
}
Response: {
  "status": "success",
  "meeting_id": "meeting_123",
  "analysis": "AI analysis of the meeting",
  "actions_taken": [
    {
      "tool": "create_notion_task",
      "arguments": {...},
      "result": {...}
    }
  ],
  "tools_used": 2,
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
    "speakers": {...},
    "summary": {...},
    "tasks": {...}
  }
}
```