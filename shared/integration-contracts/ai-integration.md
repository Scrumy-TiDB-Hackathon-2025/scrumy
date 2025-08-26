# AI Processing Integration Contract

## Overview

This contract defines the standardized interface between the AI processing system and external tools/integrations. It ensures loose coupling while enabling seamless data exchange and tool execution.

## Base URL Configuration

### Development
```
AI_PROCESSING_BASE_URL=http://localhost:8001
INTEGRATION_BASE_URL=http://localhost:3003
```

### Production
```
AI_PROCESSING_BASE_URL=https://api.scrumy.ai
INTEGRATION_BASE_URL=https://integration.scrumy.ai
```

## Data Models

### Meeting Data
```typescript
interface MeetingData {
  meeting_id: string;
  title: string;
  platform: 'google-meet' | 'zoom' | 'teams' | 'unknown';
  participants: string[];
  participant_data?: ParticipantData[];
  participant_count?: number;
  duration: string;
  transcript: string;
  created_at: string;
}

interface ParticipantData {
  id: string;
  name: string;
  platform_id: string;
  status: 'active' | 'inactive' | 'left';
  is_host: boolean;
  join_time: string;
}
```

### Task Definition
```typescript
interface TaskDefinition {
  id: string;
  title: string;
  description: string;
  assignee?: string;
  due_date?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed';
  category: 'action_item' | 'follow_up' | 'decision_required';
  meeting_id: string;
  created_at: string;
  source: 'ai_extracted' | 'manual';
}
```

### Summary Data
```typescript
interface MeetingSummary {
  meeting_id: string;
  executive_summary: {
    overview: string;
    key_outcomes: string[];
    business_impact: string;
    urgency_level: 'low' | 'medium' | 'high';
  };
  key_decisions: Array<{
    decision: string;
    rationale: string;
    impact: string;
    confidence: number;
  }>;
  participants: Array<{
    name: string;
    role: string;
    participation_level: 'high' | 'medium' | 'low';
    key_contributions: string[];
  }>;
  next_steps: Array<{
    action: string;
    owner: string;
    deadline: string;
    priority: 'high' | 'medium' | 'low';
  }>;
}
```

## AI Processing to Integration API

### 1. Process Meeting Complete
Triggered when AI processing completes full meeting analysis.

```
POST /integration/process-complete-meeting
```

**Request:**
```json
{
  "meeting_data": MeetingData,
  "summary": MeetingSummary,
  "tasks": TaskDefinition[],
  "speakers": Array<{
    "id": string,
    "name": string,
    "participant_id": string,
    "segments": string[],
    "total_words": number,
    "speaker_confidence": number
  }>,
  "participants": Array<{
    "id": string,
    "name": string,
    "platform_id": string,
    "status": string,
    "is_host": boolean,
    "join_time": string,
    "participation_level": "high" | "medium" | "low",
    "key_contributions": string[]
  }>,
  "processing_metadata": {
    "ai_model_used": string,
    "confidence_score": number,
    "processing_time": number,
    "tools_executed": string[],
    "enhanced_participant_data": boolean,
    "speaker_identification_method": "explicit_labels" | "ai_inference" | "fallback"
  }
}
```

**Response:**
```json
{
  "success": boolean,
  "integration_id": string,
  "tools_executed": Array<{
    "tool_name": string,
    "status": "success" | "failed" | "skipped",
    "result": any,
    "execution_time": number
  }>,
  "external_references": {
    "notion_pages": string[],
    "slack_messages": string[],
    "calendar_events": string[]
  }
}
```

### 2. Task Creation Request
Request creation of tasks in external systems.

```
POST /integration/create-tasks
```

**Request:**
```json
{
  "tasks": TaskDefinition[],
  "meeting_context": {
    "meeting_id": string,
    "meeting_title": string,
    "participants": string[]
  },
  "creation_options": {
    "create_notion_tasks": boolean,
    "send_slack_notifications": boolean,
    "create_calendar_events": boolean,
    "notify_assignees": boolean
  }
}
```

