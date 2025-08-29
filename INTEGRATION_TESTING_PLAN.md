# 🧪 Integration Testing Plan - ClickUp & Notion

## Overview
This document outlines the plan for testing the integration system with real API keys before implementing OAuth authentication.

## 🎯 Testing Strategy

### Phase 1: Static Key Configuration
- Set up environment variables for real API tokens
- Create test databases/workspaces in ClickUp and Notion
- Implement basic connectivity tests

### Phase 2: Integration Testing
- Test individual integration classes (NotionIntegration, ClickUpIntegration)
- Test task creation with various data scenarios
- Test error handling and validation

### Phase 3: Integration Utility Testing
- Test the callable utility interface
- Test smart routing logic
- Test pending task functionality

## 🔧 Environment Setup

### Required Environment Variables
```bash
# Notion Integration
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# ClickUp Integration  
CLICKUP_TOKEN=pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLICKUP_LIST_ID=xxxxxxxxx
CLICKUP_TEAM_ID=xxxxxxxxx

# Database (for testing)
DATABASE_URL=sqlite:///./test_integration.db
```

### Notion Setup Requirements
1. Create a Notion integration at https://www.notion.so/my-integrations
2. Create a test database with these properties:
   - **Title** (Title)
   - **Description** (Text)
   - **Priority** (Select: Low, Medium, High, Urgent)
   - **Status** (Select: Not Started, In Progress, Completed)
   - **Due Date** (Date)
   - **Assignee** (Person)
   - **Meeting** (Text)
3. Share the database with your integration
4. Copy the database ID from the URL

### ClickUp Setup Requirements
1. Get API token from ClickUp settings
2. Create a test workspace and list
3. Get Team ID and List ID from API or URL
4. Note: User assignment requires actual ClickUp user IDs

## 📋 Test Cases

### 1. Basic Connectivity Tests
```python
# Test 1.1: Notion API Connection
async def test_notion_connection():
    notion = NotionIntegration()
    # Should not be in mock mode with real token
    assert not notion.is_mock
    # Test basic API access
    
# Test 1.2: ClickUp API Connection  
async def test_clickup_connection():
    clickup = ClickUpIntegration()
    assert not clickup.is_mock
    # Test team member access
```

### 2. Task Creation Tests
```python
# Test 2.1: Basic Task Creation - Notion
async def test_notion_basic_task():
    task_data = {
        "title": "Test Task from ScrumBot",
        "description": "This is a test task created during integration testing",
        "priority": "medium"
    }
    result = await notion.create_task(task_data)
    assert result["success"] == True
    assert "task_url" in result

# Test 2.2: Basic Task Creation - ClickUp
async def test_clickup_basic_task():
    task_data = {
        "title": "Test ClickUp Task",
        "description": "Integration test task",
        "priority": "high"
    }
    result = await clickup.create_task(task_data)
    assert result["success"] == True
    assert "task_id" in result
```

### 3. Data Validation Tests
```python
# Test 3.1: Invalid Data Handling
async def test_invalid_task_data():
    # Missing title
    invalid_task = {"description": "No title"}
    result = await notion.create_task(invalid_task)
    assert result["success"] == False
    assert "title is required" in result["error"].lower()

# Test 3.2: Long Content Handling
async def test_long_content():
    long_task = {
        "title": "x" * 3000,  # Exceeds limits
        "description": "y" * 10000
    }
    # Should handle gracefully with truncation
```

### 4. Integration Utility Tests
```python
# Test 4.1: Single Provider Routing
async def test_single_provider_routing():
    # Mock auth status with only ClickUp
    auth_status = {"clickup": True, "notion": False}
    provider = await util._determine_provider("user_123", task_data, auth_status, "smart")
    assert provider == "clickup"

# Test 4.2: Smart Routing Logic
async def test_smart_routing():
    # Both providers available
    auth_status = {"clickup": True, "notion": True}
    
    # Urgent task should go to ClickUp
    urgent_task = {"title": "Urgent Fix", "priority": "urgent"}
    provider = await util._determine_provider("user_123", urgent_task, auth_status, "smart")
    assert provider == "clickup"
    
    # Long description should go to Notion
    detailed_task = {"title": "Planning", "description": "x" * 600}
    provider = await util._determine_provider("user_123", detailed_task, auth_status, "smart")
    assert provider == "notion"
```

## 🧪 Test Implementation

