import subprocess
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv
from app.db import DatabaseManager
from app.database_interface import DatabaseFactory, validate_database_config
import json
from threading import Lock
from app.transcript_processor import TranscriptProcessor
import time
import os
from app.integrated_processor import IntegratedAIProcessor
import uuid
import pytest
import asyncio
import datetime
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

# Include frontend endpoints
try:
    from app.frontend_endpoints import router as frontend_router
    app.include_router(frontend_router, tags=["frontend"])
    logger.info(f"✅ Frontend router included with {len(frontend_router.routes)} routes")
except Exception as e:
    logger.error(f"❌ Failed to include frontend router: {e}")
    logger.error(f"Frontend endpoints will not be available")
    import traceback
    traceback.print_exc()

# Lab-required endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def preprocess_audio_for_whisper(input_path: str, output_path: str) -> bool:
    """
    Convert audio to the format expected by whisper.cpp:
    - Mono channel
    - 16kHz sample rate 
    - 16-bit PCM WAV format
    """
    try:
        # Use ffmpeg to convert to whisper.cpp requirements
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ar", "16000",      # Sample rate: 16kHz
            "-ac", "1",          # Audio channels: mono
            "-c:a", "pcm_s16le", # Codec: 16-bit PCM little-endian
            "-y",                # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {str(e)}")
        return False

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        # Use the same paths as your working test
        base_dir = os.path.dirname(os.path.abspath(__file__))
        whisper_executable = os.path.join(base_dir, "../whisper.cpp/build/bin/whisper-cli")
        model_path = os.path.join(base_dir, "../whisper.cpp/models/ggml-base.en.bin")

        if not os.path.isfile(whisper_executable):
            raise HTTPException(status_code=500, detail="Whisper executable not found")
        if not os.path.isfile(model_path):
            raise HTTPException(status_code=500, detail="Whisper model not found")

        # Create temporary files for the UPLOADED audio file
        temp_audio_path = f"temp_{file.filename}"
        processed_audio_path = f"processed_{file.filename}.wav"
        
        try:
            # Save the uploaded file to disk
            with open(temp_audio_path, "wb") as f:
                f.write(await file.read())

            # Check if ffmpeg is available
            try:
                subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
                ffmpeg_available = True
            except:
                ffmpeg_available = False
                logger.warning("FFmpeg not available, using original audio file")

            # Preprocess audio if ffmpeg is available
            audio_file_to_use = temp_audio_path
            if ffmpeg_available:
                if preprocess_audio_for_whisper(temp_audio_path, processed_audio_path):
                    audio_file_to_use = processed_audio_path
                    logger.info("Audio preprocessed successfully")
                else:
                    logger.warning("Audio preprocessing failed, using original file")

            # Run whisper command
            whisper_cmd = [
                whisper_executable,
                "-m", model_path,
                "--output-json",
                "--output-file", "-",
                "--no-gpu",
                "--language", "en",
                "--threads", "4",
                "--best-of", "5",
                "--beam-size", "5",
                "--word-thold", "0.01",
                "--entropy-thold", "2.4",
                "--logprob-thold", "-1.0",
                audio_file_to_use,  # Use the uploaded file, not a hardcoded path
            ]

            logger.info(f"Running whisper command: {' '.join(whisper_cmd)}")
            
            result = subprocess.run(
                whisper_cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            logger.info(f"Whisper return code: {result.returncode}")
            logger.info(f"Whisper stderr: {result.stderr}")
            logger.info(f"Whisper stdout length: {len(result.stdout)}")

            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Whisper failed: {result.stderr}")

            # Parse JSON output from whisper
            transcript_text = ""
            if result.stdout.strip():
                try:
                    parsed = json.loads(result.stdout)
                    
                    # Debug: Log the JSON structure
                    logger.info(f"Whisper JSON keys: {list(parsed.keys())}")
                    
                    # Try different ways to extract transcript text
                    if "text" in parsed:
                        transcript_text = parsed["text"].strip()
                    elif "transcription" in parsed:
                        segments = parsed["transcription"]
                        logger.info(f"Whisper found {len(segments)} segments")
                        # Combine all segment texts
                        transcript_text = " ".join([seg.get("text", "") for seg in segments if seg.get("text")]).strip()
                    
                    # If still empty, try to extract from any text fields in segments
                    if not transcript_text and "transcription" in parsed:
                        all_texts = []
                        for seg in parsed["transcription"]:
                            if isinstance(seg, dict):
                                for key in ["text", "content", "transcript"]:
                                    if key in seg and seg[key]:
                                        all_texts.append(str(seg[key]))
                        transcript_text = " ".join(all_texts).strip()
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON, using raw output: {e}")
                    transcript_text = result.stdout.strip()
                except Exception as e:
                    logger.error(f"Error parsing Whisper output: {e}")
                    # Log first 500 chars of output for debugging
                    logger.info(f"Raw Whisper output sample: {result.stdout[:500]}...")
            
            # Save the raw Whisper output to file for debugging
            try:
                debug_file = f"whisper_output_{file.filename}_{int(time.time())}.json"
                with open(debug_file, "w") as f:
                    f.write(result.stdout)
                logger.info(f"Whisper output saved to: {debug_file}")
            except Exception as e:
                logger.warning(f"Failed to save debug output: {e}")
            
            if not transcript_text:
                logger.warning("Empty transcript received. Possible causes:")
                logger.warning("1. Audio contains no speech")
                logger.warning("2. Audio quality is too poor") 
                logger.warning("3. Audio format is not compatible")
                logger.warning("4. Whisper model sensitivity settings")

            return {"transcript": transcript_text}

        finally:
            # Cleanup temporary files
            for temp_file in [temp_audio_path, processed_audio_path]:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Global database manager instance for meeting management endpoints
db = DatabaseFactory.create_from_env()

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

class SummaryProcessor:
    """Handles the processing of summaries in a thread-safe way"""
    def __init__(self):
        try:
            # Use environment-based database configuration
            self.db = DatabaseFactory.create_from_env()
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

        num_chunks, all_json_data = await processor.process_transcript(
            text=transcript.text,
            model=transcript.model,
            model_name=transcript.model_name,
            chunk_size=transcript.chunk_size,
            overlap=transcript.overlap
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
                'summary_generated_at': datetime.datetime.now().isoformat()
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
                        'created_at': datetime.datetime.now().isoformat()
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
                    'extracted_at': datetime.datetime.now().isoformat()
                }
            }
        }

    except Exception as e:
        logger.error(f"Task extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Task extraction failed: {str(e)}")

