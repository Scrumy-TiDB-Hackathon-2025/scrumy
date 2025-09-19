"""
AI Agent with tools integration for ScrumBot
Processes meeting transcripts and automatically calls tools
"""

try:
    from .tools import tools
except ImportError:
    from tools import tools
import json
import os
import logging
from typing import Dict, List
import aiohttp

logger = logging.getLogger(__name__)

class AIAgent:
    """AI Agent that can call tools based on meeting analysis"""
    
    def __init__(self):
        self.tools = tools
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        # Import tool modules to register them
        try:
            from . import notion_tools, slack_tools
        except ImportError:
            import notion_tools, slack_tools
    
    async def process_with_tools(self, transcript: str, meeting_id: str) -> Dict:
        """Process transcript and automatically call tools based on AI analysis"""
        
        try:
            # Get available tools for the AI
            available_tools = self.tools.get_tools_schema()
            
            # Create system prompt that explains available tools
            system_prompt = f"""
            You are ScrumBot, an AI meeting assistant. You can call tools to take actions.
            
            Available tools:
            - create_notion_task: Create tasks in Notion database
            - send_slack_notification: Send notifications to Slack
            
            Analyze the meeting transcript and:
            1. Extract action items and tasks from the discussion
            2. For each clear action item, create a task in Notion using create_notion_task
            3. Send a summary notification to Slack using send_slack_notification
            4. Include meeting_id in task creation for tracking
            
            Only create tasks for clear, actionable items with specific outcomes.
            Always call appropriate tools when you identify actionable items.
            """
            
            # Choose AI provider based on availability
            if self.groq_api_key:
                response = await self._call_groq_with_tools(transcript, system_prompt, available_tools, meeting_id)
            else:
                response = await self._call_ollama_with_tools(transcript, system_prompt, available_tools, meeting_id)
            
            # Process tool calls from AI response
            tool_results = []
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    try:
                        tool_name = tool_call["function"]["name"]
                        arguments = json.loads(tool_call["function"]["arguments"])
                        
                        # Add meeting_id to arguments if not present
                        if "meeting_id" not in arguments and meeting_id:
                            arguments["meeting_id"] = meeting_id
                        
                        # Execute the tool
                        result = await self.tools.call_tool(tool_name, arguments)
                        
                        # Enhanced logging for tool results
                        if result.get("success"):
                            tool_result = result.get("result", {})
                            if tool_result.get("task_created"):
                                logger.info(f"Successfully created task: {arguments.get('title', 'Unknown')}")
                                if tool_result.get("task_urls"):
                                    logger.info(f"Task URLs: {tool_result['task_urls']}")
                        else:
                            logger.warning(f"Tool {tool_name} failed: {result.get('error', 'Unknown error')}")
                        
                        tool_results.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Error processing tool call: {str(e)}")
                        tool_results.append({
                            "tool": tool_call.get("function", {}).get("name", "unknown"),
                            "error": str(e)
                        })
            
            return {
                "analysis": response.get("content", ""),
                "tool_calls": tool_results,
                "meeting_id": meeting_id,
                "tools_used": len(tool_results)
            }
            
        except Exception as e:
            logger.error(f"Error in process_with_tools: {str(e)}")
            return {
                "analysis": f"Error processing transcript: {str(e)}",
                "tool_calls": [],
                "meeting_id": meeting_id,
                "error": str(e)
            }
    
    async def _call_groq_with_tools(self, transcript: str, system_prompt: str, tools: List[Dict], meeting_id: str) -> Dict:
        """Call Groq API with function calling"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama3-groq-70b-8192-tool-use-preview",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this meeting transcript and take appropriate actions:\n\nMeeting ID: {meeting_id}\n\nTranscript:\n{transcript}"}
                ],
                "tools": tools,
                "tool_choice": "auto",
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        message = result["choices"][0]["message"]
                        
                        return {
                            "content": message.get("content", ""),
                            "tool_calls": message.get("tool_calls", [])
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Groq API error: {response.status} - {error_text}")
                        return {"error": f"Groq API error: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            return {"error": str(e)}
    
    async def _call_ollama_with_tools(self, transcript: str, system_prompt: str, tools: List[Dict], meeting_id: str) -> Dict:
        """Call Ollama with simulated function calling"""
        try:
            # Ollama doesn't have native function calling, so we simulate it
            prompt = f"""
            {system_prompt}
            
            Meeting ID: {meeting_id}
            Meeting transcript:
            {transcript}
            
            Based on this transcript, identify tasks and respond in this JSON format:
            {{
                "analysis": "Your analysis of the meeting and what actions you're taking",
                "tool_calls": [
                    {{
                        "function": {{
                            "name": "create_notion_task",
                            "arguments": "{{\\"title\\": \\"Task title\\", \\"description\\": \\"Task description\\", \\"assignee\\": \\"Person name\\", \\"priority\\": \\"high\\", \\"meeting_id\\": \\"{meeting_id}\\"}}"
                        }}
                    }},
                    {{
                        "function": {{
                            "name": "send_slack_notification", 
                            "arguments": "{{\\"message\\": \\"Meeting summary with X tasks created\\", \\"task_title\\": \\"Task title\\"}}"
                        }}
                    }}
                ]
            }}
            
            Only include tool_calls if you identify clear, actionable items.
            """
            
            payload = {
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # Try to parse JSON response
                        try:
                            parsed = json.loads(response_text)
                            return parsed
                        except json.JSONDecodeError:
                            # Fallback if JSON parsing fails
                            return {
                                "analysis": response_text,
                                "tool_calls": []
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return {"error": f"Ollama API error: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return {"error": str(e)}