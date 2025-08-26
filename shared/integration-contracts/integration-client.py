#!/usr/bin/env python3
"""
Shared Integration Client for Scrumy AI Processing System
Provides loose coupling between AI processing and integration modules
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import os


# Configure logging
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskCategory(Enum):
    ACTION_ITEM = "action_item"
    FOLLOW_UP = "follow_up"
    DECISION_REQUIRED = "decision_required"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Participant:
    """Participant data structure following shared contract"""
    id: str
    name: str
    platform_id: str
    status: str
    is_host: bool
    join_time: str

@dataclass
class MeetingData:
    """Meeting data structure following shared contract"""
    meeting_id: str
    title: str
    platform: str
    participants: List[str]  # For backward compatibility
    participants_detailed: List[Participant]  # Enhanced participant data
    duration: str
    transcript: str
    created_at: str


@dataclass
class TaskDefinition:
    """Task definition following shared contract"""
    id: str
    title: str
    description: str
    meeting_id: str
    created_at: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = Priority.MEDIUM.value
    status: str = TaskStatus.PENDING.value
    category: str = TaskCategory.ACTION_ITEM.value
    source: str = "ai_extracted"


@dataclass
class SpeakerInfo:
    """Speaker information structure"""
    id: str
    name: str
    segments: List[str]
    total_words: int
    characteristics: Optional[str] = None


@dataclass
class ProcessingMetadata:
    """AI processing metadata"""
    ai_model_used: str
    confidence_score: float
    processing_time: float
    tools_executed: List[str]


@dataclass
class MeetingSummary:
    """Meeting summary structure"""
    meeting_id: str
    executive_summary: Dict[str, Any]
    key_decisions: List[Dict[str, Any]]
    participants: List[Dict[str, Any]]
    next_steps: List[Dict[str, Any]]


class IntegrationError(Exception):
    """Custom exception for integration errors"""
    def __init__(self, message: str, error_code: str = "INTEGRATION_ERROR", details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class IntegrationClient:
    """Base integration client for communication between AI processing and integration modules"""

    def __init__(self,
                 base_url: str = None,
                 api_key: str = None,
                 timeout: float = 30.0,
                 max_retries: int = 3):
        """
        Initialize integration client

        Args:
            base_url: Base URL for the integration service
            api_key: API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or os.getenv('INTEGRATION_BASE_URL', 'http://localhost:3003')
        self.api_key = api_key or os.getenv('INTEGRATION_API_KEY')
        self.timeout = timeout
        self.max_retries = max_retries

        # Remove trailing slash
        self.base_url = self.base_url.rstrip('/')

        # Set up headers
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Scrumy-AI-Processing/1.0'
        }

        if self.api_key:
            self.headers['Authorization'] = f'Bearer {self.api_key}'

    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """
        Make HTTP request with retry logic and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload

        Returns:
            Response data as dictionary

        Raises:
            IntegrationError: On request failure
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == 'GET':
                        response = await client.get(url, headers=self.headers)
                    elif method.upper() == 'POST':
                        response = await client.post(url, headers=self.headers, json=data)
                    elif method.upper() == 'PATCH':
                        response = await client.patch(url, headers=self.headers, json=data)
                    elif method.upper() == 'PUT':
                        response = await client.put(url, headers=self.headers, json=data)
                    elif method.upper() == 'DELETE':
                        response = await client.delete(url, headers=self.headers)
                    else:
                        raise IntegrationError(f"Unsupported HTTP method: {method}")

                    # Handle response
                    if response.status_code >= 200 and response.status_code < 300:
                        try:
                            return response.json()
                        except json.JSONDecodeError:
                            return {"success": True, "message": "Request completed"}

                    # Handle error responses
                    try:
                        error_data = response.json()
                        error_message = error_data.get('message', f'HTTP {response.status_code}')
                        error_code = error_data.get('error_code', 'HTTP_ERROR')
                    except json.JSONDecodeError:
                        error_message = f'HTTP {response.status_code}: {response.text}'
                        error_code = 'HTTP_ERROR'

                    if attempt == self.max_retries:
                        raise IntegrationError(error_message, error_code)

                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {error_message}")
                    await asyncio.sleep(wait_time)

            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    raise IntegrationError("Request timeout", "TIMEOUT_ERROR")
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                if attempt == self.max_retries:
                    raise IntegrationError(f"Request failed: {str(e)}", "REQUEST_ERROR")
                await asyncio.sleep(2 ** attempt)

    async def process_complete_meeting(self,
                                     meeting_data: MeetingData,
                                     summary: MeetingSummary,
                                     tasks: List[TaskDefinition],
                                     speakers: List[SpeakerInfo],
                                     processing_metadata: ProcessingMetadata) -> Dict:
        """
        Notify integration system that meeting processing is complete

        Args:
            meeting_data: Meeting information
            summary: Meeting summary
            tasks: Extracted tasks
            speakers: Identified speakers
            processing_metadata: Processing metadata

        Returns:
            Integration response with tool execution results
        """
        payload = {
            "meeting_data": asdict(meeting_data),
            "summary": asdict(summary),
            "tasks": [asdict(task) for task in tasks],
            "speakers": [asdict(speaker) for speaker in speakers],
            "processing_metadata": asdict(processing_metadata)
        }

        logger.info(f"Notifying integration system of completed meeting: {meeting_data.meeting_id}")
        return await self._make_request('POST', '/integration/process-complete-meeting', payload)

    async def create_tasks(self,
                          tasks: List[TaskDefinition],
                          meeting_id: str,
                          meeting_title: str,
                          participants: List[str],
                          options: Dict[str, bool] = None) -> Dict:
        """
        Request creation of tasks in external systems

        Args:
            tasks: List of tasks to create
            meeting_id: Associated meeting ID
            meeting_title: Meeting title for context
            participants: Meeting participants
            options: Creation options (create_notion_tasks, send_slack_notifications, etc.)

        Returns:
            Task creation results
        """
        default_options = {
            "create_notion_tasks": True,
            "send_slack_notifications": True,
            "create_calendar_events": False,
            "notify_assignees": True
        }

        creation_options = {**default_options, **(options or {})}

        payload = {
            "tasks": [asdict(task) for task in tasks],
            "meeting_context": {
                "meeting_id": meeting_id,
                "meeting_title": meeting_title,
                "participants": participants
            },
            "creation_options": creation_options
        }

        logger.info(f"Requesting creation of {len(tasks)} tasks for meeting: {meeting_id}")
        return await self._make_request('POST', '/integration/create-tasks', payload)

    async def update_task_status(self,
                               task_id: str,
                               status: TaskStatus,
                               updated_by: str,
                               external_reference: Dict = None,
                               completion_notes: str = None) -> Dict:
        """
        Update task status from external systems

        Args:
            task_id: Task ID to update
            status: New task status
            updated_by: User who updated the task
            external_reference: External system reference
            completion_notes: Notes about completion

        Returns:
            Update confirmation
        """
        payload = {
            "status": status.value,
            "updated_by": updated_by,
            "completion_notes": completion_notes
        }

        if external_reference:
            payload["external_reference"] = external_reference

        logger.info(f"Updating task {task_id} status to {status.value}")
        return await self._make_request('PATCH', f'/ai-processing/tasks/{task_id}/status', payload)

    async def get_meeting_context(self, meeting_id: str) -> Dict:
        """
        Get meeting context for tool execution

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting context data
        """
        logger.info(f"Retrieving context for meeting: {meeting_id}")
        return await self._make_request('GET', f'/ai-processing/meetings/{meeting_id}/context')

    async def register_tool(self,
                           tool_name: str,
                           description: str,
                           version: str,
                           endpoint: str,
                           capabilities: Dict[str, bool],
                           authentication: Dict = None,
                           input_schema: Dict = None,
                           output_schema: Dict = None) -> Dict:
        """
        Register a tool with the AI processing system

        Args:
            tool_name: Unique tool name
            description: Tool description
            version: Tool version
            endpoint: Tool execution endpoint
            capabilities: Tool capabilities
            authentication: Authentication requirements
            input_schema: Input validation schema
            output_schema: Output format schema

        Returns:
            Registration confirmation
        """
        payload = {
            "tool_name": tool_name,
            "description": description,
            "version": version,
            "endpoint": endpoint,
            "capabilities": capabilities
        }

        if authentication:
            payload["authentication"] = authentication
        if input_schema:
            payload["input_schema"] = input_schema
        if output_schema:
            payload["output_schema"] = output_schema

        logger.info(f"Registering tool: {tool_name}")
        return await self._make_request('POST', '/ai-processing/tools/register', payload)

    async def execute_tool(self,
                          tool_name: str,
                          action: str,
                          parameters: Dict,
                          context: Dict = None) -> Dict:
        """
        Execute a registered tool

        Args:
            tool_name: Tool to execute
            action: Action to perform
            parameters: Action parameters
            context: Execution context

        Returns:
            Tool execution results
        """
        payload = {
            "action": action,
            "parameters": parameters,
            "context": context or {}
        }

        logger.info(f"Executing tool: {tool_name} with action: {action}")
        return await self._make_request('POST', f'/integration/tools/{tool_name}/execute', payload)


class MockIntegrationClient(IntegrationClient):
    """Mock implementation for testing and development"""

    def __init__(self):
        # Don't call parent __init__ to avoid HTTP setup
        self.mock_data = {}

    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Mock HTTP request implementation"""
        await asyncio.sleep(0.1)  # Simulate network delay

        # Mock responses based on endpoint
        if endpoint == '/integration/process-complete-meeting':
            return {
                "success": True,
                "integration_id": f"mock_{int(time.time())}",
                "tools_executed": [
                    {
                        "tool_name": "notion_integration",
                        "status": "success",
                        "result": {"page_id": "mock_page_123"},
                        "execution_time": 0.5
                    },
                    {
                        "tool_name": "slack_integration",
                        "status": "success",
                        "result": {"message_ts": "1234567890.123"},
                        "execution_time": 0.3
                    }
                ],
                "external_references": {
                    "notion_pages": ["mock_page_123"],
                    "slack_messages": ["C1234567890:1234567890.123"],
                    "calendar_events": []
                }
            }

        elif endpoint == '/integration/create-tasks':
            task_count = len(data.get("tasks", [])) if data else 1
            return {
                "success": True,
                "created_tasks": [
                    {
                        "task_id": f"task_{i}",
                        "external_id": f"notion_page_{i}",
                        "external_url": f"https://notion.so/page_{i}",
                        "platform": "notion",
                        "status": "created"
                    } for i in range(task_count)
                ],
                "notifications_sent": [
                    {
                        "recipient": "john@example.com",
                        "method": "slack",
                        "status": "sent"
                    }
                ]
            }

        elif endpoint.startswith('/ai-processing/tasks/') and '/status' in endpoint:
            return {"success": True, "message": "Task status updated"}

        elif endpoint.startswith('/ai-processing/meetings/') and '/context' in endpoint:
            return {
                "meeting_data": {
                    "meeting_id": "mock_meeting_123",
                    "title": "Mock Meeting",
                    "platform": "google-meet",
                    "participants": ["John", "Sarah"],
                    "participants_detailed": [
                        {
                            "id": "participant_1",
                            "name": "John",
                            "platform_id": "google_meet_user_123",
                            "status": "active",
                            "is_host": True,
                            "join_time": datetime.now().isoformat()
                        },
                        {
                            "id": "participant_2",
                            "name": "Sarah",
                            "platform_id": "google_meet_user_456",
                            "status": "active",
                            "is_host": False,
                            "join_time": datetime.now().isoformat()
                        }
                    ],
                    "duration": "30 minutes",
                    "transcript": "Mock meeting transcript",
                    "created_at": datetime.now().isoformat()
                },
                "participants": [
                    {"name": "John", "email": "john@example.com", "role": "developer"},
                    {"name": "Sarah", "email": "sarah@example.com", "role": "designer"}
                ],
                "previous_meetings": [],
                "related_tasks": []
            }

        elif endpoint == '/ai-processing/tools/register':
            return {
                "success": True,
                "tool_id": f"tool_{int(time.time())}",
                "message": "Tool registered successfully"
            }

        elif endpoint.startswith('/integration/tools/') and '/execute' in endpoint:
            return {
                "success": True,
                "result": {"mock": "result"},
                "execution_time": 0.2,
                "external_references": [
                    {"type": "url", "value": "https://mock.service/result", "platform": "mock"}
                ]
            }

        else:
            return {"success": True, "message": "Mock response"}


