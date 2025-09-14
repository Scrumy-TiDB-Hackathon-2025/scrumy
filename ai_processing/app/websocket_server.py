"""
WebSocket server for real-time audio processing with participant identification
Handles Chrome extension communication for live transcription and AI processing
Enhanced with Phase 3 session management for timeout-based processing
"""

import asyncio
import json
import logging
import websockets
import tempfile
import os
import sys
import threading
from typing import Dict, Set, Optional, List
from datetime import datetime
import wave
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from app.ai_processor import AIProcessor
from app.speaker_identifier import SpeakerIdentifier
from app.meeting_summarizer import MeetingSummarizer
from app.task_extractor import TaskExtractor
from app.integration_adapter import ParticipantData, notify_meeting_processed
from app.meeting_buffer import MeetingBuffer, TranscriptChunk, BatchProcessor
from app.audio_buffer import AudioBufferManager, SessionAudioBuffer
from app.pipeline_logger import PipelineLogger
from app.background_tasks import background_manager
from app.session_manager import session_manager
from app.database_interface import DatabaseFactory
from app.chatbot_sync import chatbot_sync
import subprocess
import time
import uuid
import os

# Import WebSocket events constants and monitoring
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
try:
    from websocket_events import WebSocketEventTypes, WebSocketEventData, WebSocketEventValidator
    from websocket_event_monitor import monitor_event, get_monitoring_report
except ImportError:
    # Fallback if import fails
    class WebSocketEventTypes:
        TRANSCRIPTION_RESULT = "TRANSCRIPTION_RESULT"
        HANDSHAKE_ACK = "HANDSHAKE_ACK"
        ERROR = "ERROR"
        MEETING_UPDATE = "MEETING_UPDATE"

    class WebSocketEventData:
        @staticmethod
        def transcription_result(text, confidence, timestamp, speaker="Unknown", chunk_id=None, **kwargs):
            return {"text": text, "confidence": confidence, "timestamp": timestamp, "speaker": speaker, "chunkId": chunk_id, **kwargs}

    # Fallback monitoring functions
    def monitor_event(event_type, data, source="unknown", session_id=None):
        logger.debug(f"Event monitoring fallback: {event_type} from {source}")
        return {"is_duplicate": False, "is_deprecated": False, "validation_errors": [], "recommendations": []}

    def get_monitoring_report():
        return {"error": "Event monitoring not available"}

logger = logging.getLogger(__name__)

def get_websocket_monitoring_report():
    """Get monitoring report for WebSocket events."""
    try:
        return get_monitoring_report()
    except Exception as e:
        logger.error(f"Failed to get monitoring report: {e}")
        return {"error": str(e)}

