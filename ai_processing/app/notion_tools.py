"""
Notion integration tools for ScrumBot AI agent
"""

from .tools import tools
from .integrations import NotionIntegration
from .tidb_manager import TiDBManager
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Initialize integrations
notion = NotionIntegration()
tidb = TiDBManager()

async def create_notion_task(title: str, description: str, assignee: str = None, 
                           priority: str = "medium", due_date: str = None, 
                           meeting_id: str = None) -> Dict:
    """Tool function to create a task in Notion"""
    
    task_data = {
        "title": title,
        "description": description,
        "assignee": assignee,
        "priority": priority,
        "due_date": due_date,
        "meeting_id": meeting_id
    }
    
    try:
        # Create task in Notion
        result = await notion.create_task(task_data)
        
        if result["success"]:
            # Also save to TiDB for synchronization
            if meeting_id:
                await tidb.save_task(
                    task_id=f"task_{hash(title) % 10000}",
                    meeting_id=meeting_id,
                    title=title,
                    description=description,
                    assignee=assignee,
                    due_date=due_date,
                    priority=priority,
                    notion_page_id=result.get("notion_page_id")
                )
            
            return {
                "task_created": True,
                "notion_url": result.get("notion_url"),
                "task_id": result.get("notion_page_id"),
                "title": title,
                "assignee": assignee
            }
        else:
            return {
                "task_created": False, 
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"Error in create_notion_task: {str(e)}")
        return {"task_created": False, "error": str(e)}

# Register the tool
tools.register_tool(
    name="create_notion_task",
    description="Create a new task in Notion database with title, description, assignee, priority, and due date",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The task title (required)"
            },
            "description": {
                "type": "string", 
                "description": "Detailed description of the task (required)"
            },
            "assignee": {
                "type": "string",
                "description": "Person assigned to the task (optional)"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Task priority level (default: medium)"
            },
            "due_date": {
                "type": "string",
                "description": "Due date in YYYY-MM-DD format (optional)"
            },
            "meeting_id": {
                "type": "string",
                "description": "ID of the meeting this task came from (optional)"
            }
        },
        "required": ["title", "description"]
    },
    function=create_notion_task
)