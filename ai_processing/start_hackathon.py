#!/usr/bin/env python3
"""
TiDB AgentX 2025 Hackathon Startup Script
Scrumy AI Meeting Assistant with TiDB Integration

This script demonstrates the full integration between the AI processing system
and TiDB for the hackathon project.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database_config import DatabaseConfig, print_hackathon_banner
from app.database_interface import DatabaseFactory, validate_database_config
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Setup environment variables for hackathon demo"""
    # Check if we have TiDB credentials
    tidb_configured = all([
        os.getenv('TIDB_HOST'),
        os.getenv('TIDB_USER'),
        os.getenv('TIDB_PASSWORD')
    ])

    if tidb_configured:
        logger.info("TiDB credentials detected - configuring for production demo")
        os.environ['DATABASE_TYPE'] = 'tidb'
        return 'tidb'
    else:
        logger.info("TiDB credentials not found - using SQLite for development")
        os.environ['DATABASE_TYPE'] = 'sqlite'
        os.environ['SQLITE_DB_PATH'] = 'hackathon_demo.db'
        return 'sqlite'


async def test_database_connection():
    """Test database connection and setup"""
    logger.info("Testing database connection...")

    try:
        config = DatabaseConfig.get_config_from_env()
        if not validate_database_config(config):
            logger.error("Database configuration is invalid")
            return False

        db = DatabaseFactory.create_from_config(config)

        # Test health check
        health_ok = await db.health_check()
        if not health_ok:
            logger.error("Database health check failed")
            return False

        logger.info(f"✅ {config['type'].upper()} database connection successful")

        # Test participant functionality
        await test_participant_features(db)

        return True

    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def test_participant_features(db):
    """Test participant-related database features"""
    logger.info("Testing participant features...")

    try:
        test_meeting_id = "hackathon-demo-meeting"
        test_participants = [
            {
                "id": "participant-1",
                "name": "Alice (Host)",
                "platform_id": "alice@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:00:00Z",
                "is_host": True
            },
            {
                "id": "participant-2",
                "name": "Bob (Developer)",
                "platform_id": "bob@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:01:00Z",
                "is_host": False
            },
            {
                "id": "participant-3",
                "name": "Charlie (Designer)",
                "platform_id": "charlie@company.com",
                "status": "active",
                "join_time": "2025-01-08T10:02:00Z",
                "is_host": False
            }
        ]

        # Save test meeting
        await db.save_meeting(test_meeting_id, "TiDB AgentX 2025 Hackathon Demo")

        # Save participants
        success = await db.save_participants_batch(test_meeting_id, test_participants)
        if not success:
            logger.error("Failed to save participants")
            return False

        # Retrieve participants
        retrieved_participants = await db.get_participants(test_meeting_id)
        logger.info(f"✅ Successfully saved and retrieved {len(retrieved_participants)} participants")

        # Test participant status update
        await db.update_participant_status(test_meeting_id, "participant-2", "away")
        logger.info("✅ Participant status update successful")

        return True

    except Exception as e:
        logger.error(f"Participant features test failed: {e}")
        return False


def create_demo_data_script():
    """Create a script to populate demo data"""
    demo_script = """
# Demo Data Population Script
# Run this to create sample meeting data for hackathon demonstration

from app.database_config import DatabaseConfig
from app.database_interface import DatabaseFactory
import asyncio
import uuid
from datetime import datetime

async def populate_demo_data():
    config = DatabaseConfig.get_config_from_env()
    db = DatabaseFactory.create_from_config(config)

    # Demo meetings
    meetings = [
        ("Sprint Planning - Q1 2025", "Alice, Bob, Charlie", "2025-01-08T09:00:00Z"),
        ("Product Review Meeting", "Alice, Bob, Diana", "2025-01-07T14:00:00Z"),
        ("Architecture Discussion", "Bob, Charlie, Eve", "2025-01-06T16:00:00Z")
    ]

    for title, participants, timestamp in meetings:
        meeting_id = f"demo-{uuid.uuid4()}"
        await db.save_meeting(meeting_id, title)

        # Add sample transcript
        await db.save_meeting_transcript(
            meeting_id=meeting_id,
            transcript=f"This is a demo transcript for {title}. Meeting started at {timestamp}.",
            timestamp=timestamp,
            summary="Demo summary with key points and decisions.",
            action_items="• Follow up on demo items\\n• Prepare for hackathon presentation",
            key_points="• TiDB integration complete\\n• All features working"
        )

        print(f"Created demo meeting: {title}")

if __name__ == "__main__":
    asyncio.run(populate_demo_data())
"""

    with open("populate_demo_data.py", "w") as f:
        f.write(demo_script)

    logger.info("✅ Created demo data population script: populate_demo_data.py")


