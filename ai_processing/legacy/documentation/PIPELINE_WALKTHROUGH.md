# Audio-to-Tasks Pipeline Walkthrough

## Overview

This document provides a complete walkthrough of the Audio-to-Tasks Pipeline, a system that converts audio recordings of meetings into structured, actionable task lists using AI-powered analysis.

## Architecture

```
Audio File → Whisper.cpp → Transcript → GROQ AI → Structured Tasks
     ↓           ↓            ↓          ↓            ↓
   .mp3/.wav   Speech-to-Text  Plain Text  AI Analysis  JSON Tasks
```

## Components

### 1. Audio Transcription (Whisper.cpp)
- **Purpose**: Convert audio files to text transcripts
- **Technology**: OpenAI Whisper.cpp (local processing)
- **Models**: ggml-base.en.bin (English optimized)
- **Input**: Audio files (.mp3, .wav, etc.)
- **Output**: Plain text transcript

### 2. AI Processing (GROQ API)
- **Purpose**: Analyze transcripts and extract actionable items
- **Technology**: GROQ API with Llama models
- **Models**: llama-3.1-70b-versatile, llama3-8b-8192
- **Input**: Meeting transcript text
- **Output**: Structured tasks with metadata

### 3. Task Extraction Engine
- **Purpose**: Identify and structure action items
- **Features**:
  - Explicit task detection ("I'll do X by Friday")
  - Implicit task inference (problems needing solutions)
  - Assignee identification
  - Deadline extraction
  - Priority assessment

## Setup and Installation

### Prerequisites
```bash
# Python 3.8+
python --version

# Virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Set up GROQ API key
./setup_groq_key.sh

# Verify .env file
cat .env
# Should contain: GROQ_API_KEY=your_key_here
```

### Build Whisper.cpp
```bash
# Build whisper.cpp (if not already built)
cd whisper.cpp
make clean
make

# Verify build
ls build/bin/whisper-cli
```

## Starting the System

### Quick Start
```bash
# Start all services
./clean_start_backend.sh

# Expected output:
# ✅ [SUCCESS] 🎉 Services started successfully!
# 🐍 Python Backend (PID: XXXX) - Port: 5167
# 🎙️ Whisper.cpp: Ready for transcription
```

### Manual Start (Alternative)
```bash
# Start backend only
python -m uvicorn app.main:app --host 0.0.0.0 --port 5167

# Check health
curl http://localhost:5167/health
```

## API Endpoints

### 1. Health Check
```bash
GET /health
# Response: {"status": "healthy"}
```

### 2. Audio Transcription
```bash
POST /transcribe
Content-Type: multipart/form-data

# Example:
curl -X POST -F "file=@meeting.mp3" http://localhost:5167/transcribe

# Response:
{
  "transcript": "Meeting transcript text...",
  "processing_time": 2.34,
  "file_size": 1024000
}
```

### 3. Task Extraction
```bash
POST /extract-tasks
Content-Type: application/json

# Example:
curl -X POST -H "Content-Type: application/json" \
  -d '{"transcript": "John will update the docs by Friday"}' \
  http://localhost:5167/extract-tasks

# Response:
{
  "tasks": [
    {
      "id": "task_1",
      "title": "Update documentation",
      "assignee": "John",
      "due_date": "Friday",
      "priority": "medium",
      "description": "Update the docs",
      "source": "explicit"
    }
  ],
  "task_summary": {
    "total_tasks": 1,
    "high_priority": 0,
    "with_deadlines": 1,
    "assigned": 1
  },
  "extraction_metadata": {
    "explicit_tasks_found": 1,
    "implicit_tasks_found": 0,
    "extracted_at": "2025-08-30T07:15:01.975Z"
  }
}
```

### 4. Complete Meeting Processing
```bash
POST /process-complete-meeting
Content-Type: application/json

# Example:
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "text": "Meeting transcript...",
    "model": "groq",
    "model_name": "llama-3.1-70b-versatile",
    "meeting_id": "meeting-001"
  }' \
  http://localhost:5167/process-complete-meeting
```

