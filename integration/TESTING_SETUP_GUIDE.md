# 🧪 Integration Testing Setup Guide

## Overview
This guide walks you through setting up and running integration tests for ScrumBot's ClickUp and Notion integrations with real API credentials.

## 🎯 What We're Testing
- **Notion Integration**: Task creation, validation, error handling
- **ClickUp Integration**: Task creation, user resolution, priority mapping
- **Integration Utility**: Smart routing, pending task management
- **Error Handling**: API failures, network issues, data validation

## 🚀 Quick Start

### Step 1: Environment Setup
```bash
# 1. Copy the template
cp .env.integration.template .env.integration

# 2. Edit the file with real credentials
# (Never commit this file to git!)
```

### Step 2: Get API Credentials

#### Notion Setup (5 minutes)
1. Go to https://www.notion.so/my-integrations
2. Click "New integration"
3. Name it "ScrumBot Test Integration"
4. Copy the "Internal Integration Token" 
5. Create a test database with these properties:
   - **Title** (Title)
   - **Description** (Text) 
   - **Priority** (Select: Low, Medium, High, Urgent)
   - **Status** (Select: Not Started, In Progress, Completed)
   - **Due Date** (Date)
   - **Assignee** (Person)
   - **Meeting** (Text)
6. Share the database with your integration
7. Copy the database ID from the URL

#### ClickUp Setup (5 minutes)
1. Go to ClickUp Settings > Apps
2. Click "Generate" next to API
3. Copy the API token
4. Create a test workspace, space, and list
5. Get the IDs from URLs:
   - Team ID: from workspace URL
   - List ID: from list URL
6. Note: User assignment requires actual ClickUp workspace members

### Step 3: Run Tests
```bash
# Install dependencies and run tests
python integration/run_integration_tests.py --install-deps

# Run all tests
python integration/run_integration_tests.py --verbose

# Run only Notion tests
python integration/run_integration_tests.py --notion-only -v

# Run only ClickUp tests  
python integration/run_integration_tests.py --clickup-only -v
```

## 📝 Environment Configuration

### Required Variables
```bash
# Notion (if testing Notion)
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# ClickUp (if testing ClickUp)
CLICKUP_TOKEN=pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLICKUP_LIST_ID=xxxxxxxxx
CLICKUP_TEAM_ID=xxxxxxxxx

# Testing mode
USE_MOCK_INTEGRATIONS=false  # Set to true for mock testing
TEST_TASK_PREFIX=[ScrumBot Test]  # Prefix for test tasks
TEST_CLEANUP_ENABLED=true  # Enable cleanup tracking
```

### Optional Variables
```bash
# API Configuration
API_TIMEOUT=30
MAX_RETRIES=3

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=integration_tests.log

# ClickUp Optional
CLICKUP_SPACE_ID=xxxxxxxxx
CLICKUP_DEFAULT_USER_ID=xxxxxxxxx
```

## 🧪 Test Categories

### Basic Connectivity Tests
```bash
# Test API connections
python integration/run_integration_tests.py --test-function test_notion_connection
python integration/run_integration_tests.py --test-function test_clickup_connection
```

### Task Creation Tests
```bash
# Basic task creation
python integration/run_integration_tests.py --test-function test_notion_create_basic_task
python integration/run_integration_tests.py --test-function test_clickup_create_basic_task

# Comprehensive task creation (all fields)
python integration/run_integration_tests.py --test-function test_notion_create_task_with_all_fields
python integration/run_integration_tests.py --test-function test_clickup_create_task_with_all_fields
```

### Validation Tests
```bash
# Data validation
python integration/run_integration_tests.py --test-function test_notion_task_validation
python integration/run_integration_tests.py --test-function test_clickup_task_validation

# Edge cases
python integration/run_integration_tests.py --test-function test_notion_long_content_handling
python integration/run_integration_tests.py --test-function test_clickup_special_characters
```

### Error Handling Tests
```bash
# API error handling
python integration/run_integration_tests.py --test-function test_notion_error_handling
python integration/run_integration_tests.py --test-function test_clickup_error_handling
```

### Performance Tests
```bash
# Batch operations (marked as slow)
python integration/run_integration_tests.py --include-slow --test-function test_notion_batch_task_creation
python integration/run_integration_tests.py --include-slow --test-function test_clickup_batch_task_creation
```

