# Audio Transcription Integration Guide

## Overview

This guide provides step-by-step instructions for implementing and troubleshooting the audio transcription functionality in the Scrumy application. It addresses the specific issues encountered when adapting the original Meetily implementation into the Scrumy codebase.

## Architecture

The audio transcription system consists of several interconnected components:

1. **Frontend (Tauri Application)**
   - Captures audio from microphone and system
   - Sends audio files to backend for processing
   - Displays transcription results

2. **Backend (Python FastAPI)**
   - Receives audio files
   - Processes them using Whisper.cpp
   - Returns structured transcript data

3. **Whisper Service**
   - Local instance of Whisper.cpp
   - High-performance speech recognition
   - Processes audio files into text

## Integration Issues and Solutions

### Problem: Path Mismatches

The primary issue with the current implementation is path mismatches between code references and actual filesystem locations.

**Solution:**

1. Create symbolic links to align expected and actual file locations:

```bash
# Navigate to where whisper-server actually exists
cd meeting-minutes/backend/whisper-server-package/

# Create symbolic link from whisper-server to main
ln -sf whisper-server main

# Navigate to models directory
cd models/

# Create symbolic link from actual model to expected model name
ln -sf ggml-medium.bin for-tests-ggml-base.en.bin
```

### Problem: Working Directory Issues

The code assumes execution from different directories than actually used.

**Solution:**

Update the transcription endpoint in `scrumy/ai_processing/app/main.py` to use absolute paths:

```python
import os

# Get the absolute path to the project root
# Adjust this based on your actual directory structure
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

# Define paths relative to project root
WHISPER_DIR = os.path.join(PROJECT_ROOT, "meeting-minutes/backend/whisper-server-package")

# Use in the transcribe function
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    whisper_executable = os.path.join(WHISPER_DIR, "whisper-server")
    model_path = os.path.join(WHISPER_DIR, "models/ggml-medium.bin")
    
    # Rest of function remains the same
```

### Problem: Build Process Failures

The build scripts reference incorrect paths.

**Solution:**

1. Update `build_whisper.sh` to use correct paths:

```bash
# Original
cd backend || handle_error "Failed to change to backend directory"

# Updated
cd meeting-minutes/backend || handle_error "Failed to change to backend directory"
```

2. Update `clean_start_backend.sh` to use consistent port references:

```bash
# Ensure port variables are clear
WHISPER_PORT=8178
API_PORT=5167

# Use these variables consistently
echo -e "${BLUE}Whisper Server Port: ${WHISPER_PORT}${NC}"
echo -e "${BLUE}Python Backend Port: ${API_PORT}${NC}"
```

## Step-by-Step Integration Guide

### 1. Fix Directory Structure

Ensure the Whisper components are correctly installed:

```bash
# Navigate to project root
cd /path/to/scrumy

# Verify whisper-server-package exists
ls -la meeting-minutes/backend/whisper-server-package

# If it doesn't exist, run build script
cd meeting-minutes/backend
./build_whisper.sh medium
```

### 2. Create Required Symbolic Links

```bash
# Navigate to whisper-server-package
cd meeting-minutes/backend/whisper-server-package

# Create link from whisper-server to main
ln -sf whisper-server main

# Create link for model file
cd models
ln -sf ggml-medium.bin for-tests-ggml-base.en.bin
```

### 3. Update Path References

Edit `scrumy/ai_processing/app/main.py` to use correct paths:

```python
# Add this at the top of the file
import os

# Define project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
WHISPER_PACKAGE = os.path.join(PROJECT_ROOT, "meeting-minutes/backend/whisper-server-package")

# Update the transcribe function
@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    whisper_executable = os.path.join(WHISPER_PACKAGE, "whisper-server")
    model_path = os.path.join(WHISPER_PACKAGE, "models/ggml-medium.bin")
    
    # Continue with existing function...
```

### 4. Update Server Configuration

Ensure the Python backend correctly communicates with the Whisper server:

```python
# In app/main.py or a configuration file
WHISPER_SERVER_URL = "http://127.0.0.1:8178"
```

### 5. Test the Integration

1. Start the backend services:
   ```bash
   cd meeting-minutes/backend
   ./clean_start_backend.sh
   ```

2. Test with a sample audio file:
   ```bash
   curl -X POST -F "file=@test_audio.wav" http://127.0.0.1:5167/transcribe
   ```

3. Verify successful transcription in the response.

## Troubleshooting

### Common Issues

1. **"Whisper executable not found" error**
   - Check that the symbolic link from `whisper-server` to `main` exists
   - Verify absolute paths in the code are correct
   - Ensure execute permissions are set: `chmod +x whisper-server`

2. **"Whisper model not found" error**
   - Verify that the model file exists in the expected location
   - Check the symbolic link from actual model to expected model name
   - Ensure read permissions are set for the model file

3. **Connection refused errors**
   - Ensure Whisper server is running on port 8178
   - Check for port conflicts with other services
   - Verify firewall settings allow local connections

4. **Empty transcription results**
   - Check audio file format (16kHz mono WAV is best)
   - Ensure audio file contains clear speech
   - Test with a known good sample file

## Best Practices

1. **Path Management**
   - Use absolute paths for critical components
   - Implement a central configuration system
   - Add validation checks for required files at startup

2. **Error Handling**
   - Add detailed error messages
   - Log all steps in the transcription process
   - Implement graceful fallbacks for missing components

3. **Testing**
   - Create a suite of test audio files
   - Implement integration tests
   - Add monitoring for transcription quality

## Future Improvements

1. **Containerization**
   - Package Whisper service in Docker for easier deployment
   - Eliminate path issues with containerized approach

2. **Configuration System**
   - Create a central configuration file for all paths and settings
   - Support different environments (dev, test, prod)

3. **API Enhancements**
   - Add streaming transcription support
   - Implement speaker diarization
   - Support multiple languages

## Conclusion

By following this integration guide, you should be able to successfully implement the audio transcription functionality in the Scrumy application. The key insights are:

1. Ensure path consistency between code and filesystem
2. Use symbolic links to accommodate different naming conventions
3. Implement robust error handling and validation
4. Test thoroughly with various audio samples

Remember that speech recognition is inherently complex, and results may vary based on audio quality, speech clarity, and background noise. The system is designed to work best with clear, high-quality audio recordings.