# Factory function for creating clients
def create_integration_client(mock: bool = False, **kwargs) -> Union[IntegrationClient, MockIntegrationClient]:
    """
    Factory function to create integration client

    Args:
        mock: Whether to use mock implementation
        **kwargs: Additional arguments for IntegrationClient

    Returns:
        Integration client instance
    """
    if mock:
        return MockIntegrationClient()
    else:
        return IntegrationClient(**kwargs)


# Convenience functions for common operations
async def notify_meeting_complete(meeting_id: str,
                                summary_data: Dict,
                                tasks_data: List[Dict],
                                speakers_data: List[Dict],
                                mock: bool = False) -> Dict:
    """
    Convenience function to notify integration system of completed meeting

    Args:
        meeting_id: Meeting ID
        summary_data: Meeting summary
        tasks_data: Extracted tasks
        speakers_data: Identified speakers
        mock: Use mock client for testing

    Returns:
        Integration response
    """
    client = create_integration_client(mock=mock)

    # Convert data to proper types
    # Extract participant names for backward compatibility
    participant_names = []
    participants_detailed = []

    if isinstance(speakers_data, list):
        # speakers_data is list of speaker objects
        for speaker in speakers_data:
            name = speaker.get("name", "Unknown")
            participant_names.append(name)
            participants_detailed.append(Participant(
                id=speaker.get("id", f"participant_{len(participants_detailed)}"),
                name=name,
                platform_id=speaker.get("platform_id", ""),
                status="active",
                is_host=speaker.get("is_host", False),
                join_time=speaker.get("join_time", datetime.now().isoformat())
            ))
    elif isinstance(speakers_data, dict) and "participants" in speakers_data:
        # speakers_data contains participants array
        for participant in speakers_data.get("participants", []):
            name = participant.get("name", "Unknown")
            participant_names.append(name)
            participants_detailed.append(Participant(
                id=participant.get("id", f"participant_{len(participants_detailed)}"),
                name=name,
                platform_id=participant.get("platform_id", ""),
                status=participant.get("status", "active"),
                is_host=participant.get("is_host", False),
                join_time=participant.get("join_time", datetime.now().isoformat())
            ))

    meeting_data = MeetingData(
        meeting_id=meeting_id,
        title=summary_data.get("meeting_title", "Meeting"),
        platform="unknown",
        participants=participant_names,
        participants_detailed=participants_detailed,
        duration="unknown",
        transcript=summary_data.get("transcript", ""),
        created_at=datetime.now().isoformat()
    )

    summary = MeetingSummary(
        meeting_id=meeting_id,
        executive_summary=summary_data.get("executive_summary", {}),
        key_decisions=summary_data.get("key_decisions", []),
        participants=summary_data.get("participants", []),
        next_steps=summary_data.get("next_steps", [])
    )

    tasks = [
        TaskDefinition(
            id=task.get("id", f"task_{i}"),
            title=task.get("title", ""),
            description=task.get("description", ""),
            meeting_id=meeting_id,
            assignee=task.get("assignee"),
            due_date=task.get("due_date"),
            priority=task.get("priority", Priority.MEDIUM.value),
            category=task.get("category", TaskCategory.ACTION_ITEM.value),
            created_at=datetime.now().isoformat()
        ) for i, task in enumerate(tasks_data)
    ]

    speakers = [
        SpeakerInfo(
            id=speaker.get("id", f"speaker_{i}"),
            name=speaker.get("name", "Unknown"),
            segments=speaker.get("segments", []),
            total_words=speaker.get("total_words", 0),
            characteristics=speaker.get("characteristics")
        ) for i, speaker in enumerate(speakers_data)
    ]

    processing_metadata = ProcessingMetadata(
        ai_model_used="scrumy-ai-v1",
        confidence_score=0.85,
        processing_time=1.5,
        tools_executed=["speaker_identification", "task_extraction", "summarization"]
    )

    return await client.process_complete_meeting(
        meeting_data, summary, tasks, speakers, processing_metadata
    )


