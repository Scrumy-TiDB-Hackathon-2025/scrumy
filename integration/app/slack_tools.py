"""
Slack integration tools for ScrumBot AI agent
"""

try:
    from .tools import tools
    from .integrations import integration_manager
except ImportError:
    from tools import tools
    from integrations import integration_manager
from typing import Dict
import logging

logger = logging.getLogger(__name__)

async def send_slack_notification(message: str, channel: str = "#scrumbot-tasks", 
                                 task_title: str = None, assignee: str = None,
                                 priority: str = None, due_date: str = None) -> Dict:
    """Tool function to send notifications to Slack"""
    
    try:
        # Get Slack integration
        slack_integration = integration_manager.integrations.get("slack")
        if not slack_integration:
            return {"notification_sent": False, "error": "Slack integration not available"}
        
        if task_title:
            # Format as task notification
            task_data = {
                "title": task_title,
                "description": message,
                "assignee": assignee,
                "priority": priority,
                "due_date": due_date
            }
            result = await slack_integration.send_task_notification(task_data, channel)
        else:
            # Send simple message
            result = await slack_integration.send_task_notification({
                "title": "Meeting Update",
                "description": message
            }, channel)
        
        return {
            "notification_sent": result["success"],
            "channel": channel,
            "message": message,
            "mock": result.get("mock", False),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error in send_slack_notification: {str(e)}")
        return {
            "notification_sent": False,
            "error": str(e)
        }

async def send_meeting_summary(meeting_id: str, summary: str, tasks_created: int = 0,
                              channel: str = "#scrumbot-tasks") -> Dict:
    """Send a meeting summary notification to Slack"""
    
    try:
        slack_integration = integration_manager.integrations.get("slack")
        if not slack_integration:
            return {"notification_sent": False, "error": "Slack integration not available"}
        
        summary_message = f"📋 Meeting Summary for {meeting_id}\n\n{summary}"
        if tasks_created > 0:
            summary_message += f"\n\n✅ {tasks_created} tasks created automatically"
        
        task_data = {
            "title": f"Meeting Summary - {meeting_id}",
            "description": summary_message
        }
        
        result = await slack_integration.send_task_notification(task_data, channel)
        
        return {
            "notification_sent": result["success"],
            "channel": channel,
            "meeting_id": meeting_id,
            "tasks_created": tasks_created,
            "mock": result.get("mock", False),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error in send_meeting_summary: {str(e)}")
        return {
            "notification_sent": False,
            "error": str(e)
        }

# Register the tools
tools.register_tool(
    name="send_slack_notification",
    description="Send a notification to Slack channel about tasks or meeting updates",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message content to send (required)"
            },
            "channel": {
                "type": "string",
                "description": "Slack channel to send to (default: #scrumbot-tasks)"
            },
            "task_title": {
                "type": "string",
                "description": "If this is a task notification, provide the task title"
            },
            "assignee": {
                "type": "string",
                "description": "Person assigned to the task (for task notifications)"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Task priority (for task notifications)"
            },
            "due_date": {
                "type": "string",
                "description": "Due date in YYYY-MM-DD format (for task notifications)"
            }
        },
        "required": ["message"]
    },
    function=send_slack_notification
)

tools.register_tool(
    name="send_meeting_summary",
    description="Send a comprehensive meeting summary notification to Slack",
    parameters={
        "type": "object",
        "properties": {
            "meeting_id": {
                "type": "string",
                "description": "ID of the meeting (required)"
            },
            "summary": {
                "type": "string",
                "description": "Meeting summary text (required)"
            },
            "tasks_created": {
                "type": "integer",
                "description": "Number of tasks created from the meeting (default: 0)"
            },
            "channel": {
                "type": "string",
                "description": "Slack channel to send to (default: #scrumbot-tasks)"
            }
        },
        "required": ["meeting_id", "summary"]
    },
    function=send_meeting_summary
)