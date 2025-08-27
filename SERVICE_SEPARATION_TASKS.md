# 🔄 Service Separation Tasks: AI Processing & Integration Services

## Overview
This document outlines the comprehensive tasks required to separate the current monolithic architecture into two standalone containerized services:
- **AI Processing Service**: Handles transcription, speaker identification, summarization, and task extraction
- **Integration Service**: Manages external integrations with Notion, Slack, ClickUp, and database operations

## 📊 Current State Analysis

### AI Processing Service (`scrumy/ai_processing/`)
**Current Structure:**
```
ai_processing/
├── app/
│   ├── main.py                    # FastAPI server (comprehensive)
│   ├── integration_adapter.py     # 🚨 MOCK integration logic (REMOVE)
│   ├── integrated_processor.py    # Core AI processing
│   ├── mock_data/                 # 🚨 Mock data (CLEAN UP)
│   ├── ai_processor.py            # AI processing core
│   ├── speaker_identifier.py      # Speaker identification
│   ├── meeting_summarizer.py      # Meeting summarization
│   ├── task_extractor.py          # Task extraction
│   ├── database_*.py              # Database interfaces
│   └── websocket_server.py        # WebSocket handling
├── Dockerfile                     # ✅ Exists
└── requirements.txt               # ✅ Comprehensive
```

**Issues:**
- Contains mock integration logic that should be external
- Uses `AIProcessingIntegrationAdapter` with mock fallbacks
- Has dependencies on integration functionality

### Integration Service (`scrumy/integration/`)
**Current Structure:**
```
integration/
├── app/
│   ├── integrations.py            # ✅ Real integrations (Notion, Slack, ClickUp)
│   ├── ai_agent.py               # ✅ AI agent functionality
│   ├── tidb_manager.py           # ✅ Database management
│   ├── tools.py                  # ✅ Integration tools
│   └── __init__.py               # ✅ Package structure
├── docker/
│   └── docker-compose.yml        # 🚨 Monolithic setup
└── requirements.txt              # ✅ Exists
```

**Issues:**
- No FastAPI server (no main.py)
- No standalone Docker configuration
- Designed as library, not service
- No service interface layer

## 🎯 Task Breakdown

### Phase 1: Integration Service Foundation
**Priority: CRITICAL**

#### Task 1.1: Create FastAPI Server for Integration Service
- [ ] **File**: `integration/app/main.py`
```python
# Create FastAPI application
# Add health check endpoint
# Configure CORS and middleware
# Add error handling middleware
```

#### Task 1.2: Define API Endpoints
- [ ] **Endpoints to create**:
  - `POST /api/meetings/process` - Process complete meeting data
  - `POST /api/tasks/create` - Create tasks in external systems
  - `PUT /api/tasks/{task_id}/status` - Update task status
  - `GET /api/meetings/{meeting_id}/context` - Get meeting context
  - `GET /health` - Health check
  - `GET /api/integrations/status` - Check integration health

#### Task 1.3: Create Request/Response Models
- [ ] **File**: `integration/app/models.py`
```python
# Pydantic models for API requests/responses
# MeetingProcessRequest, TaskCreateRequest, etc.
# Error response models
# Status models
```

#### Task 1.4: Database Layer Setup
- [ ] **Files**: 
  - `integration/app/database/connection.py`
  - `integration/app/database/models.py`
  - `integration/app/database/repository.py`
```python
# TiDB connection management
# Database models (SQLAlchemy)
# Repository pattern for data access
```

#### Task 1.5: Integration Service Manager
- [ ] **File**: `integration/app/service_manager.py`
```python
# Orchestrate integrations
# Handle business logic
# Coordinate between database and external APIs
```

### Phase 2: AI Processing Service Cleanup
**Priority: CRITICAL**

#### Task 2.1: Remove Mock Integration Code
- [ ] **Delete/Modify**:
  - Remove `app/integration_adapter.py` (entire file)
  - Clean up `app/mock_data/` directory
  - Remove integration imports from `app/main.py`
  - Update `app/integrated_processor.py` to remove integration calls