## 🔧 Test Runner Options

### Test Selection
```bash
# Platform-specific tests
--notion-only           # Run only Notion tests
--clickup-only          # Run only ClickUp tests  
--integration-only      # Run only integration tests

# Specific tests
--test-file test_notion_integration.py    # Run specific file
--test-function test_create_basic_task    # Run specific function
--include-slow                            # Include slow tests
```

### Output Control
```bash
-v, --verbose           # Verbose output
-vv, --very-verbose     # Very verbose output
--capture no            # Don't capture print statements
--tb-style short        # Traceback style (short/long/no)
```

### Execution Control
```bash
-x, --stop-on-failure   # Stop on first failure
--coverage             # Run with coverage report
```

### Environment Control
```bash
--mock                 # Force mock mode
--install-deps         # Install dependencies first
--check-env           # Only check environment setup
```

## 🚨 Common Issues & Solutions

### "No module named 'app'" Error
```bash
# Make sure you're in the right directory
cd scrumy
python integration/run_integration_tests.py
```

### "NOTION_TOKEN not provided" Error
```bash
# Check environment file exists and has correct values
ls -la .env.integration
cat .env.integration | grep NOTION_TOKEN
```

### Notion "Database not found" Error
1. Verify database ID is correct (from URL)
2. Ensure database is shared with your integration
3. Check integration has proper permissions

### ClickUp "Forbidden" Error
1. Verify API token is correct
2. Check token has permissions for the workspace
3. Verify Team ID and List ID are correct

### Rate Limiting Issues
```bash
# Reduce concurrent tests or add delays
python integration/run_integration_tests.py --stop-on-failure
```

## 📊 Test Results

### Success Criteria
- ✅ **Basic Connectivity**: APIs respond to authentication
- ✅ **Task Creation**: Tasks created successfully in both platforms  
- ✅ **Data Validation**: Invalid data handled gracefully
- ✅ **Error Handling**: API errors return meaningful messages
- ✅ **Special Characters**: Unicode and emojis handled correctly

### Expected Outputs
```
🧪 Starting integration tests...
📝 Mock mode: disabled
🔗 Testing platforms: Notion, ClickUp

test_notion_connection PASSED                           [16%]
test_notion_create_basic_task PASSED                    [33%]
test_clickup_connection PASSED                          [50%]
test_clickup_create_basic_task PASSED                   [66%]
...

📋 Created 8 test tasks:
  - notion: f7d4c2a8-1234-5678-9abc-def012345678
  - clickup: 12345678
🧹 Please manually clean up test tasks if needed

🎉 All tests passed!
```

## 🧹 Cleanup

### Manual Cleanup
After testing, you may want to clean up test tasks:

1. **Notion**: Go to your test database and delete tasks with `[ScrumBot Test]` prefix
2. **ClickUp**: Go to your test list and delete test tasks
3. **Logs**: Check `integration_tests.log` for detailed execution logs

### Automated Cleanup (Future)
```bash
# Future enhancement - automated cleanup
python integration/cleanup_test_data.py --notion --clickup
```

## 🎯 Next Steps

Once integration tests pass:

1. **Fix Issues**: Address any bugs found during testing
2. **Mock OAuth**: Implement mock OAuth layer for development
3. **Database Schema**: Add user-scoped token storage
4. **OAuth Endpoints**: Implement real OAuth flows
5. **Frontend Integration**: Connect OAuth to dashboard

## 📋 Test Checklist

Before proceeding to OAuth implementation:

- [ ] Notion API connection works
- [ ] ClickUp API connection works  
- [ ] Basic task creation succeeds in both platforms
- [ ] Data validation catches invalid inputs
- [ ] Error handling provides meaningful messages
- [ ] Special characters are handled correctly
- [ ] Created tasks are visible in respective platforms
- [ ] Test cleanup completed

## 🔒 Security Notes

- **Never commit `.env.integration`** - it contains real API keys
- **Rotate tokens** after testing if needed
- **Use test workspaces** - don't test in production environments
- **Limit token permissions** - use minimal required scopes
- **Clean up test data** - don't leave test tasks in production systems

This testing phase ensures the integration foundation is solid before adding OAuth complexity!