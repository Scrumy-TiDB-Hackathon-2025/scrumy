# ScrumBot Mock Servers

This directory contains comprehensive mock servers for ScrumBot development and testing, implementing the enhanced audio chunk integration with participant data support.

## 🎯 Overview

The mock servers provide realistic testing environments for:

- **Chrome Extension Development**: WebSocket server that mimics the AI processing backend
- **Frontend Dashboard Development**: REST API server that provides meeting data and analytics
- **Integration Testing**: End-to-end testing of the complete ScrumBot system

## 📁 Directory Structure

```
mock-servers/
├── chrome-extension/          # WebSocket mock server for Chrome extension
│   ├── websocket-mock-server.py     # Main WebSocket server implementation
│   ├── start-server.sh              # Startup script with auto-setup
│   ├── test-server.py               # Comprehensive test suite
│   └── requirements.txt             # Python dependencies
│
├── frontend-dashboard/        # REST API mock server for frontend dashboard
│   ├── rest-api-mock-server.py      # Main REST API server implementation
│   ├── start-server.sh              # Startup script with auto-setup
│   ├── test-server.py               # Comprehensive test suite
│   └── requirements.txt             # Python dependencies
│
├── shared/                    # Shared mock data and utilities
│   └── mock-meetings-data.json      # Comprehensive meeting data with enhanced format
│
├── start-all-servers.sh       # Master script to start both servers
└── README.md                  # This documentation
```

## 🚀 Quick Start

### Start All Servers (Recommended)

```bash
# Navigate to mock servers directory
cd scrumy/shared/mock-servers/

# Start both servers with default settings
./start-all-servers.sh

# Or with custom configuration
./start-all-servers.sh --debug --chrome-port 8080 --frontend-port 8081
```

### Start Individual Servers

#### Chrome Extension WebSocket Server

```bash
cd chrome-extension/
./start-server.sh --host localhost --port 8000
```

#### Frontend Dashboard REST API Server

```bash
cd frontend-dashboard/
./start-server.sh --host 0.0.0.0 --port 3001
```

## 🤖 Chrome Extension WebSocket Mock Server

### Purpose
Simulates the AI processing backend that the Chrome extension connects to for real-time audio processing and transcription.

### Features
- **Enhanced Audio Chunk Support**: Full support for `AUDIO_CHUNK_ENHANCED` format with participant data
- **Backward Compatibility**: Also handles basic `audio_chunk` format
- **Realistic Speaker Identification**: Uses participant data for improved accuracy
- **Session Management**: Tracks meeting sessions and participant data
- **Meeting Events**: Handles participant join/leave events
- **Mock Transcription**: Returns realistic transcription results with confidence scores

### WebSocket Endpoint
```
ws://localhost:8000/ws/audio
```

### Supported Message Types

#### Input Messages (from Chrome Extension)
1. **AUDIO_CHUNK_ENHANCED** - Enhanced audio with participant data
2. **audio_chunk** - Basic audio chunk (legacy support)
3. **MEETING_EVENT** - Meeting state changes
4. **GET_SESSION_INFO** - Request session information

#### Output Messages (to Chrome Extension)
1. **CONNECTION_ESTABLISHED** - Welcome message
2. **TRANSCRIPTION_RESULT** - Enhanced transcription with speaker attribution
3. **MEETING_UPDATE** - Periodic meeting statistics
4. **EVENT_ACKNOWLEDGED** - Event confirmation
5. **SESSION_INFO** - Session details
6. **ERROR** - Error messages

### Example Usage

```javascript
// Chrome Extension Connection
const ws = new WebSocket('ws://localhost:8000/ws/audio');

// Send enhanced audio chunk
ws.send(JSON.stringify({
  type: "AUDIO_CHUNK_ENHANCED",
  data: "base64_encoded_audio",
  timestamp: "2025-01-09T10:00:00Z",
  platform: "google-meet",
  meetingUrl: "https://meet.google.com/abc-def-ghi",
  participants: [
    {
      id: "participant_1",
      name: "John Smith",
      platform_id: "google_meet_user_123",
      status: "active",
      is_host: true,
      join_time: "2025-01-09T10:00:00Z"
    }
  ],
  participant_count: 1,
  metadata: {
    chunk_size: 1024,
    sample_rate: 16000,
    channels: 1,
    format: "webm"
  }
}));
```

### Configuration Options

```bash
./start-server.sh [OPTIONS]

Options:
  --host HOST        Server host (default: localhost)
  --port PORT        Server port (default: 8000)
  --debug           Enable debug logging
  --setup-only      Only setup environment
  --no-venv         Don't use virtual environment
  --help            Show help message
```

### Testing

```bash
# Run comprehensive tests
python test-server.py

# Test with custom server
python test-server.py --server ws://localhost:8080/ws/audio --verbose
```

## 📊 Frontend Dashboard REST API Mock Server

### Purpose
Provides REST API endpoints that the frontend dashboard consumes for displaying meeting data, analytics, and managing tasks.

