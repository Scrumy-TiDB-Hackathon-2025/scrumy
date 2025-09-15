from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
import asyncio
from dotenv import load_dotenv
from .chatbot import ChatBot
from .tidb_vector_store import TiDBVectorStore
from .tidb_connection import TiDBConnection
from .utils.key_manager import GroqKeyManager
from sqlalchemy import text

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Chatbot API",
    description="Chatbot API with TiDB vector store and Groq",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize TiDB connection
tidb_conn = TiDBConnection()
if not tidb_conn.initialize():
    raise RuntimeError("Failed to initialize TiDB connection")

# Initialize vector store
vector_store = TiDBVectorStore(tidb_conn.get_engine())

# Initialize key manager
key_manager = GroqKeyManager()

# Initialize chatbot with Groq and key manager
chatbot = ChatBot(vector_store, model_name="llama-3.3-70b-versatile", key_manager=key_manager)

# Initialize knowledge base on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the knowledge base with sample data and meeting data"""
    try:
        await vector_store.bootstrap_knowledge_base()
        print("✅ Knowledge base initialized successfully")
        
        # CRITICAL: Always populate meeting data into vector store on startup
        try:
            result = await populate_meeting_data_to_vector_store()
            if result["status"] == "success":
                print(f"✅ Meeting data populated: {result['details']['total_items']} items")
                print(f"✅ Chatbot now has access to all meeting data")
            else:
                print(f"❌ ERROR: Could not populate meeting data: {result.get('error', 'Unknown error')}")
                print(f"❌ Chatbot will not have access to meeting data!")
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not populate meeting data: {e}")
            print(f"❌ Chatbot will not have access to meeting data!")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize knowledge base: {e}")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None

class MeetingDataRequest(BaseModel):
    force_refresh: Optional[bool] = False

class ChatResponse(BaseModel):
    session_id: str
    response: str
    metadata: Dict

