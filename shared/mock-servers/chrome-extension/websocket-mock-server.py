#!/usr/bin/env python3
"""
WebSocket Mock Server for Chrome Extension Testing

This server mimics the AI processing backend WebSocket interface,
handling enhanced audio chunks and returning realistic transcription results.
"""

import asyncio
import json
import logging
import base64
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
import websockets
from websockets.server import WebSocketServerProtocol
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockSession:
    """Represents a mock meeting session"""
    def __init__(self, meeting_id: str, platform: str = "google-meet"):
        self.meeting_id = meeting_id
        self.platform = platform
        self.participants: Dict[str, dict] = {}
        self.participant_count = 0
        self.meeting_url = ""
        self.chunks_received = 0
        self.start_time = datetime.now(timezone.utc)

    def update_participants(self, participants_data: List[Dict], participant_count: int):
        """Update participant data from enhanced audio chunk"""
        self.participant_count = participant_count
        for participant in participants_data:
            self.participants[participant['id']] = participant
        logger.info(f"Session {self.meeting_id}: Updated with {len(participants_data)} participants")

class ChromeExtensionMockServer:
    """Mock WebSocket server for Chrome extension testing"""

    def __init__(self):
        self.sessions: Dict[str, MockSession] = {}
        self.connection_count = 0

        # Mock transcription responses for realistic testing
        self.mock_transcriptions = [
            {
                "text": "Good morning everyone, let's start our meeting",
                "speaker": "Host",
                "confidence": 0.95
            },
            {
                "text": "Thanks for joining. I have some updates to share",
                "speaker": "Participant 1",
                "confidence": 0.92
            },
            {
                "text": "That sounds great. Let's discuss the next steps",
                "speaker": "Participant 2",
                "confidence": 0.88
            },
            {
                "text": "I'll take care of that action item by Friday",
                "speaker": "Host",
                "confidence": 0.91
            },
            {
                "text": "Perfect. Any other questions before we wrap up?",
                "speaker": "Participant 1",
                "confidence": 0.94
            }
        ]

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle individual WebSocket connections"""
        self.connection_count += 1
        client_id = f"client_{self.connection_count}"
        logger.info(f"New connection: {client_id} from {websocket.remote_address}")

        try:
            # Send welcome message
            await self.send_message(websocket, {
                "type": "CONNECTION_ESTABLISHED",
                "client_id": client_id,
                "server": "Chrome Extension Mock Server",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "supported_formats": ["audio_chunk", "AUDIO_CHUNK_ENHANCED"]
            })

            async for message in websocket:
                try:
                    await self.process_message(websocket, client_id, message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {e}")
                    await self.send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await self.send_error(websocket, f"Processing error: {str(e)}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {client_id}")
        except Exception as e:
            logger.error(f"Connection error for {client_id}: {e}")
        finally:
            # Clean up sessions for this client if needed
            logger.info(f"Cleaned up connection: {client_id}")

    async def process_message(self, websocket: WebSocketServerProtocol, client_id: str, message: str):
        """Process incoming messages from Chrome extension"""
        data = json.loads(message)
        message_type = data.get('type', '').upper()

        logger.info(f"Received {message_type} from {client_id}")

        if message_type in ['AUDIO_CHUNK', 'AUDIO_CHUNK_ENHANCED']:
            await self.handle_audio_chunk(websocket, client_id, data)
        elif message_type == 'MEETING_EVENT':
            await self.handle_meeting_event(websocket, client_id, data)
        elif message_type == 'GET_SESSION_INFO':
            await self.handle_session_info_request(websocket, client_id, data)
        else:
            logger.warning(f"Unknown message type: {message_type} from {client_id}")
            await self.send_error(websocket, f"Unknown message type: {message_type}")

    async def handle_audio_chunk(self, websocket: WebSocketServerProtocol, client_id: str, data: dict):
        """Handle audio chunk processing"""
        message_type = data.get('type')
        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())

        # Extract meeting information
        meeting_url = data.get('meetingUrl', '') or data.get('meeting_url', '')
        meeting_id = self.extract_meeting_id(meeting_url)
        platform = data.get('platform', 'unknown')

        # Get or create session
        if meeting_id not in self.sessions:
            self.sessions[meeting_id] = MockSession(meeting_id, platform)
            logger.info(f"Created new session: {meeting_id}")

        session = self.sessions[meeting_id]
        session.chunks_received += 1
        session.meeting_url = meeting_url

        # Handle enhanced audio chunk with participant data
        if message_type == 'AUDIO_CHUNK_ENHANCED':
            participants = data.get('participants', [])
            participant_count = data.get('participant_count', len(participants))

            if participants:
                session.update_participants(participants, participant_count)

        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Generate mock transcription result
        transcription = await self.generate_mock_transcription(session, timestamp)

        # Send transcription result
        await self.send_message(websocket, transcription)

        # Occasionally send meeting events
        if session.chunks_received % 5 == 0:
            await self.send_meeting_update(websocket, session)

    async def handle_meeting_event(self, websocket: WebSocketServerProtocol, client_id: str, data: dict):
        """Handle meeting event messages"""
        event_type = data.get('eventType', '')
        meeting_id = data.get('data', {}).get('meetingId', '')

        logger.info(f"Meeting event: {event_type} for meeting {meeting_id}")

        # Acknowledge the event
        await self.send_message(websocket, {
            "type": "EVENT_ACKNOWLEDGED",
            "eventType": event_type,
            "meetingId": meeting_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def handle_session_info_request(self, websocket: WebSocketServerProtocol, client_id: str, data: dict):
        """Handle session information requests"""
        meeting_id = data.get('meeting_id', '')

        if meeting_id in self.sessions:
            session = self.sessions[meeting_id]
            await self.send_message(websocket, {
                "type": "SESSION_INFO",
                "meeting_id": meeting_id,
                "platform": session.platform,
                "participant_count": session.participant_count,
                "chunks_received": session.chunks_received,
                "participants": list(session.participants.values()),
                "start_time": session.start_time.isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            await self.send_error(websocket, f"Session not found: {meeting_id}")

    async def generate_mock_transcription(self, session: MockSession, timestamp: str) -> dict:
        """Generate realistic mock transcription results"""
        # Select a random transcription
        mock_data = random.choice(self.mock_transcriptions)

        # Use actual participant names if available
        speaker_name = mock_data["speaker"]
        speaker_id = None
        speaker_confidence = mock_data["confidence"]

        if session.participants:
            # Try to map to actual participants
            participant_list = list(session.participants.values())
            if participant_list:
                selected_participant = random.choice(participant_list)
                speaker_name = selected_participant["name"]
                speaker_id = selected_participant["id"]
                speaker_confidence = min(0.95, mock_data["confidence"] + 0.1)  # Boost confidence with participant data

        # Create enhanced transcription result
        result = {
            "type": "TRANSCRIPTION_RESULT",
            "data": {
                "text": mock_data["text"],
                "confidence": mock_data["confidence"],
                "timestamp": timestamp,
                "speaker": speaker_name,
                "meetingId": session.meeting_id,
                "chunkId": session.chunks_received
            }
        }

        # Add enhanced fields if we have participant data
        if speaker_id:
            result["data"].update({
                "speaker_id": speaker_id,
                "speaker_confidence": speaker_confidence,
                "speakers": [{
                    "id": speaker_id,
                    "name": speaker_name,
                    "segments": [mock_data["text"]],
                    "confidence": speaker_confidence
                }]
            })

        return result

    async def send_meeting_update(self, websocket: WebSocketServerProtocol, session: MockSession):
        """Send periodic meeting updates"""
        await self.send_message(websocket, {
            "type": "MEETING_UPDATE",
            "meeting_id": session.meeting_id,
            "chunks_processed": session.chunks_received,
            "participants_active": session.participant_count,
            "session_duration_minutes": int((datetime.now(timezone.utc) - session.start_time).total_seconds() / 60),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def send_message(self, websocket: WebSocketServerProtocol, data: dict):
        """Send JSON message to WebSocket client"""
        try:
            message = json.dumps(data, indent=None, separators=(',', ':'))
            await websocket.send(message)
            logger.debug(f"Sent {data.get('type', 'unknown')} message")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """Send error message to client"""
        await self.send_message(websocket, {
            "type": "ERROR",
            "message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def extract_meeting_id(self, meeting_url: str) -> str:
        """Extract meeting ID from URL or generate one"""
        if not meeting_url:
            return f"mock_meeting_{random.randint(1000, 9999)}"

        # Extract ID from common meeting URL patterns
        if 'meet.google.com' in meeting_url:
            return meeting_url.split('/')[-1]
        elif 'zoom.us' in meeting_url:
            return meeting_url.split('/')[-1]
        elif 'teams.microsoft.com' in meeting_url:
            return f"teams_meeting_{random.randint(1000, 9999)}"
        else:
            return f"meeting_{hash(meeting_url) % 10000}"

    async def start_server(self, host: str = "localhost", port: int = 8000):
        """Start the mock WebSocket server"""
        logger.info(f"Starting Chrome Extension Mock Server on ws://{host}:{port}/ws/audio")

        async def handler(websocket, path):
            if path == '/ws/audio':
                await self.handle_client(websocket, path)
            else:
                logger.warning(f"Unknown path: {path}")
                await websocket.close(code=1000, reason="Unknown path")

        # Start the server
        server = await websockets.serve(handler, host, port)
        logger.info(f"Mock server started successfully!")
        logger.info(f"Chrome extension can connect to: ws://{host}:{port}/ws/audio")

        return server

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Chrome Extension WebSocket Mock Server")
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Server port (default: 8000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and start server
    mock_server = ChromeExtensionMockServer()
    server = await mock_server.start_server(args.host, args.port)

    try:
        # Keep the server running
        await server.wait_closed()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.close()
        await server.wait_closed()
        logger.info("Server stopped")

if __name__ == "__main__":
    asyncio.run(main())