## Testing the Pipeline

### 1. Basic Pipeline Test
```bash
# Test complete workflow
python test_full_pipeline.py

# Expected output:
# 🎉 Full pipeline test completed successfully!
```

### 2. Simple Functionality Test
```bash
# Test individual components
python test_simple_pipeline.py

# Expected output:
# ✅ Audio transcription: Working
# ✅ Task extraction: Working
```

### 3. Comprehensive Demo
```bash
# Full demonstration
python pipeline_summary.py

# Expected output:
# 🎉 PIPELINE DEMONSTRATION COMPLETE!
```

### 4. Task-Rich Meeting Test
```bash
# Test with realistic meeting content
python test_pipeline_with_tasks.py

# Note: May hit rate limits with extensive testing
```

## Usage Examples

### Example 1: Simple Meeting Recording
```python
import requests

# Upload audio file
with open('team_meeting.mp3', 'rb') as f:
    files = {'file': ('team_meeting.mp3', f, 'audio/mpeg')}
    response = requests.post('http://localhost:5167/transcribe', files=files)
    transcript = response.json()['transcript']

# Extract tasks
task_data = {'transcript': transcript}
response = requests.post('http://localhost:5167/extract-tasks', json=task_data)
tasks = response.json()['tasks']

print(f"Found {len(tasks)} tasks:")
for task in tasks:
    print(f"- {task['title']} (assigned to {task['assignee']})")
```

### Example 2: Batch Processing
```python
import os
import requests

audio_files = ['meeting1.mp3', 'meeting2.mp3', 'meeting3.mp3']
all_tasks = []

for audio_file in audio_files:
    # Transcribe
    with open(audio_file, 'rb') as f:
        files = {'file': (audio_file, f, 'audio/mpeg')}
        response = requests.post('http://localhost:5167/transcribe', files=files)
        transcript = response.json()['transcript']
    
    # Extract tasks
    task_data = {'transcript': transcript}
    response = requests.post('http://localhost:5167/extract-tasks', json=task_data)
    tasks = response.json()['tasks']
    
    all_tasks.extend(tasks)

print(f"Total tasks from all meetings: {len(all_tasks)}")
```

## Task Structure

### Task Object Schema
```json
{
  "id": "task_1",
  "title": "Clear, actionable task title",
  "description": "Detailed description of what needs to be done",
  "assignee": "Person assigned or 'Unassigned'",
  "due_date": "Deadline if mentioned or null",
  "priority": "high|medium|low",
  "status": "pending|in_progress|completed",
  "source": "explicit|implicit",
  "dependencies": ["prerequisite_task_1"],
  "business_impact": "high|medium|low",
  "created_at": "2025-08-30T07:15:01.975Z"
}
```

### Task Categories
- **Explicit Tasks**: Directly stated action items
- **Implicit Tasks**: Inferred from problems or decisions
- **Dependencies**: Tasks that depend on others
- **Priorities**: Based on urgency and business impact

## Performance Metrics

### Typical Processing Times
- **Audio Transcription**: 2-5 seconds per minute of audio
- **Task Extraction**: 5-15 seconds per transcript
- **Complete Processing**: 10-30 seconds total

### Resource Usage
- **Memory**: ~500MB-1GB during processing
- **CPU**: Moderate usage during transcription
- **Network**: API calls to GROQ (rate limited)

### Rate Limits
- **GROQ API**: 14,400 requests/day, 6,000 tokens/minute
- **Whisper.cpp**: No limits (local processing)

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start
```bash
# Check port availability
lsof -i :5167

# Kill existing processes
pkill -f "python.*main.py"

# Restart
./clean_start_backend.sh
```

#### 2. Whisper.cpp Not Found
```bash
# Verify build
ls whisper.cpp/build/bin/whisper-cli

# Rebuild if necessary
cd whisper.cpp && make clean && make
```

#### 3. GROQ API Errors
```bash
# Check API key
echo $GROQ_API_KEY

# Verify .env file
cat .env | grep GROQ_API_KEY

# Rate limit errors (429)
# Wait and retry, or reduce request frequency
```

