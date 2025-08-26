# Meetily Audio Transcription Analysis

## 1. How Meetily Works: End-to-End Architecture

### Frontend (Tauri Application)

The Meetily frontend is a desktop application built with Tauri, a framework for building lightweight, secure desktop applications with web technologies. 

#### Key Components:

1. **Audio Recording Module**
   - Located in `frontend/src-tauri/src/lib.rs` and `frontend/src-tauri/src/audio/*.rs`
   - Captures audio from two sources:
     - System audio (what's playing through the speakers)
     - Microphone input
   - Mixes audio streams (80% microphone, 20% system audio)
   - Chunks audio into 30-second segments (defined by `CHUNK_DURATION_MS: u32 = 30000`)
   - Converts audio to the format required by Whisper (16kHz sample rate, mono)

2. **Frontend UI Components**
   - `RecordingControls.tsx`: Provides UI for starting/stopping recording
   - `TranscriptView.tsx`: Displays transcribed text with timestamps
   - Uses Tauri API events for real-time updates

3. **Communication Layer**
   - Tauri commands defined in `frontend/src-tauri/src/lib.rs`
   - Key functions include:
     - `start_recording()`: Begins capturing audio
     - `stop_recording()`: Ends recording and processes audio file
     - `is_recording()`: Checks current recording status
   - Uses event system to push transcription updates to UI

4. **Analytics and Error Handling**
   - Tracks transcription success/failures
   - Handles errors like missing microphone access or transcription failures

### Backend (Python FastAPI)

The backend is composed of two separate services that work together:

#### 1. Python API Service

- Built with FastAPI framework
- Located in `meeting-minutes/backend/app/main.py`
- Key endpoints:
  - `/transcribe`: Receives audio files and returns transcribed text
  - `/get-summary`: Generates meeting summaries from transcripts
  - `/save-transcript`: Stores transcriptions in the database
  - Various meeting management endpoints (create, update, delete)
- Uses SQLite database for storing meetings, transcripts, and settings

#### 2. Whisper.cpp Server

- Compiled C++ implementation of OpenAI's Whisper model
- Located in `meeting-minutes/backend/whisper-server-package/`
- Contains:
  - `whisper-server`: The executable that processes audio
  - `models/ggml-medium.bin`: The medium-sized Whisper model (1.5GB)
  - Exposes HTTP API on port 8178
- Faster and more efficient than Python-based Whisper implementations

### Data Flow

1. **Recording Initiation**
   - User clicks record button in UI
   - Tauri frontend captures and mixes audio streams
   - Audio is processed in real-time

2. **Transcription Process**
   - When recording stops, audio is saved as WAV file
   - Audio file is sent to backend `/transcribe` endpoint
   - Backend calls whisper-server with the audio file
   - Whisper processes audio and returns JSON with transcription
   - Transcription is parsed and returned to frontend

3. **Results Display**
   - Frontend receives transcription and displays in UI
   - Transcripts are saved to database
   - User can trigger summarization or other AI processing

### Build and Setup Process

1. **Whisper Setup**
   - `build_whisper.sh` script:
     - Clones whisper.cpp repository
     - Compiles the C++ code with optimizations
     - Downloads the selected model
     - Creates a package with server and model
   
2. **Backend Startup**
   - `clean_start_backend.sh` script:
     - Starts whisper-server on port 8178
     - Starts Python API on port 5167
     - Handles model selection and environment setup

3. **Frontend Build**
   - `clean_build.sh` script:
     - Installs dependencies
     - Builds Next.js frontend
     - Packages with Tauri for desktop distribution

## 2. Differences Between Meetily and Scrumy Implementation

### Architectural Differences

| Component | Original Meetily | Scrumy Implementation | Impact |
|-----------|-----------------|----------------------|--------|
| **Directory Structure** | Clean separation between `frontend` and `backend` folders | Altered directory structure with `ai_processing` and other components | Path references broken, relative paths no longer valid |
| **Whisper Executable** | `whisper-server` in `meeting-minutes/backend/whisper-server-package/` | Looking for `main` in `./whisper-server-package/` | Executable not found due to name mismatch |
| **Model File** | `ggml-medium.bin` | Looking for `for-tests-ggml-base.en.bin` | Model file not found due to name mismatch |
| **Path References** | All relative paths aligned with project structure | Misaligned paths, incorrect working directories | Key components not found at runtime |
| **Build Process** | Complete build chain from source to packaged app | Incomplete/broken build process | Missing components, environment issues |

### Code-Level Differences

1. **Frontend Differences**:
   - Meetily: Tauri functions directly mapped to audio processing
   - Scrumy: Some event handler modifications causing state inconsistencies

2. **Backend Differences**:
   - Meetily: `/transcribe` endpoint looks for whisper at `./whisper-server-package/whisper-server`
   - Scrumy: Endpoint looks for whisper at `./whisper-server-package/main`

3. **Build Script Differences**:
   - Meetily: Builds and correctly places all components
   - Scrumy: Scripts try to use original paths, causing misplacements

4. **Environment Configuration**:
   - Meetily: Proper environment setup for relative paths
   - Scrumy: Working directory issues causing path resolution failures

### Critical File Differences

1. **Executable Name**:
   - Meetily: Uses `whisper-server` (the actual compiled binary name)
   - Scrumy: Looking for `main` (incorrect name)

2. **Model File**:
   - Meetily: Uses or creates symlink from `ggml-medium.bin` to `for-tests-ggml-base.en.bin`
   - Scrumy: Missing symbolic link, causing model not found error

3. **Directory Assumptions**:
   - Meetily: Working directory is `meeting-minutes/backend`
   - Scrumy: Working directory inconsistent, possibly at root level

## 3. Considerations to Reach Final Integration Point

### Short-Term Fixes

1. **Create Required Symbolic Links**:
   ```bash
   # In meeting-minutes/backend/whisper-server-package/
   ln -sf whisper-server main
   
   # In meeting-minutes/backend/whisper-server-package/models/
   ln -sf ggml-medium.bin for-tests-ggml-base.en.bin
   ```

2. **Fix Path References in Code**:
   - Update `scrumy/ai_processing/app/main.py` to use correct paths:
   ```python
   whisper_executable = "../meeting-minutes/backend/whisper-server-package/whisper-server"
   model_path = '../meeting-minutes/backend/whisper-server-package/models/ggml-medium.bin'
   ```
   - Or use absolute paths for more reliability

3. **Update Working Directory Settings**:
   - Modify launch scripts to set correct working directory
   - Or update all paths to be absolute rather than relative

### Long-Term Architecture Improvements

1. **Path Abstraction Layer**:
   - Create a configuration system that defines paths centrally
   - Reference this config throughout the codebase
   - Makes future migrations easier

2. **Container-Based Approach**:
   - Containerize Whisper service and Python backend
   - Eliminates path issues across environments
   - Easier deployment and scaling

3. **CI/CD Pipeline Updates**:
   - Add build tests that verify component existence
   - Check for missing files/executables before deployment
   - Validate transcription with test audio files

### Integration Guide Alignment

According to the INTEGRATION_GUIDES_OVERVIEW document, these key considerations should be addressed:

1. **Component Independence**:
   - Whisper service should be standalone and stateless
   - API layer should be environment-agnostic
   - Frontend should handle environment detection

2. **Configuration Management**:
   - Use environment variables for dynamic configuration
   - Create fall-back mechanisms for missing components
   - Implement better error messages for misconfiguration

3. **Testing Strategy**:
   - Implement unit tests for transcription components
   - Create integration tests that verify end-to-end flow
   - Add smoke tests for quick validation of deployment

4. **Documentation**:
   - Update build instructions for clarity
   - Document all path assumptions
   - Create troubleshooting guide for common issues

## Implementation Action Plan

1. **Immediate Fixes (Day 1)**:
   - Create symbolic links for executable and model
   - Fix path references in main.py
   - Test with simple audio file

2. **Short-Term Improvements (Week 1)**:
   - Refactor path handling to use configuration
   - Add better error handling and reporting
   - Create comprehensive test suite

3. **Long-Term Integration (Month 1)**:
   - Align with overall architecture goals
   - Implement containerization strategy
   - Complete CI/CD integration

## Conclusion

The audio transcription issues in the Scrumy implementation are primarily due to path and filename mismatches, not architectural flaws. The original Meetily implementation has a solid architecture for audio capture, processing, and transcription that works well when paths are correctly aligned.

By addressing the specific path and naming issues identified above, and then implementing the longer-term architectural improvements, the Scrumy implementation can achieve full parity with the original Meetily functionality while potentially improving on its architecture for better maintainability and scalability.

The key lesson is that seemingly small details like file paths and executable names can have outsized impacts on system functionality, especially in complex multi-component architectures that span different programming languages and runtime environments.