**Response:**
```json
{
  "success": boolean,
  "created_tasks": Array<{
    "task_id": string,
    "external_id": string,
    "external_url": string,
    "platform": "notion" | "slack" | "calendar",
    "status": "created" | "failed"
  }>,
  "notifications_sent": Array<{
    "recipient": string,
    "method": "slack" | "email",
    "status": "sent" | "failed"
  }>
}
```

## Integration to AI Processing API

### 1. Update Task Status
Update task status from external systems.

```
PATCH /ai-processing/tasks/{task_id}/status
```

**Request:**
```json
{
  "status": "pending" | "in_progress" | "completed",
  "updated_by": string,
  "external_reference": {
    "platform": "notion" | "slack" | "calendar",
    "external_id": string,
    "external_url": string
  },
  "completion_notes": string
}
```

### 2. Get Meeting Context
Retrieve meeting context for tool execution.

```
GET /ai-processing/meetings/{meeting_id}/context
```

**Response:**
```json
{
  "meeting_data": MeetingData,
  "participants": Array<{
    "name": string,
    "email": string,
    "role": string
  }>,
  "previous_meetings": Array<{
    "meeting_id": string,
    "title": string,
    "date": string
  }>,
  "related_tasks": TaskDefinition[]
}
```

## Tool Registration Contract

### Register Available Tools
Integration systems register their available tools with AI processing.

```
POST /ai-processing/tools/register
```

**Request:**
```json
{
  "tool_name": string,
  "description": string,
  "version": string,
  "endpoint": string,
  "authentication": {
    "type": "bearer" | "api_key" | "oauth",
    "required_scopes": string[]
  },
  "capabilities": {
    "can_create_tasks": boolean,
    "can_send_notifications": boolean,
    "can_schedule_events": boolean,
    "supported_platforms": string[]
  },
  "input_schema": object,
  "output_schema": object
}
```

### Execute Tool
AI processing executes registered tools.

```
POST /integration/tools/{tool_name}/execute
```

**Request:**
```json
{
  "action": string,
  "parameters": object,
  "context": {
    "meeting_id": string,
    "user_id": string,
    "execution_id": string
  }
}
```

**Response:**
```json
{
  "success": boolean,
  "result": object,
  "execution_time": number,
  "external_references": Array<{
    "type": "url" | "id",
    "value": string,
    "platform": string
  }>
}
```

## Event-Driven Integration

### Webhook Events
Integration systems can subscribe to AI processing events.

#### Meeting Processed Event
```json
{
  "event": "meeting.processed",
  "timestamp": "2025-01-08T15:30:00Z",
  "data": {
    "meeting_id": string,
    "status": "completed" | "failed",
    "summary": MeetingSummary,
    "tasks_count": number,
    "participants_count": number
  }
}
```

#### Task Created Event
```json
{
  "event": "task.created",
  "timestamp": "2025-01-08T15:30:00Z",
  "data": {
    "task_id": string,
    "meeting_id": string,
    "assignee": string,
    "priority": string,
    "due_date": string
  }
}
```

#### Speaker Identified Event
```json
{
  "event": "speaker.identified",
  "timestamp": "2025-01-08T15:30:00Z",
  "data": {
    "meeting_id": string,
    "speaker_name": string,
    "speaker_id": string,
    "participant_id": string,
    "confidence": number,
    "speaker_confidence": number,
    "segment_text": string,
    "identification_method": "explicit_labels" | "ai_inference" | "participant_context"
  }
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": boolean,
  "error_code": string,
  "message": string,
  "details": object,
  "timestamp": string,
  "request_id": string
}
```

### Error Codes
- `INVALID_MEETING_ID`: Meeting not found
- `PROCESSING_FAILED`: AI processing failed
- `TOOL_UNAVAILABLE`: Requested tool not available
- `AUTHENTICATION_FAILED`: Tool authentication failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `EXTERNAL_SERVICE_ERROR`: External service unavailable

## Security Considerations