def show_hackathon_features():
    """Display hackathon features and capabilities"""
    features = """
🏆 TiDB AgentX 2025 Hackathon Features Demonstrated:

📊 DATABASE INTEGRATION:
   ✅ Abstract database interface supporting both SQLite and TiDB
   ✅ Seamless switching between development and production databases
   ✅ Production-ready TiDB integration with proper connection handling
   ✅ Advanced participant management with real-time status tracking

🤖 AI PROCESSING CAPABILITIES:
   ✅ Real-time meeting transcription with Whisper integration
   ✅ Multi-model AI support (OpenAI, Anthropic, Groq, Ollama)
   ✅ Intelligent meeting summarization and action item extraction
   ✅ Participant-aware AI processing for personalized insights

🔗 CHROME EXTENSION INTEGRATION:
   ✅ Real-time participant data collection from meetings
   ✅ Automated transcript capture and processing
   ✅ Meeting metadata extraction and storage

🚀 PRODUCTION FEATURES:
   ✅ RESTful API endpoints for all functionality
   ✅ Background processing for large transcripts
   ✅ Comprehensive error handling and logging
   ✅ Configurable model selection and API key management

💾 TIDB-SPECIFIC OPTIMIZATIONS:
   ✅ Distributed database schema design
   ✅ Optimized queries for participant lookup and meeting data
   ✅ Proper indexing for performance
   ✅ Connection pooling and health monitoring

🎯 HACKATHON DEMO SCENARIOS:
   ✅ Live meeting processing with participant tracking
   ✅ Multi-model AI comparison for summary generation
   ✅ Database failover and recovery demonstration
   ✅ Real-time dashboard with meeting analytics
    """

    print(features)


async def setup_and_validate():
    """Async setup and validation without starting server"""
    print_hackathon_banner()

    # Setup environment
    db_type = setup_environment()

    # Show database status
    status = DatabaseConfig.get_database_status()
    logger.info(f"Database Status: {status}")

    # Test database connection
    db_ok = await test_database_connection()
    if not db_ok:
        logger.error("❌ Database tests failed")
        return False, None

    # Create demo utilities
    create_demo_data_script()

    # Show features
    show_hackathon_features()

    return True, db_type

def start_server(db_type):
    """Start the server after async setup is complete"""
    logger.info("🚀 Starting Scrumy AI Processing Server for TiDB AgentX 2025 Hackathon")
    logger.info(f"Database: {db_type.upper()}")
    logger.info("Server will start on http://localhost:8000")
    logger.info("Swagger UI: http://localhost:8000/docs")
    logger.info("")
    logger.info("🎯 Chrome Extension Integration Endpoints:")
    logger.info("   WebSocket (Real-time): ws://localhost:8000/ws")
    logger.info("   WebSocket (Alt path): ws://localhost:8000/ws/audio-stream")
    logger.info("   REST API Base: http://localhost:8000")
    logger.info("")
    logger.info("📡 Available Chrome Extension Endpoints:")
    logger.info("   POST /identify-speakers - Speaker identification")
    logger.info("   POST /generate-summary - Meeting summarization")
    logger.info("   POST /extract-tasks - Action item extraction")
    logger.info("   POST /process-transcript-with-tools - Full AI processing")
    logger.info("   GET  /available-tools - List available AI tools")
    logger.info("   GET  /get-model-config - Get model configuration")
    logger.info("")
    logger.info("🔧 To test Chrome extension compatibility:")
    logger.info("   python test_chrome_extension_compatibility.py")

    # Validate WebSocket components are available
    try:
        from app.websocket_server import websocket_endpoint, websocket_manager
        logger.info("✅ WebSocket server components loaded successfully")
    except ImportError as e:
        logger.warning(f"⚠️  WebSocket components issue: {e}")

    # Import here to avoid circular imports
    from app.main import app

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # Disable reload for production demo
    )


if __name__ == "__main__":
    try:
        # Run async setup first
        setup_ok, db_type = asyncio.run(setup_and_validate())
        if setup_ok:
            # Start server synchronously
            start_server(db_type)
        else:
            logger.error("Setup failed, cannot start server")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Hackathon demo stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Hackathon startup failed: {e}")
        sys.exit(1)
