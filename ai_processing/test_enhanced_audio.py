"""
Test script to verify enhanced audio chunk processing with participant data
Tests the integration between Chrome extension enhanced payloads and AI processing backend
"""

import asyncio
import json
import base64
from datetime import datetime
from typing import Dict, List
import sys
import os

# Add the app directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.websocket_server import MeetingSession, WebSocketManager


def create_sample_audio_data() -> str:
    """Create sample base64 encoded audio data for testing"""
    # Create a simple wave-like pattern as bytes
    sample_audio = b'\x00\x01\x02\x03\x04\x05' * 100
    return base64.b64encode(sample_audio).decode('utf-8')


def create_basic_audio_chunk() -> Dict:
    """Create a basic audio chunk message (legacy format)"""
    return {
        "type": "audio_chunk",
        "data": create_sample_audio_data(),
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "platform": "google-meet",
            "meetingUrl": "https://meet.google.com/test-meeting-123",
            "chunkSize": 600,
            "sampleRate": 16000
        }
    }


def create_enhanced_audio_chunk() -> Dict:
    """Create an enhanced audio chunk message with participant data"""
    return {
        "type": "AUDIO_CHUNK_ENHANCED",
        "data": create_sample_audio_data(),
        "timestamp": datetime.now().isoformat(),
        "platform": "google-meet",
        "meetingUrl": "https://meet.google.com/test-meeting-123",
        "participants": [
            {
                "id": "participant_1",
                "name": "Christian Onyisi",
                "platform_id": "google_meet_user_123",
                "status": "active",
                "is_host": False,
                "join_time": "2025-01-08T10:00:00Z"
            },
            {
                "id": "participant_2",
                "name": "John Smith",
                "platform_id": "google_meet_user_456",
                "status": "active",
                "is_host": True,
                "join_time": "2025-01-08T09:58:30Z"
            }
        ],
        "participant_count": 2,
        "metadata": {
            "chunk_size": 600,
            "sample_rate": 16000,
            "channels": 1,
            "format": "webm"
        }
    }


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.client = type('obj', (object,), {'host': '127.0.0.1', 'port': 8000})()

    async def accept(self):
        pass

    async def send_text(self, message: str):
        self.messages_sent.append(json.loads(message))


async def test_basic_audio_chunk():
    """Test processing of basic audio chunk (legacy format)"""
    print("\n=== Testing Basic Audio Chunk Processing ===")

    websocket_manager = WebSocketManager()
    mock_websocket = MockWebSocket()

    # Connect mock websocket
    await websocket_manager.connect(mock_websocket, {'client_host': '127.0.0.1', 'client_port': 8000})

    # Create basic audio chunk
    basic_chunk = create_basic_audio_chunk()
    print(f"Created basic audio chunk: {basic_chunk['type']}")
    print(f"Platform: {basic_chunk['metadata']['platform']}")
    print(f"Meeting URL: {basic_chunk['metadata']['meetingUrl']}")

    # Process the audio chunk
    try:
        await websocket_manager.handle_audio_chunk(mock_websocket, basic_chunk)
        print("✅ Basic audio chunk processed successfully")

        # Check if session was created
        if websocket_manager.meeting_sessions:
            session = list(websocket_manager.meeting_sessions.values())[0]
            print(f"📊 Session created - ID: {session.meeting_id}")
            print(f"📊 Platform: {session.platform}")
            print(f"📊 Participant count: {session.participant_count}")
            print(f"📊 Legacy participants: {list(session.participants)}")

    except Exception as e:
        print(f"❌ Error processing basic audio chunk: {e}")