class KnowledgeRequest(BaseModel):
    content: str
    metadata: Optional[Dict] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process a chat message and return a response"""
    try:
        result = await chatbot.process_message(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/add")
async def add_knowledge(request: KnowledgeRequest):
    """Add new knowledge to the vector store"""
    try:
        success = await chatbot.add_knowledge(request.content, request.metadata)
        if success:
            return {"status": "success", "message": "Knowledge added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/search")
async def search_knowledge(query: str, session_id: Optional[str] = None, top_k: int = 5):
    """Search the knowledge base"""
    try:
        results = await chatbot.search_knowledge(query, top_k, session_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 10):
    """Get chat history for a session"""
    try:
        history = vector_store.get_chat_history(session_id, limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    try:
        success = vector_store.clear_chat_history(session_id)
        if success:
            return {"status": "success", "message": "Chat history cleared"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear chat history")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Check if the chatbot service is healthy"""
    try:
        # Test TiDB connection
        with tidb_conn.get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "services": {
                "tidb": "connected",
                "groq": "configured",
                "vector_store": "ready"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Add a new endpoint to get key usage statistics
@app.get("/stats/keys")
async def get_key_stats():
    """Get usage statistics for API keys"""
    return {"keys": key_manager.get_key_stats()}

@app.get("/meetings/verify")
async def verify_meeting_access():
    """Verify chatbot can access meeting data from TiDB"""
    try:
        with tidb_conn.get_engine().connect() as conn:
            # Check if meetings table exists and get count
            result = conn.execute(text("SELECT COUNT(*) as count FROM meetings"))
            meeting_count = result.fetchone()[0]
            
            # Get recent meetings
            result = conn.execute(text("SELECT id, title, created_at FROM meetings ORDER BY created_at DESC LIMIT 5"))
            recent_meetings = [dict(row._mapping) for row in result.fetchall()]
            
            # Check if tasks table exists and get count
            result = conn.execute(text("SELECT COUNT(*) as count FROM tasks"))
            task_count = result.fetchone()[0]
            
            return {
                "status": "success",
                "data_access": {
                    "meetings_count": meeting_count,
                    "tasks_count": task_count,
                    "recent_meetings": recent_meetings,
                    "database_shared": True
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "data_access": {
                "meetings_count": 0,
                "tasks_count": 0,
                "recent_meetings": [],
                "database_shared": False
            }
        }

@app.get("/meetings/comprehensive")
async def get_comprehensive_meeting_data():
    """Get comprehensive meeting data for chatbot queries"""
    try:
        with tidb_conn.get_engine().connect() as conn:
            # Get all meetings with details
            meetings_result = conn.execute(text("""
                SELECT m.id, m.title, m.created_at, m.updated_at,
                       COUNT(DISTINCT t.id) as task_count,
                       GROUP_CONCAT(DISTINCT t.title SEPARATOR '; ') as task_titles
                FROM meetings m
                LEFT JOIN tasks t ON m.id = t.meeting_id
                GROUP BY m.id, m.title, m.created_at, m.updated_at
                ORDER BY m.created_at DESC
            """))
            
            meetings = []
            for row in meetings_result:
                # Extract platform from meeting ID or title
                platform = "unknown"
                if "meet.google.com" in row.id:
                    platform = "Google Meet"
                elif "zoom.us" in row.id:
                    platform = "Zoom"
                elif "teams.microsoft.com" in row.id:
                    platform = "Microsoft Teams"
                
                meeting_data = {
                    "id": row.id,
                    "title": row.title,
                    "platform": platform,
                    "created_at": str(row.created_at),
                    "updated_at": str(row.updated_at),
                    "task_count": row.task_count or 0,
                    "task_titles": row.task_titles or "No tasks"
                }
                meetings.append(meeting_data)
            
            # Get all tasks with meeting context
            tasks_result = conn.execute(text("""
                SELECT t.id, t.meeting_id, t.title, t.description, t.assignee, 
                       t.due_date, t.priority, t.status, t.created_at,
                       m.title as meeting_title
                FROM tasks t
                LEFT JOIN meetings m ON t.meeting_id = m.id
                ORDER BY t.created_at DESC
            """))
            
            tasks = []
            for row in tasks_result:
                # Extract platform from meeting ID
                meeting_platform = "unknown"
                if row.meeting_id and "meet.google.com" in row.meeting_id:
                    meeting_platform = "Google Meet"
                elif row.meeting_id and "zoom.us" in row.meeting_id:
                    meeting_platform = "Zoom"
                elif row.meeting_id and "teams.microsoft.com" in row.meeting_id:
                    meeting_platform = "Microsoft Teams"
                
                task_data = {
                    "id": row.id,
                    "meeting_id": row.meeting_id,
                    "title": row.title,
                    "description": row.description,
                    "assignee": row.assignee,
                    "due_date": str(row.due_date) if row.due_date else None,
                    "priority": row.priority,
                    "status": row.status,
                    "created_at": str(row.created_at),
                    "meeting_title": row.meeting_title,
                    "meeting_platform": meeting_platform
                }
                tasks.append(task_data)
            
            # Get transcripts if available (CRITICAL for chatbot context)
            try:
                transcripts_result = conn.execute(text("""
                    SELECT meeting_id, transcript, timestamp
                    FROM transcripts
                    WHERE LENGTH(TRIM(transcript)) > 10
                    ORDER BY timestamp DESC
                    LIMIT 100
                """))
                transcripts = [dict(row._mapping) for row in transcripts_result]
                print(f"✅ Found {len(transcripts)} transcript segments for vector store")
            except Exception as e:
                print(f"⚠️ Could not load transcripts: {e}")
                transcripts = []
            
            return {
                "status": "success",
                "data": {
                    "meetings": meetings,
                    "tasks": tasks,
                    "transcripts": transcripts,
                    "summary": {
                        "total_meetings": len(meetings),
                        "total_tasks": len(tasks),
                        "total_transcripts": len(transcripts)
                    }
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "data": {
                "meetings": [],
                "tasks": [],
                "transcripts": [],
                "summary": {"total_meetings": 0, "total_tasks": 0, "total_transcripts": 0}
            }
        }

@app.post("/meetings/populate-vector-store")
async def populate_meeting_data_to_vector_store():
    """Populate all meeting data into vector store for better chatbot access - CRITICAL for hackathon demo"""
    try:
        comprehensive_data = await get_comprehensive_meeting_data()
        if comprehensive_data["status"] != "success":
            raise Exception("Failed to get comprehensive meeting data")
        
        data = comprehensive_data["data"]
        texts_to_add = []
        embeddings_to_add = []
        metadata_to_add = []
        
        # Add meeting summaries with enhanced context
        for meeting in data["meetings"]:
            meeting_text = f"""Meeting: {meeting['title']}
ID: {meeting['id']}
Platform: {meeting['platform']}
Date: {meeting['created_at']}
Tasks: {meeting['task_count']} tasks - {meeting['task_titles']}
Meeting Summary: This meeting took place on {meeting['platform']} and generated {meeting['task_count']} action items."""
            
            texts_to_add.append(meeting_text)
            metadata_to_add.append({
                "type": "meeting_summary",
                "meeting_id": meeting['id'],
                "platform": meeting['platform'],
                "date": meeting['created_at'],
                "task_count": meeting['task_count']
            })
        
        # Add task details with meeting context
        for task in data["tasks"]:
            task_text = f"""Task: {task['title']}
Description: {task['description'] or 'No description'}
Assignee: {task['assignee'] or 'Unassigned'}
Priority: {task['priority']}
Status: {task['status']}
Meeting: {task['meeting_title']} ({task['meeting_id']})
Meeting Platform: {task['meeting_platform']}
Due Date: {task['due_date'] or 'No due date'}
Task Context: This task was created from meeting {task['meeting_id']} on {task['meeting_platform']}."""
            
            texts_to_add.append(task_text)
            metadata_to_add.append({
                "type": "task",
                "task_id": task['id'],
                "meeting_id": task['meeting_id'],
                "assignee": task['assignee'],
                "priority": task['priority'],
                "status": task['status']
            })
        
        # Add transcript data if available
        for transcript in data["transcripts"]:
            if transcript.get('transcript') and len(transcript['transcript'].strip()) > 20:
                transcript_text = f"""Meeting Transcript from {transcript['meeting_id']}:
Timestamp: {transcript['timestamp']}
Content: {transcript['transcript']}
Transcript Context: This is a transcript segment from meeting {transcript['meeting_id']}."""
                
                texts_to_add.append(transcript_text)
                metadata_to_add.append({
                    "type": "meeting_transcript",
                    "meeting_id": transcript['meeting_id'],
                    "timestamp": transcript['timestamp'],
                    "category": "transcript"
                })
        
        # Generate embeddings for all texts
        if texts_to_add:
            embeddings_to_add = chatbot.embedding_model.encode(texts_to_add).tolist()
            
            # Add to vector store
            await vector_store.add_texts(texts_to_add, embeddings_to_add, metadata_to_add)
        
        return {
            "status": "success",
            "message": f"Added {len(texts_to_add)} items to vector store",
            "details": {
                "meetings_added": len(data["meetings"]),
                "tasks_added": len(data["tasks"]),
                "transcripts_added": len(data["transcripts"]),
                "total_items": len(texts_to_add)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)