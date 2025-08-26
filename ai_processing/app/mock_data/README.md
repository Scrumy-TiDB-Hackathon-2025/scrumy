# Mock Data for AI Processing

This directory contains mock data generators and sample data used for testing and development of the ScrumBot AI Processing system.

## 📁 Directory Overview

```
mock_data/
├── README.md                    # This file
├── generate_mock_data.py        # Mock data generator script
├── sample_meetings/             # Sample meeting data
│   ├── standup_meeting.json     # Daily standup mock data
│   ├── planning_meeting.json    # Sprint planning mock data
│   └── retrospective.json       # Retrospective meeting data
├── sample_transcripts/          # Sample transcript data
│   ├── short_meeting.txt        # Brief meeting transcript
│   ├── long_discussion.txt      # Extended discussion transcript
│   └── multi_speaker.txt        # Multiple speakers transcript
├── sample_audio/                # Sample audio files
│   ├── meeting_sample.wav       # 5-minute meeting sample
│   ├── single_speaker.wav       # Single speaker audio
│   └── noisy_audio.wav          # Audio with background noise
└── expected_outputs/            # Expected processing results
    ├── summaries/               # Expected meeting summaries
    ├── tasks/                   # Expected extracted tasks
    └── speakers/                # Expected speaker identification
```

## 🎯 Purpose

The mock data system serves several critical purposes:

### Development & Testing
- **Unit Testing**: Consistent data for automated tests
- **Integration Testing**: End-to-end workflow validation
- **Performance Testing**: Load testing with known datasets
- **Regression Testing**: Ensuring changes don't break existing functionality

### Development Workflow
- **Offline Development**: Work without external AI services
- **Rapid Prototyping**: Quick iteration with known data
- **Demo Presentations**: Consistent results for demonstrations
- **Training**: Help new developers understand system behavior

## 🚀 Using Mock Data

### Generate Fresh Mock Data
```bash
# Generate all mock data types
python generate_mock_data.py --all

# Generate specific types
python generate_mock_data.py --meetings --transcripts

# Generate with custom parameters
python generate_mock_data.py --count 50 --type standup
```

### Enable Mock Mode
```bash
# Set environment variables
export MOCK_MODE=true
export USE_MOCK_DATA=true
export MOCK_WHISPER=true

# Start server in mock mode
python server.py --mock
```

### Use in Tests
```python
from app.mock_data.generate_mock_data import MockDataGenerator

# Initialize generator
mock_gen = MockDataGenerator()

# Generate mock meeting
mock_meeting = mock_gen.generate_meeting("standup")

# Generate mock transcript
mock_transcript = mock_gen.generate_transcript(duration_minutes=10)
```

## 📊 Mock Data Types

### 1. Meeting Data
**Sample meeting records with metadata:**
```json
{
  "meeting_id": "mock_meeting_001",
  "title": "Daily Standup",
  "date": "2025-08-27T09:00:00Z",
  "duration": 900,
  "participants": ["Alice", "Bob", "Charlie"],
  "meeting_type": "standup",
  "platform": "Google Meet"
}
```

### 2. Transcript Data
**Realistic conversation transcripts:**
```json
{
  "transcript_id": "mock_transcript_001",
  "segments": [
    {
      "speaker": "Alice",
      "text": "Good morning everyone, let's start our standup.",
      "start_time": 0.0,
      "end_time": 3.5
    }
  ],
  "language": "en",
  "confidence": 0.95
}
```

### 3. Audio Samples
**Various audio formats for testing:**
- **Short samples** (30 seconds - 2 minutes)
- **Medium samples** (5-15 minutes)
- **Long samples** (30+ minutes)
- **Multiple speakers** with distinct voices
- **Background noise** variations
- **Different audio qualities**

### 4. Expected Outputs
**Known correct results for validation:**
```json
{
  "summary": "The team discussed sprint progress...",
  "action_items": [
    {
      "task": "Fix login bug",
      "assignee": "Alice",
      "deadline": "2025-08-30"
    }
  ],
  "speakers": {
    "Alice": {"speaking_time": 120, "segments": 8},
    "Bob": {"speaking_time": 95, "segments": 6}
  }
}
```

## 🛠️ Mock Data Generator

### Core Features
The `generate_mock_data.py` script provides:

- **Realistic Data**: Generates believable meeting content
- **Variety**: Different meeting types and scenarios
- **Scalability**: Generate from 1 to 1000+ records
- **Consistency**: Reproducible results with seed values
- **Customization**: Configurable parameters and templates

### Generation Options
```python
class MockDataGenerator:
    def generate_meeting(self, meeting_type="general", participants=None):
        """Generate a mock meeting record"""
        
    def generate_transcript(self, duration_minutes=10, speakers=2):
        """Generate a mock transcript with realistic conversation"""
        
    def generate_audio_metadata(self, duration_seconds=300):
        """Generate audio file metadata without actual audio"""
        
    def generate_processing_results(self, transcript):
        """Generate expected AI processing results"""
```

