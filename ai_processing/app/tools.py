"""
Tools abstraction layer for ScrumBot AI agent
Provides structured tool calling without full MCP complexity
"""

from typing import Dict, List, Any, Callable
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry of available tools that the AI agent can call"""
    
    def __init__(self):
        self.tools = {}
    
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
            return {"error": f"Tool {tool_name} not found"}
        
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
            return {"error": str(e)}
    
    def list_tools(self) -> List[str]:
        """Get list of registered tool names"""
        return list(self.tools.keys())

# Global tool registry
tools = ToolRegistry()