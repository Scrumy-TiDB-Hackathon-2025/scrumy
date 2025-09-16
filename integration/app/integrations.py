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
from .retry_manager import retry_manager

logger = logging.getLogger(__name__)

class NotionIntegration:
    """Enhanced Notion API integration with proper validation and error handling"""

    def __init__(self, token: str = None, database_id: str = None):
        self.token = token or os.getenv("NOTION_TOKEN")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.is_mock = not self.token or self.token == "mock_token_for_dev"

    def _validate_task_data(self, task: Dict) -> Dict:
        """Validate task data according to Notion API requirements"""
        errors = []

        # Title is required and has length limits
        if not task.get("title"):
            errors.append("Title is required")
        elif len(task["title"]) > 2000:
            errors.append("Title too long (max 2000 characters)")

        # Validate priority values
        if task.get("priority") and task["priority"] not in ["low", "medium", "high", "urgent"]:
            errors.append("Priority must be one of: low, medium, high, urgent")

        # Due date validation removed - not available in database schema

        # Validate description length
        if task.get("description") and len(task["description"]) > 2000:
            errors.append("Description too long (max 2000 characters)")

        return {"valid": len(errors) == 0, "errors": errors}

    def _handle_notion_error(self, status_code: int, error_data: Dict) -> Dict:
        """Handle specific Notion API errors"""
        error_code = error_data.get("code", "unknown_error")

        error_messages = {
            401: "Unauthorized - Check your Notion integration token",
            403: "Forbidden - Integration doesn't have access to this database",
            404: "Database not found - Make sure you shared the database with your integration",
            409: "Conflict - Database is being modified by another process",
            429: "Rate limit exceeded - Please try again in a few minutes",
            400: {
                "validation_error": "Database schema mismatch - Check required properties exist in your database",
                "invalid_json": "Invalid request format",
                "invalid_request_url": "Invalid database ID format",
                "invalid_property_value": "Invalid property value - Check select options match database schema"
            },
            500: "Notion server error - Please try again later",
            502: "Notion server temporarily unavailable",
            503: "Notion service unavailable - Please try again later"
        }

        if status_code in error_messages:
            if isinstance(error_messages[status_code], dict):
                message = error_messages[status_code].get(error_code, f"Bad request: {error_code}")
            else:
                message = error_messages[status_code]
        else:
            message = f"Notion API error {status_code}: {error_code}"

        return {
            "success": False,
            "error": message,
            "error_code": error_code,
            "status_code": status_code,
            "retryable": status_code in [429, 500, 502, 503, 504]
        }

    async def create_task(self, task: Dict) -> Dict:
        """Create task in Notion with simplified, working implementation"""
        if self.is_mock:
            return self._create_mock_task(task)

        # Validate input data
        validation = self._validate_task_data(task)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Validation failed: {', '.join(validation['errors'])}",
                "validation_errors": validation["errors"]
            }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # Build Notion page properties with proper truncation
        properties = {
            "Name": {
                "title": [{"text": {"content": task["title"][:2000]}}]  # Respect Notion limits
            }
        }

        # Add optional properties with validation
        if task.get("description"):
            properties["Description"] = {
                "rich_text": [{"text": {"content": task["description"][:2000]}}]
            }

        if task.get("priority"):
            # Map priority values to match database options
            priority_mapping = {
                "low": "Low",
                "medium": "Medium",
                "high": "High",
                "urgent": "High"  # Map urgent to High since that's what's available
            }
            priority_value = priority_mapping.get(task["priority"].lower(), "Medium")
            properties["Priority"] = {
                "select": {"name": priority_value}
            }

        # Always set initial status
        properties["Status"] = {
            "select": {"name": "Not Started"}
        }

        if task.get("assignee"):
            # Use the assignee name directly - Notion will create the option if it doesn't exist
            # Clean up the assignee name for consistency
            assignee_name = task["assignee"].strip()

            # Apply some basic formatting for common cases
            if assignee_name.lower() in ["scrumbot", "scrumai", "ai"]:
                assignee_name = "ScrumAI"
            elif assignee_name.lower() == "test user":
                assignee_name = "Test User"
            else:
                # Use the original name, properly capitalized
                assignee_name = " ".join(word.capitalize() for word in assignee_name.split())

            properties["Assignee"] = {
                "select": {"name": assignee_name}
            }

        # Due Date and Meeting ID properties not available in database schema - removed

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
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
                            "task_id": result["id"],
                            "task_url": result["url"],
                            "task": task
                        }
                    else:
                        try:
                            error_data = await response.json()
                        except:
                            error_data = {"code": "unknown_error", "message": await response.text()}

                        return self._handle_notion_error(response.status, error_data)

        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout - Notion API is slow", "retryable": True}
        except Exception as e:
            logger.error(f"Error creating Notion task: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}", "retryable": True}

    def _create_mock_task(self, task: Dict) -> Dict:
        """Create mock task response for development"""
        title = task.get('title', 'Untitled Task')
        mock_page_id = f"mock_page_{hash(title) % 10000}"
        mock_url = f"https://notion.so/mock-workspace/{mock_page_id}"

        logger.info(f"[MOCK] Created Notion task: {title}")

        return {
            "success": True,
            "notion_page_id": mock_page_id,
            "notion_url": mock_url,
            "task_id": mock_page_id,
            "task_url": mock_url,
            "task": task,
            "mock": True,
            "platform": "notion",
            "message": "This is a mock response for development testing"
        }

