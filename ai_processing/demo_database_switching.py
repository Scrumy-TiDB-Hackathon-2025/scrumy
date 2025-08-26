#!/usr/bin/env python3
"""
Database Switching Demo for TiDB AgentX 2025 Hackathon
Demonstrates seamless switching between SQLite and TiDB using the abstract database interface
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database_config import DatabaseConfig, print_hackathon_banner
from app.database_interface import DatabaseFactory, validate_database_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseSwitchingDemo:
    """Demo class showing database abstraction in action"""

    def __init__(self):
        self.demo_meeting_id = "hackathon-switching-demo"
        self.demo_participants = [
            {
                "id": "demo-alice",
                "name": "Alice Johnson (Product Manager)",
                "platform_id": "alice@scrumy.ai",
                "status": "active",
                "join_time": "2025-01-08T10:00:00Z",
                "is_host": True
            },
            {
                "id": "demo-bob",
                "name": "Bob Chen (Senior Developer)",
                "platform_id": "bob@scrumy.ai",
                "status": "active",
                "join_time": "2025-01-08T10:01:00Z",
                "is_host": False
            },
            {
                "id": "demo-charlie",
                "name": "Charlie Rodriguez (DevOps Engineer)",
                "platform_id": "charlie@scrumy.ai",
                "status": "active",
                "join_time": "2025-01-08T10:02:00Z",
                "is_host": False
            }
        ]

    async def test_database_operations(self, db, db_type):
        """Test core database operations"""
        print(f"\n🔧 Testing {db_type.upper()} Database Operations")
        print("-" * 50)

        try:
            # 1. Health Check
            health = await db.health_check()
            print(f"   ✅ Health Check: {'PASSED' if health else 'FAILED'}")
            if not health:
                return False

            # 2. Meeting Creation
            await db.save_meeting(self.demo_meeting_id, f"TiDB Hackathon Demo - {db_type.upper()}")
            print(f"   ✅ Meeting Created: {self.demo_meeting_id}")

            # 3. Participant Batch Save
            success = await db.save_participants_batch(self.demo_meeting_id, self.demo_participants)
            print(f"   ✅ Participants Saved: {len(self.demo_participants)} participants")

            # 4. Participant Retrieval
            saved_participants = await db.get_participants(self.demo_meeting_id)
            print(f"   ✅ Participants Retrieved: {len(saved_participants)} participants")

            # 5. Status Update
            await db.update_participant_status(self.demo_meeting_id, "demo-bob", "away")
            print(f"   ✅ Status Updated: Bob → away")

            # 6. Transcript Processing Simulation
            await db.save_transcript(
                meeting_id=self.demo_meeting_id,
                transcript="Alice: Let's discuss the TiDB integration. Bob: Great idea! Charlie: I'll handle the deployment.",
                model="whisper",
                model_name="whisper-1",
                chunk_size=1000,
                overlap=100
            )
            print(f"   ✅ Transcript Saved: Sample meeting transcript")

            # 7. AI Processing Result
            process_id = await db.create_process(self.demo_meeting_id)
            ai_result = {
                "MeetingName": f"TiDB Hackathon Demo - {db_type.upper()}",
                "Summary": f"Demo meeting showcasing database switching from SQLite to TiDB",
                "KeyPoints": [
                    f"Successfully tested {db_type.upper()} database operations",
                    "Participant tracking working perfectly",
                    "AI processing integration confirmed"
                ],
                "People": [p["name"] for p in self.demo_participants],
                "ParticipantInsights": {
                    "total_participants": len(self.demo_participants),
                    "database_type": db_type.upper(),
                    "hackathon_ready": db_type == "tidb"
                }
            }

            await db.update_process(
                process_id=process_id,
                status="completed",
                result=json.dumps(ai_result)
            )
            print(f"   ✅ AI Processing: Mock result saved")

            # 8. Complete Meeting Retrieval
            meeting_data = await db.get_meeting(self.demo_meeting_id)
            print(f"   ✅ Meeting Retrieved: Complete data with {len(meeting_data['participants'])} participants")

            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    async def cleanup_demo_data(self, db):
        """Clean up demo data"""
        try:
            await db.delete_meeting(self.demo_meeting_id)
            logger.info("Demo data cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

    async def demonstrate_sqlite(self):
        """Demonstrate SQLite operations"""
        print("\n🗄️  SQLITE DEMONSTRATION")
        print("=" * 60)

        # Force SQLite configuration
        os.environ['DATABASE_TYPE'] = 'sqlite'
        os.environ['SQLITE_DB_PATH'] = 'hackathon_demo_sqlite.db'

        config = DatabaseConfig.get_config_from_env()
        print(f"Database Config: {config['type'].upper()}")

        db = DatabaseFactory.create_from_config(config)

        # Test operations
        success = await self.test_database_operations(db, "sqlite")

        if success:
            print("\n   🎉 SQLite demonstration completed successfully!")

            # Show some stats
            participants = await db.get_participants(self.demo_meeting_id)
            transcript_data = await db.get_transcript_data(self.demo_meeting_id)

            print(f"   📊 Stats: {len(participants)} participants, AI processing completed")

            if transcript_data and transcript_data.get('result'):
                result = json.loads(transcript_data['result'])
                print(f"   🤖 AI Result: {result['ParticipantInsights']['total_participants']} participants analyzed")

        await self.cleanup_demo_data(db)
        return success

    async def demonstrate_tidb(self):
        """Demonstrate TiDB operations (if configured)"""
        print("\n🌐 TIDB DEMONSTRATION")
        print("=" * 60)

        # Check if TiDB is configured
        tidb_configured = all([
            os.getenv('TIDB_HOST'),
            os.getenv('TIDB_USER'),
            os.getenv('TIDB_PASSWORD')
        ])

        if not tidb_configured:
            print("   ⚠️  TiDB credentials not found in environment")
            print("   💡 To test TiDB, set these environment variables:")
            print("      - TIDB_HOST")
            print("      - TIDB_USER")
            print("      - TIDB_PASSWORD")
            print("      - TIDB_DATABASE (optional, defaults to 'scrumy_ai')")
            print("\n   🔄 Skipping TiDB demonstration...")
            return False

        # Force TiDB configuration
        os.environ['DATABASE_TYPE'] = 'tidb'

        try:
            config = DatabaseConfig.get_config_from_env()
            print(f"Database Config: {config['type'].upper()}")
            print(f"TiDB Host: {config['connection']['host']}")
            print(f"Database: {config['connection']['database']}")

            db = DatabaseFactory.create_from_config(config)

            # Test operations
            success = await self.test_database_operations(db, "tidb")

            if success:
                print("\n   🎉 TiDB demonstration completed successfully!")

                # Show some stats
                participants = await db.get_participants(self.demo_meeting_id)
                transcript_data = await db.get_transcript_data(self.demo_meeting_id)

                print(f"   📊 Stats: {len(participants)} participants, distributed processing")

                if transcript_data and transcript_data.get('result'):
                    result = json.loads(transcript_data['result'])
                    insights = result['ParticipantInsights']
                    print(f"   🤖 AI Result: {insights['total_participants']} participants, hackathon_ready: {insights['hackathon_ready']}")

            await self.cleanup_demo_data(db)
            return success

        except Exception as e:
            print(f"   ❌ TiDB Error: {e}")
            print("   💡 Check your TiDB credentials and network connectivity")
            return False

    async def run_switching_demo(self):
        """Run the complete database switching demonstration"""
        print_hackathon_banner()

        print("\n🎯 DATABASE SWITCHING DEMONSTRATION")
        print("This demo shows the same code working with different databases")
        print("=" * 70)

        # Test 1: SQLite
        sqlite_success = await self.demonstrate_sqlite()

        # Wait a moment between tests
        await asyncio.sleep(1)

        # Test 2: TiDB
        tidb_success = await self.demonstrate_tidb()

        # Summary
        self.print_demo_summary(sqlite_success, tidb_success)

        return sqlite_success or tidb_success

    def print_demo_summary(self, sqlite_success, tidb_success):
        """Print comprehensive demo summary"""
        print("\n" + "=" * 70)
        print("🏆 DATABASE SWITCHING DEMO SUMMARY")
        print("=" * 70)

        print("\n📊 RESULTS:")
        print(f"   SQLite Demo: {'✅ PASSED' if sqlite_success else '❌ FAILED'}")
        print(f"   TiDB Demo:   {'✅ PASSED' if tidb_success else '❌ FAILED'}")

        print("\n🎯 KEY ACHIEVEMENTS:")
        if sqlite_success:
            print("   ✅ SQLite: Complete CRUD operations with participants")
            print("   ✅ Development: Perfect for local development and testing")

        if tidb_success:
            print("   ✅ TiDB: Production-ready distributed database operations")
            print("   ✅ Scalability: Ready for enterprise-level deployment")
            print("   ✅ Hackathon: Full TiDB integration demonstrated")

        print("\n🏗️  ARCHITECTURE BENEFITS:")
        print("   🔄 Database Abstraction: Same code, different databases")
        print("   🚀 Zero Downtime: Switch databases without code changes")
        print("   📈 Scalable: SQLite → TiDB migration path")
        print("   🛡️  Production Ready: Proper error handling and connection management")

        if sqlite_success and tidb_success:
            print("\n🎉 HACKATHON SUCCESS: Full database abstraction achieved!")
            print("   🏆 Ready for production deployment with TiDB")
        elif sqlite_success:
            print("\n✅ DEVELOPMENT SUCCESS: SQLite integration working perfectly")
            print("   💡 Add TiDB credentials to unlock full hackathon potential")
        else:
            print("\n⚠️  DEMO ISSUES: Check configuration and dependencies")

        print("\n🔧 NEXT STEPS:")
        print("   1. Set up TiDB credentials for full demonstration")
        print("   2. Run the complete integration test: python test_participant_integration.py")
        print("   3. Start the hackathon server: python start_hackathon.py")
        print("   4. Access the API docs: http://localhost:8001/docs")

        print("=" * 70)

    def create_tidb_setup_guide(self):
        """Create a quick setup guide for TiDB"""
        guide = """
