# Audio Recording and Transcription Flow Analysis

## Overview

This document provides a detailed analysis of how audio recording and transcription works in the Meeting Minutes application, tracing the complete flow from frontend user interaction to backend processing and back.

## Frontend to Backend Flow

### 1. Starting Recording

**Frontend Initialization:**
- The user clicks the record button in the UI, triggering `handleRecordingStart()` in `page.tsx`
- This function calls the Tauri command:
  ```typescript
  await invoke('start_recording', {
    args: {
      whisper_model: modelConfig.whisperModel
    }
  });
  ```

**Backend (Tauri Rust) Processing:**
- The `start_recording` command in `lib.rs` initializes the recording system:
  - Sets the `RECORDING_FLAG` to true
  - Resets error flags and counters
  - Gets the default microphone and system audio devices
  - Creates audio streams for both devices
  - Sets up a reqwest HTTP client for communication with the Whisper server
  - Prepares the stream URL: `http://127.0.0.1:8178/stream`
  - Starts the `audio_collection_task` to capture audio continuously
  - Launches multiple `transcription_worker` tasks (3 by default) to process audio chunks

### 2. Audio Processing During Recording

**Audio Collection:**
- The `audio_collection_task` continuously:
  - Collects audio samples from microphone and system audio streams
  - Mixes the audio (80% microphone, 20% system audio)
  - Creates fixed-size chunks of audio (controlled by `CHUNK_DURATION_MS`, typically 5 seconds)
  - Resamples the audio to 16kHz (Whisper's required sample rate)
  - Adds chunks to the processing queue (`AUDIO_CHUNK_QUEUE`)
  - Emits warnings if the queue starts overflowing

**Transcription Processing:**
- Multiple `transcription_worker` tasks run in parallel to:
  - Take chunks from the queue
  - Convert audio samples to the format required by Whisper
  - Send the audio data to the Whisper server using the `/stream` endpoint
  - Process the transcription response
  - Use `TranscriptAccumulator` to build complete sentences from segments
  - Emit transcript segments to the frontend via Tauri events

### 3. Transcript Delivery to Frontend

**Backend to Frontend Communication:**
- Each `transcription_worker` emits a Tauri event `transcript-update` with the transcribed text:
  ```rust
  app_handle.emit("transcript-update", &update)
  ```
  where `update` contains:
  - The transcribed text
  - Timestamp information
  - Sequence ID (for ordering)
  - Chunk start time
  - Flag indicating whether it's a partial or complete transcript

**Frontend Reception and Processing:**
- In `page.tsx`, a listener is set up for the `transcript-update` event:
  ```typescript
  unlistenFn = await listen<TranscriptUpdate>('transcript-update', (event) => {
    // Process the transcript update
  });
  ```
- The frontend implements a sophisticated buffering system:
  - Maintains a `transcriptBuffer` to handle out-of-order segments
  - Processes sequential transcripts immediately
  - Handles delayed transcripts based on age thresholds
  - Ensures proper ordering of transcripts using sequence IDs
  - Updates the UI with the processed transcripts

### 4. Stopping Recording

**Frontend Initiation:**
- The user clicks the stop button, triggering `handleRecordingStop2(true)` in `page.tsx`
- This function calls the Tauri command:
  ```typescript
  await invoke('stop_recording', { 
    args: { 
      model_config: modelConfig,
      save_path: audioPath
    }
  });
  ```

**Backend (Tauri Rust) Processing:**
- The `stop_recording` command in `lib.rs`:
  - Sets `RECORDING_FLAG` to false to prevent new data processing
  - Waits for a minimum recording duration if needed
  - Stops the running flag for audio streams
  - Waits for transcription workers to complete processing of remaining chunks
  - Monitors active workers and queue size to ensure all audio is processed
  - Stops the audio streams and cleans up resources
  - Emits a `transcription-complete` event when processing is finished

**Frontend Completion Handling:**
- The frontend listens for the `transcription-complete` event:
  ```typescript
  const unlistenComplete = await listen('transcription-complete', () => {
    transcriptionComplete = true;
  });
  ```
- The frontend also polls for transcription status:
  ```typescript
  const status = await invoke<{
    chunks_in_queue: number, 
    is_processing: boolean, 
    last_activity_ms: number
  }>('get_transcription_status');
  ```
- Once the transcription is complete:
  - The frontend performs a "final buffer flush" to ensure all transcripts are processed
  - Saves the transcript to the database with `api_save_transcript`
  - Updates the UI to show the completed transcript
  - Navigates to the meeting details page if requested

### 5. Error Handling

**Transcription Error Handling:**
- The backend emits a `transcript-error` event when transcription fails:
  ```rust
  app_handle.emit("transcript-error", error_msg)
  ```
- The frontend listens for these errors:
  ```typescript
  unsubscribe = await listen('transcript-error', (event) => {
    // Handle the error
    Analytics.trackTranscriptionError(errorMessage);
    onRecordingStop(false);
    if (onTranscriptionError) {
      onTranscriptionError(errorMessage);
    }
  });
  ```

**Audio Chunk Overflow Handling:**
- If the transcription can't keep up with audio capture:
  - Old chunks are dropped from the queue
  - A warning is emitted via the `chunk-drop-warning` event
  - The frontend displays this warning to the user

## Core API Endpoints

The primary external API endpoint used is:

- **Whisper Streaming Endpoint**:
  - URL: `http://127.0.0.1:8178/stream`
  - Method: POST
  - Content-Type: multipart/form-data
  - Request Body: Raw audio data in 32-bit float PCM format
  - Response: JSON with transcribed text segments and timestamps

## Data Flow Diagram

```
┌────────────────┐      ┌────────────────────────────────────┐     ┌───────────────────┐
│                │      │                                    │     │                   │
│                │      │           Tauri Backend            │     │                   │
│    Frontend    │      │                                    │     │   Whisper Server  │
│    (Next.js)   │──────▶  ┌────────────┐    ┌────────────┐  │     │                   │
│                │ invoke │ Recording   │    │Transcription│  │     │                   │
│                │◀──────┤ Commands    │    │  Workers    │──┼─────▶   /stream API      │
└────────────────┘ events └────────────┘    └────────────┘  │     │                   │
                                                            │     │                   │
                                                            │     │                   │
                                                            │     │                   │
                                                            │     │                   │
                                                            │     │                   │
└────────────────────────────────────────────────────────────┘     └───────────────────┘
```

## Conclusion

The audio recording and transcription system uses a multi-layered architecture:

1. **Frontend Layer**: Handles user interaction, displays transcription results, and manages the UI state
2. **Tauri Middleware**: Bridges frontend and audio processing systems, handles audio capture and communication
3. **Whisper Server**: Performs the actual speech-to-text conversion using the Whisper AI model

This architecture allows for high-quality, real-time transcription while maintaining a responsive user interface.