@app.post("/extract-tasks-comprehensive")
async def extract_tasks_comprehensive(request: ExtractTasksRequest):
    """Extract tasks with comprehensive database storage and integration filtering - NO REDUNDANCY"""
    try:
        from app.task_extractor import TaskExtractor
        from app.database_task_manager import DatabaseTaskManager
        
        # Step 1: AI extraction (REUSES existing TaskExtractor - no redundancy)
        ai_processor = AIProcessor()
        task_extractor = TaskExtractor(ai_processor)
        
        meeting_id = request.meeting_context.get('meeting_id', f"meeting_{int(datetime.datetime.now().timestamp())}") if request.meeting_context else f"meeting_{int(datetime.datetime.now().timestamp())}"
        
        # Extract tasks using existing extractor (no duplicate code)
        ai_result = await task_extractor.extract_comprehensive_tasks(
            request.transcript,
            request.meeting_context or {}
        )
        
        if not ai_result or 'tasks' not in ai_result:
            return {
                "status": "error",
                "error": "AI extraction failed",
                "data": {"ai_extraction": {"tasks": []}, "database_storage": {"stored_tasks": []}, "integration_tasks": []}
            }
        
        # Step 2: Database storage + integration filtering (NEW functionality)
        db_manager = DatabaseTaskManager()
        
        # Store all AI fields in database (comprehensive)
        storage_result = db_manager.store_comprehensive_tasks(
            ai_result['tasks'], 
            meeting_id
        )
        
        # Get filtered tasks for integration platforms (only supported fields)
        integration_tasks = db_manager.get_integration_tasks(
            storage_result["stored_tasks"], 
            platform="integration"
        )
        
        # Get field mapping analysis
        field_mapping = db_manager.show_field_mapping(storage_result["stored_tasks"])
        
        return {
            "status": "success",
            "data": {
                # Original AI extraction results (all fields)
                "ai_extraction": {"tasks": ai_result['tasks']},
                
                # Database storage results (all fields preserved)
                "database_storage": storage_result,
                
                # Integration-ready tasks (filtered to supported fields only)
                "integration_tasks": integration_tasks,
                
                # Field mapping analysis
                "field_analysis": field_mapping,
                
                # Summary
                "summary": {
                    "total_ai_tasks": len(ai_result['tasks']),
                    "database_fields_stored": len(storage_result["stored_tasks"][0].keys()) if storage_result["stored_tasks"] else 0,
                    "integration_fields_available": len(integration_tasks[0].keys()) if integration_tasks else 0,
                    "meeting_id": meeting_id,
                    "architecture": "Two-layer: Database (all fields) + Integration (filtered fields)"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive task extraction error: {e}")
        return {
            "status": "error",
            "error": f"Comprehensive task extraction failed: {str(e)}",
            "data": {
                "ai_extraction": {"tasks": []},
                "database_storage": {"stored_tasks": []},
                "integration_tasks": [],
                "field_analysis": {"available_fields": []},
                "summary": {"total_ai_tasks": 0}
            }
        }

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
            'processed_at': datetime.datetime.now().isoformat()
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