### Features
- **Complete API Coverage**: All endpoints the frontend dashboard expects
- **Enhanced Data Format**: Matches the updated contracts with participant data
- **CORS Support**: Properly configured for frontend development
- **Realistic Data**: Comprehensive mock data with relationships
- **Query Filtering**: Support for query parameters and pagination
- **Error Handling**: Proper HTTP status codes and error responses

### Base URL
```
http://0.0.0.0:3001
```

### Available Endpoints

#### Core Data Endpoints
- `GET /health` - Server health check
- `GET /get-meetings` - List all meetings (supports filtering)
- `GET /get-summary/{meeting_id}` - Get meeting summary and analysis
- `GET /get-transcripts/{meeting_id}` - Get meeting transcripts (paginated)
- `GET /get-participants/{meeting_id}` - Get meeting participants with engagement data

#### Task Management
- `GET /get-tasks` - List all tasks (supports filtering by assignee, status, priority)

#### Processing Endpoints
- `POST /process-transcript` - Process transcript text
- `POST /process-transcript-with-tools` - Process with AI tools integration
- `GET /available-tools` - List available processing tools

#### Analytics
- `GET /analytics/overview` - Dashboard analytics data

### Example API Calls

```bash
# Health check
curl http://localhost:3001/health

# Get all meetings
curl http://localhost:3001/get-meetings

# Get meetings with filters
curl "http://localhost:3001/get-meetings?status=completed&limit=5"

# Get meeting summary
curl http://localhost:3001/get-summary/meeting_001

# Get tasks for specific assignee
curl "http://localhost:3001/get-tasks?assignee=John%20Smith&status=pending"

# Process transcript with tools
curl -X POST http://localhost:3001/process-transcript-with-tools \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Meeting transcript text",
    "meeting_id": "meeting_123",
    "participants": [{"id": "p1", "name": "John", "status": "active"}],
    "participant_count": 1
  }'
```

### Frontend Dashboard Integration

Update your frontend dashboard environment to use the mock server:

```bash
# .env.local or environment configuration
NEXT_PUBLIC_API_URL=http://localhost:3001
```

### Configuration Options

```bash
./start-server.sh [OPTIONS]

Options:
  --host HOST        Server host (default: 0.0.0.0)
  --port PORT        Server port (default: 3001)
  --debug           Enable debug mode
  --setup-only      Only setup environment
  --no-venv         Don't use virtual environment
  --help            Show help message
```

### Testing

```bash
# Run comprehensive API tests
python test-server.py

# Test with custom server
python test-server.py --server http://localhost:8080 --verbose
```

## 📋 Mock Data Structure

The mock data in `shared/mock-meetings-data.json` provides comprehensive, realistic data that matches the enhanced audio integration contracts:

### Data Entities

1. **Meetings**: Complete meeting metadata with participant information
2. **Transcripts**: Timestamped transcription segments with speaker attribution
3. **Speakers**: Enhanced speaker identification with participant mapping
4. **Summaries**: AI-generated meeting summaries with decisions and next steps
5. **Tasks**: Action items extracted from meetings with assignments

### Enhanced Features

- **Participant Data Integration**: Full participant information with roles and engagement metrics
- **Speaker-Participant Mapping**: Accurate attribution using participant context
- **Confidence Scores**: Realistic confidence levels based on identification method
- **Rich Analytics**: Participation levels, speaking time, engagement scores
- **Relationship Integrity**: Consistent cross-references between all entities

### Sample Data Structure

```json
{
  "meetings": [
    {
      "id": "meeting_001",
      "title": "Sprint Planning - Q1 2025",
      "platform": "google-meet",
      "participants": [
        {
          "id": "participant_1",
          "name": "John Smith",
          "is_host": true,
          "join_time": "2025-01-08T09:58:30Z"
        }
      ],
      "participant_count": 3
    }
  ],
  "speakers": {
    "meeting_001": {
      "speakers": [...],
      "identification_method": "explicit_labels",
      "confidence": 0.92
    }
  },
  "summaries": {
    "meeting_001": {
      "executive_summary": {...},
      "key_decisions": {...},
      "next_steps": {...}
    }
  }
}
```

## 🧪 Testing

### Automated Test Suites

Both servers include comprehensive test suites that verify:

- **Connection handling** and protocol compliance
- **Message processing** with various formats
- **Error handling** and edge cases
- **Performance** and response times
- **Data integrity** and format validation

### Running Tests

```bash
# Test both servers (requires both to be running)
cd chrome-extension/
python test-server.py --server ws://localhost:8000/ws/audio

cd ../frontend-dashboard/
python test-server.py --server http://localhost:3001
```

### Test Coverage

#### Chrome Extension WebSocket Server Tests
- ✅ Connection establishment and welcome messages
- ✅ Basic audio chunk processing (legacy format)
- ✅ Enhanced audio chunk processing with participants
- ✅ Meeting event handling
- ✅ Session information requests
- ✅ Multiple chunk handling (stress testing)
- ✅ Invalid message handling and error responses

