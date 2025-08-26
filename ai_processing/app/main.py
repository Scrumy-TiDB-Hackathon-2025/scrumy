import subprocess
import asyncio
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv
from app.database_interface import DatabaseFactory, validate_database_config
import json
from threading import Lock
from app.transcript_processor import TranscriptProcessor
import time
import os
from app.integrated_processor import IntegratedAIProcessor
import uuid
import base64

# Import AIProcessor from its own module
from app.ai_processor import AIProcessor

# Import new tools functionality
try:
    from app.tools_endpoints import router as tools_router
except ImportError:
    from app.tools_endpoints import router as tools_router

# Import WebSocket functionality
from app.websocket_server import websocket_endpoint, websocket_manager

# Import integration adapter
from app.integration_adapter import get_integration_adapter, notify_meeting_processed

# Load environment variables
load_dotenv()

# Configure logger with line numbers and function names
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter with line numbers and function names
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d - %(funcName)s()] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)

# Add handler to logger if not already added
if not logger.handlers:
    logger.addHandler(console_handler)

app = FastAPI(
    title="ScrumBot AI Processing API",
    description="API for processing meeting transcripts with AI tools integration",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],     # Allow all methods
    allow_headers=["*"],     # Allow all headers
    max_age=3600,            # Cache preflight requests for 1 hour
)

# Include tools router
app.include_router(tools_router, prefix="/api/v1", tags=["tools"])

