"""
Integration Bridge for AI Processing

This module provides a bridge between the AI processing system and the integration system.
It handles task creation across multiple platforms (Notion, Slack, ClickUp) based on 
AI-extracted tasks from meeting transcripts.

CURRENT LIMITATIONS (TODO: Update when database support is available):
- meeting_id: Not supported by current database schema
- due_date: Not supported by current database schema

The integration system code supports these fields, but they are excluded here
to prevent database errors until schema is updated.
"""

import sys
import os
import asyncio
from typing import Dict, List, Optional
import logging

# Add integration directory to path to import integration modules
integration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'integration')
sys.path.insert(0, integration_path)

try:
    from app.tools import ToolsRegistry
    from app.integrations import IntegrationManager
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Integration system not available: {e}")
    INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIProcessingIntegrationBridge:
    """
    Bridge between AI processing and integration system.
    
    Handles:
    - Task data transformation from AI format to integration format
    - Error handling to ensure AI processing continues even if integrations fail
    - Configuration management for integration settings
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the integration bridge.
        
        Args:
            config: Integration configuration dict with settings like:
                   {
                       "enabled": True,
                       "platforms": ["notion", "slack", "clickup"],
                       "mock_mode": False
                   }
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True) and INTEGRATION_AVAILABLE
        self.mock_mode = self.config.get("mock_mode", False)
        
        if self.enabled:
            try:
                self.tools_registry = ToolsRegistry()
                self.integration_manager = IntegrationManager()
                logger.info("Integration bridge initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize integration components: {e}")
                self.enabled = False
        else:
            logger.info("Integration bridge disabled or not available")
    
    def _transform_ai_task_to_integration_format(self, ai_task: Dict) -> Dict:
        """
        Transform AI-extracted task to integration system format.
        
        Current supported fields (database limitations):
        - title (required)
        - description (optional)
        - assignee (optional)
        - priority (optional, defaults to 'medium')
        
        TODO: Add when database supports:
        - meeting_id: For tracking which meeting the task came from
        - due_date: For task scheduling
        
        Args:
            ai_task: Task dict from AI processing system
            
        Returns:
            Dict formatted for integration system
        """
        # Extract and validate core fields
        title = ai_task.get("title", "").strip()
        if not title:
            raise ValueError("Task title is required")
        
        description = ai_task.get("description", "").strip()
        assignee = ai_task.get("assignee", "").strip()
        priority = ai_task.get("priority", "medium").lower()
        
        # Validate priority
        valid_priorities = ["low", "medium", "high", "urgent"]
        if priority not in valid_priorities:
            logger.warning(f"Invalid priority '{priority}', defaulting to 'medium'")
            priority = "medium"
        
        integration_task = {
            "title": title,
            "description": description,
            "assignee": assignee,
            "priority": priority
        }
        
        # TODO: Uncomment when database supports these fields
        # meeting_id = ai_task.get("meeting_id")
        # if meeting_id:
        #     integration_task["meeting_id"] = meeting_id
        #
        # due_date = ai_task.get("due_date")  
        # if due_date:
        #     integration_task["due_date"] = due_date
        
        return integration_task
    
    async def create_tasks_from_ai_results(self, ai_tasks: List[Dict], 
                                         meeting_context: Optional[Dict] = None) -> Dict:
        """
        Create tasks in integration platforms based on AI-extracted tasks.
        
        Args:
            ai_tasks: List of tasks extracted by AI processing
            meeting_context: Optional context about the meeting
            
        Returns:
            Dict with integration results and statistics
        """
        if not self.enabled:
            return {
                "integration_enabled": False,
                "reason": "Integration system disabled or not available",
                "tasks_processed": 0,
                "tasks_created": 0,
                "successful_integrations": [],
                "failed_integrations": [],
                "errors": []
            }
        
        if not ai_tasks:
            return {
                "integration_enabled": True,
                "tasks_processed": 0,
                "tasks_created": 0,
                "successful_integrations": [],
                "failed_integrations": [],
                "errors": []
            }
        
        results = {
            "integration_enabled": True,
            "tasks_processed": len(ai_tasks),
            "tasks_created": 0,
            "successful_integrations": [],
            "failed_integrations": [],
            "task_urls": {},
            "errors": []
        }
        
        logger.info(f"Processing {len(ai_tasks)} tasks for integration")
        
        for i, ai_task in enumerate(ai_tasks):
            try:
                # Transform task format
                integration_task = self._transform_ai_task_to_integration_format(ai_task)
                
                # Create task using tools registry
                result = await self.tools_registry.create_task_everywhere(
                    title=integration_task["title"],
                    description=integration_task["description"],
                    assignee=integration_task["assignee"],
                    priority=integration_task["priority"]
                    # TODO: Add when supported:
                    # meeting_id=integration_task.get("meeting_id"),
                    # due_date=integration_task.get("due_date")
                )
                
                if result.get("success"):
                    results["tasks_created"] += 1
                    
                    # Track successful integrations
                    integrations_used = result.get("integrations_used", [])
                    for integration in integrations_used:
                        if integration not in results["successful_integrations"]:
                            results["successful_integrations"].append(integration)
                    
                    # Collect task URLs
                    task_urls = result.get("task_urls", {})
                    for platform, url in task_urls.items():
                        if platform not in results["task_urls"]:
                            results["task_urls"][platform] = []
                        results["task_urls"][platform].append(url)
                    
                    logger.info(f"Task {i+1} created successfully: {integration_task['title']}")
                else:
                    error_msg = f"Task {i+1} creation failed: {result.get('error', 'Unknown error')}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
                
            except Exception as e:
                error_msg = f"Task {i+1} processing failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Determine failed integrations (platforms that were attempted but failed)
        attempted_platforms = self.config.get("platforms", ["notion", "slack", "clickup"])
        results["failed_integrations"] = [
            platform for platform in attempted_platforms 
            if platform not in results["successful_integrations"]
        ]
        
        logger.info(f"Integration complete: {results['tasks_created']}/{results['tasks_processed']} tasks created")
        return results
    
    async def send_meeting_summary_notification(self, meeting_summary: str, 
                                              tasks_created: int = 0,
                                              meeting_context: Optional[Dict] = None) -> Dict:
        """
        Send meeting summary notification to configured channels.
        
        Args:
            meeting_summary: AI-generated meeting summary
            tasks_created: Number of tasks created from the meeting
            meeting_context: Optional meeting context
            
        Returns:
            Dict with notification results
        """
        if not self.enabled:
            return {
                "notification_sent": False,
                "reason": "Integration system disabled"
            }
        
        try:
            # TODO: Implement meeting summary notification
            # This would use the Slack integration to send a summary
            # For now, just log the summary
            logger.info(f"Meeting summary ready for notification: {meeting_summary[:100]}...")
            logger.info(f"Tasks created: {tasks_created}")
            
            return {
                "notification_sent": True,
                "summary_length": len(meeting_summary),
                "tasks_mentioned": tasks_created
            }
            
        except Exception as e:
            logger.error(f"Failed to send meeting summary notification: {e}")
            return {
                "notification_sent": False,
                "error": str(e)
            }

# Factory function for easy integration
def create_integration_bridge(config: Optional[Dict] = None) -> AIProcessingIntegrationBridge:
    """
    Factory function to create an integration bridge instance.
    
    Args:
        config: Optional configuration dict
        
    Returns:
        AIProcessingIntegrationBridge instance
    """
    return AIProcessingIntegrationBridge(config)

# Default configuration for AI processing
DEFAULT_INTEGRATION_CONFIG = {
    "enabled": True,
    "platforms": ["notion", "slack", "clickup"],
    "mock_mode": False,
    "timeout_seconds": 30
}