#### Frontend Dashboard REST API Tests
- ✅ Health check endpoint
- ✅ Meeting listing with filtering
- ✅ Summary retrieval and processing status
- ✅ Transcript pagination
- ✅ Task management with filters
- ✅ Participant data with engagement metrics
- ✅ Processing endpoints with tools
- ✅ Analytics data
- ✅ CORS headers and error handling

## 🔧 Configuration

### Environment Variables

```bash
# Chrome Extension WebSocket Server
CHROME_EXTENSION_HOST=localhost
CHROME_EXTENSION_PORT=8000
WEBSOCKET_DEBUG=false

# Frontend Dashboard REST API Server  
FRONTEND_DASHBOARD_HOST=0.0.0.0
FRONTEND_DASHBOARD_PORT=3001
REST_API_DEBUG=false

# Shared Configuration
MOCK_DATA_PATH=./shared/mock-meetings-data.json
```

### Custom Mock Data

You can modify `shared/mock-meetings-data.json` to add your own test scenarios:

1. **Add new meetings** with different platforms and participant configurations
2. **Create custom transcripts** for specific testing scenarios
3. **Design speaker scenarios** to test identification accuracy
4. **Build complex summaries** for analytics testing
5. **Generate task variations** for task management testing

## 🔄 Integration Workflow

### Development Workflow

1. **Start Mock Servers**
   ```bash
   ./start-all-servers.sh --debug
   ```

2. **Configure Chrome Extension**
   - Update WebSocket URL to `ws://localhost:8000/ws/audio`
   - Test enhanced audio chunk sending

3. **Configure Frontend Dashboard**
   - Update API base URL to `http://localhost:3001`
   - Test all dashboard features

4. **Run Integration Tests**
   - Use both test suites to verify functionality
   - Test end-to-end scenarios

### Production Deployment

While these are mock servers for development, the architecture can be adapted for production:

1. **WebSocket Server**: Replace with actual AI processing pipeline
2. **REST API Server**: Replace with actual database-backed API
3. **Data Format**: The enhanced formats are production-ready
4. **Error Handling**: Use the same patterns for production error handling

## 📈 Performance

### Response Times (Typical)

| Operation | Chrome Extension WS | Frontend Dashboard API |
|-----------|--------------------|-----------------------|
| Connection Setup | ~100ms | ~50ms |
| Audio Chunk Processing | 0.5-1.5s | N/A |
| Meeting Data Retrieval | N/A | ~200ms |
| Summary Generation | N/A | ~300ms |
| Task Listing | N/A | ~150ms |

### Concurrency Support

- **WebSocket Server**: Handles multiple simultaneous connections
- **REST API Server**: Thread-safe Flask implementation with CORS
- **Resource Usage**: Minimal memory footprint with efficient JSON handling

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :3001
   
   # Use different ports
   ./start-server.sh --chrome-port 8080 --frontend-port 3002
   ```

2. **Connection Refused**
   - Ensure servers are running: `./start-all-servers.sh`
   - Check firewall settings
   - Verify host/port configuration

3. **WebSocket Connection Issues**
   - Verify WebSocket URL format: `ws://host:port/ws/audio`
   - Check browser developer console for errors
   - Test with WebSocket client tools

4. **CORS Issues**
   - Frontend dashboard mock server includes CORS headers
   - For custom origins, modify the Flask-CORS configuration

5. **Mock Data Not Found**
   ```bash
   # Verify mock data file exists
   ls -la shared/mock-meetings-data.json
   
   # Check file permissions
   chmod 644 shared/mock-meetings-data.json
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
./start-all-servers.sh --debug
```

This provides:
- Detailed request/response logging
- WebSocket message tracing
- Performance timing information
- Error stack traces

### Logs Location

Logs are output to console by default. For persistent logging:

```bash
# Chrome Extension Server
./start-server.sh --debug 2>&1 | tee chrome-extension.log

# Frontend Dashboard Server  
./start-server.sh --debug 2>&1 | tee frontend-dashboard.log
```

## 🎯 Next Steps

### Immediate Development
1. **Test Chrome Extension Integration** - Connect your extension to the WebSocket mock server
2. **Test Frontend Dashboard** - Update API URLs and verify all features work
3. **Run Comprehensive Tests** - Use the provided test suites to validate functionality

### Advanced Usage
1. **Custom Mock Scenarios** - Modify mock data for specific testing scenarios
2. **Load Testing** - Use the test scripts to simulate high-load scenarios
3. **Integration Testing** - Test complete workflows from audio capture to task creation

### Production Readiness
1. **Contract Validation** - Ensure all formats match production expectations
2. **Error Handling** - Verify error scenarios work as expected
3. **Performance Benchmarking** - Establish baseline performance metrics

---

## 📞 Support

For questions or issues with the mock servers:

1. **Check this documentation** first for common solutions
2. **Run the test suites** to identify specific problems
3. **Enable debug mode** for detailed error information
4. **Review the mock data structure** to understand available test scenarios

The mock servers are designed to be comprehensive and realistic, providing an excellent development and testing environment for the complete ScrumBot system with enhanced audio chunk integration and participant data support.