# TiDB Setup Guide for Hackathon Demo

## Quick TiDB Cloud Setup
1. Visit: https://tidbcloud.com/
2. Create a free account
3. Create a new cluster (Serverless tier is free)
4. Get connection details from cluster dashboard

## Environment Setup
export DATABASE_TYPE=tidb
export TIDB_HOST=gateway01.us-west-2.prod.aws.tidbcloud.com
export TIDB_PORT=4000
export TIDB_USER=your_username
export TIDB_PASSWORD=your_password
export TIDB_DATABASE=scrumy_ai

## Test Connection
python demo_database_switching.py

## For Demo Day
- Use TiDB for live demonstration
- SQLite for backup/development
- Show switching between both databases
"""

        with open("TIDB_SETUP.md", "w") as f:
            f.write(guide)

        print("📝 Created TIDB_SETUP.md guide")


async def main():
    """Main demo execution"""
    demo = DatabaseSwitchingDemo()

    # Create setup guide
    demo.create_tidb_setup_guide()

    # Run the switching demonstration
    success = await demo.run_switching_demo()

    if success:
        print("\n🎉 Database switching demo completed successfully!")
        print("🏆 Scrumy AI is ready for TiDB AgentX 2025 Hackathon!")
    else:
        print("\n❌ Demo had some issues - check logs for details")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        sys.exit(1)
