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

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handle audio chunk processing and transcription"""

    def __init__(self):
        self.whisper_model_path = os.getenv('WHISPER_MODEL_PATH', './whisper.cpp/models/ggml-base.en.bin')
        self.whisper_executable = os.getenv('WHISPER_EXECUTABLE', './whisper.cpp/build/bin/whisper-cli')

    async def process_audio_chunk(self, audio_data: bytes, metadata: Dict) -> Dict:
        """Process audio chunk and return transcription"""
        try:
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

                # Convert audio data to WAV format if needed
                await self._write_audio_to_wav(audio_data, temp_path, metadata)

                # Run Whisper transcription
                transcript = await self._transcribe_audio(temp_path)
                
                # Log processing result
                if transcript:
                    print(f"✅ Transcription successful: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'")
                else:
                    print(f"⚠️ Empty transcription result")

                # Clean up temp file
                os.unlink(temp_path)

                return {
                    'text': transcript,
                    'confidence': 0.85,  # Default confidence
                    'timestamp': datetime.now().isoformat(),
                    'metadata': metadata
                }

        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return {
                'text': '',
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

    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            cmd = [
                self.whisper_executable,
                '-m', self.whisper_model_path,
                '-f', audio_path,
                '--output-txt'
            ]
            
            print(f"🤖 Running Whisper: {' '.join(cmd)}")

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
                return result
            else:
                logger.error(f"Whisper error: {stderr.decode('utf-8')}")
                return ""

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

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
        

    
    async def _process_timeout_buffer(self, session_id: str, buffer):
        """Process buffer due to timeout"""
        try:
            duration = buffer.get_duration_ms()
            print(f"🎤 Processing timeout buffer ({duration:.1f}ms) for session {session_id}")
            
            # Create WAV file from buffered audio
            wav_path = buffer.create_wav_file()
            if wav_path:
                try:
                    # Process audio with Whisper
                    transcription_result = await self.audio_processor.process_audio_chunk(
                        buffer.get_buffered_audio(), {}
                    )
                    print(f"📝 Timeout result: '{transcription_result.get('text', 'EMPTY')}'")
                    
                    # Send result to all connections for this session
                    await self._broadcast_transcription_result(session_id, transcription_result)
                    
                    # Clean up temp file
                    os.unlink(wav_path)
                    
                except Exception as e:
                    print(f"❌ Timeout processing failed: {e}")
                    if os.path.exists(wav_path):
                        os.unlink(wav_path)
                
                # Clear buffer after processing
                buffer.clear()
                
        except Exception as e:
            logger.error(f"Error processing timeout buffer: {e}")
    
    async def _broadcast_transcription_result(self, session_id: str, transcription_result: Dict):
        """Broadcast transcription result to all connections for a session"""
        try:
            # Find connections for this session
            target_connections = []
            for websocket, connection_info in self.active_connections.items():
                session = connection_info.get('meeting_session')
                if session and session.meeting_id == session_id:
                    target_connections.append(websocket)
            
            # Send to all connections
            for websocket in target_connections:
                try:
                    await self.send_message(websocket, {
                        'type': 'transcription_result',
                        'data': {
                            'text': transcription_result.get('text', ''),
                            'confidence': transcription_result.get('confidence', 0.0),
                            'timestamp': transcription_result.get('timestamp'),
                            'speaker': 'Unknown',
                            'trigger_reason': 'timeout'
                        }
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
                else:
                    # Timeout scenario - don't process here, let background task handle it
                    print(f"⏰ Timeout ready - leaving for background task")
                    ready_for_processing = False
            
            if not ready_for_processing:
                print(f"🔄 Buffering audio chunk ({audio_buffer.get_duration_ms():.1f}ms/{audio_buffer.target_duration_ms}ms)")
            
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
                # Create transcript chunk for buffer
                chunk = TranscriptChunk(
                    timestamp_start=len(session.transcript_chunks) * 5.0,  # Estimate based on chunk index
                    timestamp_end=(len(session.transcript_chunks) + 1) * 5.0,
                    raw_text=transcription_result['text'],
                    participants_present=participants,
                    confidence=transcription_result.get('confidence', 0.85),
                    chunk_index=len(session.transcript_chunks)
                )
                
                # Add to buffer (no AI call yet)
                session.buffer.add_chunk(chunk)
                
                # Check if we should process batch (only if AI is available)
                if session.buffer.should_process_batch():
                    try:
                        logger.info(f"Triggering batch processing for meeting {meeting_id}")
                        session.batch_processor.start_batch_processing(session.buffer)
                    except Exception as e:
                        logger.warning(f"Batch processing failed (AI unavailable): {e}")
                        # Continue without AI processing
                
                # Use fallback speaker identification for immediate response (no AI)
                speaker_name = session.buffer._fallback_speaker_identification(chunk)
                transcription_result['speakers'] = [{'name': speaker_name}] if speaker_name != 'Unknown' else []

            # Send transcription result if we processed audio (buffer full) or have text
            should_send_result = (ready_for_processing or 
                                transcription_result.get('text') or 
                                (current_samples >= audio_buffer.target_samples * 0.98))
            
            if should_send_result:
                speakers = transcription_result.get('speakers', [])
                speaker_name = speakers[0].get('name', 'Unknown') if speakers else 'Unknown'
                
                response_data = {
                    'text': transcription_result.get('text', ''),
                    'confidence': transcription_result.get('confidence', 0.0),
                    'timestamp': transcription_result.get('timestamp'),
                    'speaker': speaker_name
                }

                # Send both formats for compatibility
                await self.send_message(websocket, {
                    'type': 'transcription_result',  # Shared contract format
                    'data': response_data
                })

                # Also send extended format for Chrome extension
                await self.send_message(websocket, {
                    'type': 'TRANSCRIPTION_RESULT',
                    'data': {
                        **response_data,
                        'speakers': transcription_result.get('speakers', []),
                        'meetingId': meeting_id,
                        'chunkId': len(session.transcript_chunks),
                        'speaker_id': self._get_speaker_id_from_name(
                            response_data.get('speaker', 'Unknown'),
                            session.participant_data
                        ) if session.participant_data else None,
                        'speaker_confidence': transcription_result.get('speaker_confidence', 0.0)
                    }
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
                        'meeting_id': session.meeting_id
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
                        'total_transcripts': 0
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