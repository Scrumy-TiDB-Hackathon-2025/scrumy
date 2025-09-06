"""
WebSocket server for real-time audio processing with participant identification
Handles Chrome extension communication for live transcription and AI processing
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
import subprocess
import time

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

                # Determine if likely silence (improved thresholds)
                is_likely_silence = max_amplitude < 500 or rms < 50  # Better thresholds for 16-bit audio

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
    """Manage WebSocket connections and sessions"""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict] = {}
        self.meeting_sessions: Dict[str, MeetingSession] = {}
        self.audio_processor = AudioProcessor()
        self.audio_buffer_manager = AudioBufferManager()
        self.batch_processor = None  # Initialized when first session is created
        self.processing_locks: Dict[str, threading.Lock] = {}  # Prevent race conditions



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

                # Clear buffer after processing
                buffer.clear()

        except Exception as e:
            logger.error(f"Error processing timeout buffer: {e}")
        finally:
            # Always release the lock
            self.processing_locks[session_id].release()

    async def _broadcast_transcription_result(self, session_id: str, transcription_result: Dict):
        """Broadcast transcription result to all connections for a session"""
        try:
            # Find session for duplicate checking
            session = self.meeting_sessions.get(session_id)
            if not session:
                print(f"⚠️ No session found for {session_id} - skipping broadcast")
                return

            # Check for duplicates before broadcasting
            transcript_text = transcription_result.get('text', '').strip()
            if not transcript_text or session.buffer._is_duplicate_transcript(transcript_text):
                print(f"⚠️ Skipping duplicate timeout transcript: '{transcript_text[:50]}...'")
                return

            # Add to recent transcripts for future deduplication
            session.buffer.recent_transcripts.append(transcript_text.lower())
            if len(session.buffer.recent_transcripts) > session.buffer.max_recent_transcripts:
                session.buffer.recent_transcripts.pop(0)  # Remove oldest

            # Find connections for this session
            target_connections = []
            for websocket, connection_info in self.active_connections.items():
                connection_session = connection_info.get('meeting_session')
                if connection_session and connection_session.meeting_id == session_id:
                    target_connections.append(websocket)

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

        # Send handshake acknowledgment
        await self.send_message(websocket, {
            'type': 'HANDSHAKE_ACK',
            'serverVersion': '1.0',
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        })

    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            connection_info = self.active_connections[websocket]
            logger.info(f"WebSocket disconnected: {connection_info.get('client_info', {})}")
            del self.active_connections[websocket]

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
        """Handle incoming audio chunk"""
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

            # Get or create meeting session
            meeting_id = f"{platform}_{hash(meeting_url) % 1000000}"

            if meeting_id not in self.meeting_sessions:
                self.meeting_sessions[meeting_id] = MeetingSession(meeting_id, platform)
                logger.info(f"Created new meeting session: {meeting_id}")

            session = self.meeting_sessions[meeting_id]
            session.meeting_url = meeting_url

            # Update participant data if available (enhanced format)
            if participants and message_type == 'AUDIO_CHUNK_ENHANCED':
                session.update_participants(participants, participant_count)
                logger.debug(f"Updated participant data: {len(participants)} participants")

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
                # Early return - let background task handle timeout processing
                return

            # Only continue if we actually processed something (buffer was full, not timeout)
            # Log transcript chunk (if logger available)
            if transcription_result.get('text') and session.buffer.logger:
                session.buffer.logger.log_transcript_chunk(
                    transcription_result['text'],
                    participants[0].get('name') if participants else 'Unknown'
                )

            # Add to session
            session.add_transcript_chunk(transcription_result)

            # Add to buffer (no immediate AI processing)
            if transcription_result.get('text'):
                # Check for duplicate transcript before processing
                transcript_text = transcription_result['text'].strip()

                # Skip if duplicate or empty
                if session.buffer._is_duplicate_transcript(transcript_text):
                    print(f"⚠️ Skipping duplicate transcript: '{transcript_text[:50]}...'")
                    transcription_result['text'] = ''  # Clear duplicate
                    return  # Skip processing this duplicate

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

        # Handle different event types
        if event_type == 'meeting_started':
            await self.send_message(websocket, {
                'type': 'MEETING_EVENT_ACK',
                'eventType': event_type,
                'status': 'acknowledged'
            })
        elif event_type in ['ended', 'meeting_ended']:
            print(f"\n🏁 Meeting ended - starting final processing...")

            # Check if this is a buffer flush completion signal
            buffer_flush_complete = data.get('bufferFlushComplete', False)

            if not buffer_flush_complete:
                # Legacy behavior or partial end signal - wait for buffer flush
                print("⏳ Meeting end signal received - waiting for buffer flush completion...")
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

    async def _generate_meeting_summary(self, websocket: WebSocket, session: MeetingSession):
        """Generate and send meeting summary (only if AI is available)"""
        try:
            print(f"🎯 Starting meeting summary generation for {session.meeting_id}")

            if not session.cumulative_transcript.strip():
                print(f"⚠️ No transcript content available - skipping summary")
                logger.warning("No transcript available for summary")
                return

            print(f"📝 Transcript ready: {len(session.cumulative_transcript)} characters")

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

                print(f"🎉 AI processing completed successfully!")
                logger.info(f"AI processing completed for meeting {session.meeting_id}")

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
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        websocket_manager.disconnect(websocket)
        raise

def get_websocket_manager():
    """Get the global WebSocket manager instance"""
    return websocket_manager

async def start_server(host="0.0.0.0", port=8080):
    """Start the WebSocket server with FastAPI/Uvicorn and lifespan management"""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from contextlib import asynccontextmanager

    # Load environment
    import os
    from dotenv import load_dotenv

    # Load .env file
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print("✅ Loaded environment from .env")
    else:
        print("⚠️  No .env file found")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        print("🚀 Starting background timeout checker...")
        await background_manager.start(websocket_manager.audio_buffer_manager, websocket_manager)
        yield
        # Shutdown
        print("🛑 Stopping background timeout checker...")
        await background_manager.stop()

    print("🚀 Starting ScrumBot WebSocket Server...")
    print(f"📡 WebSocket endpoint: ws://{host}:{port}/ws")
    print(f"🏥 Health check: http://{host}:{port}/health")

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
        return {"message": "ScrumBot WebSocket Server", "websocket": "/ws"}

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    # WebSocket endpoint with full message handling
    @app.websocket("/ws")
    async def websocket_route(websocket: WebSocket):
        print(f"🔌 WebSocket connection attempt from {websocket.client}")
        await websocket_endpoint(websocket)

    # Start server
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()