#### Task 2.2: Create Integration HTTP Client
- [ ] **File**: `ai_processing/app/integration_client.py`
```python
class IntegrationServiceClient:
    def __init__(self, base_url: str, timeout: int = 30):
        # HTTP client setup
        # Retry configuration
        # Error handling
    
    async def process_meeting_complete(self, meeting_data: dict) -> dict:
        # POST to /api/meetings/process
        pass
    
    async def create_tasks(self, tasks_data: dict) -> dict:
        # POST to /api/tasks/create
        pass
    
    async def get_meeting_context(self, meeting_id: str) -> dict:
        # GET /api/meetings/{meeting_id}/context
        pass
```

#### Task 2.3: Update Main Processing Flow
- [ ] **Files to modify**:
  - `ai_processing/app/main.py` - Replace integration adapter calls
  - `ai_processing/app/integrated_processor.py` - Use HTTP client
  - `ai_processing/app/websocket_server.py` - Update integration calls

#### Task 2.4: Add Configuration Management
- [ ] **File**: `ai_processing/app/config.py`
```python
# Environment variable management
# Integration service URL configuration
# Timeout and retry settings
```

### Phase 3: Shared Components & Data Models
**Priority: HIGH**

#### Task 3.1: Create Shared Data Models
- [ ] **File**: `shared/models.py`
```python
# Shared Pydantic models
class ParticipantData(BaseModel):
    # Participant information
    pass

class MeetingData(BaseModel):
    # Meeting information
    pass

class TaskDefinition(BaseModel):
    # Task information
    pass

class ProcessingResult(BaseModel):
    # AI processing results
    pass
```

#### Task 3.2: Create Shared Constants
- [ ] **File**: `shared/constants.py`
```python
# API endpoints
# Status codes
# Error messages
# Configuration constants
```

#### Task 3.3: Shared Error Handling
- [ ] **File**: `shared/exceptions.py`
```python
class IntegrationServiceError(Exception):
    pass

class AIProcessingError(Exception):
    pass

class DatabaseError(Exception):
    pass
```

### Phase 4: Docker Configuration
**Priority: HIGH**

#### Task 4.1: Integration Service Docker Setup
- [ ] **File**: `integration/Dockerfile`
```dockerfile
FROM python:3.11-slim
# Setup for integration service
# Install dependencies
# Configure environment
EXPOSE 3003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3003"]
```

#### Task 4.2: Update AI Processing Dockerfile
- [ ] **Modify**: `ai_processing/Dockerfile`
```dockerfile
# Remove integration-related dependencies
# Add HTTP client dependencies
# Update environment variables
```

#### Task 4.3: Create Multi-Service Docker Compose
- [ ] **File**: `docker-compose.yml` (root level)
```yaml
version: '3.8'
services:
  ai-processing:
    build: ./ai_processing
    ports:
      - "5167:5167"
    environment:
      - INTEGRATION_SERVICE_URL=http://integration-service:3003
      - TIDB_CONNECTION_STRING=${TIDB_CONNECTION_STRING}
    depends_on:
      - integration-service
      - ollama

  integration-service:
    build: ./integration
    ports:
      - "3003:3003"
    environment:
      - TIDB_CONNECTION_STRING=${TIDB_CONNECTION_STRING}
      - NOTION_TOKEN=${NOTION_TOKEN}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
    depends_on:
      - tidb

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

#### Task 4.4: Create Development Docker Compose
- [ ] **File**: `docker-compose.dev.yml`
```yaml
# Development overrides
# Volume mounts for hot reload
# Debug configurations
# Local database setup
```

### Phase 5: Service Communication & Error Handling
**Priority: HIGH**

#### Task 5.1: Implement Retry Logic
- [ ] **File**: `ai_processing/app/retry_handler.py`
```python
# Exponential backoff retry
# Circuit breaker pattern
# Fallback mechanisms
```

#### Task 5.2: Add Health Checks
- [ ] **Both services**:
```python
# Health check endpoints
# Dependency health checks
# Service status monitoring
```

#### Task 5.3: Logging & Monitoring
- [ ] **Files**: `*/app/logging_config.py`
```python
# Structured logging
# Request/response logging
# Error tracking
# Performance metrics
```

#### Task 5.4: Service Discovery & Configuration
- [ ] **Environment Configuration**:
```bash
# AI Processing Service
INTEGRATION_SERVICE_URL=http://integration-service:3003
INTEGRATION_SERVICE_TIMEOUT=30
INTEGRATION_SERVICE_RETRIES=3

