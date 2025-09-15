"""
Frontend Integration Endpoints
Provides API endpoints that the frontend dashboard expects
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from app.tidb_database import TiDBDatabase
from app.task_extractor import TaskExtractor
from app.ai_processor import AIProcessor
import os

logger = logging.getLogger(__name__)
router = APIRouter()

# Use singleton database connection to avoid multiple TiDB connections
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        try:
            from dotenv import load_dotenv
            load_dotenv()  # Load environment variables
            from app.database_interface import DatabaseFactory
            _db_instance = DatabaseFactory.create_from_env()
            db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
            logger.info(f"Frontend endpoints using {db_type.upper()} database (singleton)")
        except Exception as e:
            logger.warning(f"Database not available, using mock data: {e}")
            _db_instance = None
    return _db_instance

db = get_db()

@router.get("/api/tasks")
async def get_tasks(meeting_id: Optional[str] = None):
    """Get all tasks or tasks for a specific meeting"""
    try:
        if db and hasattr(db, 'get_all_tasks'):
            # Get tasks from database
            if meeting_id and hasattr(db, 'get_tasks_by_meeting'):
                tasks = await db.get_tasks_by_meeting(meeting_id)
            elif hasattr(db, 'get_all_tasks'):
                tasks = await db.get_all_tasks()
            else:
                tasks = []
            
            return {
                "status": "success",
                "data": tasks,
                "total": len(tasks)
            }
        else:
            # Mock data for development
            mock_tasks = [
                {
                    "id": "task_1",
                    "title": "Follow up with client presentation",
                    "description": "Schedule follow-up meeting to discuss Q4 projections",
                    "assignee": "John Doe",
                    "priority": "high",
                    "status": "pending",
                    "due_date": "2025-01-15",
                    "meeting_id": "meeting_001",
                    "created_at": "2025-01-08T10:30:00Z"
                },
                {
                    "id": "task_2", 
                    "title": "Update project timeline",
                    "description": "Revise timeline based on new requirements",
                    "assignee": "Jane Smith",
                    "priority": "medium",
                    "status": "in_progress",
                    "due_date": "2025-01-12",
                    "meeting_id": "meeting_002",
                    "created_at": "2025-01-08T11:15:00Z"
                }
            ]
            
            if meeting_id:
                mock_tasks = [t for t in mock_tasks if t["meeting_id"] == meeting_id]
            
            return {
                "status": "success",
                "data": mock_tasks,
                "total": len(mock_tasks)
            }
            
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/transcripts/{meeting_id}")
async def get_transcript(meeting_id: str):
    """Get transcript for a specific meeting"""
    try:
        if db and hasattr(db, 'get_meeting_transcript'):
            # Get transcript from database
            transcript_data = await db.get_meeting_transcript(meeting_id)
            
            if not transcript_data:
                raise HTTPException(status_code=404, detail="Transcript not found")
            
            return {
                "status": "success",
                "meeting_id": meeting_id,
                "data": transcript_data
            }
        else:
            # Mock data for development
            mock_transcript = {
                "meeting_id": meeting_id,
                "transcript_chunks": [
                    {
                        "id": "chunk_1",
                        "text": "Welcome everyone to today's meeting. Let's start with the project updates.",
                        "timestamp": "2025-01-08T10:00:00Z",
                        "speaker": "John Doe"
                    },
                    {
                        "id": "chunk_2", 
                        "text": "The Q4 numbers look promising. We should schedule a follow-up with the client.",
                        "timestamp": "2025-01-08T10:05:00Z",
                        "speaker": "Jane Smith"
                    }
                ],
                "full_transcript": "Welcome everyone to today's meeting. Let's start with the project updates. The Q4 numbers look promising. We should schedule a follow-up with the client.",
                "duration": "15 minutes",
                "participants": ["John Doe", "Jane Smith"],
                "created_at": "2025-01-08T10:00:00Z"
            }
            
            return {
                "status": "success", 
                "meeting_id": meeting_id,
                "data": mock_transcript
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/meetings")
async def get_meetings_list():
    """Get all meetings with details for meetings page - OPTIMIZED"""
    import time
    start_time = time.time()
    
    try:
        if db:
            meetings = await db.get_all_meetings()
            
            # Early return for empty meetings
            if not meetings:
                return {"status": "success", "data": {"meetings": [], "stats": {"totalMeetings": 0, "completed": 0, "actionItems": 0, "avgDuration": 0}}}
            
            # Batch fetch all tasks and participants to avoid N+1 queries
            all_tasks = await db.get_all_tasks() if hasattr(db, 'get_all_tasks') else []
            
            # Group tasks by meeting_id for O(1) lookup
            tasks_by_meeting = {}
            for task in all_tasks:
                meeting_id = task.get('meeting_id')
                if meeting_id not in tasks_by_meeting:
                    tasks_by_meeting[meeting_id] = []
                tasks_by_meeting[meeting_id].append(task)
            
            formatted_meetings = []
            total_duration_minutes = 0
            total_action_items = 0
            
            for meeting in meetings:
                meeting_id = meeting.get('id', '')
                
                # Get tasks from pre-fetched data
                tasks = tasks_by_meeting.get(meeting_id, [])
                action_items_count = len(tasks)
                total_action_items += action_items_count
                
                # Simplified duration calculation (avoid expensive transcript processing)
                duration_minutes = 5  # Default 5 minutes
                duration_text = f"{duration_minutes} minutes"
                total_duration_minutes += duration_minutes
                
                # Format time from created_at
                created_at = meeting.get('created_at', '')
                time_text = "Unknown time"
                date_text = "Unknown date"
                
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            dt = created_at
                        time_text = dt.strftime("%I:%M%p")
                        date_text = dt.strftime("%Y-%m-%d")
                    except:
                        date_text = str(created_at)[:10] if created_at else "Unknown date"
                
                # Simple summary without expensive transcript processing
                summary = meeting.get('title', 'Meeting summary')
                
                formatted_meetings.append({
                    "id": meeting_id,
                    "title": meeting.get('title', 'Untitled Meeting'),
                    "date": date_text,
                    "time": time_text,
                    "duration": duration_text,
                    "attendees": 1,  # Default to 1 attendee
                    "actionItems": action_items_count,
                    "summary": summary
                })
            
            avg_duration = total_duration_minutes // max(1, len(formatted_meetings))
            
            stats = {
                "totalMeetings": len(formatted_meetings),
                "completed": len(formatted_meetings),
                "actionItems": total_action_items,
                "avgDuration": avg_duration
            }
            
            # Add performance metrics
            processing_time = round((time.time() - start_time) * 1000, 2)  # ms
            stats["processing_time_ms"] = processing_time
            
            return {"status": "success", "data": {"meetings": formatted_meetings, "stats": stats}}
        else:
            # Fast mock response
            processing_time = round((time.time() - start_time) * 1000, 2)
            return {"status": "success", "data": {"meetings": [], "stats": {"totalMeetings": 0, "completed": 0, "actionItems": 0, "avgDuration": 0, "processing_time_ms": processing_time}}}
            
    except Exception as e:
        processing_time = round((time.time() - start_time) * 1000, 2)
        logger.error(f"Error getting meetings (took {processing_time}ms): {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/meetings/{meeting_id}")
async def get_meeting_detail(meeting_id: str):
    """Get meeting detail with transcript for meeting detail page"""
    try:
        if db and hasattr(db, 'get_meeting_transcript'):
            transcript_data = await db.get_meeting_transcript(meeting_id)
            if transcript_data:
                # Also get the meeting title from the meetings table
                meeting_data = await db.get_meeting(meeting_id) if hasattr(db, 'get_meeting') else None
                meeting_title = meeting_data.get('title', 'Untitled Meeting') if meeting_data else transcript_data.get('title', 'Untitled Meeting')
                
                return {
                    "status": "success",
                    "data": {
                        "id": meeting_id,
                        "title": meeting_title,
                        "transcript": transcript_data.get('full_transcript', ''),
                        "transcript_chunks": transcript_data.get('transcript_chunks', []),
                        "participants": transcript_data.get('participants', []),
                        "duration": transcript_data.get('duration', '35 minutes'),
                        "created_at": transcript_data.get('created_at')
                    }
                }
        
        # Fallback mock data
        return {
            "status": "success",
            "data": {
                "id": meeting_id,
                "title": f"Meeting {meeting_id}",
                "transcript": "Welcome everyone to today's meeting. Let's start with the project updates.",
                "transcript_chunks": [
                    {"speaker": "John", "text": "Welcome everyone to today's meeting.", "timestamp": "0:00"},
                    {"speaker": "Jane", "text": "Let's start with the project updates.", "timestamp": "0:05"}
                ],
                "participants": ["John", "Jane"],
                "duration": "35 minutes"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting meeting detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/projects")
async def get_projects():
    """Get project tracker data"""
    try:
        projects = {
            "todo": [{"id": 1, "title": "Create new feature spec", "project": "Project Alpha", "code": "PA-001"}],
            "inProgress": [
                {"id": 2, "title": "UI/UX | Recreate the Onboarding flow", "project": "Project Beta", "code": "PB-002"},
                {"id": 3, "title": "Backend API integration", "project": "Project Gamma", "code": "PG-003"}
            ],
            "blocked": [],
            "review": [{"id": 4, "title": "Code review for authentication", "project": "Project Alpha", "code": "PA-004"}],
            "done": [
                {"id": 5, "title": "Database schema design", "project": "Project Beta", "code": "PB-005"},
                {"id": 6, "title": "Initial wireframes", "project": "Project Gamma", "code": "PG-006"}
            ]
        }
        
        return {"status": "success", "data": projects}
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/integrations")
async def get_integrations_list():
    """Get all available integrations for integrations page"""
    try:
        notion_configured = bool(os.getenv('NOTION_TOKEN'))
        slack_configured = bool(os.getenv('SLACK_BOT_TOKEN'))
        clickup_configured = bool(os.getenv('CLICKUP_TOKEN'))
        
        integrations = [
            {"id": 1, "name": "Google Calendar", "description": "Sync meeting schedules and automatically detect when to start recording", "status": "Connected", "icon": "📅", "features": ["Meeting reminder", "Auto-detect meetings", "Schedule sync"], "lastSync": "2 minutes ago", "category": "Calendar"},
            {"id": 2, "name": "Google Meet", "description": "Automatically join and record Google Meet sessions with AI transcription", "status": "Connected", "icon": "📹", "features": ["Auto-join meetings", "Recording", "Transcription"], "lastSync": "2 minutes ago", "category": "Video Conferencing"},
            {"id": 3, "name": "Slack", "description": "Send meeting summaries and action items to Slack channels", "status": "Connected" if slack_configured else "Available", "icon": "💬", "features": ["Channel notifications", "Summary sharing", "Action item alerts"], "lastSync": "1 minute ago" if slack_configured else None, "category": "Communication"},
            {"id": 4, "name": "Notion", "description": "Automatically create meeting notes and action items in Notion", "status": "Connected" if notion_configured else "Available", "icon": "📝", "features": ["Note creation", "Action items sync", "Database integration"], "lastSync": "3 minutes ago" if notion_configured else None, "category": "Productivity"},
            {"id": 5, "name": "ClickUp", "description": "Create tasks and projects from meeting action items", "status": "Connected" if clickup_configured else "Available", "icon": "🎯", "features": ["Task creation", "Project management", "Sprint integration"], "lastSync": "5 minutes ago" if clickup_configured else None, "category": "Project Management"},
            {"id": 6, "name": "Microsoft Teams", "description": "Join and record Microsoft Teams meetings automatically", "status": "Available", "icon": "👥", "features": ["Auto-join meetings", "Recording", "Transcription"], "lastSync": None, "category": "Video Conferencing"},
            {"id": 7, "name": "Zoom", "description": "Record and transcribe Zoom meetings with AI-powered insights", "status": "Available", "icon": "🎥", "features": ["Auto-recording", "Transcription", "Meeting insights"], "lastSync": None, "category": "Video Conferencing"}
        ]
        
        return {"status": "success", "data": integrations}
        
    except Exception as e:
        logger.error(f"Error getting integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/clear-database")
async def clear_database():
    """Clear all database data for fresh testing"""
    try:
        if db:
            success = db.clear_all()
            if success:
                return {"status": "success", "message": "Database cleared successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to clear database")
        else:
            return {"status": "success", "message": "No database to clear (using mock data)"}
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/integration-status")
async def get_integration_status():
    """Get status of external integrations"""
    try:
        # Check environment variables for integration status
        notion_configured = bool(os.getenv('NOTION_TOKEN'))
        slack_configured = bool(os.getenv('SLACK_BOT_TOKEN'))
        clickup_configured = bool(os.getenv('CLICKUP_TOKEN'))
        
        integrations = {
            "notion": {
                "name": "Notion",
                "configured": notion_configured,
                "status": "connected" if notion_configured else "not_configured",
                "last_sync": "2025-01-08T10:30:00Z" if notion_configured else None,
                "tasks_created": 5 if notion_configured else 0
            },
            "slack": {
                "name": "Slack", 
                "configured": slack_configured,
                "status": "connected" if slack_configured else "not_configured",
                "last_sync": "2025-01-08T10:25:00Z" if slack_configured else None,
                "notifications_sent": 3 if slack_configured else 0
            },
            "clickup": {
                "name": "ClickUp",
                "configured": clickup_configured, 
                "status": "connected" if clickup_configured else "not_configured",
                "last_sync": "2025-01-08T10:20:00Z" if clickup_configured else None,
                "tasks_created": 2 if clickup_configured else 0
            }
        }
        
        # Overall status
        total_configured = sum(1 for i in integrations.values() if i["configured"])
        overall_status = "fully_connected" if total_configured == 3 else "partially_connected" if total_configured > 0 else "not_connected"
        
        return {
            "status": "success",
            "data": {
                "overall_status": overall_status,
                "integrations": integrations,
                "summary": {
                    "total_integrations": 3,
                    "configured": total_configured,
                    "active": total_configured,
                    "last_activity": "2025-01-08T10:30:00Z" if total_configured > 0 else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))