### Meeting Types
- **Standup**: Daily team updates
- **Planning**: Sprint/project planning sessions
- **Retrospective**: Team reflection meetings
- **Review**: Product/code review sessions
- **All-hands**: Company-wide meetings
- **1-on-1**: Personal development discussions
- **Interview**: Candidate interview sessions

## 🔧 Configuration

### Environment Variables
```bash
# Mock mode settings
MOCK_MODE=true                    # Enable mock mode globally
USE_MOCK_DATA=true               # Use mock data instead of real data
MOCK_WHISPER=true                # Mock Whisper API responses
MOCK_DATABASE=true               # Use in-memory mock database

# Mock data paths
MOCK_DATA_PATH=app/mock_data     # Base path for mock data
MOCK_AUDIO_PATH=app/mock_data/sample_audio  # Audio samples path

# Generation settings
MOCK_SEED=12345                  # Seed for reproducible data
MOCK_PARTICIPANTS_COUNT=5        # Default participants per meeting
MOCK_MEETING_DURATION=600        # Default meeting duration (seconds)
```

### Custom Templates
Create custom meeting templates:
```python
# Custom meeting template
CUSTOM_TEMPLATE = {
    "type": "retrospective",
    "typical_duration": 3600,  # 1 hour
    "typical_participants": ["Product Owner", "Scrum Master", "Dev Team"],
    "common_topics": ["What went well", "What could improve", "Action items"]
}

# Register template
mock_gen.add_template("custom_retro", CUSTOM_TEMPLATE)
```

## 🧪 Testing Integration

### Unit Tests
```python
import pytest
from app.mock_data.generate_mock_data import MockDataGenerator

class TestMockData:
    def setup_method(self):
        self.mock_gen = MockDataGenerator(seed=12345)
    
    def test_meeting_generation(self):
        meeting = self.mock_gen.generate_meeting("standup")
        assert meeting["meeting_type"] == "standup"
        assert len(meeting["participants"]) >= 2
    
    def test_transcript_generation(self):
        transcript = self.mock_gen.generate_transcript(duration_minutes=5)
        assert transcript["duration"] <= 300  # 5 minutes
        assert len(transcript["segments"]) > 0
```

### Integration Tests
```python
def test_full_workflow_with_mock_data():
    # Use mock data for full pipeline test
    mock_audio = mock_gen.generate_audio_metadata()
    mock_transcript = mock_gen.generate_transcript()
    
    # Process through AI pipeline
    result = ai_processor.process_meeting(mock_audio, mock_transcript)
    
    # Validate results
    assert "summary" in result
    assert "action_items" in result
```

## 📈 Performance Considerations

### Data Size Management
- **Small datasets** (1-10 records): Quick tests and debugging
- **Medium datasets** (100-1000 records): Performance testing
- **Large datasets** (10000+ records): Stress testing and benchmarks

### Memory Usage
```python
# Efficient data generation for large datasets
def generate_large_dataset(count=10000):
    for i in range(count):
        yield mock_gen.generate_meeting()  # Generator to save memory
```

### Caching
```python
# Cache frequently used mock data
@lru_cache(maxsize=128)
def get_cached_mock_meeting(meeting_type, participant_count):
    return mock_gen.generate_meeting(meeting_type, participants=participant_count)
```

## 🚨 Best Practices

### Mock Data Quality
- **Realistic Content**: Use actual meeting scenarios
- **Diverse Data**: Include edge cases and variations
- **Consistent Format**: Maintain data structure consistency
- **Version Control**: Track changes to mock data schemas

### Development Workflow
- **Isolated Testing**: Each test uses independent mock data
- **Reproducible Results**: Use seeds for consistent generation
- **Clean State**: Reset mock data between test runs
- **Documentation**: Document mock data scenarios and expectations

### Production Considerations
- **Never in Production**: Ensure mock mode is disabled in production
- **Environment Separation**: Clear distinction between mock and real data
- **Performance Impact**: Mock data should be faster than real processing
- **Data Privacy**: Mock data contains no real user information

## 🔍 Troubleshooting

### Common Issues

#### Mock Data Not Loading
```bash
# Check mock mode settings
echo $MOCK_MODE
echo $USE_MOCK_DATA

# Verify file paths
ls -la app/mock_data/
```

#### Inconsistent Test Results
```bash
# Set consistent seed
export MOCK_SEED=12345

# Clear cache if using cached data
rm -rf __pycache__/
```

#### Performance Issues
```bash
# Use smaller datasets for quick tests
python generate_mock_data.py --count 10 --type standup

# Monitor memory usage
python -m memory_profiler generate_mock_data.py
```

## 📚 Related Documentation

- [Main AI Processing README](../../README.md)
- [Application Core Guide](../README.md)
- [Testing Guide](../../tests/README.md)
- [Examples Guide](../../examples/README.md)
- [API Documentation](../../API_DOCUMENTATION.md)

---

**Maintainer**: ScrumBot AI Team  
**Last Updated**: August 2025  
**Mock Data Version**: 2.1.0  
**Status**: ✅ All mock generators working