# WebSocket endpoint for real-time audio processing
@app.websocket("/ws")
async def websocket_audio_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming and transcription"""
    await websocket_endpoint(websocket)

@app.websocket("/ws/audio")
async def websocket_audio_shared_contract(websocket: WebSocket):
    """WebSocket endpoint matching shared contract specification"""
    await websocket_endpoint(websocket)

@app.websocket("/ws/audio-stream")
async def websocket_audio_stream_alt(websocket: WebSocket):
    """Alternative WebSocket endpoint path for compatibility"""
    await websocket_endpoint(websocket)

# Lab-required endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        # Check if whisper server components exist
        whisper_server_path = "./whisper-server-package/main"
        model_path = './whisper-server-package/models/for-tests-ggml-base.en.bin'

        if not os.path.isfile(whisper_server_path):
            raise HTTPException(status_code=500, detail="Whisper server executable not found")
        if not os.path.isfile(model_path):
            raise HTTPException(status_code=500, detail="Whisper model not found")

        # Start whisper server if not running
        whisper_server_url = "http://127.0.0.1:8080"

        # Check if server is already running
        server_running = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{whisper_server_url}/")
                server_running = True
                logger.info("Whisper server already running")
        except:
            # Server not running, start it
            logger.info("Starting Whisper server...")
            server_process = subprocess.Popen([
                whisper_server_path,
                "-m", model_path,
                "--host", "127.0.0.1",
                "--port", "8080",
                "--convert"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for server to start with retries
            max_retries = 15
            for i in range(max_retries):
                await asyncio.sleep(2)
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{whisper_server_url}/")
                        server_running = True
                        logger.info(f"Whisper server started after {i+1} attempts")
                        break
                except:
                    logger.debug(f"Server not ready yet, attempt {i+1}/{max_retries}")
                    continue

        if not server_running:
            raise HTTPException(status_code=500, detail="Failed to start Whisper server")

        # Save uploaded file temporarily
        temp_audio_path = f"temp_{file.filename}"
        with open(temp_audio_path, "wb") as f:
            f.write(await file.read())

        try:
            # Send transcription request to whisper server
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(temp_audio_path, "rb") as f:
                    files = {"file": (file.filename, f, file.content_type or "audio/wav")}
                    response = await client.post(
                        f"{whisper_server_url}/inference",
                        files=files
                    )

            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Whisper server error: {response.text}")

            # Parse response - whisper server returns JSON with text field
            try:
                result = response.json()
                transcript_text = result.get("text", "").strip()
            except:
                # Fallback to raw text response
                transcript_text = response.text.strip()

            return {"transcript": transcript_text}

        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Initialize database based on environment configuration
def create_database():
    """Create database instance based on environment configuration"""
    db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()

    if db_type == 'tidb':
        # TiDB configuration from environment
        config = {
            "type": "tidb",
            "connection": {
                "host": os.getenv('TIDB_HOST', 'localhost'),
                "port": int(os.getenv('TIDB_PORT', 4000)),
                "user": os.getenv('TIDB_USER'),
                "password": os.getenv('TIDB_PASSWORD'),
                "database": os.getenv('TIDB_DATABASE', 'scrumy_ai'),
                "ssl_mode": os.getenv('TIDB_SSL_MODE', 'REQUIRED')
            }
        }
    else:
        # SQLite configuration (default for development)
        config = {
            "type": "sqlite",
            "connection": {
                "db_path": os.getenv('SQLITE_DB_PATH', 'meeting_minutes.db')
            }
        }

    if validate_database_config(config):
        logger.info(f"Initializing {db_type.upper()} database")
        return DatabaseFactory.create_from_config(config)
    else:
        logger.error("Invalid database configuration, falling back to SQLite")
        fallback_config = {"type": "sqlite", "connection": {"db_path": "meeting_minutes.db"}}
        return DatabaseFactory.create_from_config(fallback_config)

# Global database instance
db = create_database()

# New Pydantic models for meeting management with participant support
class Participant(BaseModel):
    """Participant data from chrome extension"""
    id: str
    name: str
    platform_id: Optional[str] = None
    status: str = "active"
    join_time: str
    is_host: bool = False

class Transcript(BaseModel):
    id: str
    text: str
    timestamp: str

class MeetingResponse(BaseModel):
    id: str
    title: str

class MeetingDetailsResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    transcripts: List[Transcript]

class MeetingTitleUpdate(BaseModel):
    meeting_id: str
    title: str

class DeleteMeetingRequest(BaseModel):
    meeting_id: str

class SaveTranscriptRequest(BaseModel):
    meeting_title: str
    transcripts: List[Transcript]
    participants: Optional[List[Participant]] = []

class SaveModelConfigRequest(BaseModel):
    provider: str
    model: str
    whisperModel: str
    apiKey: Optional[str] = None

class TranscriptRequest(BaseModel):
    """Request model for transcript text, updated with meeting_id"""
    text: str
    model: str
    model_name: str
    meeting_id: str
    chunk_size: Optional[int] = 5000
    overlap: Optional[int] = 1000
    platform: Optional[str] = None
    timestamp: Optional[str] = None
    participants: Optional[List[Participant]] = []

class SummaryProcessor:
    """Handles the processing of summaries in a thread-safe way"""
    def __init__(self):
        try:
            self.db = db  # Use the global database instance

            logger.info("Initializing SummaryProcessor components")
            self.transcript_processor = TranscriptProcessor()
            logger.info("SummaryProcessor initialized successfully (core components)")
        except Exception as e:
            logger.error(f"Failed to initialize SummaryProcessor: {str(e)}", exc_info=True)
            raise

    async def process_transcript(self, text: str, model: str, model_name: str, chunk_size: int = 5000, overlap: int = 1000) -> tuple:
        """Process a transcript text"""
        try:
            if not text:
                raise ValueError("Empty transcript text provided")

            # Validate chunk_size and overlap
            if chunk_size <= 0:
                raise ValueError("chunk_size must be positive")
            if overlap < 0:
                raise ValueError("overlap must be non-negative")
            if overlap >= chunk_size:
                overlap = chunk_size - 1  # Ensure overlap is less than chunk_size

            # Ensure step size is positive
            step_size = chunk_size - overlap
            if step_size <= 0:
                chunk_size = overlap + 1  # Adjust chunk_size to ensure positive step

            logger.info(f"Processing transcript of length {len(text)} with chunk_size={chunk_size}, overlap={overlap}")
            num_chunks, all_json_data = await self.transcript_processor.process_transcript(
                text=text,
                model=model,
                model_name=model_name,
                chunk_size=chunk_size,
                overlap=overlap
            )
            logger.info(f"Successfully processed transcript into {num_chunks} chunks")

            return num_chunks, all_json_data
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}", exc_info=True)
            raise

    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up resources")
            if hasattr(self, 'transcript_processor'):
                self.transcript_processor.cleanup()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)

# Initialize processor
processor = SummaryProcessor()

# New meeting management endpoints
@app.get("/get-meetings", response_model=List[MeetingResponse])
async def get_meetings():
    """Get all meetings with their basic information"""
    try:
        meetings = await db.get_all_meetings()
        return [{"id": meeting["id"], "title": meeting["title"]} for meeting in meetings]
    except Exception as e:
        logger.error(f"Error getting meetings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-meeting/{meeting_id}", response_model=MeetingDetailsResponse)
async def get_meeting(meeting_id: str):
    """Get a specific meeting by ID with all its details"""
    try:
        meeting = await db.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-meeting-title")
async def save_meeting_title(data: MeetingTitleUpdate):
    """Save a meeting title"""
    try:
        await db.update_meeting_title(data.meeting_id, data.title)
        return {"message": "Meeting title saved successfully"}
    except Exception as e:
        logger.error(f"Error saving meeting title: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete-meeting")
async def delete_meeting(data: DeleteMeetingRequest):
    """Delete a meeting and all its associated data"""
    try:
        success = await db.delete_meeting(data.meeting_id)
        if success:
            return {"message": "Meeting deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete meeting")
    except Exception as e:
        logger.error(f"Error deleting meeting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_transcript_background(process_id: str, transcript: TranscriptRequest):
    """Background task to process transcript"""
    try:
        logger.info(f"Starting background processing for process_id: {process_id}")

        # Convert participants to dict format for transcript processor
        participants_dict = None
        if transcript.participants:
            participants_dict = [p.dict() if hasattr(p, 'dict') else p for p in transcript.participants]

        num_chunks, all_json_data = await processor.process_transcript(
            text=transcript.text,
            model=transcript.model,
            model_name=transcript.model_name,
            chunk_size=transcript.chunk_size,
            overlap=transcript.overlap,
            participants=participants_dict
        )

        # Create final summary structure by aggregating chunk results
        final_summary = {
            "MeetingName": "",
            "SectionSummary": {"title": "Section Summary", "blocks": []},
            "CriticalDeadlines": {"title": "Critical Deadlines", "blocks": []},
            "KeyItemsDecisions": {"title": "Key Items & Decisions", "blocks": []},
            "ImmediateActionItems": {"title": "Immediate Action Items", "blocks": []},
            "NextSteps": {"title": "Next Steps", "blocks": []},
            "OtherImportantPoints": {"title": "Other Important Points", "blocks": []},
            "ClosingRemarks": {"title": "Closing Remarks", "blocks": []}
        }

        # Process each chunk's data
        for json_str in all_json_data:
            try:
                json_dict = json.loads(json_str)
                if "MeetingName" in json_dict and json_dict["MeetingName"]:
                    final_summary["MeetingName"] = json_dict["MeetingName"]
                for key in final_summary:
                    if key != "MeetingName" and key in json_dict and isinstance(json_dict[key], dict) and "blocks" in json_dict[key]:
                        if isinstance(json_dict[key]["blocks"], list):
                            final_summary[key]["blocks"].extend(json_dict[key]["blocks"])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON chunk for {process_id}: {e}. Chunk: {json_str[:100]}...")
            except Exception as e:
                logger.error(f"Error processing chunk data for {process_id}: {e}. Chunk: {json_str[:100]}...")

        # Update database with meeting name using meeting_id
        if final_summary["MeetingName"]:
            await processor.db.update_meeting_name(transcript.meeting_id, final_summary["MeetingName"])

        # Save final result
        if all_json_data:
            await processor.db.update_process(process_id, status="completed", result=json.dumps(final_summary))
            logger.info(f"Background processing completed for process_id: {process_id}")
        else:
            error_msg = "Summary generation failed: No summary could be generated. Please check your model/API key settings."
            await processor.db.update_process(process_id, status="failed", error=error_msg)
            logger.error(f"Background processing failed for process_id: {process_id} - {error_msg}")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in background processing for {process_id}: {error_msg}", exc_info=True)
        try:
            await processor.db.update_process(process_id, status="failed", error=error_msg)
        except Exception as db_e:
            logger.error(f"Failed to update DB status to failed for {process_id}: {db_e}", exc_info=True)

@app.post("/process-transcript")
async def process_transcript_api(
    transcript: TranscriptRequest,
    background_tasks: BackgroundTasks
):
    """Process a transcript text with background processing"""
    try:
        # Create new process linked to meeting_id
        process_id = await processor.db.create_process(transcript.meeting_id)

        # Save transcript data associated with meeting_id
        await processor.db.save_transcript(
            transcript.meeting_id,
            transcript.text,
            transcript.model,
            transcript.model_name,
            transcript.chunk_size,
            transcript.overlap
        )

        # Save participants if provided
        if transcript.participants:
            logger.info(f"Saving {len(transcript.participants)} participants from transcript request")
            participants_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "platform_id": p.platform_id or p.id,
                    "status": p.status,
                    "join_time": p.join_time,
                    "is_host": p.is_host
                }
                for p in transcript.participants
            ]
            await processor.db.save_participants_batch(transcript.meeting_id, participants_data)

        # Start background processing
        background_tasks.add_task(
            process_transcript_background,
            process_id,
            transcript
        )

        return JSONResponse({
            "message": "Processing started",
            "process_id": process_id
        })

    except Exception as e:
        logger.error(f"Error in process_transcript_api: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-summary/{meeting_id}")
async def get_summary(meeting_id: str):
    """Get the summary for a given meeting ID"""
    try:
        result = await processor.db.get_transcript_data(meeting_id)
        if not result:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "meetingName": None,
                    "meeting_id": meeting_id,
                    "data": None,
                    "start": None,
                    "end": None,
                    "error": "Meeting ID not found"
                }
            )

        status = result.get("status", "unknown").lower()

        # Parse result data if available
        summary_data = None
        if result.get("result"):
            try:
                parsed_result = json.loads(result["result"])
                if isinstance(parsed_result, str):
                    summary_data = json.loads(parsed_result)
                else:
                    summary_data = parsed_result
                if not isinstance(summary_data, dict):
                    logger.error(f"Parsed summary data is not a dictionary for meeting {meeting_id}")
                    summary_data = None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data for meeting {meeting_id}: {str(e)}")
                status = "failed"
                result["error"] = f"Invalid summary data format: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error parsing summary data for {meeting_id}: {str(e)}")
                status = "failed"
                result["error"] = f"Error processing summary data: {str(e)}"

        response = {
            "status": "processing" if status in ["processing", "pending", "started"] else status,
            "meetingName": summary_data.get("MeetingName") if isinstance(summary_data, dict) else None,
            "meeting_id": meeting_id,
            "start": result.get("start_time"),
            "end": result.get("end_time"),
            "data": summary_data if status == "completed" else None
        }

        if status == "failed":
            response["status"] = "error"
            response["error"] = result.get("error", "Unknown processing error")
            response["data"] = None
            response["meetingName"] = None
            return JSONResponse(status_code=400, content=response)

        elif status in ["processing", "pending", "started"]:
            response["data"] = None
            return JSONResponse(status_code=202, content=response)

        elif status == "completed":
            if not summary_data:
                response["status"] = "error"
                response["error"] = "Completed but summary data is missing or invalid"
                response["data"] = None
                response["meetingName"] = None
                return JSONResponse(status_code=500, content=response)
            return JSONResponse(status_code=200, content=response)

        else:
            response["status"] = "error"
            response["error"] = f"Unknown or unexpected status: {status}"
            response["data"] = None
            response["meetingName"] = None
            return JSONResponse(status_code=500, content=response)

    except Exception as e:
        logger.error(f"Error getting summary for {meeting_id}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "meetingName": None,
                "meeting_id": meeting_id,
                "data": None,
                "start": None,
                "end": None,
                "error": f"Internal server error: {str(e)}"
            }
        )

@app.post("/save-transcript")
async def save_transcript(request: SaveTranscriptRequest):
    """Save transcript segments for a meeting without processing"""
    try:
        logger.info(f"Received save-transcript request for meeting: {request.meeting_title}")
        logger.info(f"Number of transcripts to save: {len(request.transcripts)}")

        # Generate a unique meeting ID using UUID
        meeting_id = f"meeting-{uuid.uuid4()}"

        # Save the meeting
        await db.save_meeting(meeting_id, request.meeting_title)

        # Save participants if provided
        if request.participants:
            logger.info(f"Saving {len(request.participants)} participants for meeting {meeting_id}")
            participants_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "platform_id": p.platform_id or p.id,
                    "status": p.status,
                    "join_time": p.join_time,
                    "is_host": p.is_host
                }
                for p in request.participants
            ]
            await db.save_participants_batch(meeting_id, participants_data)

        # Save each transcript segment
        for transcript in request.transcripts:
            await db.save_meeting_transcript(
                meeting_id=meeting_id,
                transcript=transcript.text,
                timestamp=transcript.timestamp,
                summary="",
                action_items="",
                key_points=""
            )

        logger.info("Transcripts saved successfully")
        return {"status": "success", "message": "Transcript saved successfully", "meeting_id": meeting_id}
    except Exception as e:
        logger.error(f"Error saving transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-model-config")
async def get_model_config():
    """Get the current model configuration"""
    model_config = await db.get_model_config()
    if not model_config:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "No model configuration found"
            }
        )
    api_key = await db.get_api_key(model_config["provider"])
    if api_key is not None:
        model_config["apiKey"] = api_key
    return model_config

@app.post("/save-model-config")
async def save_model_config(request: SaveModelConfigRequest):
    """Save the model configuration"""
    await db.save_model_config(request.provider, request.model, request.whisperModel)
    if request.apiKey != None:
        await db.save_api_key(request.apiKey, request.provider)
    return {"status": "success", "message": "Model configuration saved successfully"}

@app.post("/process-complete-meeting")

async def process_complete_meeting(request: TranscriptRequest):
    """Process complete meeting with all AI features"""
    integrated_processor = IntegratedAIProcessor()
    meeting_context = {
        "meeting_id": request.meeting_id,
        "platform": request.platform,
        "timestamp": request.timestamp

    }
    result = await integrated_processor.process_complete_meeting(request.text, meeting_context)
    return result
class GetApiKeyRequest(BaseModel):
    provider: str

@app.post("/get-api-key")
async def get_api_key(request: GetApiKeyRequest):
    """Get the API key for a given provider"""
    return await db.get_api_key(request.provider)

# Chrome Extension Compatible Endpoints

class IdentifySpeakersRequest(BaseModel):
    text: str
    context: Optional[str] = ""

class GenerateSummaryRequest(BaseModel):
    transcript: str
    meeting_id: Optional[str] = None
    meeting_title: Optional[str] = None

class ExtractTasksRequest(BaseModel):
    transcript: str
    meeting_context: Optional[Dict] = None

class ProcessTranscriptWithToolsRequest(BaseModel):
    text: str
    meeting_id: str
    timestamp: Optional[str] = None
    platform: Optional[str] = "unknown"

@app.post("/identify-speakers")
async def identify_speakers(request: IdentifySpeakersRequest):
    """Identify speakers in meeting transcript - Chrome extension compatible"""
    try:
        from app.speaker_identifier import SpeakerIdentifier

        ai_processor = AIProcessor()
        speaker_identifier = SpeakerIdentifier(ai_processor)

        result = await speaker_identifier.identify_speakers_advanced(
            request.text,
            request.context
        )

        # Format response to match Chrome extension expectations
        speakers_data = []
        if 'speakers' in result:
            for i, speaker in enumerate(result['speakers']):
                if isinstance(speaker, dict):
                    speakers_data.append({
                        'id': f"speaker_{i + 1}",
                        'name': speaker.get('name', f'Speaker {i + 1}'),
                        'segments': speaker.get('segments', []),
                        'total_words': speaker.get('word_count', 0),
                        'characteristics': speaker.get('characteristics', '')
                    })
                elif isinstance(speaker, str):
                    speakers_data.append({
                        'id': f"speaker_{i + 1}",
                        'name': speaker,
                        'segments': [f"{speaker} contributed to the discussion"],
                        'total_words': 50,
                        'characteristics': f"{speaker} - active participant"
                    })

        return {
            'status': 'success',
            'data': {
                'speakers': speakers_data,
                'confidence': result.get('confidence', 0.85),
                'total_speakers': len(speakers_data),
                'identification_method': 'ai_inference',
                'processing_time': result.get('processing_time', 1.5)
            }
        }

    except Exception as e:
        logger.error(f"Speaker identification error: {e}")
        raise HTTPException(status_code=500, detail=f"Speaker identification failed: {str(e)}")

@app.post("/generate-summary")
async def generate_summary(request: GenerateSummaryRequest):
    """Generate comprehensive meeting summary - Chrome extension compatible"""
    try:
        from app.meeting_summarizer import MeetingSummarizer

        ai_processor = AIProcessor()
        summarizer = MeetingSummarizer(ai_processor)

        meeting_context = {
            'meeting_id': request.meeting_id,
            'meeting_title': request.meeting_title or "Team Meeting"
        }

        summary = await summarizer.generate_comprehensive_summary(
            request.transcript,
            meeting_context
        )

        # Format response to match Chrome extension expectations
        return {
            'status': 'success',
            'data': {
                'meeting_title': request.meeting_title or "Team Meeting",
                'executive_summary': {
                    'overview': summary.get('overview', 'Meeting summary generated'),
                    'key_outcomes': summary.get('key_points', ['Meeting completed successfully']),
                    'business_impact': summary.get('business_impact', 'Positive impact on team collaboration'),
                    'urgency_level': summary.get('urgency_level', 'medium'),
                    'follow_up_required': summary.get('follow_up_required', True)
                },
                'key_decisions': {
                    'decisions': summary.get('decisions', []),
                    'total_decisions': len(summary.get('decisions', [])),
                    'consensus_level': summary.get('consensus_level', 'good')
                },
                'participants': {
                    'participants': summary.get('participants', []),
                    'meeting_leader': summary.get('meeting_leader', 'Unknown'),
                    'total_participants': len(summary.get('participants', [])),
                    'participation_balance': summary.get('participation_balance', 'balanced')
                },
                'summary_generated_at': datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@app.post("/extract-tasks")
async def extract_tasks(request: ExtractTasksRequest):
    """Extract action items and tasks - Chrome extension compatible"""
    try:
        from app.task_extractor import TaskExtractor

        ai_processor = AIProcessor()
        task_extractor = TaskExtractor(ai_processor)

        tasks_result = await task_extractor.extract_comprehensive_tasks(
            request.transcript,
            request.meeting_context or {}
        )

        # Format tasks to match Chrome extension expectations
        formatted_tasks = []
        if 'tasks' in tasks_result:
            for i, task in enumerate(tasks_result['tasks']):
                if isinstance(task, dict):
                    formatted_tasks.append({
                        'id': f"task_{i + 1}",
                        'title': task.get('title', f'Task {i + 1}'),
                        'description': task.get('description', ''),
                        'assignee': task.get('assignee', 'Unassigned'),
                        'due_date': task.get('due_date'),
                        'priority': task.get('priority', 'medium'),
                        'status': 'pending',
                        'category': task.get('category', 'action_item'),
                        'dependencies': task.get('dependencies', []),
                        'business_impact': task.get('priority', 'medium'),
                        'created_at': datetime.now().isoformat()
                    })

        return {
            'status': 'success',
            'data': {
                'tasks': formatted_tasks,
                'task_summary': {
                    'total_tasks': len(formatted_tasks),
                    'high_priority': len([t for t in formatted_tasks if t['priority'] == 'high']),
                    'with_deadlines': len([t for t in formatted_tasks if t['due_date']]),
                    'assigned': len([t for t in formatted_tasks if t['assignee'] != 'Unassigned'])
                },
                'extraction_metadata': {
                    'explicit_tasks_found': len(formatted_tasks),
                    'implicit_tasks_found': 0,
                    'extracted_at': datetime.now().isoformat()
                }
            }
        }

    except Exception as e:
        logger.error(f"Task extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Task extraction failed: {str(e)}")

@app.post("/process-transcript-with-tools")
async def process_transcript_with_tools(request: ProcessTranscriptWithToolsRequest):
    """Process transcript with all AI tools - Chrome extension compatible"""
    try:
        # Use integrated processor for comprehensive analysis
        integrated_processor = IntegratedAIProcessor()

        meeting_context = {
            'meeting_id': request.meeting_id,
            'platform': request.platform,
            'timestamp': request.timestamp
        }

        result = await integrated_processor.process_complete_meeting(
            request.text,
            meeting_context
        )

        # Extract participants for integration
        participants = []
        if 'speakers' in result:
            participants = [
                speaker.get('name', 'Unknown')
                for speaker in result['speakers']
                if isinstance(speaker, dict)
            ]

        # Notify integration systems (async, non-blocking)
        try:
            asyncio.create_task(notify_meeting_processed(
                meeting_id=request.meeting_id,
                meeting_title=f"Meeting {request.meeting_id}",
                platform=request.platform,
                participants=participants,
                transcript=request.text,
                summary_data=result.get('summary', {}),
                tasks_data=result.get('tasks', []),
                speakers_data=result.get('speakers', [])
            ))
            logger.info(f"Triggered integration processing for meeting {request.meeting_id}")
        except Exception as integration_error:
            logger.warning(f"Integration notification failed: {integration_error}")

        # Format response to match Chrome extension expectations
        return {
            'status': 'success',
            'meeting_id': request.meeting_id,
            'analysis': result.get('summary', {}),
            'actions_taken': result.get('tasks', []),
            'speakers': result.get('speakers', []),
            'tools_used': 3,  # Speaker ID, Summary, Tasks
            'processed_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Comprehensive processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/available-tools")
async def get_available_tools():
    """Get list of available AI tools - Chrome extension compatible"""
    return {
        'tools': [
            {
                'name': 'identify_speakers',
                'description': 'Identify speakers in meeting transcript',
                'parameters': ['text', 'context']
            },
            {
                'name': 'extract_tasks',
                'description': 'Extract action items and tasks',
                'parameters': ['transcript', 'meeting_context']
            },
            {
                'name': 'generate_summary',
                'description': 'Generate comprehensive meeting summary',
                'parameters': ['transcript', 'meeting_title']
            }
        ],
        'tool_names': ['identify_speakers', 'extract_tasks', 'generate_summary'],
        'count': 3
    }



@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on API shutdown"""
    logger.info("API shutting down, cleaning up resources")
    try:
        processor.cleanup()
        logger.info("Successfully cleaned up resources")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}", exc_info=True)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=5167)