class SlackIntegration:
    """Enhanced Slack API integration with proper error handling"""

    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.base_url = "https://slack.com/api"
        self.is_mock = not self.bot_token or self.bot_token == "mock_token_for_dev"
        self._channel_cache = {}  # Cache for channel ID resolution

    async def _resolve_channel_name(self, channel_name: str) -> str:
        """Resolve channel name to channel ID"""
        if channel_name in self._channel_cache:
            return self._channel_cache[channel_name]

        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{self.base_url}/conversations.list",
                    headers=headers,
                    params={"types": "public_channel,private_channel"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            for channel in result.get("channels", []):
                                if channel.get("name") == channel_name:
                                    channel_id = channel.get("id")
                                    self._channel_cache[channel_name] = channel_id
                                    return channel_id
            return None
        except Exception as e:
            logger.error(f"Error resolving channel name {channel_name}: {str(e)}")
            return None

    def _handle_slack_error(self, error_code: str) -> str:
        """Handle specific Slack API errors"""
        error_messages = {
            "not_in_channel": "Bot is not in the channel. Please invite the bot to the channel.",
            "channel_not_found": "Channel not found. Please check the channel name or create the channel.",
            "invalid_auth": "Invalid bot token. Please check your SLACK_BOT_TOKEN environment variable.",
            "missing_scope": "Missing required OAuth scope. Bot needs 'chat:write' permission.",
            "rate_limited": "Rate limit exceeded. Please try again in a few minutes.",
            "invalid_blocks": "Invalid message blocks format.",
            "msg_too_long": "Message is too long. Please shorten the task description.",
            "restricted_action": "Bot doesn't have permission to post in this channel."
        }
        return error_messages.get(error_code, f"Slack API error: {error_code}")

    async def send_task_notification(self, task: Dict, channel: str = "#scrumbot-tasks") -> Dict:
        """Send enhanced task notification to Slack with proper error handling"""
        if self.is_mock:
            return self._send_mock_notification(task, channel)

        # Validate input
        if not task.get("title"):
            return {"success": False, "error": "Task title is required"}

        # Resolve channel name to ID if needed
        channel_id = channel
        if channel.startswith('#'):
            resolved_id = await self._resolve_channel_name(channel[1:])
            if resolved_id:
                channel_id = resolved_id
            else:
                logger.warning(f"Could not resolve channel {channel}, using as-is")

        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # Create enhanced Slack message with better formatting
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 New Task: {task['title'][:150]}",  # Slack header limit
                    "emoji": True
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
            }
        ]

        # Add description if provided
        if task.get("description"):
            description = task["description"][:1000]  # Limit description length
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{description}"
                }
            })

        # Add due date if provided
        if task.get("due_date"):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Due Date:* {task['due_date']}"
                }
            })

        # Add meeting context if available
        if task.get("meeting_id"):
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 From meeting: {task['meeting_id']}"
                    }
                ]
            })

        payload = {
            "channel": channel_id,
            "text": f"New task: {task['title']}",  # Fallback text for notifications
            "blocks": blocks,
            "unfurl_links": False,
            "unfurl_media": False
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=headers,
                    json=payload
                ) as response:
                    result = await response.json()

                    if response.status == 200 and result.get("ok"):
                        return {
                            "success": True,
                            "message_ts": result.get("ts"),
                            "channel": result.get("channel"),
                            "permalink": result.get("message", {}).get("permalink")
                        }
                    else:
                        # Handle Slack-specific errors
                        error_code = result.get("error", "unknown_error")
                        error_message = self._handle_slack_error(error_code)

                        logger.error(f"Slack API error: {error_code} - {error_message}")
                        return {
                            "success": False,
                            "error": error_message,
                            "error_code": error_code,
                            "retryable": error_code in ["rate_limited", "timeout"]
                        }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout - Slack API is slow", "retryable": True}
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}", "retryable": True}

    def _send_mock_notification(self, task: Dict, channel: str) -> Dict:
        """Send mock notification for development"""
        title = task.get('title', 'Untitled Task')
        logger.info(f"[MOCK] Slack notification to {channel}: {title}")

        return {
            "success": True,
            "message_ts": "1234567890.123456",
            "channel": "C1234567890",
            "mock": True
        }


