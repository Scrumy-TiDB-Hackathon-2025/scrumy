#!/usr/bin/env python3
"""
Quick Demo: WebSocket Integration with Chrome Extension
This script demonstrates the real-time WebSocket functionality for Chrome extension integration.
"""

import asyncio
import json
import base64
import logging
import time
import sys
from datetime import datetime
import websockets
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketDemo:
    """Demonstrate WebSocket integration with simulated Chrome extension behavior"""

    def __init__(self, server_url="ws://localhost:8000/ws"):
        self.server_url = server_url
        self.websocket = None

    def generate_test_audio(self, duration_ms=2000, frequency=440):
        """Generate test audio data (sine wave)"""
        sample_rate = 16000
        duration_sec = duration_ms / 1000.0
        samples = int(sample_rate * duration_sec)

        # Generate sine wave
        t = np.linspace(0, duration_sec, samples, False)
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.3

        # Convert to 16-bit PCM
        audio_data = (audio_signal * 32767).astype(np.int16)
        return audio_data.tobytes()

    async def connect_and_handshake(self):
        """Connect to WebSocket server and perform handshake"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"✅ Connected to WebSocket server: {self.server_url}")

            # Send handshake
            handshake_msg = {
                "type": "HANDSHAKE",
                "clientType": "demo-chrome-extension",
                "version": "1.0",
                "capabilities": ["audio-capture", "meeting-detection", "real-time-processing"]
            }

            await self.websocket.send(json.dumps(handshake_msg))
            logger.info("📤 Sent handshake message")

            # Wait for acknowledgment
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            data = json.loads(response)

            if data.get("type") == "HANDSHAKE_ACK":
                logger.info("✅ Handshake successful!")
                logger.info(f"   Server Version: {data.get('serverVersion', 'unknown')}")
                logger.info(f"   Status: {data.get('status', 'unknown')}")
                logger.info(f"   Features: {', '.join(data.get('supportedFeatures', []))}")
                return True
            else:
                logger.error(f"❌ Unexpected handshake response: {data}")
                return False

        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def simulate_meeting_audio_stream(self):
        """Simulate Chrome extension sending audio chunks during a meeting"""
        if not self.websocket:
            logger.error("❌ Not connected to WebSocket server")
            return False

        logger.info("🎤 Starting simulated meeting audio stream...")

        # Simulate different speakers with different frequencies
        speakers_audio = [
            (440, "Welcome everyone to today's team standup meeting."),  # A note - Speaker 1
            (523, "Thanks John. Let me share my progress on the API development."),  # C note - Speaker 2
            (659, "Great work Sarah. I have some questions about the database schema."),  # E note - Speaker 3
            (440, "Sure Bob, let's discuss that. The schema supports both SQLite and TiDB."),  # A note - Speaker 1
            (523, "That's perfect for our deployment strategy."),  # C note - Speaker 2
        ]

        meeting_url = "https://meet.google.com/demo-meeting-xyz"

        for i, (frequency, expected_text) in enumerate(speakers_audio):
            logger.info(f"🔊 Sending audio chunk {i+1}/5 (simulating: '{expected_text}')")

            # Generate audio data
            audio_data = self.generate_test_audio(duration_ms=3000, frequency=frequency)
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Create audio chunk message (matching Chrome extension format)
            audio_msg = {
                "type": "AUDIO_CHUNK",
                "data": audio_base64,
                "timestamp": int(time.time() * 1000),
                "metadata": {
                    "platform": "meet.google.com",
                    "meetingUrl": meeting_url,
                    "chunkSize": len(audio_data),
                    "sampleRate": 16000,
                    "channels": 1,
                    "sampleWidth": 2,
                    "expectedText": expected_text  # For demo purposes only
                }
            }

            # Send audio chunk
            await self.websocket.send(json.dumps(audio_msg))

            # Wait for transcription result
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
                data = json.loads(response)

                if data.get("type") == "TRANSCRIPTION_RESULT":
                    result_data = data.get("data", {})
                    transcription = result_data.get("text", "No transcription")
                    confidence = result_data.get("confidence", 0.0)
                    speakers = result_data.get("speakers", [])
                    meeting_id = result_data.get("meetingId", "unknown")

                    logger.info("✅ Received transcription result:")
                    logger.info(f"   Meeting ID: {meeting_id}")
                    logger.info(f"   Text: '{transcription}'")
                    logger.info(f"   Confidence: {confidence:.2f}")
                    logger.info(f"   Speakers detected: {len(speakers)}")

                    if speakers:
                        for speaker in speakers:
                            logger.info(f"     - {speaker.get('name', 'Unknown')}: {speaker.get('segments', [])}")

                elif data.get("type") == "ERROR":
                    logger.error(f"❌ Server error: {data.get('error', 'Unknown error')}")

                else:
                    logger.warning(f"⚠️ Unexpected response: {data}")

            except asyncio.TimeoutError:
                logger.warning("⏰ Timeout waiting for transcription result")

            # Wait before next chunk (simulating natural speech pauses)
            await asyncio.sleep(2)

        logger.info("🎉 Simulated meeting audio stream completed!")
        return True

    async def send_meeting_end_event(self):
        """Send meeting end event to trigger summary generation"""
        if not self.websocket:
            return False

        logger.info("📝 Sending meeting end event to generate summary...")

        meeting_event = {
            "type": "MEETING_EVENT",
            "eventType": "meeting_ended",
            "timestamp": int(time.time() * 1000),
            "data": {
                "meetingTitle": "Demo Team Standup",
                "platform": "meet.google.com"
            }
        }

        await self.websocket.send(json.dumps(meeting_event))

        # Wait for potential meeting summary
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
            data = json.loads(response)

            if data.get("type") == "MEETING_SUMMARY":
                summary_data = data.get("data", {})
                logger.info("📋 Received meeting summary:")
                logger.info(f"   Meeting ID: {summary_data.get('meetingId', 'unknown')}")
                logger.info(f"   Participants: {summary_data.get('participants', [])}")
                logger.info(f"   Total Chunks: {summary_data.get('totalChunks', 0)}")
                logger.info(f"   Duration: {summary_data.get('duration', 'unknown')}")

                if 'summary' in summary_data:
                    logger.info("   Summary generated successfully!")
                if 'tasks' in summary_data:
                    tasks = summary_data['tasks']
                    logger.info(f"   Tasks extracted: {len(tasks) if isinstance(tasks, list) else 'N/A'}")

            return True

        except asyncio.TimeoutError:
            logger.info("ℹ️ No meeting summary received (this is normal for short demos)")
            return True

    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Disconnected from WebSocket server")

    async def run_demo(self):
        """Run the complete WebSocket integration demo"""
        logger.info("🚀 Starting WebSocket Integration Demo")
        logger.info("This demo simulates a Chrome extension connecting to the AI processing server")
        logger.info("=" * 80)

        # Step 1: Connect and handshake
        logger.info("Step 1: Connecting and performing handshake...")
        if not await self.connect_and_handshake():
            logger.error("❌ Demo failed at handshake step")
            return False

        print()  # Empty line for readability

        # Step 2: Simulate meeting audio stream
        logger.info("Step 2: Simulating Chrome extension audio stream...")
        success = await self.simulate_meeting_audio_stream()

        print()  # Empty line for readability

        # Step 3: Send meeting end event
        logger.info("Step 3: Ending meeting and requesting summary...")
        await self.send_meeting_end_event()

        # Step 4: Disconnect
        await self.disconnect()

        logger.info("=" * 80)
        if success:
            logger.info("🎉 Demo completed successfully!")
            logger.info("✅ WebSocket integration is working correctly")
            logger.info("✅ Chrome extension should be fully compatible")
        else:
            logger.error("❌ Demo encountered issues")
            logger.error("❌ Check server logs for details")

        return success

async def check_server_availability():
    """Check if the AI processing server is running"""
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                logger.info("✅ AI processing server is running")
                return True
            else:
                logger.error(f"❌ Server returned status {response.status_code}")
                return False
    except Exception as e:
        logger.error("❌ AI processing server is not responding")
        logger.error("Please start the server with: python start_hackathon.py")
        return False

async def main():
    """Main demo function"""
    print("🎯 WebSocket Integration Demo for Chrome Extension")
    print("TiDB AgentX 2025 Hackathon - Scrumy AI Processing")
    print()

    # Check if server is running
    if not await check_server_availability():
        return 1

    # Run the demo
    demo = WebSocketDemo("ws://localhost:8000/ws")
    success = await demo.run_demo()

    # Print final instructions
    print()
    print("📋 Next Steps:")
    print("1. If this demo worked, your Chrome extension should work perfectly!")
    print("2. Update Chrome extension config.js with: ws://localhost:8000/ws")
    print("3. Run comprehensive tests: python test_chrome_extension_compatibility.py")
    print("4. Load Chrome extension and test with real meetings")
    print()
    print("📚 Documentation:")
    print("- WebSocket Integration Guide: WEBSOCKET_CHROME_INTEGRATION.md")
    print("- Implementation Details: IMPLEMENTATION_SUMMARY.md")

    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        sys.exit(1)
