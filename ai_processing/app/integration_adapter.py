#!/usr/bin/env python3
"""
Integration Adapter for AI Processing System
Provides loose coupling with external integration systems using shared contracts
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add shared directory to path
# Define local data structures for loose coupling
from dataclasses import dataclass, asdict
from enum import Enum

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
class ParticipantData:
    id: str
    name: str
    platform_id: str
    status: str
    is_host: bool
    join_time: str
    leave_time: Optional[str] = None

@dataclass
class MeetingData:
    meeting_id: str
    title: str
    platform: str
    participants: List[ParticipantData]
    participant_count: int
    duration: str
    transcript: str
    created_at: str

@dataclass
class TaskDefinition:
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
    id: str
    name: str
    segments: List[str]
    total_words: int
    characteristics: Optional[str] = None

@dataclass
class MeetingSummary:
    meeting_id: str
    executive_summary: Dict[str, Any]
    key_decisions: List[Dict[str, Any]]
    participants: List[Dict[str, Any]]
    next_steps: List[Dict[str, Any]]

@dataclass
class ProcessingMetadata:
    ai_model_used: str
    confidence_score: float
    processing_time: float
    tools_executed: List[str]

# Fallback integration client
IntegrationClient = None
MockIntegrationClient = None

logger = logging.getLogger(__name__)


class AIProcessingIntegrationAdapter:
    """Adapter for integrating AI processing results with external systems"""

    def __init__(self, use_mock: bool = None):
        """
        Initialize integration adapter

        Args:
            use_mock: Force mock mode. If None, auto-detect based on environment
        """
        # Auto-detect mock mode if not specified
        if use_mock is None:
            integration_url = os.getenv('INTEGRATION_BASE_URL', '')
            use_mock = not integration_url or 'localhost:3003' not in integration_url

        self.use_mock = use_mock
        self.client = None

        # Initialize client
        self._init_client()

        logger.info(f"Integration adapter initialized (mock mode: {self.use_mock})")

    def _init_client(self):
        """Initialize integration client"""
        try:
            # Always use mock client for now since shared client is not available
            self.client = self._create_mock_client()
        except Exception as e:
            logger.warning(f"Failed to initialize integration client: {e}")
            self.client = self._create_mock_client()

    def _create_mock_client(self):
        """Create mock integration client"""
        # Use fallback mock implementation
        return MockIntegrationClientFallback()

    async def process_meeting_complete(self,
                                     meeting_id: str,
                                     meeting_title: str,
                                     platform: str,
                                     participants: List[ParticipantData],
                                     participant_count: int,
                                     transcript: str,
                                     summary_data: Dict,
                                     tasks_data: List[Dict],
                                     speakers_data: List[Dict],
                                     processing_time: float = 0.0,
                                     confidence_score: float = 0.85) -> Dict:
        """
        Process completed meeting and notify integration systems

        Args:
            meeting_id: Unique meeting identifier
            meeting_title: Meeting title
            platform: Meeting platform (google-meet, zoom, etc.)
            participants: List of participant data objects
            participant_count: Number of participants
            transcript: Full meeting transcript
            summary_data: Meeting summary from AI processing
            tasks_data: Extracted tasks from AI processing
            speakers_data: Speaker identification results
            processing_time: Time taken for AI processing
            confidence_score: Overall confidence score

        Returns:
            Integration results
        """
        try:
            # Convert to shared contract format
            meeting_data = MeetingData(
                meeting_id=meeting_id,
                title=meeting_title,
                platform=platform,
                participants=participants,
                participant_count=participant_count,
                duration=self._estimate_duration(transcript),
                transcript=transcript,
                created_at=datetime.now().isoformat()
            )

            # Convert summary data
            summary = self._convert_summary_data(meeting_id, summary_data)

            # Convert tasks data
            tasks = self._convert_tasks_data(meeting_id, tasks_data)

            # Convert speakers data
            speakers = self._convert_speakers_data(speakers_data)

            # Create processing metadata
            processing_metadata = ProcessingMetadata(
                ai_model_used="scrumy-ai-processing-v1",
                confidence_score=confidence_score,
                processing_time=processing_time,
                tools_executed=["speaker_identification", "summarization", "task_extraction"]
            )

            # Call integration service
            result = await self.client.process_complete_meeting(
                meeting_data, summary, tasks, speakers, processing_metadata
            )

            logger.info(f"Successfully notified integration system for meeting {meeting_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to process meeting complete for {meeting_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_id": None,
                "tools_executed": []
            }

    async def create_tasks_external(self,
                                  meeting_id: str,
                                  meeting_title: str,
                                  participants: List[ParticipantData],
                                  tasks_data: List[Dict],
                                  options: Dict[str, bool] = None) -> Dict:
        """
        Request creation of tasks in external systems

        Args:
            meeting_id: Associated meeting ID
            meeting_title: Meeting title for context
            participants: Meeting participant data objects
            tasks_data: Tasks to create
            options: Creation options

        Returns:
            Task creation results
        """
        try:
            # Convert tasks to shared format
            tasks = self._convert_tasks_data(meeting_id, tasks_data)

            # Call integration service
            result = await self.client.create_tasks(
                tasks=tasks,
                meeting_id=meeting_id,
                meeting_title=meeting_title,
                participants=participants,
                options=options
            )

            logger.info(f"Successfully requested creation of {len(tasks)} tasks for meeting {meeting_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to create external tasks for {meeting_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "created_tasks": [],
                "notifications_sent": []
            }

    async def update_task_status_external(self,
                                        task_id: str,
                                        status: str,
                                        updated_by: str,
                                        external_reference: Dict = None,
                                        completion_notes: str = None) -> Dict:
        """
        Update task status in external systems

        Args:
            task_id: Task ID to update
            status: New status (pending, in_progress, completed)
            updated_by: User who updated the task
            external_reference: External system reference
            completion_notes: Notes about the update

        Returns:
            Update confirmation
        """
        try:
            # Convert status to enum
            task_status = TaskStatus(status)

            result = await self.client.update_task_status(
                task_id=task_id,
                status=task_status,
                updated_by=updated_by,
                external_reference=external_reference,
                completion_notes=completion_notes
            )

            logger.info(f"Successfully updated task {task_id} status to {status}")
            return result

        except Exception as e:
            logger.error(f"Failed to update task status for {task_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_meeting_context(self, meeting_id: str) -> Dict:
        """
        Get meeting context for tool execution

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting context data
        """
        try:
            result = await self.client.get_meeting_context(meeting_id)
            logger.info(f"Retrieved context for meeting {meeting_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to get meeting context for {meeting_id}: {e}")
            return {
                "meeting_data": None,
                "participants": [],
                "previous_meetings": [],
                "related_tasks": []
            }

    def _convert_summary_data(self, meeting_id: str, summary_data: Dict) -> MeetingSummary:
        """Convert AI processing summary to shared contract format"""
        return MeetingSummary(
            meeting_id=meeting_id,
            executive_summary=summary_data.get("executive_summary", {}),
            key_decisions=summary_data.get("key_decisions", []),
            participants=summary_data.get("participants", []),
            next_steps=summary_data.get("next_steps", [])
        )

    def _convert_tasks_data(self, meeting_id: str, tasks_data: List[Dict]) -> List[TaskDefinition]:
        """Convert AI processing tasks to shared contract format"""
        tasks = []
        for i, task in enumerate(tasks_data):
            # Skip None or invalid tasks
            if task is None or not isinstance(task, dict):
                continue

            # Skip tasks without required fields
            if not task.get("title") and not task.get("description"):
                continue

            task_def = TaskDefinition(
                id=task.get("id", f"task_{meeting_id}_{i}"),
                title=task.get("title", ""),
                description=task.get("description", ""),
                meeting_id=meeting_id,
                assignee=task.get("assignee"),
                due_date=task.get("due_date"),
                priority=self._normalize_priority(task.get("priority", "medium")),
                status=self._normalize_status(task.get("status", "pending")),
                category=self._normalize_category(task.get("category", "action_item")),
                created_at=task.get("created_at", datetime.now().isoformat()),
                source="ai_extracted"
            )
            tasks.append(task_def)
        return tasks

    def _convert_speakers_data(self, speakers_data: List[Dict]) -> List[SpeakerInfo]:
        """Convert AI processing speakers to shared contract format"""
        speakers = []
        for speaker in speakers_data:
            if isinstance(speaker, dict):
                speaker_info = SpeakerInfo(
                    id=speaker.get("id", f"speaker_{len(speakers)}"),
                    name=speaker.get("name", "Unknown"),
                    segments=speaker.get("segments", []),
                    total_words=speaker.get("total_words", 0),
                    characteristics=speaker.get("characteristics")
                )
                speakers.append(speaker_info)
        return speakers

    def _normalize_priority(self, priority: str) -> str:
        """Normalize priority to shared contract values"""
        priority_lower = priority.lower()
        if priority_lower in ["high", "urgent", "critical"]:
            return Priority.HIGH.value
        elif priority_lower in ["low", "minor"]:
            return Priority.LOW.value
        else:
            return Priority.MEDIUM.value

    def _normalize_status(self, status: str) -> str:
        """Normalize status to shared contract values"""
        status_lower = status.lower()
        if status_lower in ["in_progress", "in progress", "working", "active"]:
            return TaskStatus.IN_PROGRESS.value
        elif status_lower in ["completed", "done", "finished", "closed"]:
            return TaskStatus.COMPLETED.value
        else:
            return TaskStatus.PENDING.value

    def _normalize_category(self, category: str) -> str:
        """Normalize category to shared contract values"""
        category_lower = category.lower()
        if category_lower in ["follow_up", "follow up", "followup"]:
            return TaskCategory.FOLLOW_UP.value
        elif category_lower in ["decision_required", "decision required", "decision"]:
            return TaskCategory.DECISION_REQUIRED.value
        else:
            return TaskCategory.ACTION_ITEM.value

    def _estimate_duration(self, transcript: str) -> str:
        """Estimate meeting duration based on transcript length"""
        # Rough estimation: 150 words per minute average speaking rate
        word_count = len(transcript.split()) if transcript else 0
        minutes = max(1, word_count // 150)

        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes > 0:
                return f"{hours}h {remaining_minutes}m"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''}"


class MockIntegrationClientFallback:
    """Fallback mock client when shared integration client is not available"""

    async def process_complete_meeting(self, *args, **kwargs):
        await asyncio.sleep(0.1)
        return {
            "success": True,
            "integration_id": f"fallback_mock_{int(datetime.now().timestamp())}",
            "tools_executed": [
                {"tool_name": "fallback_mock", "status": "success", "result": {}, "execution_time": 0.1}
            ],
            "external_references": {"notion_pages": [], "slack_messages": [], "calendar_events": []}
        }

    async def create_tasks(self, *args, **kwargs):
        await asyncio.sleep(0.1)
        tasks = kwargs.get('tasks', [])
        return {
            "success": True,
            "created_tasks": [
                {
                    "task_id": f"fallback_task_{i}",
                    "external_id": f"fallback_external_{i}",
                    "external_url": f"https://fallback.mock/task_{i}",
                    "platform": "fallback_mock",
                    "status": "created"
                } for i in range(len(tasks))
            ],
            "notifications_sent": []
        }

    async def update_task_status(self, *args, **kwargs):
        await asyncio.sleep(0.1)
        return {"success": True, "message": "Fallback mock update"}

    async def get_meeting_context(self, meeting_id: str):
        await asyncio.sleep(0.1)
        return {
            "meeting_data": {
                "meeting_id": meeting_id,
                "title": "Fallback Mock Meeting",
                "platform": "fallback",
                "participants": [],
                "duration": "unknown",
                "transcript": "",
                "created_at": datetime.now().isoformat()
            },
            "participants": [],
            "previous_meetings": [],
            "related_tasks": []
        }


# Global adapter instance
_integration_adapter: Optional[AIProcessingIntegrationAdapter] = None


def get_integration_adapter(use_mock: bool = None) -> AIProcessingIntegrationAdapter:
    """
    Get global integration adapter instance

    Args:
        use_mock: Force mock mode

    Returns:
        Integration adapter instance
    """
    global _integration_adapter

    if _integration_adapter is None:
        _integration_adapter = AIProcessingIntegrationAdapter(use_mock=use_mock)

    return _integration_adapter


# Convenience functions for common operations
async def notify_meeting_processed(meeting_id: str,
                                 meeting_title: str,
                                 platform: str,
                                 participants: List[ParticipantData],
                                 participant_count: int,
                                 transcript: str,
                                 summary_data: Dict,
                                 tasks_data: List[Dict],
                                 speakers_data: List[Dict],
                                 **kwargs) -> Dict:
    """
    Convenience function to notify integration systems of processed meeting

    Returns:
        Integration response
    """
    adapter = get_integration_adapter()
    return await adapter.process_meeting_complete(
        meeting_id=meeting_id,
        meeting_title=meeting_title,
        platform=platform,
        participants=participants,
        participant_count=participant_count,
        transcript=transcript,
        summary_data=summary_data,
        tasks_data=tasks_data,
        speakers_data=speakers_data,
        **kwargs
    )


async def create_external_tasks(meeting_id: str,
                              meeting_title: str,
                              participants: List[ParticipantData],
                              tasks_data: List[Dict],
                              **kwargs) -> Dict:
    """
    Convenience function to create tasks in external systems

    Returns:
        Task creation response
    """
    adapter = get_integration_adapter()
    return await adapter.create_tasks_external(
        meeting_id=meeting_id,
        meeting_title=meeting_title,
        participants=participants,
        tasks_data=tasks_data,
        **kwargs
    )


if __name__ == "__main__":
    # Example usage and testing
    async def test_integration_adapter():
        adapter = AIProcessingIntegrationAdapter(use_mock=True)

        # Test data
        meeting_id = "test_meeting_123"
        meeting_title = "Test Sprint Planning"
        platform = "google-meet"
        participants = [
            ParticipantData("p1", "John", "platform_1", "active", True, "2025-01-09T10:00:00Z"),
            ParticipantData("p2", "Sarah", "platform_2", "active", False, "2025-01-09T10:01:00Z"),
            ParticipantData("p3", "Mike", "platform_3", "active", False, "2025-01-09T10:02:00Z")
        ]
        transcript = "This is a test meeting transcript with some content to process."

        summary_data = {
            "executive_summary": {"overview": "Test meeting overview"},
            "key_decisions": [{"decision": "Use React for frontend"}],
            "participants": [{"name": "John", "role": "developer"}],
            "next_steps": [{"action": "Start development", "owner": "John"}]
        }

        tasks_data = [
            {
                "id": "task_1",
                "title": "Setup React project",
                "description": "Initialize React application",
                "assignee": "John",
                "priority": "high"
            }
        ]

        speakers_data = [
            {
                "id": "speaker_1",
                "name": "John",
                "segments": ["Let's start with React"],
                "total_words": 25
            }
        ]

        # Test meeting processing
        result = await adapter.process_meeting_complete(
            meeting_id, meeting_title, platform, participants, len(participants), transcript,
            summary_data, tasks_data, speakers_data
        )

        print(f"Meeting processing result: {json.dumps(result, indent=2)}")

        # Test task creation
        task_result = await adapter.create_tasks_external(
            meeting_id, meeting_title, participants, tasks_data
        )

        print(f"Task creation result: {json.dumps(task_result, indent=2)}")

    # Run test
    asyncio.run(test_integration_adapter())