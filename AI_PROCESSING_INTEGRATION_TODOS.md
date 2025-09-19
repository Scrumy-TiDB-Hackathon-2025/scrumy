# AI Processing Integration - TODO List

## Overview
This document tracks all TODO items for the AI processing integration system, including current limitations and future enhancements.

## 🚨 Critical TODOs - Database Schema Updates

### 1. Add `meeting_id` Support
**Priority**: High  
**Status**: Blocked by database schema  
**Impact**: Task tracking and meeting context

**Current State**:
- AI processing generates meeting IDs
- Integration system code supports meeting_id
- Database schema does NOT support meeting_id column

**Required Changes**:
```sql
-- Add to tasks table
ALTER TABLE tasks ADD COLUMN meeting_id VARCHAR(255);
```

**Code Updates Needed**:
```python
# File: ai_processing/app/integration_bridge.py
# Line: ~95 (in _transform_ai_task_to_integration_format)

# TODO: Uncomment when database supports meeting_id
meeting_id = ai_task.get("meeting_id")
if meeting_id:
    integration_task["meeting_id"] = meeting_id
```

```python
# File: ai_processing/app/integration_bridge.py  
# Line: ~165 (in create_tasks_from_ai_results)

# TODO: Add when supported:
result = await self.tools_registry.create_task_everywhere(
    title=integration_task["title"],
    description=integration_task["description"],
    assignee=integration_task["assignee"],
    priority=integration_task["priority"],
    meeting_id=integration_task.get("meeting_id")  # Add this line
)
```

### 2. Add `due_date` Support
**Priority**: High  
**Status**: Blocked by database schema  
**Impact**: Task scheduling and deadline management

**Current State**:
- AI processing can extract due dates from meeting content
- Integration system code supports due_date formatting
- Database schema does NOT support due_date column

**Required Changes**:
```sql
-- Add to tasks table
ALTER TABLE tasks ADD COLUMN due_date DATE;
```

**Code Updates Needed**:
```python
# File: ai_processing/app/integration_bridge.py
# Line: ~100 (in _transform_ai_task_to_integration_format)

# TODO: Uncomment when database supports due_date
due_date = ai_task.get("due_date")  
if due_date:
    integration_task["due_date"] = due_date
```

```python
# File: ai_processing/app/integration_bridge.py
# Line: ~165 (in create_tasks_from_ai_results)

# TODO: Add when supported:
result = await self.tools_registry.create_task_everywhere(
    title=integration_task["title"],
    description=integration_task["description"],
    assignee=integration_task["assignee"],
    priority=integration_task["priority"],
    due_date=integration_task.get("due_date")  # Add this line
)
```

## 🔧 Enhancement TODOs

### 3. Implement Meeting Summary Notifications
**Priority**: Medium  
**Status**: Placeholder implementation  
**Impact**: Team communication and meeting follow-up

**Current State**:
- Method exists but only logs summary
- Slack integration available but not connected

**Required Implementation**:
```python
# File: ai_processing/app/integration_bridge.py
# Method: send_meeting_summary_notification

# TODO: Implement actual Slack notification
# Replace current logging with:
from app.slack_tools import send_meeting_summary

result = await send_meeting_summary(
    meeting_id=meeting_context.get("meeting_id", "unknown"),
    summary=meeting_summary,
    tasks_created=tasks_created
)
```

### 4. Add Configuration Management
**Priority**: Medium  
**Status**: Basic config exists  
**Impact**: Deployment flexibility and environment management

**Current State**:
- Hard-coded configuration in DEFAULT_INTEGRATION_CONFIG
- No environment variable support

**Required Implementation**:
```python
# File: ai_processing/app/integration_bridge.py
# Add environment variable support

import os
from dotenv import load_dotenv

def load_integration_config():
    """Load integration config from environment variables"""
    load_dotenv()
    
    return {
        "enabled": os.getenv("INTEGRATION_ENABLED", "true").lower() == "true",
        "platforms": os.getenv("INTEGRATION_PLATFORMS", "notion,slack,clickup").split(","),
        "mock_mode": os.getenv("INTEGRATION_MOCK_MODE", "false").lower() == "true",
        "timeout_seconds": int(os.getenv("INTEGRATION_TIMEOUT", "30"))
    }
```