class ClickUpIntegration:
    """Enhanced ClickUp API integration with proper user resolution and error handling"""

    def __init__(self, token: str = None, list_id: str = None, team_id: str = None):
        self.token = token or os.getenv("CLICKUP_TOKEN")
        self.list_id = list_id or os.getenv("CLICKUP_LIST_ID")
        self.team_id = team_id or os.getenv("CLICKUP_TEAM_ID")
        self.base_url = "https://api.clickup.com/api/v2"
        self.is_mock = not self.token or self.token == "mock_token_for_dev"
        self._user_cache = {}  # Cache for user ID resolution

    async def _resolve_user_name(self, name: str) -> str:
        """Resolve user name/email to user ID (required by ClickUp API)"""
        if name in self._user_cache:
            return self._user_cache[name]

        headers = {
            "Authorization": self.token,  # ClickUp doesn't use "Bearer"
            "Content-Type": "application/json"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{self.base_url}/team/{self.team_id}/member",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        for member in result.get("members", []):
                            user = member.get("user", {})
                            # Match by username, email, or display name
                            if (user.get("username") == name or
                                user.get("email") == name or
                                user.get("username", "").lower() == name.lower()):
                                user_id = str(user.get("id"))
                                self._user_cache[name] = user_id
                                return user_id
            return None
        except Exception as e:
            logger.error(f"Error resolving ClickUp user {name}: {str(e)}")
            return None

    def _handle_clickup_error(self, status_code: int, error_data: Dict) -> Dict:
        """Handle specific ClickUp API errors"""
        error_msg = error_data.get("err", error_data.get("error", "Unknown error"))

        error_messages = {
            401: "Unauthorized - Check your ClickUp API token",
            403: "Forbidden - Token doesn't have access to this workspace/list",
            404: "Not found - Check your LIST_ID and TEAM_ID",
            429: "Rate limit exceeded - Please try again later",
            400: f"Bad request - {error_msg}",
            500: "ClickUp server error - Please try again later"
        }

        message = error_messages.get(status_code, f"ClickUp API error {status_code}: {error_msg}")

        return {
            "success": False,
            "error": message,
            "error_code": error_msg,
            "status_code": status_code,
            "retryable": status_code in [429, 500, 502, 503, 504]
        }

    async def create_task(self, task: Dict) -> Dict:
        """Create task in ClickUp with proper user resolution and error handling"""
        if self.is_mock:
            return self._create_mock_task(task)

        # Validate required fields
        if not task.get("title"):
            return {"success": False, "error": "Task title is required"}

        headers = {
            "Authorization": self.token,  # ClickUp uses direct token, not "Bearer"
            "Content-Type": "application/json"
        }

        # Map priority levels (ClickUp: 1=urgent, 2=high, 3=normal, 4=low)
        priority_map = {"urgent": 1, "high": 2, "medium": 3, "low": 4}

        payload = {
            "name": task["title"][:255],  # ClickUp title limit
            "description": task.get("description", "")[:8000],  # ClickUp description limit
            "priority": priority_map.get(task.get("priority", "medium"), 3),
            "status": "to do",  # Use proper ClickUp status
            "tags": ["scrumbot", "ai-generated"]
        }

        # Handle due date (ClickUp expects Unix timestamp in milliseconds)
        if task.get("due_date"):
            try:
                dt = datetime.fromisoformat(task["due_date"])
                payload["due_date"] = int(dt.timestamp() * 1000)
            except ValueError:
                logger.warning(f"Invalid due_date format: {task['due_date']}")

        # Handle assignees (CRITICAL: Must be user IDs, not names)
        if task.get("assignee"):
            user_id = await self._resolve_user_name(task["assignee"])
            if user_id:
                payload["assignees"] = [int(user_id)]  # ClickUp expects integer IDs
                logger.info(f"Resolved assignee '{task['assignee']}' to user ID {user_id}")
            else:
                logger.warning(f"Could not resolve assignee '{task['assignee']}' to user ID")
                # Don't fail the task creation, just skip assignee

        # Add meeting context as a tag if available
        if task.get("meeting_id"):
            payload["tags"].append(f"meeting-{task['meeting_id']}")

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/list/{self.list_id}/task",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "task_id": result["id"],
                            "task_url": result["url"],
                            "clickup_task_id": result["id"],
                            "clickup_url": result["url"],
                            "task": task
                        }
                    else:
                        try:
                            error_data = await response.json()
                        except:
                            error_data = {"err": await response.text()}

                        return self._handle_clickup_error(response.status, error_data)

        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout - ClickUp API is slow", "retryable": True}
        except Exception as e:
            logger.error(f"Error creating ClickUp task: {str(e)}")
            return {"success": False, "error": f"Network error: {str(e)}", "retryable": True}

    def _create_mock_task(self, task: Dict) -> Dict:
        """Create mock task for development"""
        title = task.get('title', 'Untitled Task')
        mock_task_id = f"cu_mock_{hash(title) % 10000}"
        mock_url = f"https://app.clickup.com/t/{mock_task_id}"

        logger.info(f"[MOCK] Created ClickUp task: {title}")

        return {
            "success": True,
            "platform": "clickup",
            "task_id": mock_task_id,
            "task_url": mock_url,
            "clickup_task_id": mock_task_id,
            "clickup_url": mock_url,
            "task": task,
            "mock": True,
            "message": "This is a mock response - ClickUp task creation simulated"
        }


