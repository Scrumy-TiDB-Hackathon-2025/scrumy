#!/usr/bin/env python3
"""
Chrome Extension Compatibility Test
Test the complete integration between AI processing backend and Chrome extension

This test validates that the backend is fully compatible with the Chrome extension's
expected communication patterns and data formats.
"""

import asyncio
import json
import base64
import logging
import sys
import time
from datetime import datetime
import httpx
import websockets
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromeExtensionCompatibilityTester:
    """Test Chrome extension compatibility with the AI processing backend"""

    def __init__(self, base_url="http://localhost:8000", websocket_url="ws://localhost:8000/ws"):
        self.base_url = base_url
        self.websocket_url = websocket_url
        self.test_results = []

    def log_test_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if details:
            logger.info(f"  Details: {details}")

        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    async def test_health_endpoint(self):
        """Test the health endpoint - Chrome extension uses this for server status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")

                if response.status_code == 200:
                    data = response.json()
                    expected_format = data.get("status") == "healthy"
                    self.log_test_result(
                        "Health Endpoint",
                        expected_format,
                        f"Status: {data.get('status', 'unknown')}"
                    )
                    return expected_format
                else:
                    self.log_test_result("Health Endpoint", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Health Endpoint", False, str(e))
            return False

    async def test_model_config_endpoint(self):
        """Test model configuration endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/get-model-config")

                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["model", "language", "sample_rate", "chunk_length"]
                    has_all_fields = all(field in data for field in required_fields)

                    self.log_test_result(
                        "Model Config Endpoint",
                        has_all_fields,
                        f"Model: {data.get('model', 'unknown')}, Sample Rate: {data.get('sample_rate', 'unknown')}"
                    )
                    return has_all_fields
                else:
                    self.log_test_result("Model Config Endpoint", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Model Config Endpoint", False, str(e))
            return False

    async def test_available_tools_endpoint(self):
        """Test available tools endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/available-tools")

                if response.status_code == 200:
                    data = response.json()
                    expected_tools = ["identify_speakers", "extract_tasks", "generate_summary"]
                    has_tools = "tools" in data and "tool_names" in data
                    tool_names = data.get("tool_names", [])
                    has_expected_tools = all(tool in tool_names for tool in expected_tools)

                    success = has_tools and has_expected_tools
                    self.log_test_result(
                        "Available Tools Endpoint",
                        success,
                        f"Tools found: {len(tool_names)}, Expected tools present: {has_expected_tools}"
                    )
                    return success
                else:
                    self.log_test_result("Available Tools Endpoint", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Available Tools Endpoint", False, str(e))
            return False

    async def test_speaker_identification(self):
        """Test speaker identification endpoint with Chrome extension format"""
        try:
            # Test data simulating what Chrome extension would send
            test_request = {
                "text": "Hello everyone, this is John speaking. How are you doing today, Sarah? I'm doing well, thank you for asking, replies Sarah.",
                "context": "Meeting transcript with multiple speakers discussing project status"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/identify-speakers",
                    json=test_request,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verify Chrome extension expected format
                    has_status = data.get("status") == "success"
                    has_data = "data" in data
                    has_speakers = "speakers" in data.get("data", {})
                    speakers = data.get("data", {}).get("speakers", [])

                    # Check speaker format
                    valid_speaker_format = True
                    if speakers:
                        for speaker in speakers[:2]:  # Check first 2 speakers
                            required_fields = ["id", "name", "segments"]
                            if not all(field in speaker for field in required_fields):
                                valid_speaker_format = False
                                break

                    success = has_status and has_data and has_speakers and valid_speaker_format
                    self.log_test_result(
                        "Speaker Identification",
                        success,
                        f"Speakers found: {len(speakers)}, Format valid: {valid_speaker_format}"
                    )
                    return success
                else:
                    self.log_test_result("Speaker Identification", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Speaker Identification", False, str(e))
            return False

    async def test_summary_generation(self):
        """Test summary generation endpoint"""
        try:
            test_request = {
                "transcript": "Meeting started at 9 AM. John discussed the project timeline. Sarah mentioned the budget concerns. Bob suggested we meet again next week to finalize details. The meeting ended with action items assigned.",
                "meeting_id": "test-meeting-123",
                "meeting_title": "Weekly Team Standup"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate-summary",
                    json=test_request,
                    timeout=45.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verify Chrome extension expected format
                    has_status = data.get("status") == "success"
                    has_data = "data" in data
                    summary_data = data.get("data", {})

                    expected_sections = ["meeting_title", "executive_summary", "participants"]
                    has_expected_sections = all(section in summary_data for section in expected_sections)

                    success = has_status and has_data and has_expected_sections
                    self.log_test_result(
                        "Summary Generation",
                        success,
                        f"Has required sections: {has_expected_sections}, Title: {summary_data.get('meeting_title', 'unknown')}"
                    )
                    return success
                else:
                    self.log_test_result("Summary Generation", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Summary Generation", False, str(e))
            return False

    async def test_task_extraction(self):
        """Test task extraction endpoint"""
        try:
            test_request = {
                "transcript": "John, please update the documentation by Friday. Sarah, can you review the code changes? Bob will handle the deployment next week. We need to schedule a follow-up meeting.",
                "meeting_context": {
                    "participants": ["John", "Sarah", "Bob"]
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/extract-tasks",
                    json=test_request,
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verify Chrome extension expected format
                    has_status = data.get("status") == "success"
                    has_data = "data" in data
                    task_data = data.get("data", {})

                    has_tasks = "tasks" in task_data
                    has_summary = "task_summary" in task_data
                    tasks = task_data.get("tasks", [])

                    # Check task format
                    valid_task_format = True
                    if tasks:
                        for task in tasks[:2]:  # Check first 2 tasks
                            required_fields = ["id", "title", "assignee", "priority", "status"]
                            if not all(field in task for field in required_fields):
                                valid_task_format = False
                                break

                    success = has_status and has_data and has_tasks and has_summary and valid_task_format
                    self.log_test_result(
                        "Task Extraction",
                        success,
                        f"Tasks found: {len(tasks)}, Format valid: {valid_task_format}"
                    )
                    return success
                else:
                    self.log_test_result("Task Extraction", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Task Extraction", False, str(e))
            return False

    def generate_mock_audio_data(self, duration_ms=2000):
        """Generate mock audio data for WebSocket testing"""
        sample_rate = 16000
        duration_sec = duration_ms / 1000.0
        samples = int(sample_rate * duration_sec)

        # Generate sine wave
        frequency = 440.0  # A note
        t = np.linspace(0, duration_sec, samples, False)
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.3

        # Convert to 16-bit PCM
        audio_data = (audio_signal * 32767).astype(np.int16)
        return audio_data.tobytes()

    async def test_websocket_handshake(self):
        """Test WebSocket handshake - Chrome extension's first step"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Send handshake message
                handshake_msg = {
                    "type": "HANDSHAKE",
                    "clientType": "chrome-extension",
                    "version": "1.0",
                    "capabilities": ["audio-capture", "meeting-detection"]
                }

                await websocket.send(json.dumps(handshake_msg))

                # Wait for acknowledgment
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)

                # Verify expected response format
                is_handshake_ack = data.get("type") == "HANDSHAKE_ACK"
                has_server_version = "serverVersion" in data
                has_status = data.get("status") == "ready"

                success = is_handshake_ack and has_server_version and has_status
                self.log_test_result(
                    "WebSocket Handshake",
                    success,
                    f"Server version: {data.get('serverVersion', 'unknown')}, Status: {data.get('status', 'unknown')}"
                )
                return success

        except Exception as e:
            self.log_test_result("WebSocket Handshake", False, str(e))
            return False

    async def test_websocket_audio_processing(self):
        """Test WebSocket audio chunk processing - Chrome extension's core functionality"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # First, handshake
                handshake_msg = {
                    "type": "HANDSHAKE",
                    "clientType": "chrome-extension-test",
                    "version": "1.0",
                    "capabilities": ["audio-capture"]
                }
                await websocket.send(json.dumps(handshake_msg))
                await websocket.recv()  # Consume handshake ack

                # Generate test audio data
                audio_data = self.generate_mock_audio_data(2000)
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                # Send audio chunk - this is what Chrome extension sends
                audio_msg = {
                    "type": "AUDIO_CHUNK",
                    "data": audio_base64,
                    "timestamp": int(time.time() * 1000),
                    "metadata": {
                        "platform": "meet.google.com",
                        "meetingUrl": "https://meet.google.com/test-meeting-123",
                        "chunkSize": len(audio_data),
                        "sampleRate": 16000,
                        "channels": 1,
                        "sampleWidth": 2
                    }
                }

                await websocket.send(json.dumps(audio_msg))

                # Wait for transcription result
                response = await asyncio.wait_for(websocket.recv(), timeout=60)
                data = json.loads(response)

                # Verify expected response format
                is_transcription = data.get("type") == "TRANSCRIPTION_RESULT"
                has_data = "data" in data
                result_data = data.get("data", {})

                has_text = "text" in result_data
                has_confidence = "confidence" in result_data
                has_meeting_id = "meetingId" in result_data

                success = is_transcription and has_data and has_text and has_confidence and has_meeting_id
                self.log_test_result(
                    "WebSocket Audio Processing",
                    success,
                    f"Transcription received: {len(result_data.get('text', '')) > 0}, Meeting ID: {result_data.get('meetingId', 'unknown')}"
                )
                return success

        except Exception as e:
            self.log_test_result("WebSocket Audio Processing", False, str(e))
            return False

    async def test_comprehensive_processing(self):
        """Test the comprehensive processing endpoint that Chrome extension uses"""
        try:
            test_request = {
                "text": "John said we need to finish the API documentation by Friday. Sarah mentioned she'll handle the testing. Bob will deploy to production next week.",
                "meeting_id": "comprehensive-test-123",
                "timestamp": datetime.now().isoformat(),
                "platform": "meet.google.com"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/process-transcript-with-tools",
                    json=test_request,
                    timeout=60.0
                )

                if response.status_code == 200:
                    data = response.json()

                    # Verify Chrome extension expected format
                    has_status = data.get("status") == "success"
                    has_meeting_id = data.get("meeting_id") == test_request["meeting_id"]
                    has_analysis = "analysis" in data
                    has_actions = "actions_taken" in data
                    has_speakers = "speakers" in data
                    has_tools_used = "tools_used" in data

                    success = all([has_status, has_meeting_id, has_analysis, has_actions, has_speakers, has_tools_used])
                    self.log_test_result(
                        "Comprehensive Processing",
                        success,
                        f"Tools used: {data.get('tools_used', 0)}, Actions: {len(data.get('actions_taken', []))}"
                    )
                    return success
                else:
                    self.log_test_result("Comprehensive Processing", False, f"HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.log_test_result("Comprehensive Processing", False, str(e))
            return False

    async def run_all_tests(self):
        """Run all Chrome extension compatibility tests"""
        logger.info("🚀 Starting Chrome Extension Compatibility Tests")
        logger.info(f"Testing against: {self.base_url} (HTTP) and {self.websocket_url} (WebSocket)")
        logger.info("=" * 80)

        # REST API Tests
        logger.info("📡 Testing REST API Endpoints...")
        rest_tests = [
            self.test_health_endpoint(),
            self.test_model_config_endpoint(),
            self.test_available_tools_endpoint(),
            self.test_speaker_identification(),
            self.test_summary_generation(),
            self.test_task_extraction(),
            self.test_comprehensive_processing()
        ]

        rest_results = await asyncio.gather(*rest_tests, return_exceptions=True)
        rest_passed = sum(1 for result in rest_results if result is True)

        logger.info(f"REST API Tests: {rest_passed}/{len(rest_tests)} passed")
        logger.info("=" * 40)

        # WebSocket Tests
        logger.info("🔌 Testing WebSocket Endpoints...")
        websocket_tests = [
            self.test_websocket_handshake(),
            self.test_websocket_audio_processing()
        ]

        ws_results = await asyncio.gather(*websocket_tests, return_exceptions=True)
        ws_passed = sum(1 for result in ws_results if result is True)

        logger.info(f"WebSocket Tests: {ws_passed}/{len(websocket_tests)} passed")
        logger.info("=" * 80)

        # Summary
        total_tests = len(rest_tests) + len(websocket_tests)
        total_passed = rest_passed + ws_passed

        logger.info("📋 TEST RESULTS SUMMARY:")
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {total_passed}")
        logger.info(f"Failed: {total_tests - total_passed}")
        logger.info(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")

        if total_passed == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Chrome extension should work perfectly.")
            return True
        else:
            logger.error("❌ Some tests failed. Chrome extension may not work correctly.")
            logger.info("\nFailed tests need to be fixed before Chrome extension integration.")
            return False

async def main():
    """Main test execution"""
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
    except Exception as e:
        logger.error("🚨 Server not responding at http://localhost:8000")
        logger.error("Please start the server with: python start_hackathon.py")
        return 1

    # Run compatibility tests
    tester = ChromeExtensionCompatibilityTester()
    success = await tester.run_all_tests()

    # Save results
    results_file = f"chrome_extension_compatibility_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "tests": tester.test_results
        }, f, indent=2)

    logger.info(f"📄 Detailed results saved to: {results_file}")

    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
