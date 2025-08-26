#!/usr/bin/env python3
"""
Test script for Chrome Extension WebSocket Mock Server

This script tests the WebSocket mock server by sending various
audio chunk formats and verifying the responses.
"""

import asyncio
import json
import logging
import random
import base64
from datetime import datetime, timezone
from typing import Dict, List, Optional
import websockets
from websockets.client import WebSocketClientProtocol
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChromeExtensionMockServerTest:
    """Test client for Chrome Extension WebSocket Mock Server"""

    def __init__(self, server_url: str = "ws://localhost:8000/ws/audio"):
        self.server_url = server_url
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.test_results: Dict[str, bool] = {}
        self.received_messages: List[Dict] = []

    async def connect(self) -> bool:
        """Connect to the WebSocket server"""
        try:
            logger.info(f"Connecting to {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            logger.info("Connected successfully")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")

    async def send_message(self, message: Dict) -> bool:
        """Send a message to the server"""
        try:
            if not self.websocket:
                logger.error("Not connected to server")
                return False

            message_json = json.dumps(message)
            await self.websocket.send(message_json)
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def receive_message(self, timeout: float = 5.0) -> Optional[Dict]:
        """Receive a message from the server"""
        try:
            if not self.websocket:
                return None

            message = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )

            data = json.loads(message)
            self.received_messages.append(data)
            logger.debug(f"Received message: {data.get('type', 'unknown')}")
            return data
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for message")
            return None
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            return None

    def generate_mock_audio_data(self) -> str:
        """Generate mock base64 audio data"""
        # Create some fake audio data
        mock_data = b'\x52\x49\x46\x46' + b'\x00' * 1020  # Basic WAV header + silence
        return base64.b64encode(mock_data).decode('utf-8')

    async def test_connection_establishment(self) -> bool:
        """Test basic connection and welcome message"""
        logger.info("Testing connection establishment...")

        # Should receive welcome message upon connection
        welcome_msg = await self.receive_message()

        if welcome_msg and welcome_msg.get('type') == 'CONNECTION_ESTABLISHED':
            logger.info("✓ Connection establishment test passed")
            self.test_results['connection'] = True
            return True
        else:
            logger.error("✗ Connection establishment test failed")
            self.test_results['connection'] = False
            return False

    async def test_basic_audio_chunk(self) -> bool:
        """Test basic audio chunk processing"""
        logger.info("Testing basic audio chunk...")

        message = {
            "type": "audio_chunk",
            "data": self.generate_mock_audio_data(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "platform": "google-meet",
                "meetingUrl": "https://meet.google.com/test-meeting",
                "chunkSize": 1024,
                "sampleRate": 16000
            }
        }

        if await self.send_message(message):
            response = await self.receive_message()

            if response and response.get('type') == 'TRANSCRIPTION_RESULT':
                logger.info("✓ Basic audio chunk test passed")
                self.test_results['basic_audio'] = True
                return True

        logger.error("✗ Basic audio chunk test failed")
        self.test_results['basic_audio'] = False
        return False

    async def test_enhanced_audio_chunk(self) -> bool:
        """Test enhanced audio chunk with participant data"""
        logger.info("Testing enhanced audio chunk with participants...")

        message = {
            "type": "AUDIO_CHUNK_ENHANCED",
            "data": self.generate_mock_audio_data(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": "google-meet",
            "meetingUrl": "https://meet.google.com/test-enhanced-meeting",
            "participants": [
                {
                    "id": "participant_1",
                    "name": "John Doe",
                    "platform_id": "google_meet_user_123",
                    "status": "active",
                    "is_host": True,
                    "join_time": "2025-01-09T10:00:00Z"
                },
                {
                    "id": "participant_2",
                    "name": "Jane Smith",
                    "platform_id": "google_meet_user_456",
                    "status": "active",
                    "is_host": False,
                    "join_time": "2025-01-09T10:00:30Z"
                }
            ],
            "participant_count": 2,
            "metadata": {
                "chunk_size": 1024,
                "sample_rate": 16000,
                "channels": 1,
                "format": "webm"
            }
        }

        if await self.send_message(message):
            response = await self.receive_message()

            if (response and
                response.get('type') == 'TRANSCRIPTION_RESULT' and
                response.get('data', {}).get('speaker_id') is not None):
                logger.info("✓ Enhanced audio chunk test passed")
                self.test_results['enhanced_audio'] = True
                return True

        logger.error("✗ Enhanced audio chunk test failed")
        self.test_results['enhanced_audio'] = False
        return False

    async def test_meeting_events(self) -> bool:
        """Test meeting event handling"""
        logger.info("Testing meeting events...")

        message = {
            "type": "MEETING_EVENT",
            "eventType": "participant_joined",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "meetingId": "test_meeting_123",
                "participant": {
                    "id": "participant_3",
                    "name": "Bob Johnson",
                    "platform_id": "google_meet_user_789",
                    "status": "active",
                    "is_host": False,
                    "join_time": datetime.now(timezone.utc).isoformat()
                },
                "total_participants": 3
            }
        }

        if await self.send_message(message):
            response = await self.receive_message()

            if response and response.get('type') == 'EVENT_ACKNOWLEDGED':
                logger.info("✓ Meeting events test passed")
                self.test_results['meeting_events'] = True
                return True

        logger.error("✗ Meeting events test failed")
        self.test_results['meeting_events'] = False
        return False

    async def test_session_info_request(self) -> bool:
        """Test session information request"""
        logger.info("Testing session info request...")

        # First send an enhanced audio chunk to create a session
        setup_message = {
            "type": "AUDIO_CHUNK_ENHANCED",
            "data": self.generate_mock_audio_data(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platform": "zoom",
            "meetingUrl": "https://zoom.us/j/test123456",
            "participants": [
                {
                    "id": "participant_1",
                    "name": "Test User",
                    "platform_id": "zoom_user_123",
                    "status": "active",
                    "is_host": True,
                    "join_time": datetime.now(timezone.utc).isoformat()
                }
            ],
            "participant_count": 1,
            "metadata": {"chunk_size": 1024, "sample_rate": 16000}
        }

        if await self.send_message(setup_message):
            # Wait for transcription result
            await self.receive_message()

            # Now request session info
            info_request = {
                "type": "GET_SESSION_INFO",
                "meeting_id": "test123456"
            }

            if await self.send_message(info_request):
                response = await self.receive_message()

                if (response and
                    response.get('type') == 'SESSION_INFO' and
                    response.get('participant_count') == 1):
                    logger.info("✓ Session info request test passed")
                    self.test_results['session_info'] = True
                    return True

        logger.error("✗ Session info request test failed")
        self.test_results['session_info'] = False
        return False

    async def test_multiple_audio_chunks(self) -> bool:
        """Test handling multiple audio chunks (simulates real usage)"""
        logger.info("Testing multiple audio chunks...")

        success_count = 0
        total_chunks = 5

        for i in range(total_chunks):
            message = {
                "type": "AUDIO_CHUNK_ENHANCED",
                "data": self.generate_mock_audio_data(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "platform": "teams",
                "meetingUrl": f"https://teams.microsoft.com/test-multi-{i}",
                "participants": [
                    {
                        "id": f"participant_{i}",
                        "name": f"User {i}",
                        "platform_id": f"teams_user_{i}",
                        "status": "active",
                        "is_host": i == 0,
                        "join_time": datetime.now(timezone.utc).isoformat()
                    }
                ],
                "participant_count": 1,
                "metadata": {"chunk_size": 1024, "sample_rate": 16000}
            }

            if await self.send_message(message):
                response = await self.receive_message()
                if response and response.get('type') == 'TRANSCRIPTION_RESULT':
                    success_count += 1

            # Small delay between chunks
            await asyncio.sleep(0.2)

        if success_count >= total_chunks - 1:  # Allow for one failure
            logger.info(f"✓ Multiple audio chunks test passed ({success_count}/{total_chunks})")
            self.test_results['multiple_chunks'] = True
            return True
        else:
            logger.error(f"✗ Multiple audio chunks test failed ({success_count}/{total_chunks})")
            self.test_results['multiple_chunks'] = False
            return False

    async def test_invalid_messages(self) -> bool:
        """Test handling of invalid messages"""
        logger.info("Testing invalid message handling...")

        # Test invalid JSON
        try:
            if self.websocket:
                await self.websocket.send("invalid json")
                response = await self.receive_message()

                if response and response.get('type') == 'ERROR':
                    logger.info("✓ Invalid JSON handling test passed")
                    self.test_results['invalid_messages'] = True
                    return True
        except Exception as e:
            logger.debug(f"Expected error for invalid JSON: {e}")

        # Test unknown message type
        invalid_message = {
            "type": "UNKNOWN_MESSAGE_TYPE",
            "data": "test"
        }

        if await self.send_message(invalid_message):
            response = await self.receive_message()
            if response and response.get('type') == 'ERROR':
                logger.info("✓ Unknown message type handling test passed")
                self.test_results['invalid_messages'] = True
                return True

        logger.error("✗ Invalid message handling test failed")
        self.test_results['invalid_messages'] = False
        return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests"""
        logger.info("Starting Chrome Extension Mock Server tests...")
        logger.info("=" * 60)

        if not await self.connect():
            logger.error("Failed to connect to server. Is it running?")
            return {"connection": False}

        try:
            # Run tests in order
            await self.test_connection_establishment()
            await asyncio.sleep(1)

            await self.test_basic_audio_chunk()
            await asyncio.sleep(1)

            await self.test_enhanced_audio_chunk()
            await asyncio.sleep(1)

            await self.test_meeting_events()
            await asyncio.sleep(1)

            await self.test_session_info_request()
            await asyncio.sleep(1)

            await self.test_multiple_audio_chunks()
            await asyncio.sleep(1)

            await self.test_invalid_messages()

        except Exception as e:
            logger.error(f"Test execution error: {e}")
        finally:
            await self.disconnect()

        return self.test_results

    def print_test_summary(self):
        """Print test results summary"""
        logger.info("=" * 60)
        logger.info("Test Results Summary:")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        for test_name, passed in self.test_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title():<30} {status}")

        logger.info("-" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning("⚠️  Some tests failed. Check the logs above.")

        logger.info("=" * 60)
        logger.info(f"Received {len(self.received_messages)} total messages from server")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Chrome Extension WebSocket Mock Server")
    parser.add_argument('--server', default='ws://localhost:8000/ws/audio',
                       help='WebSocket server URL (default: ws://localhost:8000/ws/audio)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run tests
    tester = ChromeExtensionMockServerTest(args.server)

    try:
        results = await tester.run_all_tests()
        tester.print_test_summary()

        # Exit with appropriate code
        all_passed = all(results.values()) if results else False
        exit_code = 0 if all_passed else 1

        return exit_code

    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