# Integration Service
TIDB_CONNECTION_STRING=mysql://...
NOTION_TOKEN=secret_...
SLACK_BOT_TOKEN=xoxb-...
CLICKUP_API_TOKEN=pk_...
```

### Phase 6: Testing Infrastructure
**Priority: MEDIUM**

#### Task 6.1: Integration Service Tests
- [ ] **Files**: `integration/tests/`
```python
# test_api_endpoints.py
# test_integrations.py
# test_database.py
# test_service_manager.py
```

#### Task 6.2: AI Processing Service Tests
- [ ] **Files**: `ai_processing/tests/`
```python
# test_integration_client.py
# test_main_endpoints.py
# test_processing_flow.py
```

#### Task 6.3: End-to-End Tests
- [ ] **File**: `tests/e2e/test_service_communication.py`
```python
# Test complete workflow
# Service-to-service communication
# Error handling scenarios
# Performance tests
```

#### Task 6.4: Mock Server for Development
- [ ] **File**: `tests/mocks/integration_mock_server.py`
```python
# Mock integration service for AI processing tests
# Simulate various response scenarios
# Error simulation
```

### Phase 7: Documentation & Deployment
**Priority: LOW**

#### Task 7.1: API Documentation
- [ ] **Files**:
  - `integration/API.md`
  - `ai_processing/API.md`
  - Update existing documentation

#### Task 7.2: Deployment Scripts
- [ ] **Files**:
  - `scripts/deploy-services.sh`
  - `scripts/health-check.sh`
  - `scripts/logs.sh`

#### Task 7.3: Environment Setup
- [ ] **Files**:
  - `.env.example`
  - `docker-compose.prod.yml`
  - `docker-compose.staging.yml`

## 📋 Implementation Checklist

### Week 1: Core Infrastructure
- [ ] ✅ Task 1.1-1.5: Integration Service Foundation
- [ ] ✅ Task 2.1-2.2: AI Processing Cleanup & Client
- [ ] ✅ Task 4.1-4.2: Basic Docker Setup

### Week 2: Service Communication
- [ ] ✅ Task 2.3-2.4: Update Processing Flow
- [ ] ✅ Task 3.1-3.3: Shared Components
- [ ] ✅ Task 5.1-5.4: Communication & Error Handling

### Week 3: Testing & Production Readiness
- [ ] ✅ Task 4.3-4.4: Complete Docker Setup
- [ ] ✅ Task 6.1-6.4: Testing Infrastructure
- [ ] ✅ Task 7.1-7.3: Documentation & Deployment

## 🔍 Validation Criteria

### Service Independence
- [ ] AI Processing service runs without integration code
- [ ] Integration service runs as standalone FastAPI app
- [ ] Services communicate only via HTTP APIs
- [ ] Each service has independent database connections

### Docker Containerization
- [ ] Each service builds independently
- [ ] Services start with docker-compose
- [ ] Environment variables properly configured
- [ ] Health checks working for all services

### Error Handling & Resilience
- [ ] Services handle communication failures gracefully
- [ ] Retry logic implemented and tested
- [ ] Proper error responses and logging
- [ ] Circuit breaker prevents cascade failures

### Testing Coverage
- [ ] Unit tests for both services
- [ ] Integration tests for API endpoints
- [ ] End-to-end workflow tests
- [ ] Mock services for development

## 📊 Risk Assessment

### High Risk
- **Database connection management**: Ensure both services can connect to TiDB
- **Service communication**: HTTP client reliability and error handling
- **Shared state**: Avoid service dependencies beyond API calls

### Medium Risk
- **Configuration management**: Environment variables and secrets
- **Testing complexity**: Mocking service interactions
- **Deployment coordination**: Starting services in correct order

### Low Risk
- **Code organization**: Moving files between services
- **Docker setup**: Standard containerization practices
- **Documentation**: Updating existing docs

## 🚀 Getting Started

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/service-separation
   ```

2. **Start with Integration Service**:
   ```bash
   # Focus on Task 1.1-1.5 first
   touch integration/app/main.py
   ```

3. **Test Incrementally**:
   ```bash
   # Test each service independently
   docker-compose up integration-service
   docker-compose up ai-processing
   ```

4. **Validate Communication**:
   ```bash
   # Test service-to-service calls
   curl http://localhost:5167/health
   curl http://localhost:3003/health
   ```

This task breakdown provides a comprehensive roadmap for separating the services while maintaining functionality and adding proper containerization support.