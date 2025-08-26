
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
            action_items="• Follow up on demo items\n• Prepare for hackathon presentation",
            key_points="• TiDB integration complete\n• All features working"
        )

        print(f"Created demo meeting: {title}")

if __name__ == "__main__":
    asyncio.run(populate_demo_data())
