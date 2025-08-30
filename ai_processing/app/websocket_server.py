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
from app.ai_processor import AIProcessor
from app.speaker_identifier import SpeakerIdentifier
from app.meeting_summarizer import MeetingSummarizer
from app.task_extractor import TaskExtractor
from app.integration_adapter import ParticipantData, notify_meeting_processed
from app.meeting_buffer import MeetingBuffer, TranscriptChunk, BatchProcessor
import subprocess

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

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
            else:
                logger.error(f"Whisper error: {stderr.decode('utf-8')}")
                return ""

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

class MeetingSession:
    """Manage individual meeting session state"""

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

        # Initialize AI processors
        self.ai_processor = AIProcessor()
        self.speaker_identifier = SpeakerIdentifier(self.ai_processor)
        self.meeting_summarizer = MeetingSummarizer(self.ai_processor)
        self.task_extractor = TaskExtractor(self.ai_processor)
        
        # Initialize optimized buffer system
        self.buffer = MeetingBuffer(meeting_id)
        self.batch_processor = BatchProcessor(self.ai_processor)

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
        self.batch_processor = None  # Initialized when first session is created

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
        client_type = message.get('clientType', 'unknown')
        version = message.get('version', '1.0')
        capabilities = message.get('capabilities', [])

        logger.info(f"Handshake from {client_type} v{version} with capabilities: {capabilities}")

        await self.send_message(websocket, {
            'type': 'HANDSHAKE_ACK',
            'serverVersion': '1.0',
            'status': 'ready',
            'supportedFeatures': [
                'audio-transcription',
                'speaker-identification',
                'real-time-processing'
            ]
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

            # Convert base64 audio data to bytes if needed
            if isinstance(audio_data, str):
                import base64
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = bytes(audio_data)

            # Process audio chunk
            transcription_result = await self.audio_processor.process_audio_chunk(
                audio_bytes, metadata
            )

            # Add to session
            session.add_transcript_chunk(transcription_result)

            # Add to buffer instead of immediate AI processing
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
                
                # Check if we should process batch
                if session.buffer.should_process_batch():
                    logger.info(f"Triggering batch processing for meeting {meeting_id}")
                    session.batch_processor.start_batch_processing(session.buffer)
                
                # Use fallback speaker identification for immediate response
                speaker_name = session.buffer._fallback_speaker_identification(chunk)
                transcription_result['speakers'] = [{'name': speaker_name}] if speaker_name != 'Unknown' else []

            # Send transcription result back to client - support shared contract format
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

            # Broadcast to other clients in the same meeting
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
            await self.send_message(websocket, {
                'type': 'ERROR',
                'error': f"Audio processing failed: {str(e)}"
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
        elif event_type == 'meeting_ended':
            # Process final summary if we have a session
            connection_info = self.active_connections.get(websocket)
            if connection_info and connection_info.get('meeting_session'):
                session = connection_info['meeting_session']
                await self._generate_meeting_summary(websocket, session)

    async def _generate_meeting_summary(self, websocket: WebSocket, session: MeetingSession):
        """Generate and send meeting summary"""
        try:
            if not session.cumulative_transcript.strip():
                logger.warning("No transcript available for summary")
                return

            # Generate comprehensive summary
            summary = await session.meeting_summarizer.generate_comprehensive_summary(
                session.cumulative_transcript,
                {
                    'meeting_id': session.meeting_id,
                    'platform': session.platform,
                    'participants': list(session.participants),
                    'duration': str(datetime.now() - session.start_time)
                }
            )

            # Extract tasks
            tasks = await session.task_extractor.extract_comprehensive_tasks(
                session.cumulative_transcript,
                {'participants': list(session.participants)}
            )

            # Notify integration systems with proper participant data
            try:
                participant_objects = session.get_participant_data_objects()
                await notify_meeting_processed(
                    meeting_id=session.meeting_id,
                    meeting_title=f"Meeting {session.meeting_id}",
                    platform=session.platform,
                    participants=participant_objects,
                    participant_count=session.participant_count,
                    transcript=session.cumulative_transcript,
                    summary_data=summary,
                    tasks_data=tasks,
                    speakers_data=[]
                )
                logger.info(f"Notified integration systems for meeting {session.meeting_id}")
            except Exception as e:
                logger.warning(f"Failed to notify integration systems: {e}")

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
    """Main WebSocket endpoint handler"""
    client_info = {
        'client_host': websocket.client.host if websocket.client else 'unknown',
        'client_port': websocket.client.port if websocket.client else 0
    }

    await websocket_manager.connect(websocket, client_info)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get('type')
            logger.debug(f"Received message type: {message_type}")

            # Route message based on type - support both formats
            if message_type == 'HANDSHAKE':
                await websocket_manager.handle_handshake(websocket, message)
            elif message_type in ['AUDIO_CHUNK', 'audio_chunk', 'AUDIO_CHUNK_ENHANCED']:
                await websocket_manager.handle_audio_chunk(websocket, message)
            elif message_type == 'MEETING_EVENT':
                await websocket_manager.handle_meeting_event(websocket, message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket_manager.send_message(websocket, {
                    'type': 'ERROR',
                    'error': f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

def get_websocket_manager():
    """Get the global WebSocket manager instance"""
    return websocket_manager