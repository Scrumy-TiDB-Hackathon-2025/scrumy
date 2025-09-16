# Endpoint Analysis

This document provides a functional overview of the main API endpoints in the Meetily (ScrumBot) backend, describing their purpose, usage scenarios, and how they connect within the overall workflow.

---

## 1. `/process-transcript` (POST)

**Functionality:**  
Initiates processing of a transcript for summarization and analysis.  
- Accepts transcript text, model/provider info, and chunking parameters.
- Creates a new processing job (process/meeting ID).
- Starts background processing (chunking, LLM summarization, etc.).
- Returns a `process_id` (usually the meeting ID) for tracking.

**When to Use:**  
- When you want to submit a transcript for AI-powered summarization and meeting analysis.
- Use this as the first step in the workflow.

**Connection:**  
- The returned `process_id` is used to poll for results via `/get-summary/{process_id}`.

---

## 2. `/get-summary/{process_id}` (GET)

**Functionality:**  
Retrieves the status and result of a transcript processing job.
- Returns status: `"processing"`, `"completed"`, or `"error"`.
- If completed, returns the structured meeting summary.
- If processing, returns status and allows polling.
- If error, returns error details.

**When to Use:**  
- After submitting a transcript via `/process-transcript`, poll this endpoint to check if processing is done and to retrieve the summary.

**Connection:**  
- The `process_id` is obtained from `/process-transcript`.
- Can be polled repeatedly until status is `"completed"` or `"error"`.

---

## 3. `/save-transcript` (POST)

**Functionality:**  
Saves a transcript and its segments to the database without triggering AI processing.
- Accepts meeting title and a list of transcript segments.
- Generates and returns a unique meeting ID.

**When to Use:**  
- When you want to store a transcript for later processing or retrieval, but not immediately process it with AI.
- Useful for draft uploads or manual transcript management.

**Connection:**  
- The returned meeting ID can be used with `/get-meeting/{meeting_id}` and other meeting management endpoints.

---

## 4. `/get-meetings` (GET)

**Functionality:**  
Lists all meetings stored in the system.
- Returns basic info (ID, title) for each meeting.

**When to Use:**  
- To display a list of all meetings to the user.
- For dashboards or meeting selection UIs.

---

## 5. `/get-meeting/{meeting_id}` (GET)

**Functionality:**  
Retrieves full details for a specific meeting.
- Returns title, timestamps, and all transcript segments.

**When to Use:**  
- To display or edit the details of a specific meeting.
- For reviewing or managing meeting data.

---

## 6. `/save-meeting-title` (POST)

**Functionality:**  
Updates the title of an existing meeting.

**When to Use:**  
- To rename a meeting after creation.

---

## 7. `/delete-meeting` (POST)

**Functionality:**  
Deletes a meeting and all its associated data.

**When to Use:**  
- To remove a meeting from the system.

---

## 8. `/get-model-config` (GET) and `/save-model-config` (POST)

**Functionality:**  
- `/get-model-config`: Retrieves the current AI model configuration (provider, model, API key, etc.).
- `/save-model-config`: Updates the AI model configuration.

**When to Use:**  
- To view or change which LLM/AI model is used for processing.

---

## 9. `/get-api-key` (POST)

**Functionality:**  
Retrieves the API key for a given provider.

**When to Use:**  
- To fetch API keys for integration with external AI providers.

---

## 10. `/process-complete-meeting` (POST)

**Functionality:**  
Runs a comprehensive AI analysis on a meeting transcript, integrating multiple features (summarization, action items, etc.).

**When to Use:**  
- For advanced workflows where a full suite of AI features is required in one step.

---

## 11. `/transcribe` (POST)

**Functionality:**  
Accepts an audio file and returns its transcript using Whisper.

**When to Use:**  
- To convert audio recordings to text before further processing.

---

## 12. `/api/v1/tools/process_transcript` (POST)

**Functionality:**  
Processes a transcript and automatically executes integrated tools (e.g., creates tasks in Notion).

**When to Use:**  
- When you want to trigger tool automation (e.g., task creation) based on transcript content.

---

## 13. `/api/v1/tools/available` (GET)

**Functionality:**  
Lists all available tools that can be invoked by the AI agent.

**When to Use:**  
- To display or select tools for automation/integration.

---

## Endpoint Workflow Example

1. **Audio to Text:**  
   - Upload audio to `/transcribe` → get transcript text.

2. **Submit Transcript for Processing:**  
   - POST transcript to `/process-transcript` → get `process_id`.

3. **Poll for Results:**  
   - GET `/get-summary/{process_id}` until status is `"completed"`.

4. **Store/Manage Meetings:**  
   - Use `/save-transcript`, `/get-meetings`, `/get-meeting/{meeting_id}`, `/save-meeting-title`, `/delete-meeting` as needed.

5. **Advanced Automation:**  
   - Use `/api/v1/tools/process_transcript` for tool integration (e.g., Notion task creation).

---

## How Endpoints Connect

- `/transcribe` → `/process-transcript` → `/get-summary/{process_id}` is the main workflow for transcript analysis.
- `/save-transcript` and meeting endpoints allow manual management and retrieval of meeting data.
- Tool endpoints (`/api/v1/tools/...`) enable automation and integration with external systems.
- Model config endpoints allow dynamic switching of AI providers/models.

---

**Summary:**  
These endpoints together provide a full pipeline from raw audio, through transcription, AI-powered analysis, storage, and automation, supporting both synchronous and asynchronous workflows for meeting intelligence.