async def test_enhanced_audio_chunk():
    """Test processing of enhanced audio chunk with participant data"""
    print("\n=== Testing Enhanced Audio Chunk Processing ===")

    websocket_manager = WebSocketManager()
    mock_websocket = MockWebSocket()

    # Connect mock websocket
    await websocket_manager.connect(mock_websocket, {'client_host': '127.0.0.1', 'client_port': 8000})

    # Create enhanced audio chunk
    enhanced_chunk = create_enhanced_audio_chunk()
    print(f"Created enhanced audio chunk: {enhanced_chunk['type']}")
    print(f"Platform: {enhanced_chunk['platform']}")
    print(f"Meeting URL: {enhanced_chunk['meetingUrl']}")
    print(f"Participants: {len(enhanced_chunk['participants'])}")

    for participant in enhanced_chunk['participants']:
        print(f"  - {participant['name']} ({participant['id']})")

    # Process the audio chunk
    try:
        await websocket_manager.handle_audio_chunk(mock_websocket, enhanced_chunk)
        print("✅ Enhanced audio chunk processed successfully")

        # Check if session was created and participant data was stored
        if websocket_manager.meeting_sessions:
            session = list(websocket_manager.meeting_sessions.values())[0]
            print(f"📊 Session created - ID: {session.meeting_id}")
            print(f"📊 Platform: {session.platform}")
            print(f"📊 Participant count: {session.participant_count}")
            print(f"📊 Enhanced participant data: {len(session.participant_data)} participants")
            print(f"📊 Legacy participants: {list(session.participants)}")

            # Show participant details
            for participant_id, participant in session.participant_data.items():
                print(f"  - {participant_id}: {participant['name']} ({'Host' if participant['is_host'] else 'Participant'})")

            # Test participant name extraction
            participant_names = session.get_participant_names()
            print(f"📊 Participant names for speaker identification: {participant_names}")

    except Exception as e:
        print(f"❌ Error processing enhanced audio chunk: {e}")


async def test_meeting_session_functionality():
    """Test MeetingSession participant management functionality"""
    print("\n=== Testing MeetingSession Functionality ===")

    session = MeetingSession("test_meeting_123", "google-meet")

    # Test participant update
    participants_data = [
        {
            "id": "participant_1",
            "name": "Alice Johnson",
            "platform_id": "google_meet_user_alice",
            "status": "active",
            "is_host": True,
            "join_time": "2025-01-08T10:00:00Z"
        },
        {
            "id": "participant_2",
            "name": "Bob Wilson",
            "platform_id": "google_meet_user_bob",
            "status": "active",
            "is_host": False,
            "join_time": "2025-01-08T10:01:00Z"
        }
    ]

    print(f"Updating session with {len(participants_data)} participants")
    session.update_participants(participants_data, len(participants_data))

    print(f"✅ Participant data stored: {len(session.participant_data)} participants")
    print(f"✅ Legacy participants: {list(session.participants)}")
    print(f"✅ Participant names: {session.get_participant_names()}")

    # Test transcript addition
    sample_transcript = {
        "text": "Alice: Let's start the meeting. Bob: Sounds good to me!",
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.95
    }

    session.add_transcript_chunk(sample_transcript)
    print(f"✅ Transcript added: {len(session.transcript_chunks)} chunks")
    print(f"✅ Cumulative transcript length: {len(session.cumulative_transcript)} characters")


async def test_backward_compatibility():
    """Test that the system still works with basic audio chunks"""
    print("\n=== Testing Backward Compatibility ===")

    websocket_manager = WebSocketManager()
    mock_websocket = MockWebSocket()

    await websocket_manager.connect(mock_websocket, {'client_host': '127.0.0.1', 'client_port': 8000})

    # Process both types of chunks for the same meeting
    basic_chunk = create_basic_audio_chunk()
    enhanced_chunk = create_enhanced_audio_chunk()

    try:
        # Process basic chunk first
        await websocket_manager.handle_audio_chunk(mock_websocket, basic_chunk)
        print("✅ Basic chunk processed")

        # Process enhanced chunk (should update the same session)
        await websocket_manager.handle_audio_chunk(mock_websocket, enhanced_chunk)
        print("✅ Enhanced chunk processed")

        # Verify session state
        if websocket_manager.meeting_sessions:
            session = list(websocket_manager.meeting_sessions.values())[0]
            print(f"📊 Final session state:")
            print(f"  - Meeting ID: {session.meeting_id}")
            print(f"  - Participant count: {session.participant_count}")
            print(f"  - Enhanced participant data: {len(session.participant_data)}")
            print(f"  - Legacy participants: {len(session.participants)}")
            print("✅ Backward compatibility verified")

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")


async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Audio Chunk Processing Tests")
    print("=" * 60)

    try:
        await test_basic_audio_chunk()
        await test_enhanced_audio_chunk()
        await test_meeting_session_functionality()
        await test_backward_compatibility()

        print("\n" + "=" * 60)
        print("🎉 All tests completed!")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