if __name__ == "__main__":
    # Example usage
    async def example_usage():
        # Create client
        client = create_integration_client(mock=True)

        # Example meeting data
        # Example participants with detailed information
        participants_detailed = [
            Participant(
                id="participant_1",
                name="John",
                platform_id="google_meet_user_123",
                status="active",
                is_host=True,
                join_time=datetime.now().isoformat()
            ),
            Participant(
                id="participant_2",
                name="Sarah",
                platform_id="google_meet_user_456",
                status="active",
                is_host=False,
                join_time=datetime.now().isoformat()
            ),
            Participant(
                id="participant_3",
                name="Mike",
                platform_id="google_meet_user_789",
                status="active",
                is_host=False,
                join_time=datetime.now().isoformat()
            )
        ]

        meeting_data = MeetingData(
            meeting_id="example_meeting_123",
            title="Sprint Planning",
            platform="google-meet",
            participants=["John", "Sarah", "Mike"],
            participants_detailed=participants_detailed,
            duration="45 minutes",
            transcript="Example meeting transcript...",
            created_at=datetime.now().isoformat()
        )

        # Example summary
        summary = MeetingSummary(
            meeting_id="example_meeting_123",
            executive_summary={"overview": "Sprint planning session"},
            key_decisions=[{"decision": "Use React for frontend"}],
            participants=[{"name": "John", "role": "developer"}],
            next_steps=[{"action": "Start development", "owner": "John"}]
        )

        # Example tasks
        tasks = [
            TaskDefinition(
                id="task_1",
                title="Setup React project",
                description="Initialize React application with TypeScript",
                meeting_id="example_meeting_123",
                assignee="John",
                priority=Priority.HIGH.value,
                created_at=datetime.now().isoformat()
            )
        ]

        # Example speakers
        speakers = [
            SpeakerInfo(
                id="speaker_1",
                name="John",
                segments=["Let's use React for the frontend"],
                total_words=25
            )
        ]

        # Example metadata
        metadata = ProcessingMetadata(
            ai_model_used="scrumy-ai-v1",
            confidence_score=0.92,
            processing_time=2.1,
            tools_executed=["summarization", "task_extraction"]
        )

        # Process complete meeting
        result = await client.process_complete_meeting(
            meeting_data, summary, tasks, speakers, metadata
        )

        print(f"Integration result: {result}")

    # Run example
    asyncio.run(example_usage())