### Test File Structure
```
integration/tests/
├── __init__.py
├── conftest.py              # Test configuration
├── test_notion_integration.py
├── test_clickup_integration.py
├── test_integration_utility.py
├── test_error_handling.py
└── integration_test_data.py # Test data samples
```

### Sample Test Data
```python
# integration_test_data.py
SAMPLE_MEETING_DATA = {
    "meeting_id": "test_meeting_001",
    "meeting_title": "Sprint Planning - Integration Test",
    "participants": [
        {"name": "Test User 1", "email": "test1@example.com"},
        {"name": "Test User 2", "email": "test2@example.com"}
    ],
    "tasks": [
        {
            "title": "Review API documentation",
            "description": "Go through the new API endpoints and update integration tests",
            "priority": "high",
            "assignee": "Test User 1",
            "due_date": "2025-01-15"
        },
        {
            "title": "Update UI components",  
            "description": "Modify the dashboard to show integration status",
            "priority": "medium",
            "assignee": "Test User 2",
            "due_date": "2025-01-17"
        },
        {
            "title": "Database optimization research",
            "description": "Research and document potential optimizations for our database queries. This includes analyzing slow queries, index usage, and potential schema improvements that could boost performance.",
            "priority": "low",
            "assignee": "Test User 1",
            "due_date": "2025-01-20"
        }
    ]
}

ERROR_TEST_CASES = [
    {"title": "", "description": "Empty title test"},
    {"title": "x" * 3000, "description": "Title too long"},
    {"title": "Valid title", "priority": "invalid_priority"},
    {"title": "Valid title", "due_date": "invalid-date-format"},
    {"title": "Valid title", "assignee": "nonexistent_user@test.com"}
]
```

## 🔄 Test Execution Plan

### Step 1: Environment Setup
```bash
# Create test environment file
cp .env.example .env.test

# Add real API credentials to .env.test
# NEVER commit real credentials!

# Install test dependencies
pip install pytest pytest-asyncio python-dotenv
```

### Step 2: Run Basic Connectivity Tests
```bash
# Test individual integrations
python -m pytest integration/tests/test_notion_integration.py::test_connection -v
python -m pytest integration/tests/test_clickup_integration.py::test_connection -v
```

### Step 3: Run Task Creation Tests
```bash
# Test basic task creation
python -m pytest integration/tests/test_notion_integration.py::test_create_basic_task -v
python -m pytest integration/tests/test_clickup_integration.py::test_create_basic_task -v
```

### Step 4: Run Comprehensive Test Suite
```bash
# Run all integration tests
python -m pytest integration/tests/ -v --tb=short
```

### Step 5: Manual Verification
1. Check created tasks in Notion database
2. Check created tasks in ClickUp list
3. Verify task details match input data
4. Test error scenarios manually

## 🚨 Common Issues & Solutions

### Notion Issues
- **401 Unauthorized**: Check integration token
- **403 Forbidden**: Database not shared with integration
- **400 Bad Request**: Property schema mismatch
- **404 Not Found**: Invalid database ID

### ClickUp Issues
- **401 Unauthorized**: Invalid API token
- **403 Forbidden**: Missing permissions for list/team
- **404 Not Found**: Invalid list ID or team ID
- **400 Bad Request**: Usually assignee-related (user ID issues)

### General Issues
- **Network timeouts**: Increase timeout values
- **Rate limiting**: Implement retry logic
- **Data validation**: Check input data format

## 📊 Success Criteria

### Phase 1 Success
- [ ] Both integrations connect successfully with real tokens
- [ ] Basic task creation works in both platforms
- [ ] Created tasks visible in respective platforms

### Phase 2 Success  
- [ ] All validation tests pass
- [ ] Error handling works correctly
- [ ] Edge cases handled gracefully

### Phase 3 Success
- [ ] Integration utility routes tasks correctly
- [ ] Smart routing logic works as expected
- [ ] Pending task functionality implemented

### Ready for OAuth Implementation
- [ ] All integration tests pass with real APIs
- [ ] Error handling comprehensive and tested
- [ ] Integration utility interface stable
- [ ] Mock authentication layer ready

## 🔄 Next Steps After Testing

1. **Fix Issues**: Address any bugs found during testing
2. **Mock OAuth Layer**: Create mock OAuth for testing without real user auth
3. **Database Schema**: Implement user-scoped token storage
4. **OAuth Endpoints**: Implement ClickUp and Notion OAuth flows
5. **Frontend Integration**: Connect OAuth to frontend dashboard

This testing phase ensures the core integration functionality is solid before adding the complexity of OAuth authentication.