class AudioProcessor:
    """Handle audio chunk processing and transcription"""

    def __init__(self):
        self.whisper_model_path = os.getenv('WHISPER_MODEL_PATH', './whisper.cpp/models/ggml-base.en.bin')
        self.whisper_executable = os.getenv('WHISPER_EXECUTABLE', './whisper.cpp/build/bin/whisper-cli')

    async def process_audio_chunk(self, audio_data: bytes, metadata: Dict) -> Dict:
        """Enhanced audio chunk processing with better analysis"""
        try:
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

                # Convert audio data to WAV format if needed
                await self._write_audio_to_wav(audio_data, temp_path, metadata)

                # Analyze audio before processing
                audio_stats = await self._analyze_audio_file(temp_path)
                print(f"🎵 Audio Stats: {audio_stats}")

                # Skip processing if clearly silence
                if audio_stats.get('is_likely_silence', False):
                    print("⚠️ Skipping Whisper processing - audio appears to be silence")
                    os.unlink(temp_path)
                    return {
                        'text': '[SILENCE_DETECTED]',
                        'confidence': 0.0,
                        'timestamp': datetime.now().isoformat(),
                        'metadata': metadata
                    }

                # Run enhanced Whisper transcription
                transcript = await self._transcribe_audio_enhanced(temp_path)

                # Log processing result
                if transcript and transcript not in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]']:
                    print(f"✅ Transcription successful: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'")
                    print(f"📝 Whisper result: '{transcript}'")
                else:
                    print(f"⚠️ Empty or blank transcription result: '{transcript}'")

                # Clean up temp file
                os.unlink(temp_path)

                return {
                    'text': transcript,
                    'confidence': 0.85 if transcript and transcript not in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]'] else 0.0,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata,
                    'audio_stats': audio_stats
                }

        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return {
                'text': '[PROCESSING_ERROR]',
                'confidence': 0.0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    async def _write_audio_to_wav(self, audio_data: bytes, output_path: str, metadata: Dict):
        """Write audio data to WAV file"""
        try:
            # Default audio parameters
            sample_rate = metadata.get('sampleRate', 16000)
            channels = metadata.get('channels', 1)
            sample_width = metadata.get('sampleWidth', 2)

            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)

            # Log audio file details
            duration_ms = (len(audio_data) / (sample_rate * channels * sample_width)) * 1000
            print(f"📁 Created WAV: {output_path} ({duration_ms:.1f}ms, {len(audio_data)} bytes)")

        except Exception as e:
            logger.error(f"Error writing WAV file: {e}")
            # Fallback: write raw data
            with open(output_path, 'wb') as f:
                f.write(audio_data)

    async def _analyze_audio_file(self, audio_path: str) -> Dict:
        """Analyze audio file for quality and content"""
        try:
            import wave
            import numpy as np

            with wave.open(audio_path, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(-1)
                audio_data = np.frombuffer(frames, dtype=np.int16)

                if len(audio_data) == 0:
                    return {'is_likely_silence': True, 'error': 'No audio data'}

                # Calculate audio statistics
                max_amplitude = np.max(np.abs(audio_data))
                rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
                duration = len(audio_data) / sample_rate

                # Determine if likely silence (more permissive thresholds)
                is_likely_silence = max_amplitude < 100 or rms < 15  # More permissive for Chrome extension audio

                return {
                    'sample_rate': sample_rate,
                    'duration': duration,
                    'max_amplitude': int(max_amplitude),
                    'rms': float(rms),
                    'is_likely_silence': is_likely_silence,
                    'samples': len(audio_data)
                }

        except Exception as e:
            logger.error(f"Audio analysis error: {e}")
            return {'is_likely_silence': False, 'error': str(e)}

    async def _transcribe_audio_enhanced(self, audio_path: str) -> str:
        """Enhanced Whisper transcription with better parameters"""
        try:
            # Enhanced Whisper command with optimized parameters for meeting transcription
            cmd = [
                self.whisper_executable,
                '-m', self.whisper_model_path,
                '-f', audio_path,
                '--output-txt',
                '--language', 'en',
                '--threads', '4',
                '--processors', '1',
                '--word-thold', '0.4',  # Higher word threshold for better accuracy
                '--entropy-thold', '2.8',  # Higher entropy threshold to reduce hallucinations
                '--logprob-thold', '-1.0',  # Better probability threshold
                '--no-fallback',  # Prevent fallback to less accurate models
                '--suppress-nst',  # Suppress non-speech tokens
            ]

            print(f"🤖 Running Enhanced Whisper: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            print(f"🤖 Whisper return code: {process.returncode}")
            print(f"🤖 Whisper stdout: '{stdout.decode('utf-8').strip()}'")
            if stderr:
                print(f"🤖 Whisper stderr: '{stderr.decode('utf-8').strip()}'")

            if process.returncode == 0:
                result = stdout.decode('utf-8').strip()
                if not result:
                    # Check if output file was created
                    output_file = f"{audio_path}.txt"
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            result = f.read().strip()
                        os.unlink(output_file)  # Clean up

                # Clean and enhance the output
                if result:
                    # Remove timestamp patterns and clean text
                    import re
                    result = re.sub(r'\[[\d:.\s\->]+\]\s*', '', result)
                    result = result.replace('[MUSIC PLAYING]', '')
                    result = result.replace('[BLANK_AUDIO]', '')
                    result = result.strip()

                    # Skip very short or nonsensical results
                    if len(result) < 3 or result.lower() in ['and', 'uh', 'um', 'eh', 'ah']:
                        result = '[SILENCE_DETECTED]'
                    result = result.strip()

                    if result and result != '[BLANK_AUDIO]':
                        return result
                    else:
                        return '[BLANK_AUDIO]'
                else:
                    return '[BLANK_AUDIO]'
            else:
                logger.error(f"Whisper error: {stderr.decode('utf-8')}")
                return '[WHISPER_ERROR]'

        except Exception as e:
            logger.error(f"Enhanced transcription error: {e}")
            return '[PROCESSING_ERROR]'

    async def _transcribe_audio(self, audio_path: str) -> str:
        """Legacy transcribe method - redirects to enhanced version"""
        return await self._transcribe_audio_enhanced(audio_path)

class MeetingSession:
    """Manage individual meeting session state with lazy AI initialization"""

    def __init__(self, meeting_id: str, platform: str = "unknown"):
        self.meeting_id = meeting_id
        self.platform = platform
        self.start_time = datetime.now()
        self.participants: Set[str] = set()  # Legacy: participant names only
        self.participant_data: Dict[str, Dict] = {}  # Enhanced: full participant data
        self.participant_count = 0
        self.meeting_url = ""
        self.transcript_chunks: List[Dict] = []
        self.cumulative_transcript = ""
        self._ai_processing_completed = False  # Prevent duplicate AI processing
        self.last_disconnect_time: Optional[datetime] = None  # Track when last connection disconnected

        # Initialize buffer system immediately (no AI dependency)
        self.buffer = MeetingBuffer(meeting_id)

        # Lazy AI initialization - only created when needed
        self._ai_processor = None
        self._speaker_identifier = None
        self._meeting_summarizer = None
        self._task_extractor = None
        self._batch_processor = None

    def _ensure_ai_components(self):
        """Lazy initialization of AI components"""
        if self._ai_processor is None:
            self._ai_processor = AIProcessor()
            self._speaker_identifier = SpeakerIdentifier(self._ai_processor)
            self._meeting_summarizer = MeetingSummarizer(self._ai_processor)
            self._task_extractor = TaskExtractor(self._ai_processor)
            self._batch_processor = BatchProcessor(self._ai_processor)

    @property
    def ai_processor(self):
        self._ensure_ai_components()
        return self._ai_processor

    @property
    def speaker_identifier(self):
        self._ensure_ai_components()
        return self._speaker_identifier

    @property
    def meeting_summarizer(self):
        self._ensure_ai_components()
        return self._meeting_summarizer

    @property
    def task_extractor(self):
        self._ensure_ai_components()
        return self._task_extractor

    @property
    def batch_processor(self):
        self._ensure_ai_components()
        return self._batch_processor

    def add_transcript_chunk(self, chunk: Dict):
        """Add transcription chunk to session"""
        self.transcript_chunks.append(chunk)
        if chunk.get('text'):
            self.cumulative_transcript += f" {chunk['text']}"

    def update_participants(self, participants_data: List[Dict], participant_count: int = 0):
        """Update participant data from enhanced audio chunk"""
        try:
            self.participant_count = participant_count

            # Update participant_data with full information
            for participant in participants_data:
                participant_id = participant.get('id')
                if participant_id:
                    self.participant_data[participant_id] = participant
                    # Also add to legacy participants set
                    participant_name = participant.get('name')
                    if participant_name:
                        self.participants.add(participant_name)

            logger.info(f"Updated participants for meeting {self.meeting_id}: {len(self.participant_data)} participants")

        except Exception as e:
            logger.error(f"Error updating participants: {e}")

    def get_participant_names(self) -> List[str]:
        """Get list of participant names for speaker identification context"""
        # Prefer enhanced participant data if available
        if self.participant_data:
            return [p.get('name', 'Unknown') for p in self.participant_data.values() if p.get('name')]
        # Fallback to legacy participant set
        return list(self.participants)

    def get_participant_data_objects(self) -> List[ParticipantData]:
        """Get list of ParticipantData objects for integration adapter"""
        participant_objects = []
        for participant_dict in self.participant_data.values():
            try:
                participant_obj = ParticipantData(
                    id=participant_dict.get('id', ''),
                    name=participant_dict.get('name', ''),
                    platform_id=participant_dict.get('platform_id', ''),
                    status=participant_dict.get('status', 'unknown'),
                    is_host=participant_dict.get('is_host', False),
                    join_time=participant_dict.get('join_time', ''),
                    leave_time=participant_dict.get('leave_time')
                )
                participant_objects.append(participant_obj)
            except Exception as e:
                logger.warning(f"Could not convert participant data to object: {e}")
                continue
        return participant_objects

    async def identify_speakers(self, recent_transcript: str, participant_context: Optional[List[str]] = None) -> Dict:
        """Identify speakers in recent transcript"""
        try:
            # Use the last few chunks for context
            context_text = " ".join([
                chunk.get('text', '') for chunk in self.transcript_chunks[-5:]
            ])

            result = await self.speaker_identifier.identify_speakers_advanced(
                recent_transcript,
                context=context_text,
                participant_names=participant_context if participant_context is not None else []
            )

            # Update participants list
            if 'speakers' in result:
                for speaker in result['speakers']:
                    if isinstance(speaker, dict) and 'name' in speaker:
                        self.participants.add(speaker['name'])
                    elif isinstance(speaker, str):
                        self.participants.add(speaker)

            return result

        except Exception as e:
            logger.error(f"Speaker identification error: {e}")
            return {'speakers': [], 'error': str(e)}

class WebSocketManager:
    """Manage WebSocket connections and sessions with Phase 3 session management"""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict] = {}
        self.meeting_sessions: Dict[str, MeetingSession] = {}
        self.audio_processor = AudioProcessor()
        self.audio_buffer_manager = AudioBufferManager()
        self.batch_processor = None  # Initialized when first session is created
        self.processing_locks: Dict[str, threading.Lock] = {}  # Prevent race conditions
        self.websocket_to_session: Dict[WebSocket, str] = {}  # Track websocket to session mapping
        self.saved_transcript_hashes: Set[str] = set()  # Track saved transcript hashes to prevent duplicates
        self.cleanup_tasks: Dict[str, asyncio.Task] = {}  # Track cleanup tasks for sessions
        
        # Initialize database using same factory as main app for TiDB compatibility
        self.db = self._init_database()
        
        # Force database table creation immediately
        if self.db:
            try:
                # For SQLite, force table creation by calling _init_db directly
                if hasattr(self.db, '_init_db'):
                    self.db._init_db()
                    logger.info("Database tables created successfully")
                    print(f"✅ Database tables initialized")
                else:
                    logger.warning("Database doesn't support table initialization")
            except Exception as e:
                logger.error(f"Database table creation failed: {e}")
                print(f"❌ Database table creation failed: {e}")

    def _init_database(self):
        """Initialize database using same configuration as main app"""
        try:
            # Load environment variables first
            from dotenv import load_dotenv
            load_dotenv()
            
            # Use environment-based database configuration (same as main.py)
            db = DatabaseFactory.create_from_env()
            
            db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
            logger.info(f"WebSocket server using {db_type.upper()} database")
            print(f"✅ Database initialized: {db_type.upper()}")
            return db
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            print(f"❌ Database initialization failed: {e}")
            return None
    
    async def _ensure_database_ready(self):
        """Ensure database is ready and tables are created"""
        try:
            if self.db:
                # Run health check
                is_healthy = await self.db.health_check()
                if is_healthy:
                    logger.info("Database health check passed - tables ready")
                    print(f"✅ Database health check passed")
                else:
                    logger.warning("Database health check failed")
                    print(f"⚠️ Database health check failed")
        except Exception as e:
            logger.error(f"Database readiness check failed: {e}")
            print(f"❌ Database readiness check failed: {e}")



    async def _process_timeout_buffer(self, session_id: str, buffer):
        """Process buffer due to timeout"""
        # Get or create processing lock for this session
        if session_id not in self.processing_locks:
            self.processing_locks[session_id] = threading.Lock()

        # Try to acquire lock - if already processing, skip
        if not self.processing_locks[session_id].acquire(blocking=False):
            print(f"⏰ Skipping timeout processing - session {session_id} already being processed")
            return

        try:
            if buffer and len(buffer.buffer) > 0:
                print(f"⏰ Processing timeout buffer: {session_id} ({buffer.get_duration_ms():.1f}ms)")

                # Create WAV file from buffered audio
                wav_path = buffer.create_wav_file()
                if wav_path:
                    # Process audio with Whisper
                    transcription_result = await self.audio_processor.process_audio_chunk(
                        buffer.get_buffered_audio(), {}
                    )
                    print(f"📝 Timeout result: '{transcription_result.get('text', 'EMPTY')}'")

                    # Send result to all connections for this session
                    await self._broadcast_transcription_result(session_id, transcription_result)

                    # Clean up temp file
                    os.unlink(wav_path)
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)

                # CRITICAL: Clear buffer after processing to prevent duplicates
                buffer.clear()
                print(f"🧹 Cleared timeout buffer for session {session_id}")
            else:
                print(f"⏰ Timeout buffer empty for session {session_id} - skipping")

        except Exception as e:
            logger.error(f"Error processing timeout buffer: {e}")
        finally:
            # Always release the lock
            self.processing_locks[session_id].release()

    async def _broadcast_transcription_result(self, session_id: str, transcription_result: Dict):
        """Broadcast transcription result to all connections for a session with Phase 3 session updates"""
        try:
            # Find session for duplicate checking
            session = self.meeting_sessions.get(session_id)
            if not session:
                print(f"⚠️ No session found for {session_id} - skipping broadcast")
                return

            # Check for duplicates before broadcasting
            transcript_text = transcription_result.get('text', '').strip()
            if not transcript_text or transcript_text in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]', '[PROCESSING_ERROR]', '[WHISPER_ERROR]']:
                print(f"⚠️ Skipping empty/invalid timeout transcript: '{transcript_text}'")
                return
                
            # Enhanced duplicate detection
            if hasattr(session.buffer, '_is_duplicate_transcript') and session.buffer._is_duplicate_transcript(transcript_text):
                print(f"⚠️ Skipping duplicate timeout transcript: '{transcript_text[:50]}...'")
                return
            
            # Additional check against recent transcripts in session
            if hasattr(session, 'transcript_chunks'):
                recent_texts = [chunk.get('text', '').strip().lower() for chunk in session.transcript_chunks[-3:]]
                if transcript_text.lower() in recent_texts:
                    print(f"⚠️ Skipping duplicate against recent session transcripts: '{transcript_text[:50]}...'")
                    return

            # Save timeout transcript to database immediately (with hash check)
            if self.db:
                import hashlib
                transcript_hash = hashlib.md5(f"{session_id}:{transcript_text}".encode()).hexdigest()
                if transcript_hash not in self.saved_transcript_hashes:
                    try:
                        print(f"💾 Saving timeout transcript to DB: '{transcript_text[:50]}...'")
                        await self.db.save_meeting_transcript(
                            meeting_id=session_id,
                            transcript=transcript_text,
                            timestamp=transcription_result.get('timestamp', datetime.now().isoformat())
                        )
                        self.saved_transcript_hashes.add(transcript_hash)
                        print(f"✅ Successfully saved timeout transcript to database")
                        
                        # ALWAYS add timeout transcript to vector store
                        asyncio.create_task(self._add_transcript_to_vector_store(
                            session_id, transcript_text, getattr(session, 'platform', 'unknown'), list(getattr(session, 'participants', []))
                        ))
                    except Exception as db_error:
                        print(f"❌ Failed to save timeout transcript: {db_error}")
                        logger.error(f"Failed to save timeout transcript: {db_error}")
                else:
                    print(f"⚠️ Skipping duplicate timeout transcript (hash: {transcript_hash[:8]}...)")

            # Add to recent transcripts for future deduplication
            if hasattr(session.buffer, 'recent_transcripts'):
                session.buffer.recent_transcripts.append(transcript_text.lower())
                if len(session.buffer.recent_transcripts) > getattr(session.buffer, 'max_recent_transcripts', 10):
                    session.buffer.recent_transcripts.pop(0)  # Remove oldest

            # Update session activity with transcript segment
            transcript_segment = {
                'text': transcript_text,
                'timestamp': transcription_result.get('timestamp', time.time()),
                'confidence': transcription_result.get('confidence', 0.0),
                'trigger': 'timeout'
            }

            # Find connections for this session and update activity
            target_connections = []
            for websocket, connection_info in self.active_connections.items():
                connection_session = connection_info.get('meeting_session')
                if connection_session and connection_session.meeting_id == session_id:
                    target_connections.append(websocket)
                    # Update session activity for this websocket
                    await self._update_session_activity(websocket, transcript_segment)

            # Send to all connections
            for websocket in target_connections:
                try:
                    timeout_data = WebSocketEventData.transcription_result(
                        text=transcript_text,
                        confidence=transcription_result.get('confidence', 0.0),
                        timestamp=transcription_result.get('timestamp'),
                        speaker='Unknown',
                        trigger_reason='timeout'
                    )

                    # Monitor timeout transcription events
                    monitor_event(
                        WebSocketEventTypes.TRANSCRIPTION_RESULT,
                        timeout_data,
                        source="websocket_server_timeout",
                        session_id=session_id
                    )

                    await self.send_message(websocket, {
                        'type': WebSocketEventTypes.TRANSCRIPTION_RESULT,
                        'data': timeout_data
                    })
                except Exception as e:
                    logger.error(f"Error sending timeout result to connection: {e}")

        except Exception as e:
            logger.error(f"Error broadcasting timeout result: {e}")

    async def connect(self, websocket: WebSocket, client_info: Dict):
        """Handle new WebSocket connection"""
        await websocket.accept()

        connection_info = {
            'connected_at': datetime.now(),
            'client_info': client_info,
            'meeting_session': None
        }

        self.active_connections[websocket] = connection_info
        logger.info(f"New WebSocket connection: {client_info}")

        # Send handshake acknowledgment only once
        await self.send_message(websocket, {
            'type': 'HANDSHAKE_ACK',
            'serverVersion': '1.0',
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        })

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection with Phase 3 session management"""
        if websocket in self.active_connections:
            connection_info = self.active_connections[websocket]
            session_id = self.websocket_to_session.get(websocket)
            meeting_session = connection_info.get('meeting_session')

            logger.info(f"WebSocket disconnected: {connection_info.get('client_info', {})}")

            # Handle session disconnection if session exists
            if session_id:
                disconnect_result = await session_manager.handle_disconnect(session_id)
                logger.info(f"Session disconnect handled: {disconnect_result}")

                # Remove websocket mapping
                if websocket in self.websocket_to_session:
                    del self.websocket_to_session[websocket]

            # Mark session for potential cleanup but don't remove immediately
            if meeting_session:
                meeting_id = meeting_session.meeting_id
                # Check if any other active connections are using this meeting session
                other_connections_using_session = any(
                    conn_info.get('meeting_session') and 
                    conn_info['meeting_session'].meeting_id == meeting_id
                    for ws, conn_info in self.active_connections.items() 
                    if ws != websocket
                )
                
                if not other_connections_using_session:
                    # Mark session as disconnected but keep it alive for 5 minutes
                    meeting_session.last_disconnect_time = datetime.now()
                    logger.info(f"Marked meeting session for cleanup in 5 minutes: {meeting_id}")
                    
                    # Schedule cleanup task
                    if meeting_id not in self.cleanup_tasks:
                        cleanup_task = asyncio.create_task(self._schedule_session_cleanup(meeting_id))
                        self.cleanup_tasks[meeting_id] = cleanup_task

            del self.active_connections[websocket]
    
    async def _schedule_session_cleanup(self, meeting_id: str):
        """Schedule session cleanup after 5 minute timeout"""
        try:
            # Wait 5 minutes
            await asyncio.sleep(300)  # 5 minutes
            
            # Check if session still exists and has no active connections
            if meeting_id in self.meeting_sessions:
                session = self.meeting_sessions[meeting_id]
                
                # Check if any connections have reconnected
                has_active_connections = any(
                    conn_info.get('meeting_session') and 
                    conn_info['meeting_session'].meeting_id == meeting_id
                    for conn_info in self.active_connections.values()
                )
                
                if not has_active_connections and session.last_disconnect_time:
                    # No reconnection happened, proceed with cleanup and pipeline
                    logger.info(f"Cleaning up session after timeout: {meeting_id}")
                    
                    # Trigger final processing pipeline
                    await self._finalize_session(session)
                    
                    # Clean up session and buffers
                    del self.meeting_sessions[meeting_id]
                    self.audio_buffer_manager.remove_buffer(meeting_id)
                    
                    logger.info(f"Session cleanup completed: {meeting_id}")
                else:
                    logger.info(f"Session reconnected, canceling cleanup: {meeting_id}")
            
            # Remove cleanup task
            if meeting_id in self.cleanup_tasks:
                del self.cleanup_tasks[meeting_id]
                
        except asyncio.CancelledError:
            logger.info(f"Cleanup task cancelled for session: {meeting_id}")
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
    
    async def _finalize_session(self, session: MeetingSession):
        """Finalize session by running the processing pipeline"""
        try:
            logger.info(f"Finalizing session: {session.meeting_id}")
            
            # Process any remaining buffered audio
            audio_buffer = self.audio_buffer_manager.get_buffer(session.meeting_id)
            if len(audio_buffer.buffer) > 0:
                logger.info(f"Processing final buffered audio for {session.meeting_id}")
                wav_path = audio_buffer.create_wav_file()
                if wav_path:
                    try:
                        final_result = await self.audio_processor.process_audio_chunk(
                            audio_buffer.get_buffered_audio(), {}
                        )
                        if final_result.get('text'):
                            session.add_transcript_chunk(final_result)
                            
                            # Save final transcript to database
                            final_text = final_result['text'].strip()
                            if self.db and final_text:
                                await self.db.save_meeting_transcript(
                                    meeting_id=session.meeting_id,
                                    transcript=final_text,
                                    timestamp=final_result.get('timestamp', datetime.now().isoformat())
                                )
                                
                                # ALWAYS add final transcript to vector store
                                await self._add_transcript_to_vector_store(
                                    session.meeting_id, final_text, session.platform, list(session.participants)
                                )
                        os.unlink(wav_path)
                    except Exception as e:
                        logger.error(f"Error processing final audio: {e}")
                        if os.path.exists(wav_path):
                            os.unlink(wav_path)
            
            # Generate meeting summary if we have transcript content
            if session.cumulative_transcript.strip():
                await self._generate_meeting_summary_standalone(session)
            
        except Exception as e:
            logger.error(f"Error finalizing session {session.meeting_id}: {e}")
    
    async def _generate_meeting_summary_standalone(self, session: MeetingSession):
        """Generate meeting summary without WebSocket connection"""
        try:
            logger.info(f"Generating summary for disconnected session: {session.meeting_id}")
            
            # Save full transcript to database
            if self.db and session.cumulative_transcript.strip():
                await self.db.save_meeting_transcript(
                    meeting_id=session.meeting_id,
                    transcript=session.cumulative_transcript,
                    timestamp=datetime.now().isoformat()
                )
            
            # Skip AI processing if already completed
            if session._ai_processing_completed:
                return
            
            # Generate AI summary and tasks
            try:
                summary = await session.meeting_summarizer.generate_comprehensive_summary(
                    session.cumulative_transcript,
                    {
                        'meeting_id': session.meeting_id,
                        'platform': session.platform,
                        'participants': list(session.participants)
                    }
                )
                
                tasks = await session.task_extractor.extract_comprehensive_tasks(
                    session.cumulative_transcript,
                    {'participants': list(session.participants)}
                )
                
                # Save tasks to database
                if self.db and tasks.get('tasks'):
                    for task in tasks['tasks']:
                        task_id = f"task-{uuid.uuid4()}"
                        await self.db.save_task(
                            task_id=task_id,
                            meeting_id=session.meeting_id,
                            title=task.get('title', 'Untitled Task'),
                            description=task.get('description', ''),
                            assignee=task.get('assignee', 'Unassigned'),
                            priority=task.get('priority', 'medium'),
                            status='pending'
                        )
                
                # Populate vector store
                await self._populate_vector_store(session.meeting_id, summary, tasks)
                
                # Mark as completed
                session._ai_processing_completed = True
                
                logger.info(f"Summary generation completed for {session.meeting_id}")
                
            except Exception as ai_error:
                logger.warning(f"AI processing failed for {session.meeting_id}: {ai_error}")
                
        except Exception as e:
            logger.error(f"Error generating summary for {session.meeting_id}: {e}")

    async def send_message(self, websocket: WebSocket, message: Dict):
        """Send message to WebSocket client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast_to_meeting(self, meeting_id: str, message: Dict):
        """Broadcast message to all clients in a meeting"""
        for websocket, connection_info in self.active_connections.items():
            session = connection_info.get('meeting_session')
            if session and session.meeting_id == meeting_id:
                await self.send_message(websocket, message)

    async def handle_handshake(self, websocket: WebSocket, message: Dict):
        """Handle handshake message"""
        await self.send_message(websocket, {
            'type': 'HANDSHAKE_ACK',
            'serverVersion': '1.0',
            'status': 'ready'
        })

    async def handle_audio_chunk(self, websocket: WebSocket, message: Dict):
        """Handle incoming audio chunk with Phase 3 session management"""
        try:
            audio_data = message.get('data')
            timestamp = message.get('timestamp')
            message_type = message.get('type')
            chunk_id = message.get('chunkId')  # For buffer flush tracking
            is_flushing = message.get('isFlushing', False)

            # Handle both basic and enhanced audio chunk formats
            if message_type == 'AUDIO_CHUNK_ENHANCED':
                # Enhanced format with participant data
                platform = message.get('platform', 'unknown')
                meeting_url = message.get('meetingUrl', 'unknown')
                participants = message.get('participants', [])
                participant_count = message.get('participant_count', 0)

                # Only register session if not already registered for this websocket
                if websocket not in self.websocket_to_session:
                    await self._handle_session_registration(websocket, message, participants)
                metadata = message.get('metadata', {})
            else:
                # Legacy format
                metadata = message.get('metadata', {})
                platform = metadata.get('platform', 'unknown')
                meeting_url = metadata.get('meetingUrl', 'unknown')
                participants = []
                participant_count = 0

            if not audio_data:
                logger.warning("Received empty audio chunk")
                return

            # Get or create meeting session - use consistent ID generation
            meeting_id = f"{platform}_{hash(meeting_url) % 1000000}"
            
            # Check if session already exists with different ID format
            existing_session = None
            for session in self.meeting_sessions.values():
                if session.meeting_url == meeting_url and session.platform == platform:
                    existing_session = session
                    meeting_id = session.meeting_id  # Use existing ID
                    break

            if meeting_id not in self.meeting_sessions and not existing_session:
                self.meeting_sessions[meeting_id] = MeetingSession(meeting_id, platform)
                logger.info(f"Created new meeting session: {meeting_id}")
                
                # Save meeting to database
                if self.db:
                    try:
                        await self.db.save_meeting(meeting_id, f"Meeting {platform} {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        logger.info(f"💾 Saved meeting to database: {meeting_id}")
                    except Exception as db_error:
                        logger.error(f"Failed to save meeting to database: {db_error}")
            elif existing_session:
                logger.info(f"Using existing meeting session: {meeting_id}")

            session = existing_session or self.meeting_sessions[meeting_id]
            session.meeting_url = meeting_url

            # Update participant data if available (enhanced format)
            if participants and message_type == 'AUDIO_CHUNK_ENHANCED':
                session.update_participants(participants, participant_count)
                logger.debug(f"Updated participant data: {len(participants)} participants")
                
                # Sync participants to chatbot (non-blocking)
                participant_names = [p.get('name', 'Unknown') for p in participants if p.get('name')]
                if participant_names:
                    asyncio.create_task(chatbot_sync.add_meeting_participants(meeting_id, participant_names))
            
            # Clear disconnect time and cancel cleanup if reconnected
            if hasattr(session, 'last_disconnect_time') and session.last_disconnect_time:
                session.last_disconnect_time = None
                if meeting_id in self.cleanup_tasks:
                    self.cleanup_tasks[meeting_id].cancel()
                    del self.cleanup_tasks[meeting_id]
                    logger.info(f"Cancelled cleanup task for reconnected session: {meeting_id}")

            self.active_connections[websocket]['meeting_session'] = session

            # Log audio chunk (if logger available)
            if session.buffer.logger:
                session.buffer.logger.log_audio_chunk({
                    "audio_data": audio_data,
                    "participant": participants[0].get('name') if participants else 'Unknown',
                    "chunk_id": len(session.transcript_chunks),
                    "meeting_id": meeting_id
                })

            # Convert base64 audio data to bytes if needed
            if isinstance(audio_data, str):
                import base64
                audio_bytes = base64.b64decode(audio_data)
                print(f"🎵 Decoded audio: {len(audio_bytes)} bytes from base64")
            else:
                audio_bytes = bytes(audio_data)
                print(f"🎵 Raw audio: {len(audio_bytes)} bytes")

            # Add to audio buffer and check if ready for processing
            audio_buffer = self.audio_buffer_manager.get_buffer(meeting_id)
            ready_for_processing = audio_buffer.add_chunk(audio_bytes, timestamp, metadata)

            transcription_result = {'text': '', 'confidence': 0.0, 'timestamp': datetime.now().isoformat()}

            # Calculate current samples for later use
            bytes_per_sample = audio_buffer.sample_width * audio_buffer.channels
            current_samples = len(audio_buffer.buffer) // bytes_per_sample

            if ready_for_processing:
                # Check if this is buffer full or timeout
                buffer_full = current_samples >= audio_buffer.target_samples

                if buffer_full:
                    # Get or create processing lock for this session
                    if meeting_id not in self.processing_locks:
                        self.processing_locks[meeting_id] = threading.Lock()

                    # Try to acquire lock - if already processing, skip
                    if not self.processing_locks[meeting_id].acquire(blocking=False):
                        print(f"🎤 Skipping regular processing - session {meeting_id} already being processed")
                        return

                    try:
                        print(f"🎤 Buffer full ({audio_buffer.get_duration_ms():.1f}ms) - processing with Whisper...")

                        # Create WAV file from buffered audio
                        wav_path = audio_buffer.create_wav_file()
                        if wav_path:
                            try:
                                # Process combined audio with Whisper
                                transcription_result = await self.audio_processor.process_audio_chunk(
                                    audio_buffer.get_buffered_audio(), metadata
                                )
                                print(f"📝 Whisper result: '{transcription_result.get('text', 'EMPTY')}'")

                                # Clean up temp file
                                os.unlink(wav_path)

                            except Exception as e:
                                print(f"❌ Whisper processing failed: {e}")
                                if os.path.exists(wav_path):
                                    os.unlink(wav_path)

                            # Clear buffer after processing
                            audio_buffer.clear()
                        else:
                            print(f"❌ Failed to create WAV file from buffer")
                    finally:
                        # Always release the lock
                        self.processing_locks[meeting_id].release()
                else:
                    # Timeout scenario - don't process here, let background task handle it
                    print(f"⏰ Timeout ready - leaving for background task")
                    ready_for_processing = False

            if not ready_for_processing:
                print(f"🔄 Buffering audio chunk ({audio_buffer.get_duration_ms():.1f}ms/{audio_buffer.target_duration_ms}ms)")
                # Still save any transcript we got to database before early return
                transcript_text = transcription_result.get('text', '').strip()
                if self.db and transcript_text and transcript_text not in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]', '[PROCESSING_ERROR]', '[WHISPER_ERROR]']:
                    try:
                        print(f"💾 Saving buffered transcript to DB: '{transcript_text[:50]}...'")
                        await self.db.save_meeting_transcript(
                            meeting_id=session.meeting_id,
                            transcript=transcript_text,
                            timestamp=transcription_result.get('timestamp', datetime.now().isoformat())
                        )
                        print(f"✅ Successfully saved buffered transcript to database")
                    except Exception as db_error:
                        print(f"❌ Failed to save buffered transcript: {db_error}")
                        logger.error(f"Failed to save buffered transcript: {db_error}")
                # Early return - let background task handle timeout processing
                return
            
            print(f"🎤 Ready for processing - buffer full: {ready_for_processing}")

            # Only continue if we actually processed something (buffer was full, not timeout)
            print(f"🎯 Processing result: '{transcription_result.get('text', 'EMPTY')[:50]}...'")
            
            # Log transcript chunk (if logger available)
            if transcription_result.get('text') and session.buffer.logger:
                session.buffer.logger.log_transcript_chunk(
                    transcription_result['text'],
                    participants[0].get('name') if participants else 'Unknown'
                )

            # Add to session
            session.add_transcript_chunk(transcription_result)
            print(f"📝 Added to session: '{transcription_result.get('text', 'EMPTY')[:50]}...'")
            
            # Save transcript chunk to database immediately (with hash check)
            transcript_text = transcription_result.get('text', '').strip()
            if self.db and transcript_text and transcript_text not in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]', '[PROCESSING_ERROR]', '[WHISPER_ERROR]']:
                import hashlib
                transcript_hash = hashlib.md5(f"{session.meeting_id}:{transcript_text}".encode()).hexdigest()
                if transcript_hash not in self.saved_transcript_hashes:
                    try:
                        print(f"💾 Saving transcript to DB: '{transcript_text[:50]}...'")
                        await self.db.save_meeting_transcript(
                            meeting_id=session.meeting_id,
                            transcript=transcript_text,
                            timestamp=transcription_result.get('timestamp', datetime.now().isoformat())
                        )
                        self.saved_transcript_hashes.add(transcript_hash)
                        print(f"✅ Successfully saved transcript chunk to database")
                        
                        # Sync to chatbot for real-time context (non-blocking)
                        speaker_name = participants[0].get('name', 'Unknown') if participants else 'Unknown'
                        asyncio.create_task(chatbot_sync.add_live_transcript_chunk(
                            meeting_id, transcript_text, speaker_name
                        ))
                        
                        # ALWAYS add transcript to vector store immediately (not just after AI processing)
                        asyncio.create_task(self._add_transcript_to_vector_store(
                            session.meeting_id, transcript_text, session.platform, list(session.participants)
                        ))
                        
                    except Exception as db_error:
                        print(f"❌ Failed to save transcript chunk: {db_error}")
                        logger.error(f"Failed to save transcript chunk: {db_error}")
                else:
                    print(f"⚠️ Skipping duplicate transcript (hash: {transcript_hash[:8]}...)")
            else:
                print(f"⚠️ Skipping DB save - db: {self.db is not None}, text: '{transcript_text[:30]}...'")

            # Add to buffer (no immediate AI processing)
            if transcript_text:
                # Check for duplicate transcript before processing
                # Skip if duplicate or empty
                if session.buffer._is_duplicate_transcript(transcript_text):
                    print(f"⚠️ Skipping duplicate transcript: '{transcript_text[:50]}...'")
                    transcription_result['text'] = ''  # Clear duplicate
                    return  # Skip processing this duplicate
                
                print(f"🔄 Processing transcript: '{transcript_text[:50]}...'")

                # Add to recent transcripts for future deduplication
                session.buffer.recent_transcripts.append(transcript_text.lower())
                if len(session.buffer.recent_transcripts) > session.buffer.max_recent_transcripts:
                    session.buffer.recent_transcripts.pop(0)  # Remove oldest

                # Create transcript chunk for buffer
                chunk = TranscriptChunk(
                    timestamp_start=len(session.transcript_chunks) * 5.0,  # Estimate based on chunk index
                    timestamp_end=(len(session.transcript_chunks) + 1) * 5.0,
                    raw_text=transcript_text,
                    participants_present=participants,
                    confidence=transcription_result.get('confidence', 0.0),
                    chunk_index=len(session.transcript_chunks),
                    speaker=participants[0].get('name', 'Unknown') if participants else 'Unknown'
                )

                session.buffer.add_chunk(chunk)

                # Calculate speaker information
                speaker_name = 'Unknown'
                if participants:
                    speaker_name = participants[0].get('name', 'Unknown')
                elif session.participant_data:
                    # Use the most recent speaker or first participant
                    speaker_name = list(session.participant_data.values())[0].get('name', 'Unknown')

                # Generate response with chunk ID for tracking
                chunk_id = f"chunk_{int(time.time() * 1000)}_{meeting_id}"
                is_flushing = ready_for_processing

                response_data = {
                    'text': transcription_result.get('text', ''),
                    'confidence': transcription_result.get('confidence', 0.0),
                    'timestamp': transcription_result.get('timestamp'),
                    'speaker': speaker_name,
                    'chunkId': chunk_id,  # Include chunk ID for tracking
                    'isFlushing': is_flushing
                }

                # Prepare transcription data
                transcription_data = WebSocketEventData.transcription_result(
                    text=response_data.get('text', ''),
                    confidence=response_data.get('confidence', 0.0),
                    timestamp=response_data.get('timestamp'),
                    speaker=response_data.get('speaker', 'Unknown'),
                    chunk_id=response_data.get('chunkId'),
                    is_final=False,
                    # Extended data for Chrome extension compatibility
                    speakers=transcription_result.get('speakers', []),
                    meetingId=meeting_id,
                    speaker_id=self._get_speaker_id_from_name(
                        response_data.get('speaker', 'Unknown'),
                        session.participant_data
                    ) if session.participant_data else None,
                    speaker_confidence=transcription_result.get('speaker_confidence', 0.0),
                    isFlushing=response_data.get('isFlushing', False)
                )

                # Monitor the event for duplicates and validation
                monitoring_result = monitor_event(
                    WebSocketEventTypes.TRANSCRIPTION_RESULT,
                    transcription_data,
                    source="websocket_server",
                    session_id=meeting_id
                )

                # Log monitoring results if issues detected
                if monitoring_result.get('is_duplicate') or monitoring_result.get('is_deprecated') or monitoring_result.get('validation_errors'):
                    logger.warning(f"Event monitoring detected issues: {monitoring_result.get('recommendations', [])}")

                # Send standardized TRANSCRIPTION_RESULT event (no more duplicates)
                await self.send_message(websocket, {
                    'type': WebSocketEventTypes.TRANSCRIPTION_RESULT,
                    'data': transcription_data
                })

                # Broadcast to other clients in the same meeting (only if we have transcription)
                meeting_update_data = {
                    'meetingId': meeting_id,
                    'participants': list(session.participants),
                    'latestTranscript': transcription_result.get('text', ''),
                    'timestamp': datetime.now().isoformat()
                }

                # Include enhanced participant data if available
                if session.participant_data:
                    meeting_update_data['participant_data'] = list(session.participant_data.values())
                    meeting_update_data['participant_count'] = session.participant_count
                    meeting_update_data['platform'] = session.platform

                await self.broadcast_to_meeting(meeting_id, {
                    'type': 'MEETING_UPDATE',
                    'data': meeting_update_data
                })

            logger.info(f"Processed audio chunk for meeting {meeting_id}: {len(transcription_result.get('text', ''))} chars")

        except Exception as e:
            logger.error(f"Error handling audio chunk: {e}")
            # Send error but continue processing
            await self.send_message(websocket, {
                'type': 'ERROR',
                'error': f"Audio processing failed: {str(e)}",
                'recoverable': True
            })

    async def handle_meeting_event(self, websocket: WebSocket, message: Dict):
        """Handle meeting events (start, end, participant changes)"""
        event_type = message.get('eventType')
        data = message.get('data', {})

        logger.info(f"Meeting event: {event_type}")
        print(f"📋 Meeting event received: {event_type} with data: {data}")

        # Handle different event types
        if event_type == 'meeting_started':
            await self.send_message(websocket, {
                'type': 'MEETING_EVENT_ACK',
                'eventType': event_type,
                'status': 'acknowledged'
            })
        elif event_type in ['ended', 'meeting_ended']:
            print(f"\n🏁 Meeting ended - starting final processing...")

            # Check if this is a buffer flush completion signal (support both formats)
            buffer_flush_complete = data.get('bufferFlushComplete', data.get('buffer_flush_complete', False))

            if not buffer_flush_complete:
                # Legacy behavior or partial end signal - wait for buffer flush
                print("⏳ Meeting end signal received - waiting for buffer flush completion...")
                print(f"📋 Data received: {data}")
                await self.send_message(websocket, {
                    'type': 'PROCESSING_STATUS',
                    'data': {
                        'message': 'Waiting for audio buffer flush completion...',
                        'stage': 'buffer_flush_wait'
                    }
                })
                return

            # Send initial processing status
            await self.send_message(websocket, {
                'type': 'PROCESSING_STATUS',
                'data': {
                    'message': 'Starting final processing...',
                    'stage': 'initialization'
                }
            })

            # Process final summary if we have a session
            connection_info = self.active_connections.get(websocket)
            if connection_info and connection_info.get('meeting_session'):
                session = connection_info['meeting_session']
                print(f"📋 Processing meeting: {session.meeting_id}")
                print(f"👥 Participants: {', '.join(session.participants)}")

                # Process any remaining buffered audio
                audio_buffer = self.audio_buffer_manager.get_buffer(session.meeting_id)
                if len(audio_buffer.buffer) > 0:
                    await self.send_message(websocket, {
                        'type': 'PROCESSING_STATUS',
                        'data': {
                            'message': f'Processing final audio ({audio_buffer.get_duration_ms():.1f}ms)...',
                            'stage': 'final_audio'
                        }
                    })

                    print(f"🎵 Processing final buffered audio ({audio_buffer.get_duration_ms():.1f}ms)...")
                    wav_path = audio_buffer.create_wav_file()
                    if wav_path:
                        try:
                            final_result = await self.audio_processor.process_audio_chunk(
                                audio_buffer.get_buffered_audio(), {}
                            )
                            if final_result.get('text'):
                                session.add_transcript_chunk(final_result)
                                print(f"✅ Final audio processed: '{final_result['text'][:50]}...'")

                                # Save final transcript to database
                                final_text = final_result['text'].strip()
                                if self.db and final_text and final_text not in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]', '[PROCESSING_ERROR]', '[WHISPER_ERROR]']:
                                    try:
                                        print(f"💾 Saving final transcript to DB: '{final_text[:50]}...'")
                                        await self.db.save_meeting_transcript(
                                            meeting_id=session.meeting_id,
                                            transcript=final_text,
                                            timestamp=final_result.get('timestamp', datetime.now().isoformat())
                                        )
                                        print(f"✅ Successfully saved final transcript to database")
                                        
                                        # ALWAYS add final transcript to vector store
                                        asyncio.create_task(self._add_transcript_to_vector_store(
                                            session.meeting_id, final_text, session.platform, list(session.participants)
                                        ))
                                    except Exception as db_error:
                                        print(f"❌ Failed to save final transcript: {db_error}")
                                        logger.error(f"Failed to save final transcript: {db_error}")

                                final_transcription_data = WebSocketEventData.transcription_result(
                                    text=final_result['text'],
                                    timestamp=final_result.get('timestamp', datetime.now().isoformat()),
                                    speaker='Unknown',
                                    confidence=final_result.get('confidence', 0.0),
                                    is_final=True
                                )

                                # Monitor final transcription event
                                monitor_event(
                                    WebSocketEventTypes.TRANSCRIPTION_RESULT,
                                    final_transcription_data,
                                    source="websocket_server_final",
                                    session_id=meeting_id
                                )

                                # Send transcription result with processing complete flag
                                await self.send_message(websocket, {
                                    'type': WebSocketEventTypes.TRANSCRIPTION_RESULT,
                                    'data': final_transcription_data
                                })
                            os.unlink(wav_path)
                        except Exception as e:
                            print(f"❌ Final audio processing failed: {e}")
                            if os.path.exists(wav_path):
                                os.unlink(wav_path)

                # Send processing status before summary generation
                await self.send_message(websocket, {
                    'type': 'PROCESSING_STATUS',
                    'data': {
                        'message': 'Generating meeting summary and tasks...',
                        'stage': 'summary_generation'
                    }
                })

                await self._generate_meeting_summary(websocket, session)

                # Send completion signal
                await self.send_message(websocket, {
                    'type': 'PROCESSING_COMPLETE',
                    'data': {
                        'message': 'Meeting processing completed',
                        'total_transcripts': len(session.transcript_chunks),
                        'meeting_id': session.meeting_id,
                        'buffer_flush_confirmed': True
                    }
                })

                # Clean up audio buffer
                self.audio_buffer_manager.remove_buffer(session.meeting_id)
                print(f"🧹 Cleaned up audio buffer for {session.meeting_id}")
            else:
                print(f"⚠️ No active meeting session found")
                # Send completion even if no session
                await self.send_message(websocket, {
                    'type': 'PROCESSING_COMPLETE',
                    'data': {
                        'message': 'No active session - processing completed',
                        'total_transcripts': 0,
                        'buffer_flush_confirmed': True
                    }
                })
            print(f"✅ Meeting end processing completed!")

    async def _add_transcript_to_vector_store(self, meeting_id: str, transcript_text: str, platform: str = "unknown", participants: List[str] = None):
        """Immediately add transcript to vector store (called for every transcript chunk)"""
        try:
            import httpx
            import os
            
            # Get chatbot URL from environment
            chatbot_url = os.getenv('CHATBOT_URL', 'http://127.0.0.1:8001')
            knowledge_endpoint = f"{chatbot_url}/knowledge/add"
            
            # Skip if chatbot URL is disabled or transcript too short
            if chatbot_url.lower() in ['none', 'disabled', ''] or len(transcript_text.strip()) < 10:
                return
            
            # Create enhanced transcript content with context
            participants_str = ', '.join(participants) if participants else 'Unknown'
            meeting_date = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            content = f"Meeting {meeting_id} transcript ({platform}) on {meeting_date} with participants {participants_str}: {transcript_text}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    knowledge_endpoint,
                    json={
                        "content": content,
                        "metadata": {
                            "type": "meeting_transcript",
                            "meeting_id": meeting_id,
                            "category": "transcript",
                            "platform": platform,
                            "date": meeting_date,
                            "participants": participants or []
                        }
                    }
                )
            
            print(f"✅ Added transcript chunk to vector store: '{transcript_text[:50]}...'")
            
        except Exception as e:
            # Non-critical - don't break the main flow
            logger.debug(f"Failed to add transcript to vector store: {e}")
    
    async def _populate_vector_store(self, meeting_id: str, summary: dict, tasks: dict):
        """Add meeting data to vector store for AI chatbot context"""
        try:
            import httpx
            import os
            
            # Get chatbot URL from environment (configurable for deployment)
            chatbot_url = os.getenv('CHATBOT_URL', 'http://127.0.0.1:8001')
            knowledge_endpoint = f"{chatbot_url}/knowledge/add"
            
            # Skip if chatbot URL is disabled
            if chatbot_url.lower() in ['none', 'disabled', '']:
                print(f"⚠️ Chatbot integration disabled - skipping vector store population")
                return
            
            # Add comprehensive meeting data to knowledge base
            
            # 1. Meeting summary with full context
            summary_text = summary.get('summary', '')
            if summary_text:
                # Enhanced meeting summary with participants and platform
                participants_list = ', '.join(session.participants) if hasattr(session, 'participants') else 'Unknown'
                meeting_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                summary_content = f"""Meeting {meeting_id} ({session.platform if hasattr(session, 'platform') else 'Unknown'}) on {meeting_date}:
Participants: {participants_list}
Summary: {summary_text}
Key Points: {', '.join(summary.get('key_points', []))}"""
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        knowledge_endpoint,
                        json={
                            "content": summary_content,
                            "metadata": {
                                "type": "meeting_summary",
                                "meeting_id": meeting_id,
                                "category": "meeting",
                                "platform": getattr(session, 'platform', 'unknown'),
                                "date": meeting_date,
                                "participants": list(getattr(session, 'participants', []))
                            }
                        },
                        timeout=10.0
                    )
            
            # 2. Add full meeting summary transcript (comprehensive version)
            if hasattr(session, 'cumulative_transcript') and session.cumulative_transcript.strip():
                transcript_content = f"Complete meeting summary for {meeting_id}: {session.cumulative_transcript}"
                async with httpx.AsyncClient() as client:
                    await client.post(
                        knowledge_endpoint,
                        json={
                            "content": transcript_content,
                            "metadata": {
                                "type": "meeting_summary_transcript",
                                "meeting_id": meeting_id,
                                "category": "summary"
                            }
                        },
                        timeout=10.0
                    )
            
            # 3. Add tasks with enhanced context
            for i, task in enumerate(tasks.get('tasks', [])):
                task_content = f"""Task #{i+1} from meeting {meeting_id}:
Title: {task.get('title', 'Untitled')}
Description: {task.get('description', 'No description')}
Assigned to: {task.get('assignee', 'Unassigned')}
Priority: {task.get('priority', 'medium')}
Status: {task.get('status', 'pending')}
Meeting Context: {summary.get('summary', '')[:200]}..."""
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        knowledge_endpoint,
                        json={
                            "content": task_content,
                            "metadata": {
                                "type": "task",
                                "meeting_id": meeting_id,
                                "category": "task",
                                "assignee": task.get('assignee', ''),
                                "priority": task.get('priority', 'medium'),
                                "status": task.get('status', 'pending'),
                                "task_index": i + 1
                            }
                        },
                        timeout=10.0
                    )
            
            print(f"✅ Added meeting {meeting_id} data to vector store at {chatbot_url}")
        except Exception as e:
            print(f"❌ Failed to populate vector store: {e}")
    
    async def _generate_meeting_summary(self, websocket: WebSocket, session: MeetingSession):
        """Generate and send meeting summary (only if AI is available)"""
        try:
            print(f"🎯 Starting meeting summary generation for {session.meeting_id}")

            print(f"📝 Session transcript chunks: {len(session.transcript_chunks)}")
            print(f"📝 Cumulative transcript length: {len(session.cumulative_transcript)} characters")
            print(f"📝 Transcript preview: '{session.cumulative_transcript[:200]}...'")
            
            if not session.cumulative_transcript.strip():
                print(f"⚠️ No transcript content available - skipping summary")
                logger.warning("No transcript available for summary")
                return

            print(f"📝 Transcript ready: {len(session.cumulative_transcript)} characters")

            # Save full transcript to database before AI processing
            if self.db and session.cumulative_transcript.strip():
                try:
                    await self.db.save_meeting_transcript(
                        meeting_id=session.meeting_id,
                        transcript=session.cumulative_transcript,
                        timestamp=datetime.now().isoformat(),
                        summary="",
                        action_items="",
                        key_points=""
                    )
                    logger.info(f"💾 Saved full transcript to database before AI processing: {len(session.cumulative_transcript)} chars")
                except Exception as db_error:
                    logger.error(f"Failed to save full transcript: {db_error}")

            # Check if AI processing already completed to prevent duplicates
            if session._ai_processing_completed:
                print(f"⚠️ AI processing already completed for {session.meeting_id} - skipping duplicate")
                return

            # Try to generate AI summary and tasks (may fail if no API key)
            summary = {}
            tasks = {}

            try:
                print(f"🤖 Starting AI processing...")

                # Generate comprehensive summary
                print(f"📋 Generating meeting summary...")
                summary = await session.meeting_summarizer.generate_comprehensive_summary(
                    session.cumulative_transcript,
                    {
                        'meeting_id': session.meeting_id,
                        'platform': session.platform,
                        'participants': list(session.participants),
                        'duration': str(datetime.now() - session.start_time)
                    }
                )
                print(f"✅ Summary generated: {len(summary.get('summary', ''))} characters")

                # Extract tasks
                print(f"📋 Extracting action items and tasks...")
                tasks = await session.task_extractor.extract_comprehensive_tasks(
                    session.cumulative_transcript,
                    {'participants': list(session.participants)}
                )
                task_count = len(tasks.get('tasks', []))
                print(f"✅ Tasks extracted: {task_count} action items found")
                
                # Save tasks to database
                if self.db and tasks.get('tasks'):
                    for task in tasks['tasks']:
                        task_id = f"task-{uuid.uuid4()}"
                        await self.db.save_task(
                            task_id=task_id,
                            meeting_id=session.meeting_id,
                            title=task.get('title', 'Untitled Task'),
                            description=task.get('description', ''),
                            assignee=task.get('assignee', 'Unassigned'),
                            priority=task.get('priority', 'medium'),
                            status='pending'
                        )
                    print(f"💾 Saved {len(tasks['tasks'])} tasks to database")
                    
                    # Add meeting data to vector store for AI chatbot
                    await self._populate_vector_store(session.meeting_id, summary, tasks)

                print(f"🎉 AI processing completed successfully!")
                logger.info(f"AI processing completed for meeting {session.meeting_id}")
                
                # Mark AI processing as completed to prevent duplicates
                session._ai_processing_completed = True

            except Exception as ai_error:
                print(f"⚠️ AI processing failed: {str(ai_error)}")
                print(f"📝 Creating basic summary without AI...")
                logger.warning(f"AI processing failed (continuing without AI): {ai_error}")
                # Create basic summary without AI
                summary = {
                    'summary': f"Meeting transcript with {len(session.transcript_chunks)} segments",
                    'key_points': ['Transcript available for review'],
                    'participants': list(session.participants)
                }
                tasks = {'tasks': []}
                print(f"✅ Basic summary created")

            # Notify integration systems (only if tasks were extracted)
            task_count = len(tasks.get('tasks', []))
            if task_count > 0:
                try:
                    print(f"\n🔗 Starting integration processing...")
                    print(f"📋 Creating {task_count} tasks in external systems...")

                    participant_objects = session.get_participant_data_objects()

                    # Add pipeline logger to meeting context for integration logging
                    meeting_context_with_logger = {
                        'meeting_id': session.meeting_id,
                        'platform': session.platform,
                        'participants': list(session.participants),
                        'summary': summary,
                        'pipeline_logger': session.buffer.logger
                    }

                    await notify_meeting_processed(
                        meeting_id=session.meeting_id,
                        meeting_title=f"Meeting {session.meeting_id}",
                        platform=session.platform,
                        participants=participant_objects,
                        participant_count=session.participant_count,
                        transcript=session.cumulative_transcript,
                        summary_data=summary,
                        tasks_data=tasks,
                        speakers_data=[],
                        meeting_context=meeting_context_with_logger
                    )

                    print(f"✅ Integration processing completed!")
                    print(f"📋 Tasks created in: Notion, Slack, and other configured systems")
                    logger.info(f"Notified integration systems for meeting {session.meeting_id}")

                except Exception as e:
                    print(f"❌ Integration processing failed: {str(e)}")
                    logger.warning(f"Failed to notify integration systems: {e}")
            else:
                print(f"ℹ️ No tasks found - skipping integration processing")

            # Always log pipeline summary
            try:
                session.buffer.logger.log_pipeline_summary({
                    "meeting_id": session.meeting_id,
                    "platform": session.platform,
                    "total_chunks": len(session.transcript_chunks),
                    "participants": list(session.participants),
                    "summary_length": len(summary.get('summary', '')),
                    "tasks_extracted": len(tasks.get('tasks', [])),
                    "duration": str(datetime.now() - session.start_time),
                    "ai_processing": bool(tasks.get('tasks'))
                })
                logger.info(f"Pipeline logs saved to: {session.buffer.logger.get_log_directory()}")
            except Exception as e:
                logger.warning(f"Failed to log pipeline summary: {e}")

            # Send final summary
            await self.send_message(websocket, {
                'type': 'MEETING_SUMMARY',
                'data': {
                    'meetingId': session.meeting_id,
                    'summary': summary,
                    'tasks': tasks,
                    'participants': list(session.participants),
                    'totalChunks': len(session.transcript_chunks),
                    'duration': str(datetime.now() - session.start_time),
                    'generatedAt': datetime.now().isoformat()
                }
            })

            logger.info(f"Generated meeting summary for {session.meeting_id}")

        except Exception as e:
            print(f"❌ Meeting summary generation failed: {str(e)}")
            logger.error(f"Error generating meeting summary: {e}")

    def _get_speaker_id_from_name(self, speaker_name: str, participant_data: Dict[str, Dict]) -> Optional[str]:
        """Map speaker name to participant ID from enhanced participant data"""
        try:
            for participant_id, participant in participant_data.items():
                if participant.get('name', '').lower() == speaker_name.lower():
                    return participant_id
            return None
        except Exception as e:
            logger.error(f"Error mapping speaker name to ID: {e}")
            return None

    async def _handle_session_registration(self, websocket: WebSocket, message: Dict, participants: List[str]):
        """Handle session registration with Phase 3 session manager"""
        try:
            # Generate session and meeting IDs
            websocket_id = str(id(websocket))
            meeting_url = message.get('meetingUrl', 'unknown')
            platform = message.get('platform', 'unknown')

            # Use consistent meeting_id generation - match audio chunk handler
            if meeting_url and meeting_url != 'unknown':
                meeting_id = f"{platform}_{hash(meeting_url) % 1000000}"  # Match audio chunk handler
            else:
                meeting_id = f"meeting_{int(time.time())}"

            session_id = f"session_{websocket_id}_{int(time.time())}"

            # Register with session manager
            registration_result = await session_manager.register_session(
                session_id=session_id,
                meeting_id=meeting_id,
                websocket_id=websocket_id,
                participants=participants
            )

            # Track websocket to session mapping
            self.websocket_to_session[websocket] = session_id

            logger.info(f"Session registration result: {registration_result}")

            # Send session info to client
            await self.send_message(websocket, {
                'type': 'SESSION_REGISTERED',
                'data': {
                    'sessionId': session_id,
                    'meetingId': meeting_id,
                    'isNewSession': registration_result.get('is_new_session', True),
                    'reconnectionCount': registration_result.get('reconnection_count', 0)
                }
            })

        except Exception as e:
            logger.error(f"Error in session registration: {e}")

    async def _update_session_activity(self, websocket: WebSocket, transcript_segment: Optional[Dict] = None, audio_duration: Optional[float] = None):
        """Update session activity with session manager"""
        try:
            session_id = self.websocket_to_session.get(websocket)
            if session_id:
                await session_manager.update_session_activity(
                    session_id=session_id,
                    transcript_segment=transcript_segment,
                    audio_duration=audio_duration
                )
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint handler with full message routing"""
    print(f"🔌 Starting WebSocket endpoint handler")

    client_info = {
        'client_host': websocket.client.host if websocket.client else 'unknown',
        'client_port': websocket.client.port if websocket.client else 0
    }

    print(f"🔌 Client info: {client_info}")

    try:
        # Connect using WebSocketManager (sends HANDSHAKE_ACK automatically)
        await websocket_manager.connect(websocket, client_info)
        print(f"✅ WebSocket connected successfully")

        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()

                if not data or data.strip() == "":
                    print(f"⚠️  Received empty message, skipping...")
                    continue

                message = json.loads(data)
                message_type = message.get('type')
                print(f"📬 Received {message_type}: {message}")

                # Route message based on type
                if message_type == 'HANDSHAKE':
                    await websocket_manager.handle_handshake(websocket, message)
                elif message_type in ['AUDIO_CHUNK', 'audio_chunk', 'AUDIO_CHUNK_ENHANCED']:
                    await websocket_manager.handle_audio_chunk(websocket, message)
                elif message_type == 'MEETING_EVENT':
                    await websocket_manager.handle_meeting_event(websocket, message)
                else:
                    print(f"⚠️  Unknown message type: {message_type}")
                    await websocket_manager.send_message(websocket, {
                        'type': 'ERROR',
                        'error': f"Unknown message type: {message_type}"
                    })

            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e} - Data: '{data}'")
                await websocket_manager.send_message(websocket, {
                    'type': 'ERROR',
                    'error': 'Invalid JSON format'
                })
            except Exception as e:
                print(f"❌ Message handling error: {e}")
                break

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected normally")
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)
        raise

def get_websocket_manager():
    """Get the global WebSocket manager instance"""
    return websocket_manager

# Create FastAPI app instance for uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("✅ Loaded environment from .env")
else:
    print("⚠️  No .env file found")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🗄️ Ensuring database is ready...")
    await websocket_manager._ensure_database_ready()
    print("🚀 Starting background timeout checker...")
    await background_manager.start(websocket_manager.audio_buffer_manager, websocket_manager)
    yield
    # Shutdown
    print("🛑 Stopping background timeout checker...")
    await background_manager.stop()

# Create FastAPI app with lifespan
app = FastAPI(title="ScrumBot WebSocket Server", lifespan=lifespan)

# Add CORS middleware with WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add root endpoint for testing
@app.get("/")
async def root():
    return {"message": "ScrumBot WebSocket Server with Auto-Restart", "websocket": "/ws"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "auto_restart": "enabled"}

# WebSocket endpoint with full message handling
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    print(f"🔌 WebSocket connection attempt from {websocket.client}")
    await websocket_endpoint(websocket)

async def start_server(host="0.0.0.0", port=8080):
    """Legacy start server function for backward compatibility"""
    import uvicorn
    
    print("🚀 Starting ScrumBot WebSocket Server...")
    print(f"📡 WebSocket endpoint: ws://{host}:{port}/ws")
    print(f"🏥 Health check: http://{host}:{port}/health")

    # Start server
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()
