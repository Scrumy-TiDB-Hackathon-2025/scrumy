"""
Slack integration tools for ScrumBot AI agent
"""

from .tools import tools
from .integrations import SlackIntegration
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Initialize Slack integration
slack = SlackIntegration()

async def send_slack_notification(message: str, channel: str = "#scrumbot-tasks", 
                                 task_title: str = None, assignee: str = None,
                                 priority: str = None, due_date: str = None) -> Dict:
    """Tool function to send notifications to Slack"""
    
    try:
        if task_title:
            # Format as task notification
            task_data = {
                "title": task_title,
                "description": message,
                "assignee": assignee,
                "priority": priority,
                "due_date": due_date
            }
            result = await slack.send_task_notification(task_data, channel)
        else:
            # Send simple message (would need to implement this method)
            result = await slack.send_task_notification({
                "title": "Meeting Update",
                "description": message
            }, channel)
        
        return {
            "notification_sent": result["success"],
            "channel": channel,
            "message": message,
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error in send_slack_notification: {str(e)}")
        return {
            "notification_sent": False,
            "error": str(e)
        }

# Register the tool
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