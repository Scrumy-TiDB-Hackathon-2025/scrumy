"""
Additional FastAPI endpoints for tools integration
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
from fastapi import APIRouter

# Create a router instance
router = APIRouter()
logger = logging.getLogger(__name__)

class TranscriptWithToolsRequest(BaseModel):
    text: str
    meeting_id: str
    timestamp: Optional[str] = None
    platform: Optional[str] = "unknown"

class TranscriptWithToolsRequest(BaseModel):
    text: str
    meeting_id: str
    timestamp: Optional[str] = None
    platform: Optional[str] = "unknown"


@router.post("/tools/process_transcript")
async def process_transcript_with_tools(request: TranscriptWithToolsRequest):
    """Process transcript and automatically execute tools"""
    try:
        from .ai_agent import AIAgent
        
        agent = AIAgent()
        
        result = await agent.process_with_tools(
            transcript=request.text,
            meeting_id=request.meeting_id
        )
        
        return {
            "status": "success",
            "meeting_id": request.meeting_id,
            "analysis": result["analysis"],
            "actions_taken": result["tool_calls"],
            "tools_used": result.get("tools_used", 0),
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing transcript with tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/available")
async def get_available_tools():
    """Get list of available tools for the agent"""
    from .tools import tools
    return {
        "tools": tools.get_tools_schema(),
        "tool_names": tools.list_tools(),
        "count": len(tools.tools)
    }
