"""
End-to-end integration test for enhanced audio chunk processing
Tests the complete flow from Chrome extension to AI processing backend
"""

import asyncio
import json
import websockets
import base64
from datetime import datetime
import sys
import os

# Test configuration
WEBSOCKET_URL = "ws://localhost:8000/ws/audio"
TEST_TIMEOUT = 30  # seconds

def create_test_audio_data():
    """Create sample base64 encoded audio data for testing"""
    # Create a simple wave-like pattern as bytes
    sample_audio = b'\x00\x01\x02\x03\x04\x05' * 100
    return base64.b64encode(sample_audio).decode('utf-8')

def create_enhanced_audio_chunk_message():
    """Create enhanced audio chunk message matching Chrome extension format"""
    return {
        "type": "AUDIO_CHUNK_ENHANCED",
        "data": create_test_audio_data(),
        "timestamp": datetime.now().isoformat(),
        "platform": "google-meet",
        "meetingUrl": "https://meet.google.com/test-integration-123",
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
            },
            {
                "id": "participant_3",
                "name": "Sarah Johnson",
                "platform_id": "google_meet_user_789",
                "status": "active",
                "is_host": False,
                "join_time": "2025-01-08T10:02:00Z"
            }
        ],
        "participant_count": 3,
        "metadata": {
            "chunk_size": 600,
            "sample_rate": 16000,
            "channels": 1,
            "format": "webm"
        }
    }

def create_basic_audio_chunk_message():
    """Create basic audio chunk message for backward compatibility testing"""
    return {
        "type": "AUDIO_CHUNK",
        "data": create_test_audio_data(),
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "platform": "google-meet",
            "meetingUrl": "https://meet.google.com/test-integration-123",
            "chunkSize": 600,
            "sampleRate": 16000
        }
    }

def create_handshake_message():
    """Create handshake message"""
    return {
        "type": "HANDSHAKE",
        "clientType": "chrome-extension",
        "version": "1.0",
        "capabilities": ["audio-capture", "meeting-detection", "participant-detection"]
    }

def create_meeting_event_message(event_type="meeting_started"):
    """Create meeting event message"""
    return {
        "type": "MEETING_EVENT",
        "eventType": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "meetingId": "test-integration-123",
            "participant": {
                "id": "participant_4",
                "name": "Alice Brown",
                "platform_id": "google_meet_user_999",
                "status": "active",
                "is_host": False,
                "join_time": datetime.now().isoformat()
            },
            "total_participants": 4
        }
    }

async def test_websocket_connection():
    """Test WebSocket connection and handshake"""
    print("\n=== Testing WebSocket Connection ===")

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ WebSocket connection established")

            # Send handshake
            handshake = create_handshake_message()
            await websocket.send(json.dumps(handshake))
            print("📤 Handshake sent")

            # Wait for handshake acknowledgment
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)

                if message.get("type") == "HANDSHAKE_ACK":
                    print("✅ Handshake acknowledged")
                    print(f"   Server status: {message.get('status')}")
                    print(f"   Server version: {message.get('serverVersion')}")
                    return True
                else:
                    print(f"❌ Unexpected handshake response: {message.get('type')}")
                    return False

            except asyncio.TimeoutError:
                print("❌ Handshake timeout")
                return False

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def test_enhanced_audio_processing():
    """Test enhanced audio chunk processing with participant data"""
    print("\n=== Testing Enhanced Audio Processing ===")

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Send handshake first
            handshake = create_handshake_message()
            await websocket.send(json.dumps(handshake))

            # Wait for handshake ack
            await websocket.recv()

            # Create and send enhanced audio chunk
            enhanced_chunk = create_enhanced_audio_chunk_message()
            print(f"📤 Sending enhanced audio chunk with {enhanced_chunk['participant_count']} participants")

            for participant in enhanced_chunk['participants']:
                print(f"   - {participant['name']} ({participant['id']})")

            await websocket.send(json.dumps(enhanced_chunk))

            # Wait for responses
            responses_received = 0
            expected_responses = 2  # transcription_result and TRANSCRIPTION_RESULT

            while responses_received < expected_responses:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    message = json.loads(response)

                    print(f"📥 Received: {message.get('type')}")

                    if message.get("type") in ["transcription_result", "TRANSCRIPTION_RESULT"]:
                        data = message.get("data", {})
                        print(f"   Speaker: {data.get('speaker', 'Unknown')}")
                        print(f"   Confidence: {data.get('confidence', 0.0)}")

                        if message.get("type") == "TRANSCRIPTION_RESULT":
                            # Enhanced format should include speaker_id
                            speaker_id = data.get('speaker_id')
                            if speaker_id:
                                print(f"   ✅ Speaker ID mapped: {speaker_id}")

                            # Check for speakers array
                            speakers = data.get('speakers', [])
                            if speakers:
                                print(f"   ✅ Speakers array: {len(speakers)} speakers")

                        responses_received += 1

                    elif message.get("type") == "MEETING_UPDATE":
                        data = message.get("data", {})
                        print(f"   Meeting ID: {data.get('meetingId')}")
                        print(f"   Participants: {len(data.get('participants', []))}")

                        # Check for enhanced participant data
                        if 'participant_data' in data:
                            print(f"   ✅ Enhanced participant data: {len(data['participant_data'])} participants")
                        if 'participant_count' in data:
                            print(f"   ✅ Participant count: {data['participant_count']}")

                    elif message.get("type") == "ERROR":
                        print(f"   ❌ Error: {message.get('error')}")

                except asyncio.TimeoutError:
                    print("❌ Response timeout")
                    break

            if responses_received >= expected_responses:
                print("✅ Enhanced audio processing successful")
                return True
            else:
                print(f"⚠️  Partial success: {responses_received}/{expected_responses} responses")
                return False

    except Exception as e:
        print(f"❌ Enhanced audio processing failed: {e}")
        return False

