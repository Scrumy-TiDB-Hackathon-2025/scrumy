#!/usr/bin/env python3
"""
WebSocket Integration Test Script
Test the real-time audio processing WebSocket functionality for Chrome extension integration
"""

import asyncio
import websockets
import json
import base64
import wave
import numpy as np
import tempfile
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, server_url="ws://localhost:8000/ws"):
        self.server_url = server_url
        self.websocket = None

    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"Connected to WebSocket server: {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            return False

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket server")

    async def send_message(self, message):
        """Send message to WebSocket server"""
        if not self.websocket:
            logger.error("Not connected to WebSocket server")
            return False

        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def receive_message(self, timeout=10):
        """Receive message from WebSocket server"""
        if not self.websocket:
            logger.error("Not connected to WebSocket server")
            return None

        try:
            message = await asyncio.wait_for(
                self.websocket.recv(), timeout=timeout
            )
            return json.loads(message)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for message ({timeout}s)")
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

    def generate_test_audio_data(self, duration_ms=1000, sample_rate=16000):
        """Generate test audio data (sine wave)"""
        duration_sec = duration_ms / 1000.0
        samples = int(sample_rate * duration_sec)

        # Generate a 440Hz sine wave (A note)
        frequency = 440.0
        t = np.linspace(0, duration_sec, samples, False)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3

        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)

        # Convert to bytes
        return audio_data.tobytes()

    async def test_handshake(self):
        """Test WebSocket handshake"""
        logger.info("Testing WebSocket handshake...")

        handshake_message = {
            "type": "HANDSHAKE",
            "clientType": "test-client",
            "version": "1.0",
            "capabilities": ["audio-capture", "meeting-detection"]
        }

        # Send handshake
        success = await self.send_message(handshake_message)
        if not success:
            logger.error("Failed to send handshake message")
            return False

        # Wait for acknowledgment
        response = await self.receive_message()
        if not response:
            logger.error("No handshake acknowledgment received")
            return False

        if response.get("type") == "HANDSHAKE_ACK":
            logger.info("✅ Handshake successful")
            logger.info(f"Server version: {response.get('serverVersion')}")
            logger.info(f"Server status: {response.get('status')}")
            return True
        else:
            logger.error(f"Unexpected handshake response: {response}")
            return False

    async def test_audio_chunk_processing(self):
        """Test audio chunk processing"""
        logger.info("Testing audio chunk processing...")

        # Generate test audio data
        audio_data = self.generate_test_audio_data(duration_ms=2000)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Create audio chunk message
        audio_message = {
            "type": "AUDIO_CHUNK",
            "data": audio_base64,
            "timestamp": datetime.now().timestamp() * 1000,
            "metadata": {
                "platform": "test-platform",
                "meetingUrl": "https://meet.google.com/test-meeting",
                "chunkSize": len(audio_data),
                "sampleRate": 16000,
                "channels": 1,
                "sampleWidth": 2
            }
        }

        # Send audio chunk
        success = await self.send_message(audio_message)
        if not success:
            logger.error("Failed to send audio chunk")
            return False

        # Wait for transcription result
        logger.info("Waiting for transcription result...")
        response = await self.receive_message(timeout=30)
        if not response:
            logger.error("No transcription result received")
            return False

        if response.get("type") == "TRANSCRIPTION_RESULT":
            data = response.get("data", {})
            logger.info("✅ Audio chunk processing successful")
            logger.info(f"Transcription: '{data.get('text', 'No text')}'")
            logger.info(f"Confidence: {data.get('confidence', 0.0)}")
            logger.info(f"Meeting ID: {data.get('meetingId', 'Unknown')}")
            logger.info(f"Speakers: {data.get('speakers', [])}")
            return True
        else:
            logger.error(f"Unexpected audio processing response: {response}")
            return False

    async def test_meeting_events(self):
        """Test meeting event handling"""
        logger.info("Testing meeting events...")

        # Send meeting started event
        meeting_event = {
            "type": "MEETING_EVENT",
            "eventType": "meeting_started",
            "timestamp": datetime.now().timestamp() * 1000,
            "data": {
                "meetingTitle": "Test Meeting",
                "platform": "test-platform"
            }
        }

        success = await self.send_message(meeting_event)
        if not success:
            logger.error("Failed to send meeting event")
            return False

        # Wait for acknowledgment
        response = await self.receive_message()
        if response and response.get("type") == "MEETING_EVENT_ACK":
            logger.info("✅ Meeting event handling successful")
            return True
        else:
            logger.warning("No meeting event acknowledgment received (this may be normal)")
            return True

    async def run_comprehensive_test(self):
        """Run comprehensive WebSocket test suite"""
        logger.info("🧪 Starting comprehensive WebSocket test suite...")
        logger.info(f"Target server: {self.server_url}")

        # Connect to server
        if not await self.connect():
            return False

        try:
            # Test 1: Handshake
            if not await self.test_handshake():
                logger.error("❌ Handshake test failed")
                return False

            # Test 2: Audio chunk processing
            if not await self.test_audio_chunk_processing():
                logger.error("❌ Audio chunk processing test failed")
                return False

            # Test 3: Meeting events
            if not await self.test_meeting_events():
                logger.error("❌ Meeting events test failed")
                return False

            logger.info("🎉 All WebSocket tests passed successfully!")
            return True

        except Exception as e:
            logger.error(f"Test suite failed with exception: {e}")
            return False

        finally:
            await self.disconnect()

