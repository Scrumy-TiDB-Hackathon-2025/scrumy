#!/usr/bin/env python3
"""
Participant Integration Test for TiDB AgentX 2025 Hackathon
Tests the complete participant data flow from Chrome extension to AI processing
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database_config import DatabaseConfig, print_hackathon_banner
from app.database_interface import DatabaseFactory, validate_database_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ParticipantIntegrationTest:
    """Test class for participant integration functionality"""

    def __init__(self):
        self.db = None
        self.test_meeting_id = "test-participant-integration"

    async def setup(self):
        """Setup test environment"""
        logger.info("Setting up participant integration test...")

        # Get database configuration
        config = DatabaseConfig.get_config_from_env()

        if not validate_database_config(config):
            raise Exception("Invalid database configuration")

        self.db = DatabaseFactory.create_from_config(config)

        # Test connection
        if not await self.db.health_check():
            raise Exception("Database health check failed")

        logger.info(f"✅ Connected to {config['type'].upper()} database")

    async def cleanup(self):
        """Cleanup test data"""
        logger.info("Cleaning up test data...")
        try:
            await self.db.delete_meeting(self.test_meeting_id)
            logger.info("✅ Test data cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

    async def test_chrome_extension_participant_data(self):
        """Test participant data as it would come from Chrome extension"""
        logger.info("🧪 Testing Chrome extension participant data format...")

        # Simulate participant data from Chrome extension
        chrome_participants = [
            {
                "id": "user-123-abc",
                "name": "Alice Johnson (Host)",
                "platform_id": "alice.johnson@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:00:00Z",
                "is_host": True
            },
            {
                "id": "user-456-def",
                "name": "Bob Smith",
                "platform_id": "bob.smith@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:01:30Z",
                "is_host": False
            },
            {
                "id": "user-789-ghi",
                "name": "Charlie Brown",
                "platform_id": "charlie.brown@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:02:15Z",
                "is_host": False
            },
            {
                "id": "user-101-jkl",
                "name": "Diana Prince",
                "platform_id": "diana.prince@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:03:45Z",
                "is_host": False
            }
        ]

        # Create meeting
        await self.db.save_meeting(self.test_meeting_id, "Sprint Planning - TiDB Integration")
        logger.info("✅ Test meeting created")

        # Save participants batch
        success = await self.db.save_participants_batch(self.test_meeting_id, chrome_participants)
        if not success:
            raise Exception("Failed to save participants batch")

        logger.info(f"✅ Saved {len(chrome_participants)} participants from Chrome extension data")

        # Verify participants were saved
        saved_participants = await self.db.get_participants(self.test_meeting_id)
        if len(saved_participants) != len(chrome_participants):
            raise Exception(f"Expected {len(chrome_participants)} participants, got {len(saved_participants)}")

        logger.info("✅ All participants successfully retrieved from database")

        return chrome_participants, saved_participants

    async def test_participant_status_updates(self):
        """Test real-time participant status updates"""
        logger.info("🧪 Testing participant status updates...")

        # Simulate participant leaving
        await self.db.update_participant_status(self.test_meeting_id, "user-456-def", "left")

        # Simulate participant going away
        await self.db.update_participant_status(self.test_meeting_id, "user-789-ghi", "away")

        # Verify status updates
        updated_participants = await self.db.get_participants(self.test_meeting_id)

        status_map = {p["id"]: p["status"] for p in updated_participants}

        if status_map.get("user-456-def") != "left":
            raise Exception("Participant status update failed for 'left' status")

        if status_map.get("user-789-ghi") != "away":
            raise Exception("Participant status update failed for 'away' status")

        logger.info("✅ Participant status updates working correctly")

        return updated_participants

    async def test_ai_processing_with_participants(self):
        """Test AI processing integration with participant context"""
        logger.info("🧪 Testing AI processing with participant context...")

        # Get current participants
        participants = await self.db.get_participants(self.test_meeting_id)

        # Simulate transcript with participant context
        sample_transcript = """
        Alice Johnson: Good morning everyone, let's start our sprint planning.
        Bob Smith: Thanks Alice. I've prepared the backlog items for review.
        Charlie Brown: I have some questions about the TiDB integration timeline.
        Diana Prince: I can help with the database schema design.
        Alice Johnson: Great! Let's go through each item systematically.
        """

        # Save transcript data
        await self.db.save_transcript(
            meeting_id=self.test_meeting_id,
            transcript=sample_transcript,
            model="whisper",
            model_name="whisper-1",
            chunk_size=5000,
            overlap=1000
        )

        logger.info("✅ Transcript saved with participant context")

        # Simulate AI processing result with participant insights
        ai_summary = {
            "MeetingName": "Sprint Planning - TiDB Integration",
            "Summary": "Team discussed TiDB integration timeline and database schema design",
            "KeyPoints": [
                "Alice (Host) facilitated the meeting effectively",
                "Bob prepared comprehensive backlog items",
                "Charlie raised important timeline questions",
                "Diana offered database expertise"
            ],
            "ActionItems": [
                {
                    "item": "Review TiDB integration timeline",
                    "assignee": "Charlie Brown",
                    "priority": "high"
                },
                {
                    "item": "Design database schema",
                    "assignee": "Diana Prince",
                    "priority": "medium"
                }
            ],
            "People": [
                {"name": "Alice Johnson", "role": "Meeting Host", "contribution": "high"},
                {"name": "Bob Smith", "role": "Developer", "contribution": "high"},
                {"name": "Charlie Brown", "role": "Developer", "contribution": "medium"},
                {"name": "Diana Prince", "role": "Database Expert", "contribution": "high"}
            ],
            "ParticipantInsights": {
                "total_participants": len(participants),
                "active_participants": len([p for p in participants if p["status"] == "active"]),
                "host_participation": "High engagement from meeting host",
                "team_dynamics": "Collaborative discussion with good participation"
            }
        }

        # Save AI processing result
        process_id = await self.db.create_process(self.test_meeting_id)
        await self.db.update_process(
            process_id=process_id,
            status="completed",
            result=json.dumps(ai_summary)
        )

        logger.info("✅ AI processing result saved with participant insights")

        return ai_summary

    async def test_meeting_retrieval_with_participants(self):
        """Test complete meeting retrieval with all participant data"""
        logger.info("🧪 Testing complete meeting data retrieval...")

        # Get complete meeting data
        meeting_data = await self.db.get_meeting(self.test_meeting_id)

        if not meeting_data:
            raise Exception("Failed to retrieve meeting data")

        # Verify all components are present
        required_fields = ["id", "title", "participants", "transcripts"]
        for field in required_fields:
            if field not in meeting_data:
                raise Exception(f"Missing required field in meeting data: {field}")

        logger.info(f"✅ Complete meeting data retrieved:")
        logger.info(f"   - Meeting: {meeting_data['title']}")
        logger.info(f"   - Participants: {len(meeting_data['participants'])}")
        logger.info(f"   - Transcripts: {len(meeting_data['transcripts'])}")

        # Get transcript processing data
        transcript_data = await self.db.get_transcript_data(self.test_meeting_id)

        if transcript_data and transcript_data.get("result"):
            result = json.loads(transcript_data["result"])
            if "ParticipantInsights" in result:
                insights = result["ParticipantInsights"]
                logger.info(f"   - AI Insights: {insights['total_participants']} participants analyzed")

        return meeting_data

    async def run_integration_test(self):
        """Run complete participant integration test suite"""
        logger.info("🚀 Starting Participant Integration Test Suite")

        try:
            await self.setup()

            # Test 1: Chrome extension data handling
            original_participants, saved_participants = await self.test_chrome_extension_participant_data()

            # Test 2: Status updates
            updated_participants = await self.test_participant_status_updates()

            # Test 3: AI processing with participant context
            ai_summary = await self.test_ai_processing_with_participants()

            # Test 4: Complete data retrieval
            meeting_data = await self.test_meeting_retrieval_with_participants()

            # Summary report
            await self.print_test_summary(original_participants, ai_summary, meeting_data)

            logger.info("✅ All participant integration tests passed!")
            return True

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False

        finally:
            await self.cleanup()

    async def print_test_summary(self, participants, ai_summary, meeting_data):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("🏆 PARTICIPANT INTEGRATION TEST SUMMARY")
        print("="*60)

        print(f"📊 DATABASE TYPE: {DatabaseConfig.get_config_from_env()['type'].upper()}")
        print(f"👥 PARTICIPANTS TESTED: {len(participants)}")
        print(f"📝 TRANSCRIPTS SAVED: {len(meeting_data['transcripts'])}")

        print("\n🎯 PARTICIPANT DATA FLOW:")
        print("   1. ✅ Chrome Extension → Database")
        print("   2. ✅ Real-time Status Updates")
        print("   3. ✅ AI Processing with Participant Context")
        print("   4. ✅ Complete Meeting Retrieval")

        print("\n🤖 AI PROCESSING RESULTS:")
        if ai_summary.get("ParticipantInsights"):
            insights = ai_summary["ParticipantInsights"]
            print(f"   - Total Participants: {insights['total_participants']}")
            print(f"   - Active Participants: {insights['active_participants']}")
            print(f"   - Team Dynamics: {insights['team_dynamics']}")

        print("\n👥 PARTICIPANT DETAILS:")
        for participant in participants:
            status_indicator = "🟢" if participant["status"] == "active" else "🔴"
            host_indicator = " (HOST)" if participant["is_host"] else ""
            print(f"   {status_indicator} {participant['name']}{host_indicator}")

        print("\n🚀 HACKATHON FEATURES DEMONSTRATED:")
        print("   ✅ TiDB/SQLite abstraction layer")
        print("   ✅ Real-time participant tracking")
        print("   ✅ Chrome extension integration")
        print("   ✅ AI-powered participant insights")
        print("   ✅ Complete meeting lifecycle management")

        print("="*60)


async def main():
    """Main test execution"""
    print_hackathon_banner()

    # Run integration tests
    test_suite = ParticipantIntegrationTest()
    success = await test_suite.run_integration_test()

    if success:
        print("\n🎉 Participant integration test completed successfully!")
        print("🏆 Ready for TiDB AgentX 2025 Hackathon demonstration!")
    else:
        print("\n❌ Participant integration test failed!")
        print("Please check the logs for error details.")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
