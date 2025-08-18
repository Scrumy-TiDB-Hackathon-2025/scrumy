"""
Tools abstraction layer for ScrumBot AI agent
Provides structured tool calling without full MCP complexity
"""

from typing import Dict, List, Any, Callable
import json
import asyncio
import logging
try:
    from .integrations import integration_manager
except ImportError:
    from integrations import integration_manager

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry of available tools that the AI agent can call"""
    
    def __init__(self):
        self.tools = {}
        self.integration_manager = integration_manager
    
    def register_tool(self, name: str, description: str, parameters: Dict, function: Callable):
        """Register a tool that the agent can call"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "function": function
        }
        logger.info(f"Registered tool: {name}")
    
    def get_tools_schema(self) -> List[Dict]:
        """Get OpenAI-compatible tools schema for the agent"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for tool in self.tools.values()
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute a tool call from the agent"""
        if tool_name not in self.tools:
            logger.error(f"Tool {tool_name} not found. Available tools: {list(self.tools.keys())}")
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        try:
            tool = self.tools[tool_name]
            logger.info(f"Calling tool: {tool_name} with args: {arguments}")
            
            # Call the tool function
            if asyncio.iscoroutinefunction(tool["function"]):
                result = await tool["function"](**arguments)
            else:
                result = tool["function"](**arguments)
                
            logger.info(f"Tool {tool_name} completed successfully")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_tools(self) -> List[str]:
        """Get list of registered tool names"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict:
        """Get detailed information about a specific tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}
        
        tool = self.tools[tool_name]
        return {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
            "available": True
        }
    
    async def create_task_everywhere(self, title: str, description: str, assignee: str = None,
                                   priority: str = "medium", due_date: str = None,
                                   meeting_id: str = None) -> Dict:
        """Universal tool to create tasks in all available integrations with enhanced error handling"""
        # Validate inputs
        if not title:
            return {"task_created": False, "error": "Title is required"}
        
        if priority not in ["low", "medium", "high", "urgent"]:
            priority = "medium"  # Default to medium for invalid priorities
        
        task_data = {
            "title": title,
            "description": description or "",
            "assignee": assignee,
            "priority": priority,
            "due_date": due_date,
            "meeting_id": meeting_id
        }
        
        logger.info(f"Creating task everywhere: {title} (priority: {priority})")
        result = await self.integration_manager.create_task_all(task_data, max_retries=2)
        
        # Enhanced response with detailed information
        response = {
            "task_created": result["success"],
            "integrations_used": result["integrations_used"],
            "successful_integrations": result["successful_integrations"],
            "total_integrations": result["total_integrations"],
            "results": result["results"],
            "title": title,
            "assignee": assignee,
            "priority": priority
        }
        
        # Add specific integration URLs if available
        urls = {}
        for integration_name, integration_result in result["results"].items():
            if integration_result.get("success"):
                if integration_name == "notion" and integration_result.get("notion_url"):
                    urls["notion"] = integration_result["notion_url"]
                elif integration_name == "clickup" and integration_result.get("clickup_url"):
                    urls["clickup"] = integration_result["clickup_url"]
                elif integration_name == "slack" and integration_result.get("permalink"):
                    urls["slack"] = integration_result["permalink"]
        
        if urls:
            response["task_urls"] = urls
        
        return response

# Global tool registry
tools = ToolRegistry()

# Register the universal task creation tool
tools.register_tool(
    name="create_task_everywhere",
    description="Create a task in all available project management tools (Notion, ClickUp, etc.)",
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
                "enum": ["low", "medium", "high", "urgent"],
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
    function=tools.create_task_everywhere
)