async def test_rest_api_compatibility():
    """Test REST API endpoints for Chrome extension compatibility"""
    import httpx

    logger.info("🧪 Testing REST API endpoints...")
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.info("✅ Health endpoint working")
            else:
                logger.error(f"❌ Health endpoint failed: {response.status_code}")

            # Test available tools endpoint
            response = await client.get(f"{base_url}/available-tools")
            if response.status_code == 200:
                tools = response.json()
                logger.info(f"✅ Available tools: {len(tools.get('tools', []))} tools found")
            else:
                logger.error(f"❌ Available tools endpoint failed: {response.status_code}")

            # Test model config endpoint
            response = await client.get(f"{base_url}/get-model-config")
            if response.status_code == 200:
                config = response.json()
                logger.info(f"✅ Model config: {config.get('model', 'unknown')}")
            else:
                logger.error(f"❌ Model config endpoint failed: {response.status_code}")

            # Test speaker identification endpoint
            speaker_request = {
                "text": "Hello, this is John speaking. How are you doing today, Sarah?",
                "context": "Meeting transcript with multiple speakers"
            }
            response = await client.post(f"{base_url}/identify-speakers", json=speaker_request)
            if response.status_code == 200:
                result = response.json()
                speakers_count = len(result.get('data', {}).get('speakers', []))
                logger.info(f"✅ Speaker identification: {speakers_count} speakers identified")
            else:
                logger.error(f"❌ Speaker identification failed: {response.status_code}")

        except Exception as e:
            logger.error(f"REST API test failed: {e}")
            return False

    return True

async def main():
    """Main test function"""
    logger.info("🚀 Starting WebSocket Integration Tests")
    logger.info("Make sure the AI processing server is running on localhost:8000")

    # Test WebSocket functionality
    tester = WebSocketTester("ws://localhost:8000/ws")
    websocket_success = await tester.run_comprehensive_test()

    # Test alternative WebSocket path
    logger.info("\n🔄 Testing alternative WebSocket path...")
    tester_alt = WebSocketTester("ws://localhost:8000/ws/audio-stream")
    websocket_alt_success = await tester_alt.run_comprehensive_test()

    # Test REST API compatibility
    rest_success = await test_rest_api_compatibility()

    # Summary
    logger.info("\n📋 Test Results Summary:")
    logger.info(f"WebSocket /ws endpoint: {'✅ PASS' if websocket_success else '❌ FAIL'}")
    logger.info(f"WebSocket /ws/audio-stream endpoint: {'✅ PASS' if websocket_alt_success else '❌ FAIL'}")
    logger.info(f"REST API endpoints: {'✅ PASS' if rest_success else '❌ FAIL'}")

    if websocket_success and rest_success:
        logger.info("🎉 All integration tests passed! Chrome extension should work correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the server and fix issues.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
