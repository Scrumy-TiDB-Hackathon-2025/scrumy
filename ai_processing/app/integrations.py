"""
Direct API integrations for Notion, ClickUp, and Slack
Simplified approach without MCP servers
"""

import requests
import asyncio
import aiohttp
import json
import os
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotionIntegration:
    """Direct Notion API integration"""
    
    def __init__(self, token: str = None, database_id: str = None):
        self.token = token or os.getenv("NOTION_TOKEN")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.is_mock = not self.token or self.token == "mock_token_for_dev"
    
    async def create_task(self, task: Dict) -> Dict:
        """Create task directly in Notion"""
        if self.is_mock:
            return self._create_mock_task(task)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # Build Notion page properties
        properties = {
            "Name": {
                "title": [{"text": {"content": task["title"]}}]
            },
            "Description": {
                "rich_text": [{"text": {"content": task.get("description", "")}}]
            },
            "Priority": {
                "select": {"name": task.get("priority", "medium").capitalize()}
            },
            "Status": {
                "select": {"name": "Not Started"}
            }
        }
        
        # Add optional fields
        if task.get("assignee"):
            properties["Assignee"] = {
                "rich_text": [{"text": {"content": task["assignee"]}}]
            }
        
        if task.get("due_date"):
            properties["Due Date"] = {
                "date": {"start": task["due_date"]}
            }
        
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/pages",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "notion_page_id": result["id"],
                            "notion_url": result["url"],
                            "task": task
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Notion API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Notion API error: {response.status}",
                            "details": error_text
                        }
        except Exception as e:
            logger.error(f"Error creating Notion task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_mock_task(self, task: Dict) -> Dict:
        """Create mock task response for development"""
        mock_page_id = f"mock_page_{hash(task['title']) % 10000}"
        mock_url = f"https://notion.so/mock-workspace/{mock_page_id}"
        
        logger.info(f"[MOCK] Created Notion task: {task['title']}")
        
        return {
            "success": True,
            "notion_page_id": mock_page_id,
            "notion_url": mock_url,
            "task": task,
            "mock": True
        }

class SlackIntegration:
    """Direct Slack API integration"""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.base_url = "https://slack.com/api"
        self.is_mock = not self.bot_token or self.bot_token == "mock_token_for_dev"
    
    async def send_task_notification(self, task: Dict, channel: str = "#scrumbot-tasks") -> Dict:
        """Send task notification to Slack"""
        if self.is_mock:
            return self._send_mock_notification(task, channel)
        
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        # Create rich Slack message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 New Task: {task['title']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Assignee:*\n{task.get('assignee', 'Unassigned')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{task.get('priority', 'medium').upper()}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{task.get('description', 'No description provided')}"
                }
            }
        ]
        
        if task.get("due_date"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Due Date:* {task['due_date']}"
                }
            })
        
        payload = {
            "channel": channel,
            "text": f"New task: {task['title']}",
            "blocks": blocks
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            return {
                                "success": True,
                                "message_ts": result.get("ts"),
                                "channel": result.get("channel")
                            }
                        else:
                            return {
                                "success": False,
                                "error": result.get("error", "Unknown Slack API error")
                            }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _send_mock_notification(self, task: Dict, channel: str) -> Dict:
        """Send mock notification for development"""
        logger.info(f"[MOCK] Slack notification to {channel}: {task['title']}")
        
        return {
            "success": True,
            "message_ts": "1234567890.123456",
            "channel": "C1234567890",
            "mock": True
        }


class ClickUpIntegration:
    """Direct ClickUp API integration"""
    
    def __init__(self, token: str = None, list_id: str = None, team_id: str = None):
        self.token = token or os.getenv("CLICKUP_TOKEN")
        self.list_id = list_id or os.getenv("CLICKUP_LIST_ID")
        self.team_id = team_id or os.getenv("CLICKUP_TEAM_ID")
        self.base_url = "https://api.clickup.com/api/v2"
        self.is_mock = not self.token or self.token == "mock_token_for_dev"
    
    async def create_task(self, task: Dict) -> Dict:
        """Create task in ClickUp"""
        if self.is_mock:
            return self._create_mock_task(task)
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Map priority levels (ClickUp uses 1-4, 1=urgent, 4=low)
        priority_map = {"low": 4, "medium": 3, "high": 2, "urgent": 1}
        
        payload = {
            "name": task["title"],
            "description": task.get("description", ""),
            "priority": priority_map.get(task.get("priority", "medium"), 3),
            "status": "to do",
            "tags": ["scrumbot", "ai-generated"],
            "notify_all": True
        }
        
        # Add due date if provided
        if task.get("due_date"):
            try:
                due_timestamp = int(datetime.fromisoformat(task["due_date"]).timestamp() * 1000)
                payload["due_date"] = due_timestamp
            except:
                pass  # Skip invalid dates
        
        # Add assignee if provided
        if task.get("a