#### 4. Task Extraction Returns Empty
- **Cause**: Conservative AI model or unclear transcript
- **Solution**: Use more explicit language in meetings
- **Example**: "John, please update the documentation by Friday" vs "We should update docs"

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Monitor logs
tail -f backend.log
```

## Integration Guide

### Web Application Integration
```javascript
// Frontend example
async function processAudioFile(audioFile) {
  // Step 1: Transcribe
  const formData = new FormData();
  formData.append('file', audioFile);
  
  const transcribeResponse = await fetch('/transcribe', {
    method: 'POST',
    body: formData
  });
  const { transcript } = await transcribeResponse.json();
  
  // Step 2: Extract tasks
  const taskResponse = await fetch('/extract-tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript })
  });
  const { tasks } = await taskResponse.json();
  
  return tasks;
}
```

### Mobile App Integration
```swift
// iOS Swift example
func processAudio(audioData: Data) async throws -> [Task] {
    // Transcribe audio
    let transcriptResponse = try await uploadAudio(audioData)
    let transcript = transcriptResponse.transcript
    
    // Extract tasks
    let tasksResponse = try await extractTasks(transcript: transcript)
    return tasksResponse.tasks
}
```

## Production Deployment

### Environment Variables
```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
LOG_LEVEL=INFO
MAX_FILE_SIZE=50MB
WHISPER_MODEL=ggml-base.en.bin
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5167

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5167"]
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple backend instances behind load balancer
- **Queue System**: Redis/Celery for async processing
- **File Storage**: S3/GCS for audio file storage
- **Database**: PostgreSQL for task persistence

## Security Considerations

### API Security
- **Authentication**: Implement JWT or API key authentication
- **Rate Limiting**: Prevent abuse with request throttling
- **File Validation**: Validate audio file types and sizes
- **Input Sanitization**: Clean transcript text before processing

### Data Privacy
- **Audio Files**: Delete after processing or encrypt at rest
- **Transcripts**: Consider PII detection and redaction
- **API Keys**: Store securely, rotate regularly
- **Logs**: Avoid logging sensitive information

## Monitoring and Maintenance

### Health Monitoring
```bash
# System health
curl http://localhost:5167/health

# Detailed metrics
curl http://localhost:5167/metrics
```

### Log Analysis
```bash
# Error tracking
grep "ERROR" backend.log

# Performance monitoring
grep "processing_time" backend.log

# API usage
grep "POST /transcribe" backend.log | wc -l
```

### Maintenance Tasks
- **Model Updates**: Update Whisper models periodically
- **API Key Rotation**: Rotate GROQ API keys regularly
- **Log Cleanup**: Archive or delete old log files
- **Performance Tuning**: Monitor and optimize based on usage

## Future Enhancements

### Planned Features
- **Speaker Identification**: Identify who said what
- **Real-time Processing**: Live meeting transcription
- **Multi-language Support**: Support for non-English meetings
- **Task Prioritization**: Advanced priority algorithms
- **Integration APIs**: Slack, Teams, Jira integration

### Performance Improvements
- **Caching**: Cache frequent transcriptions
- **Batch Processing**: Process multiple files together
- **Model Optimization**: Fine-tune models for specific domains
- **Edge Deployment**: Local processing for sensitive data

## Support and Resources

### Documentation
- **API Docs**: http://localhost:5167/docs (when running)
- **Whisper.cpp**: https://github.com/ggerganov/whisper.cpp
- **GROQ API**: https://console.groq.com/docs

### Testing Files
- `test_full_pipeline.py`: Complete workflow test
- `test_simple_pipeline.py`: Basic functionality test
- `pipeline_summary.py`: Comprehensive demonstration
- `test_pipeline_with_tasks.py`: Task-rich meeting test

### Configuration Files
- `clean_start_backend.sh`: Service startup script
- `setup_groq_key.sh`: API key configuration
- `.env`: Environment variables
- `requirements.txt`: Python dependencies

---

**Last Updated**: August 30, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