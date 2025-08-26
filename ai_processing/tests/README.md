# AI Processing Tests

This directory contains comprehensive tests for the ScrumBot AI Processing backend, ensuring reliability and correctness of all AI processing components.

## 📁 Directory Structure

```
tests/
├── README.md              # This file
├── conftest.py           # Pytest configuration and fixtures
├── test_endpoints.py     # API endpoint tests
├── test_results.json     # Latest test execution results
├── data/                 # Test data and fixtures
│   ├── sample_audio.wav  # Sample audio files for testing
│   ├── mock_transcripts/ # Mock transcript data
│   └── test_configs/     # Test configuration files
└── __pycache__/          # Python bytecode cache
```

## 🧪 Test Categories

### 1. API Endpoint Tests
**`test_endpoints.py`** - Comprehensive API testing
- Health check endpoints
- Transcription API endpoints
- WebSocket connection tests
- Meeting processing endpoints
- Database interaction tests
- Error handling validation

### 2. Integration Tests
**`../test_integration.py`** - End-to-end integration testing
- Full processing pipeline tests
- Database connectivity tests
- External service integration
- Real-time processing validation

### 3. Core Functionality Tests
**`../test_core_functionality_integration.py`** - Core feature validation
- AI processing accuracy tests
- Transcript processing quality
- Meeting summarization tests
- Speaker identification validation
- Task extraction accuracy

### 4. WebSocket Tests
**`../test_websocket_integration.py`** - Real-time communication testing
- WebSocket connection lifecycle
- Audio streaming tests
- Real-time transcription validation
- Chrome extension compatibility

### 5. Chrome Extension Compatibility
**`../test_chrome_extension_compatibility.py`** - Extension integration
- Message format validation
- API compatibility tests
- Real-time communication tests
- Error handling scenarios

## 🚀 Running Tests

### Quick Test Suite
```bash
# Run all tests in tests/ directory
pytest tests/ -v

# Run specific test file
pytest tests/test_endpoints.py -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

### Full Integration Tests
```bash
# Run comprehensive integration tests
python test_core_functionality_integration.py

# Test WebSocket functionality
python test_websocket_integration.py

# Test Chrome extension compatibility
python test_chrome_extension_compatibility.py
```

### Focused Unit Tests
```bash
# Run focused unit tests
python test_focused_unit_tests.py

# Run enhanced audio tests
python test_enhanced_audio.py
```

## 📋 Test Configuration

### Pytest Configuration
**`conftest.py`** contains:
- Common test fixtures
- Database setup/teardown
- Mock server configurations
- Shared test utilities
- Environment setup

### Test Data Setup
**`data/`** directory contains:
- Sample audio files for transcription testing
- Mock transcript data for processing tests
- Test configuration files
- Expected output samples

## 🔍 Test Results

### Latest Results
**`test_results.json`** contains:
- Test execution timestamps
- Pass/fail status for each test
- Performance metrics
- Error logs and stack traces
- Coverage reports

### Continuous Testing
```bash
# Watch for file changes and auto-run tests
pytest-watch tests/

# Run tests on file change
ptw -- tests/ -v
```

## 🛠️ Writing New Tests

### Test Structure
```python
import pytest
from app.main import app
from fastapi.testclient import TestClient

class TestNewFeature:
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_feature_functionality(self):
        """Test specific functionality"""
        response = self.client.post("/api/endpoint", json={})
        assert response.status_code == 200
        assert "expected_field" in response.json()
```

### Test Categories

#### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution
- High coverage

#### Integration Tests  
- Test component interactions
- Use real database connections
- Test external API calls
- Validate end-to-end workflows

#### Performance Tests
- Measure response times
- Test under load
- Memory usage validation
- Concurrent request handling

## 🔧 Test Environment Setup

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Set up test database
python populate_demo_data.py

# Start required services
python server.py &  # Start backend server
```

### Environment Variables
```bash
export TEST_MODE=true
export DATABASE_TYPE=sqlite
export DEBUG_MODE=true
export MOCK_WHISPER=true
```

## 📊 Test Metrics

### Coverage Targets
- **Unit Tests**: >90% code coverage
- **Integration Tests**: >80% feature coverage
- **API Tests**: 100% endpoint coverage

### Performance Benchmarks
- API response time: <200ms
- Transcription processing: <5s per minute of audio
- WebSocket latency: <100ms
- Database queries: <50ms

## 🚨 Common Test Issues

### Database Connection Errors
```bash
# Reset test database
rm -f test_meeting_minutes.db
python populate_demo_data.py
```

### Whisper Server Issues
```bash
# Start mock Whisper server
export MOCK_WHISPER=true
python server.py
```

### WebSocket Test Failures
```bash
# Check WebSocket server status
curl -v http://localhost:8000/health
```

### Audio Processing Errors
```bash
# Verify audio test files
ls -la tests/data/sample_audio.wav
```

## 🔄 Test Automation

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI/CD Integration
Tests are automatically run on:
- Pull request creation
- Merge to main branch
- Nightly builds
- Release preparation

## 📈 Test Reporting

### HTML Coverage Reports
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### JSON Test Results
```bash
pytest tests/ --json-report --json-report-file=test_results.json
```

### Performance Reports
```bash
pytest tests/ --benchmark-only --benchmark-json=performance.json
```

## 🔍 Debugging Tests

### Verbose Output
```bash
pytest tests/ -v -s  # Show print statements
```

### Debug Specific Test
```bash
pytest tests/test_endpoints.py::TestAPI::test_health_check -v -s
```

### Debug with PDB
```bash
pytest tests/ --pdb  # Drop to debugger on failure
```

## 📚 Related Documentation

- [Main AI Processing README](../README.md)
- [API Documentation](../API_DOCUMENTATION.md)
- [Integration Guide](../AI_INTEGRATION_GUIDE.md)
- [Troubleshooting Guide](../TRANSCRIPTION_TROUBLESHOOTING.md)

---

**Maintainer**: ScrumBot AI Team  
**Last Updated**: August 2025  
**Test Coverage**: 85%+  
**Status**: ✅ All tests passing