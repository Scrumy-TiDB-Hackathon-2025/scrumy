# Audio-to-Tasks Pipeline

🎤 **Convert meeting recordings into actionable task lists using AI**

## Quick Start

```bash
# 1. Setup environment
./setup_groq_key.sh

# 2. Start the pipeline
./clean_start_backend.sh

# 3. Test the system
python pipeline_summary.py
```

## What It Does

- **Audio → Text**: Transcribe meeting recordings using Whisper.cpp
- **Text → Tasks**: Extract actionable items using GROQ AI
- **Structure**: Organize tasks with assignees, deadlines, and priorities

## API Usage

### Transcribe Audio
```bash
curl -X POST -F "file=@meeting.mp3" http://localhost:5167/transcribe
```

### Extract Tasks
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"transcript": "John will update the docs by Friday"}' \
  http://localhost:5167/extract-tasks
```

## Example Output

```json
{
  "tasks": [
    {
      "title": "Update documentation",
      "assignee": "John",
      "due_date": "Friday",
      "priority": "medium",
      "description": "Update the project documentation"
    }
  ]
}
```

## Architecture

```
Audio File → Whisper.cpp → Transcript → GROQ AI → Structured Tasks
```

## Key Features

- ✅ **Local Audio Processing**: No external API for transcription
- ✅ **AI-Powered Analysis**: Advanced task extraction using LLMs
- ✅ **RESTful API**: Easy integration with existing systems
- ✅ **Structured Output**: JSON format with rich metadata
- ✅ **Production Ready**: Error handling, logging, monitoring

## Testing

| Test File | Purpose |
|-----------|---------|
| `pipeline_summary.py` | Complete demonstration |
| `test_full_pipeline.py` | End-to-end workflow |
| `test_simple_pipeline.py` | Basic functionality |
| `test_pipeline_with_tasks.py` | Task-rich meetings |

## Requirements

- Python 3.8+
- GROQ API key
- ~1GB disk space (for models)
- ~500MB RAM during processing

## Documentation

- 📖 **[Complete Walkthrough](PIPELINE_WALKTHROUGH.md)** - Detailed setup and usage guide
- 🔗 **[API Docs](http://localhost:5167/docs)** - Interactive API documentation (when running)

## Status

🎉 **Production Ready** - Fully functional audio-to-tasks pipeline

---

*Last updated: August 30, 2025*