#!/usr/bin/env python3
"""
Add test data to the database for testing the frontend
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from app.database_interface import DatabaseFactory

async def add_test_data():
    """Add some test meetings and data"""
    try:
        # Create database connection
        db = DatabaseFactory.create_from_env()
        
        # Test meetings data
        test_meetings = [
            {
                "id": "meet.google.com_test_001",
                "title": "Daily Standup - Frontend Team",
                "participants": [
                    {"name": "Alice Johnson", "id": "alice_001"},
                    {"name": "Bob Smith", "id": "bob_002"},
                    {"name": "Carol Davis", "id": "carol_003"}
                ],
                "transcript_segments": [
                    {"text": "Good morning everyone, let's start our daily standup.", "timestamp": "0"},
                    {"text": "I completed the user authentication module yesterday.", "timestamp": "15"},
                    {"text": "Today I'm working on the dashboard components.", "timestamp": "30"},
                    {"text": "I'm blocked on the API integration, need help from backend team.", "timestamp": "45"},
                    {"text": "I can help with that after this meeting.", "timestamp": "60"},
                    {"text": "Great, let's sync up after standup. Any other blockers?", "timestamp": "75"},
                    {"text": "No other blockers from my side.", "timestamp": "90"},
                    {"text": "Same here, all good.", "timestamp": "105"},
                    {"text": "Perfect, let's wrap up. Thanks everyone!", "timestamp": "120"}
                ],
                "tasks": [
                    {"title": "Complete API integration", "assignee": "Alice Johnson", "priority": "high"},
                    {"title": "Review dashboard components", "assignee": "Bob Smith", "priority": "medium"},
                    {"title": "Update user documentation", "assignee": "Carol Davis", "priority": "low"}
                ]
            },
            {
                "id": "meet.google.com_test_002", 
                "title": "Sprint Planning - Q1 2025",
                "participants": [
                    {"name": "David Wilson", "id": "david_001"},
                    {"name": "Emma Brown", "id": "emma_002"},
                    {"name": "Frank Miller", "id": "frank_003"},
                    {"name": "Grace Lee", "id": "grace_004"}
                ],
                "transcript_segments": [
                    {"text": "Welcome to our Q1 sprint planning session.", "timestamp": "0"},
                    {"text": "Let's review the backlog items for this sprint.", "timestamp": "20"},
                    {"text": "The user authentication feature is our top priority.", "timestamp": "40"},
                    {"text": "I estimate that will take about 5 story points.", "timestamp": "60"},
                    {"text": "Agreed, and we should also include the dashboard redesign.", "timestamp": "80"},
                    {"text": "That's another 8 story points based on the mockups.", "timestamp": "100"},
                    {"text": "We also need to address the performance issues reported.", "timestamp": "120"},
                    {"text": "Let's allocate 3 story points for performance optimization.", "timestamp": "140"},
                    {"text": "Sounds good, that gives us 16 story points total.", "timestamp": "160"},
                    {"text": "Perfect, let's commit to this sprint scope.", "timestamp": "180"}
                ],
                "tasks": [
                    {"title": "Implement user authentication system", "assignee": "David Wilson", "priority": "high"},
                    {"title": "Redesign main dashboard", "assignee": "Emma Brown", "priority": "high"},
                    {"title": "Optimize database queries", "assignee": "Frank Miller", "priority": "medium"},
                    {"title": "Update API documentation", "assignee": "Grace Lee", "priority": "low"}
                ]
            },
            {
                "id": "meet.google.com_test_003",
                "title": "Client Demo Preparation",
                "participants": [
                    {"name": "Henry Taylor", "id": "henry_001"},
                    {"name": "Ivy Chen", "id": "ivy_002"}
                ],
                "transcript_segments": [
                    {"text": "Let's prepare for tomorrow's client demo.", "timestamp": "0"},
                    {"text": "We need to showcase the new features we built.", "timestamp": "15"},
                    {"text": "The authentication flow looks great now.", "timestamp": "30"},
                    {"text": "Yes, and the dashboard is much more intuitive.", "timestamp": "45"},
                    {"text": "Should we prepare a backup plan in case of technical issues?", "timestamp": "60"},
                    {"text": "Good idea, let's have screenshots ready.", "timestamp": "75"},
                    {"text": "I'll prepare the demo script tonight.", "timestamp": "90"},
                    {"text": "Perfect, I'll handle the technical setup.", "timestamp": "105"}
                ],
                "tasks": [
                    {"title": "Prepare demo script", "assignee": "Henry Taylor", "priority": "high"},
                    {"title": "Setup demo environment", "assignee": "Ivy Chen", "priority": "high"},
                    {"title": "Prepare backup screenshots", "assignee": "Henry Taylor", "priority": "medium"}
                ]
            }
        ]
        
        print("Adding test meetings to database...")
        
        for meeting_data in test_meetings:
            meeting_id = meeting_data["id"]
            title = meeting_data["title"]
            
            # Save meeting
            await db.save_meeting(meeting_id, title)
            print(f"✓ Added meeting: {title}")
            
            # Save participants
            for participant in meeting_data["participants"]:
                await db.save_participant(
                    meeting_id=meeting_id,
                    participant_id=participant["id"],
                    name=participant["name"],
                    platform_id=participant["id"],
                    status="active",
                    join_time=datetime.now().isoformat(),
                    is_host=False
                )
            print(f"  ✓ Added {len(meeting_data['participants'])} participants")
            
            # Save transcript segments
            for i, segment in enumerate(meeting_data["transcript_segments"]):
                await db.save_meeting_transcript(
                    meeting_id=meeting_id,
                    transcript=segment["text"],
                    timestamp=segment["timestamp"],
                    summary="",
                    action_items="",
                    key_points=""
                )
            print(f"  ✓ Added {len(meeting_data['transcript_segments'])} transcript segments")
            
            # Save tasks
            for task_data in meeting_data["tasks"]:
                task_id = f"task-{uuid.uuid4()}"
                await db.save_task(
                    task_id=task_id,
                    meeting_id=meeting_id,
                    title=task_data["title"],
                    description=f"Task from meeting: {title}",
                    assignee=task_data["assignee"],
                    priority=task_data["priority"],
                    status="pending"
                )
            print(f"  ✓ Added {len(meeting_data['tasks'])} tasks")
            
        print(f"\n🎉 Successfully added {len(test_meetings)} test meetings with participants, transcripts, and tasks!")
        print("\nYou can now test the frontend with real data from the database.")
        
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_test_data())