async def test_backward_compatibility():
    """Test backward compatibility with basic audio chunks"""
    print("\n=== Testing Backward Compatibility ===")

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Send handshake first
            handshake = create_handshake_message()
            await websocket.send(json.dumps(handshake))
            await websocket.recv()  # Wait for handshake ack

            # Send basic audio chunk
            basic_chunk = create_basic_audio_chunk_message()
            print("📤 Sending basic audio chunk (legacy format)")
            await websocket.send(json.dumps(basic_chunk))

            # Wait for transcription result
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                message = json.loads(response)

                if message.get("type") == "transcription_result":
                    print("✅ Basic audio chunk processed successfully")
                    data = message.get("data", {})
                    print(f"   Speaker: {data.get('speaker', 'Unknown')}")
                    print(f"   Confidence: {data.get('confidence', 0.0)}")
                    return True
                else:
                    print(f"❌ Unexpected response type: {message.get('type')}")
                    return False

            except asyncio.TimeoutError:
                print("❌ Response timeout for basic audio chunk")
                return False

    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

async def test_meeting_events():
    """Test meeting event processing"""
    print("\n=== Testing Meeting Events ===")

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Send handshake first
            handshake = create_handshake_message()
            await websocket.send(json.dumps(handshake))
            await websocket.recv()  # Wait for handshake ack

            # Send meeting started event
            meeting_event = create_meeting_event_message("meeting_started")
            print("📤 Sending meeting started event")
            await websocket.send(json.dumps(meeting_event))

            # Wait for acknowledgment
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)

                if message.get("type") == "MEETING_EVENT_ACK":
                    print("✅ Meeting event acknowledged")
                    return True
                else:
                    print(f"❌ Unexpected response: {message.get('type')}")
                    return False

            except asyncio.TimeoutError:
                print("❌ Meeting event timeout")
                return False

    except Exception as e:
        print(f"❌ Meeting event test failed: {e}")
        return False

async def test_mixed_message_flow():
    """Test mixed message flow - enhanced chunks, basic chunks, and events"""
    print("\n=== Testing Mixed Message Flow ===")

    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Handshake
            handshake = create_handshake_message()
            await websocket.send(json.dumps(handshake))
            await websocket.recv()

            print("📤 Sending mixed message sequence...")

            # 1. Meeting started event
            meeting_start = create_meeting_event_message("meeting_started")
            await websocket.send(json.dumps(meeting_start))

            # 2. Enhanced audio chunk
            enhanced_chunk = create_enhanced_audio_chunk_message()
            await websocket.send(json.dumps(enhanced_chunk))

            # 3. Basic audio chunk (same meeting)
            basic_chunk = create_basic_audio_chunk_message()
            await websocket.send(json.dumps(basic_chunk))

            # 4. Participant joined event
            participant_joined = create_meeting_event_message("participant_joined")
            await websocket.send(json.dumps(participant_joined))

            # Collect responses
            responses = []
            response_count = 0
            max_responses = 6  # Expect multiple responses

            while response_count < max_responses:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message = json.loads(response)
                    responses.append(message)
                    response_count += 1

                    print(f"📥 {response_count}: {message.get('type')}")

                except asyncio.TimeoutError:
                    break

            print(f"✅ Mixed flow completed: {len(responses)} responses received")

            # Verify we got expected message types
            response_types = [r.get('type') for r in responses]
            expected_types = ['MEETING_EVENT_ACK', 'transcription_result', 'TRANSCRIPTION_RESULT', 'MEETING_UPDATE']

            found_types = [t for t in expected_types if t in response_types]
            print(f"   Expected message types found: {len(found_types)}/{len(expected_types)}")

            return len(found_types) >= 2  # At least some core functionality working

    except Exception as e:
        print(f"❌ Mixed message flow failed: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting End-to-End Integration Tests")
    print("=" * 60)
    print(f"WebSocket URL: {WEBSOCKET_URL}")
    print(f"Test Timeout: {TEST_TIMEOUT}s")
    print()

    tests = [
        ("WebSocket Connection", test_websocket_connection),
        ("Enhanced Audio Processing", test_enhanced_audio_processing),
        ("Backward Compatibility", test_backward_compatibility),
        ("Meeting Events", test_meeting_events),
        ("Mixed Message Flow", test_mixed_message_flow)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            result = await asyncio.wait_for(test_func(), timeout=TEST_TIMEOUT)
            results.append((test_name, result))

            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")

        except asyncio.TimeoutError:
            print(f"⏰ {test_name} TIMEOUT")
            results.append((test_name, False))
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            results.append((test_name, False))

        print()

    # Summary
    print("=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the AI processing backend server.")
        return False

def check_server_status():
    """Check if the AI processing server is running"""
    import socket
    try:
        # Extract host and port from WebSocket URL
        url_parts = WEBSOCKET_URL.replace('ws://', '').replace('wss://', '').split('/')
        host_port = url_parts[0].split(':')
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 8000

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()

        return result == 0
    except Exception:
        return False

async def main():
    """Main test runner"""
    print("🔍 Checking server status...")

    if not check_server_status():
        print("❌ AI processing server not accessible")
        print(f"   Make sure the server is running at {WEBSOCKET_URL}")
        print("   Start the server with: cd ai_processing && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False

    print("✅ Server is accessible")

    try:
        success = await run_integration_tests()
        return success
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