class IntegrationManager:
    """Unified integration manager for all tools"""

    def __init__(self):
        self.integrations = {}

        # Initialize available integrations
        try:
            self.integrations["notion"] = NotionIntegration()
            logger.info("Notion integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Notion integration: {e}")

        try:
            self.integrations["slack"] = SlackIntegration()
            logger.info("Slack integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Slack integration: {e}")

        try:
            self.integrations["clickup"] = ClickUpIntegration()
            logger.info("ClickUp integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ClickUp integration: {e}")

    async def create_task_all(self, task_data: Dict, max_retries: int = 2) -> Dict:
        """Create task in all available integrations with sophisticated retry logic"""
        results = {}

        for name, integration in self.integrations.items():
            if hasattr(integration, 'create_task'):
                # Use sophisticated retry manager for each integration
                logger.info(f"Creating task in {name} with retry mechanism")

                result = await retry_manager.execute_with_retry(
                    integration.create_task,
                    name,  # service_name for retry manager
                    task_data
                )

                # Handle retry manager response format
                if result.get("success"):
                    results[name] = result.get("result", {"success": True})
                    logger.info(f"Task creation successful for {name}")

                    # Log retry statistics if retries were used
                    if result.get("attempts_made", 1) > 1:
                        logger.info(f"Task in {name} succeeded after {result.get('attempts_made')} attempts")
                else:
                    results[name] = {
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                        "retryable": result.get("retries_exhausted", False)
                    }
                    if result.get("retries_exhausted"):
                        logger.error(f"Task creation in {name} failed after {result.get('attempts_made')} attempts: {result.get('error')}")
                    else:
                        logger.error(f"Task creation in {name} failed (non-retryable): {result.get('error')}")

        success_count = sum(1 for r in results.values() if r.get("success", False))

        return {
            "success": success_count > 0,
            "results": results,
            "integrations_used": list(self.integrations.keys()),
            "successful_integrations": success_count,
            "total_integrations": len(self.integrations),
            "retry_manager_used": True
        }

    async def send_notifications_all(self, message: str, task_data: Dict = None) -> Dict:
        """Send notifications to all integrations that support it"""
        results = {}

        for name, integration in self.integrations.items():
            if hasattr(integration, 'send_task_notification'):
                try:
                    if task_data:
                        result = await integration.send_task_notification(task_data)
                    else:
                        # Create a simple notification task
                        simple_task = {
                            "title": "Meeting Update",
                            "description": message
                        }
                        result = await integration.send_task_notification(simple_task)

                    results[name] = result
                    logger.info(f"Notification result for {name}: {result.get('success', False)}")
                except Exception as e:
                    logger.error(f"Error sending notification to {name}: {str(e)}")
                    results[name] = {"success": False, "error": str(e)}

        success_count = sum(1 for r in results.values() if r.get("success", False))

        return {
            "success": success_count > 0,
            "results": results,
            "successful_notifications": success_count
        }

# Global integration manager instance
integration_manager = IntegrationManager()