### 5. Add Retry Logic for Failed Integrations
**Priority**: Medium  
**Status**: Not implemented  
**Impact**: Reliability and error recovery

**Required Implementation**:
```python
# File: ai_processing/app/integration_bridge.py
# Add retry decorator or logic

import asyncio
from functools import wraps

def retry_on_failure(max_retries=3, delay=1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator
```

### 6. Add Integration Health Monitoring
**Priority**: Low  
**Status**: Not implemented  
**Impact**: Observability and debugging

**Required Implementation**:
```python
# File: ai_processing/app/integration_bridge.py
# Add health check method

async def check_integration_health(self) -> Dict:
    """Check health of all integration platforms"""
    health_status = {
        "overall_healthy": True,
        "platforms": {},
        "last_check": datetime.now().isoformat()
    }
    
    # Check each platform availability
    for platform in self.config.get("platforms", []):
        try:
            # Platform-specific health check
            health_status["platforms"][platform] = {
                "healthy": True,
                "response_time_ms": 0  # Measure actual response time
            }
        except Exception as e:
            health_status["platforms"][platform] = {
                "healthy": False,
                "error": str(e)
            }
            health_status["overall_healthy"] = False
    
    return health_status
```

## 🧪 Testing TODOs

### 7. Add End-to-End Integration Tests
**Priority**: High  
**Status**: Basic tests exist  
**Impact**: Quality assurance and regression prevention

**Required Tests**:
- Full AI processing → task creation flow
- Error handling scenarios
- Integration failure recovery
- Performance testing with large transcripts

### 8. Add Mock Integration Testing
**Priority**: Medium  
**Status**: Partially implemented  
**Impact**: Development and CI/CD pipeline

**Required Implementation**:
- Mock all external API calls
- Simulate various failure scenarios
- Test data transformation edge cases

## 📚 Documentation TODOs

### 9. Add API Documentation
**Priority**: Medium  
**Status**: Basic docstrings exist  
**Impact**: Developer experience and maintenance

**Required Documentation**:
- OpenAPI/Swagger specs for integration endpoints
- Integration bridge usage examples
- Configuration reference guide

### 10. Add Deployment Guide
**Priority**: Medium  
**Status**: Not implemented  
**Impact**: Production deployment and operations

**Required Documentation**:
- Environment setup instructions
- Configuration management guide
- Monitoring and alerting setup
- Troubleshooting guide

## 🔍 Search Tags for Future Updates

When implementing these TODOs, search for these tags in the codebase:

- `TODO: Add when database supports` - Database schema related updates
- `TODO: Implement` - Feature implementation needed
- `TODO: Uncomment when` - Code that needs to be enabled
- `FIXME:` - Code that needs fixing
- `HACK:` - Temporary solutions that need proper implementation

## 📋 Implementation Priority Order

1. **Database Schema Updates** (meeting_id, due_date) - Enables full functionality
2. **End-to-End Testing** - Ensures reliability
3. **Meeting Summary Notifications** - Completes core workflow
4. **Configuration Management** - Enables production deployment
5. **Retry Logic** - Improves reliability
6. **Health Monitoring** - Enables observability
7. **Documentation** - Improves maintainability

## 🎯 Success Criteria

The AI processing integration will be considered complete when:

- ✅ Tasks are created automatically from AI-extracted meeting content
- ✅ All database fields are supported (meeting_id, due_date)
- ✅ Meeting summaries are sent to team channels
- ✅ Integration failures don't break AI processing
- ✅ Configuration is environment-based
- ✅ Comprehensive test coverage exists
- ✅ Production deployment guide is available

## 📝 Notes

- Keep `DATABASE_LIMITATIONS.md` updated as schema changes are made
- Update this TODO list as items are completed
- Add new TODOs as they are discovered during development
- Link to specific GitHub issues when available