### Authentication
- All API calls must include valid JWT tokens
- Service-to-service authentication using API keys
- OAuth 2.0 for user-delegated actions

### Data Privacy
- Meeting transcripts encrypted in transit and at rest
- PII data anonymization options
- GDPR compliance for EU users
- Data retention policies enforced

### Rate Limiting
- 100 requests per minute per API key
- Burst allowance of 20 requests
- WebSocket connections limited to 10 per user

## Implementation Guidelines

### AI Processing Side
```typescript
// Example implementation in AI processing
class IntegrationClient {
  async notifyMeetingComplete(meetingData: MeetingData, results: ProcessingResults) {
    const payload = {
      meeting_data: meetingData,
      summary: results.summary,
      tasks: results.tasks,
      speakers: results.speakers,
      participants: results.participants,
      processing_metadata: {
        ...results.metadata,
        enhanced_participant_data: results.participantData?.length > 0,
        speaker_identification_method: results.speakerIdentificationMethod
      }
    };
    
    await this.post('/integration/process-complete-meeting', payload);
  }
  
  async processEnhancedAudioChunk(audioChunk: AudioChunkEnhanced) {
    // Enhanced audio processing with participant context
    const result = await this.audioProcessor.processWithParticipants(
      audioChunk.data,
      audioChunk.participants,
      audioChunk.participant_count
    );
    
    return {
      ...result,
      participant_context: audioChunk.participants,
      speaker_mapping: this.mapSpeakersToParticipants(result.speakers, audioChunk.participants)
    };
  }
}
```

### Integration Side
```typescript
// Example implementation in integration module
class AIProcessingClient {
  async updateTaskStatus(taskId: string, status: TaskStatus) {
    const payload = {
      status: status.value,
      updated_by: status.updatedBy,
      external_reference: status.externalRef
    };
    
    await this.patch(`/ai-processing/tasks/${taskId}/status`, payload);
  }
}
```

## Testing Contract

### Mock Implementations
Both sides should provide mock implementations for testing:

```typescript
// AI Processing Mock
class MockIntegrationService {
  async processCompleteMeeting(data: any) {
    return {
      success: true,
      integration_id: 'mock_' + Date.now(),
      tools_executed: []
    };
  }
}

// Integration Mock
class MockAIProcessingService {
  async getMeetingContext(meetingId: string) {
    return {
      meeting_data: { /* mock data */ },
      participants: [],
      previous_meetings: [],
      related_tasks: []
    };
  }
}
```

## Versioning

### API Versioning
- Version in URL path: `/v1/integration/...`
- Backward compatibility for 2 major versions
- Deprecation notices 6 months before removal

### Contract Versioning
- Semantic versioning: `MAJOR.MINOR.PATCH`
- Current version: `1.0.0`
- Breaking changes increment MAJOR version

## Enhanced Audio Processing

### WebSocket Audio Streaming with Participant Data

The AI processing system now supports enhanced audio chunks that include real-time participant information from video conferencing platforms.

#### Enhanced Audio Chunk Format
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

#### Enhanced Processing Benefits
- **Improved Speaker Identification**: Uses participant names for more accurate speaker attribution
- **Real-time Participant Tracking**: Maintains current participant list and status
- **Enhanced Meeting Analytics**: Better insights into participation levels and engagement
- **Backward Compatibility**: Still supports legacy `audio_chunk` format

#### Integration Impact
Enhanced audio processing provides richer data for:
- Task assignment based on actual participants
- More accurate meeting summaries with proper speaker attribution  
- Better notification targeting to actual meeting attendees
- Improved analytics and participation metrics

## Monitoring and Observability

### Metrics to Track
- Request/response times
- Error rates by endpoint
- Tool execution success rates
- Meeting processing completion rates
- External service availability
- Enhanced audio chunk processing rates
- Speaker identification accuracy
- Participant data extraction success rates

### Logging Requirements
- Structured JSON logging
- Request correlation IDs
- Performance metrics
- Error stack traces (sanitized)
- User action audit trails