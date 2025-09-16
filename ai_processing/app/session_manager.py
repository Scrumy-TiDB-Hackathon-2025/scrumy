"""
Meeting Session Manager for Phase 3: Session Management
Handles meeting session lifecycle, disconnections, and timeout-based processing
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class MeetingSession:
    """Data class for meeting session information"""
    session_id: str
    meeting_id: str
    start_time: float
    last_activity: float
    participants: List[str]
    transcript_segments: List[Dict]
    total_audio_duration: float
    is_active: bool
    reconnection_count: int
    processed_for_tasks: bool
    websocket_id: Optional[str] = None

class MeetingSessionManager:
    """
    Manages meeting sessions with timeout-based processing and reconnection handling

    Key Features:
    - Track active meeting sessions
    - Handle disconnections gracefully
    - 5-minute timeout automatic processing
    - Prevent duplicate task extraction
    - Session reconnection management
    """

    def __init__(self,
                 timeout_minutes: int = 5,
                 max_reconnections: int = 3,
                 cleanup_interval: int = 300):  # 5 minutes
        """
        Initialize session manager

        Args:
            timeout_minutes: Minutes to wait before processing disconnected meeting
            max_reconnections: Maximum reconnections allowed per session
            cleanup_interval: Seconds between cleanup cycles
        """
        self.timeout_seconds = timeout_minutes * 60
        self.max_reconnections = max_reconnections
        self.cleanup_interval = cleanup_interval

        # Session storage
        self.active_sessions: Dict[str, MeetingSession] = {}
        self.disconnected_sessions: Dict[str, MeetingSession] = {}
        self.processed_sessions: Set[str] = set()  # Track processed meeting_ids

        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.timeout_tasks: Dict[str, asyncio.Task] = {}

        # Statistics
        self.stats = {
            "sessions_created": 0,
            "sessions_processed_timeout": 0,
            "sessions_reconnected": 0,
            "duplicate_prevented": 0,
            "cleanup_cycles": 0
        }

        logger.info(f"Session manager initialized (timeout: {timeout_minutes}min, max_reconnections: {max_reconnections})")

    async def start(self):
        """Start the session manager background tasks"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session manager started with background cleanup")

    async def stop(self):
        """Stop the session manager and cleanup resources"""
        # Cancel all timeout tasks
        for task in self.timeout_tasks.values():
            if not task.done():
                task.cancel()

        # Cancel cleanup task
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()

        # Wait for tasks to complete
        pending_tasks = [task for task in self.timeout_tasks.values() if not task.done()]
        if self.cleanup_task and not self.cleanup_task.done():
            pending_tasks.append(self.cleanup_task)

        if pending_tasks:
            await asyncio.gather(*pending_tasks, return_exceptions=True)

        logger.info("Session manager stopped")

    async def register_session(self,
                             session_id: str,
                             meeting_id: str,
                             websocket_id: Optional[str] = None,
                             participants: Optional[List[str]] = None) -> Dict:
        """
        Register a new meeting session

        Args:
            session_id: Unique session identifier
            meeting_id: Meeting identifier (can be shared across reconnections)
            websocket_id: WebSocket connection identifier
            participants: List of meeting participants

        Returns:
            Dict with registration result
        """
        current_time = time.time()
        participants = participants or []

        # Check if meeting was already processed to prevent duplicates
        if meeting_id in self.processed_sessions:
            logger.warning(f"Meeting {meeting_id} already processed, preventing duplicate")
            self.stats["duplicate_prevented"] += 1
            return {
                "success": False,
                "reason": "duplicate_meeting",
                "message": f"Meeting {meeting_id} was already processed"
            }

        # Check if this is a reconnection (same meeting_id, different session_id)
        existing_session = None
        for session in list(self.active_sessions.values()) + list(self.disconnected_sessions.values()):
            if session.meeting_id == meeting_id:
                existing_session = session
                break

        if existing_session:
            return await self._handle_reconnection(session_id, existing_session, websocket_id)

        # Create new session
        session = MeetingSession(
            session_id=session_id,
            meeting_id=meeting_id,
            start_time=current_time,
            last_activity=current_time,
            participants=participants,
            transcript_segments=[],
            total_audio_duration=0.0,
            is_active=True,
            reconnection_count=0,
            processed_for_tasks=False,
            websocket_id=websocket_id
        )

        self.active_sessions[session_id] = session
        self.stats["sessions_created"] += 1

        logger.info(f"Registered new session: {session_id} for meeting: {meeting_id}")
        logger.info(f"Participants: {participants}")

        return {
            "success": True,
            "session_id": session_id,
            "meeting_id": meeting_id,
            "is_new_session": True,
            "reconnection_count": 0
        }

    async def handle_disconnect(self, session_id: str) -> Dict:
        """
        Handle session disconnection with timeout scheduling

        Args:
            session_id: Session to disconnect

        Returns:
            Dict with disconnect handling result
        """
        if session_id not in self.active_sessions:
            logger.warning(f"Disconnect request for unknown session: {session_id}")
            return {"success": False, "reason": "session_not_found"}

        session = self.active_sessions[session_id]
        session.is_active = False
        session.last_activity = time.time()

        # Move to disconnected sessions
        self.disconnected_sessions[session_id] = session
        del self.active_sessions[session_id]

        # Schedule timeout processing
        await self._schedule_timeout_processing(session)

        logger.info(f"Session {session_id} disconnected, scheduled for timeout processing in {self.timeout_seconds}s")

        return {
            "success": True,
            "session_id": session_id,
            "meeting_id": session.meeting_id,
            "timeout_scheduled": True,
            "timeout_seconds": self.timeout_seconds
        }

    async def handle_reconnection(self,
                                session_id: str,
                                meeting_id: str,
                                websocket_id: Optional[str] = None) -> Dict:
        """
        Handle session reconnection

        Args:
            session_id: New session identifier
            meeting_id: Meeting identifier to reconnect to
            websocket_id: New WebSocket connection identifier

        Returns:
            Dict with reconnection result
        """
        # Find existing session for this meeting
        existing_session = None
        existing_session_id = None

        # Check disconnected sessions first
        for sid, session in self.disconnected_sessions.items():
            if session.meeting_id == meeting_id:
                existing_session = session
                existing_session_id = sid
                break

        # Check active sessions
        if not existing_session:
            for sid, session in self.active_sessions.items():
                if session.meeting_id == meeting_id:
                    existing_session = session
                    existing_session_id = sid
                    break

        if not existing_session:
            logger.warning(f"Reconnection attempt for unknown meeting: {meeting_id}")
            return {"success": False, "reason": "meeting_not_found"}

        return await self._handle_reconnection(session_id, existing_session, websocket_id)

    async def update_session_activity(self,
                                    session_id: str,
                                    transcript_segment: Optional[Dict] = None,
                                    audio_duration: Optional[float] = None) -> bool:
        """
        Update session activity with new transcript or audio data

        Args:
            session_id: Session to update
            transcript_segment: New transcript segment
            audio_duration: Additional audio duration

        Returns:
            bool indicating success
        """
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Activity update for unknown session: {session_id}")
            return False

        session.last_activity = time.time()

        if transcript_segment:
            session.transcript_segments.append(transcript_segment)

        if audio_duration:
            session.total_audio_duration += audio_duration

        return True

    def should_process_tasks(self, meeting_id: str) -> bool:
        """
        Check if meeting should be processed for tasks

        Args:
            meeting_id: Meeting to check

        Returns:
            bool indicating if processing should occur
        """
        # Already processed
        if meeting_id in self.processed_sessions:
            return False

        # Find session for meeting
        for session in list(self.active_sessions.values()) + list(self.disconnected_sessions.values()):
            if session.meeting_id == meeting_id:
                return not session.processed_for_tasks

        return True

    async def _handle_reconnection(self,
                                 new_session_id: str,
                                 existing_session: MeetingSession,
                                 websocket_id: Optional[str] = None) -> Dict:
        """Handle reconnection to existing meeting session"""

        # Check reconnection limit
        if existing_session.reconnection_count >= self.max_reconnections:
            logger.warning(f"Max reconnections exceeded for meeting {existing_session.meeting_id}")
            return {
                "success": False,
                "reason": "max_reconnections_exceeded",
                "max_reconnections": self.max_reconnections
            }

        # Cancel existing timeout if session was disconnected
        old_session_id = existing_session.session_id
        if old_session_id in self.timeout_tasks:
            self.timeout_tasks[old_session_id].cancel()
            del self.timeout_tasks[old_session_id]
            logger.info(f"Cancelled timeout processing for reconnected session")

        # Update session for reconnection
        existing_session.session_id = new_session_id
        existing_session.websocket_id = websocket_id
        existing_session.is_active = True
        existing_session.last_activity = time.time()
        existing_session.reconnection_count += 1

        # Move back to active sessions if it was disconnected
        if old_session_id in self.disconnected_sessions:
            del self.disconnected_sessions[old_session_id]

        self.active_sessions[new_session_id] = existing_session
        self.stats["sessions_reconnected"] += 1

        logger.info(f"Reconnected session {new_session_id} to meeting {existing_session.meeting_id} (attempt {existing_session.reconnection_count})")

        return {
            "success": True,
            "session_id": new_session_id,
            "meeting_id": existing_session.meeting_id,
            "is_new_session": False,
            "reconnection_count": existing_session.reconnection_count,
            "transcript_segments": len(existing_session.transcript_segments),
            "total_duration": existing_session.total_audio_duration
        }

    async def _schedule_timeout_processing(self, session: MeetingSession):
        """Schedule timeout processing for disconnected session"""

        async def timeout_processor():
            try:
                await asyncio.sleep(self.timeout_seconds)
                await self._process_timeout_meeting(session)
            except asyncio.CancelledError:
                logger.info(f"Timeout processing cancelled for session {session.session_id}")
            except Exception as e:
                logger.error(f"Error in timeout processing for {session.session_id}: {e}")

        # Cancel existing timeout if any
        if session.session_id in self.timeout_tasks:
            self.timeout_tasks[session.session_id].cancel()

        # Schedule new timeout
        self.timeout_tasks[session.session_id] = asyncio.create_task(timeout_processor())

    async def _process_timeout_meeting(self, session: MeetingSession):
        """Process meeting tasks after timeout period"""

        if session.processed_for_tasks:
            logger.info(f"Meeting {session.meeting_id} already processed, skipping timeout processing")
            return

        if not session.transcript_segments:
            logger.warning(f"No transcript data for timeout processing: {session.meeting_id}")
            return

        logger.info(f"Processing timeout meeting: {session.meeting_id}")
        logger.info(f"Session stats: {len(session.transcript_segments)} segments, {session.total_audio_duration:.1f}s audio")

        try:
            # Merge transcript segments
            full_transcript = self._merge_transcripts(session.transcript_segments)

            # Import AI components
            from .task_extractor import TaskExtractor
            from .ai_processor import AIProcessor
            from .integration_bridge import create_integration_bridge

            # Process tasks
            ai_processor = AIProcessor()
            task_extractor = TaskExtractor(ai_processor)

            meeting_context = {
                "meeting_id": session.meeting_id,
                "title": f"Meeting Session (Timeout Processed)",
                "participants": session.participants,
                "duration": session.total_audio_duration,
                "reconnections": session.reconnection_count
            }

            # Extract tasks using unified method (Phase 1 optimization)
            task_result = await task_extractor.extract_tasks_unified(full_transcript, meeting_context)

            if task_result.get("tasks"):
                # Create integration bridge and process tasks (with Phase 2 retry mechanism)
                integration_bridge = create_integration_bridge({"enabled": True})
                integration_result = await integration_bridge.create_tasks_from_ai_results(
                    task_result["tasks"],
                    meeting_context
                )

                logger.info(f"Timeout processing complete for {session.meeting_id}")
                logger.info(f"Tasks extracted: {len(task_result['tasks'])}")
                logger.info(f"Tasks created: {integration_result.get('tasks_created', 0)}")

                self.stats["sessions_processed_timeout"] += 1
            else:
                logger.info(f"No tasks extracted from timeout processing for {session.meeting_id}")

            # Mark as processed
            session.processed_for_tasks = True
            self.processed_sessions.add(session.meeting_id)

        except Exception as e:
            logger.error(f"Failed to process timeout meeting {session.meeting_id}: {e}")

        finally:
            # Cleanup
            if session.session_id in self.disconnected_sessions:
                del self.disconnected_sessions[session.session_id]
            if session.session_id in self.timeout_tasks:
                del self.timeout_tasks[session.session_id]

    def _merge_transcripts(self, transcript_segments: List[Dict]) -> str:
        """Merge transcript segments into single text"""
        if not transcript_segments:
            return ""

        # Sort by timestamp if available
        try:
            sorted_segments = sorted(
                transcript_segments,
                key=lambda x: x.get('timestamp', 0)
            )
        except (KeyError, TypeError):
            sorted_segments = transcript_segments

        # Extract text from segments
        transcript_parts = []
        for segment in sorted_segments:
            if isinstance(segment, dict):
                text = segment.get('text', segment.get('transcript', ''))
                if text and text.strip():
                    transcript_parts.append(text.strip())
            elif isinstance(segment, str):
                if segment.strip():
                    transcript_parts.append(segment.strip())

        return " ".join(transcript_parts)

    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_sessions()
                self.stats["cleanup_cycles"] += 1
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _cleanup_old_sessions(self):
        """Clean up old processed sessions"""
        current_time = time.time()
        cleanup_threshold = 3600  # 1 hour

        # Cleanup old disconnected sessions that have been processed
        sessions_to_remove = []
        for session_id, session in self.disconnected_sessions.items():
            if (current_time - session.last_activity > cleanup_threshold and
                session.processed_for_tasks):
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.disconnected_sessions[session_id]
            if session_id in self.timeout_tasks:
                self.timeout_tasks[session_id].cancel()
                del self.timeout_tasks[session_id]

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")

    def get_session_stats(self) -> Dict:
        """Get session management statistics"""
        return {
            "active_sessions": len(self.active_sessions),
            "disconnected_sessions": len(self.disconnected_sessions),
            "processed_meetings": len(self.processed_sessions),
            "pending_timeouts": len(self.timeout_tasks),
            **self.stats
        }

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a specific session"""
        session = self.active_sessions.get(session_id) or self.disconnected_sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "meeting_id": session.meeting_id,
            "is_active": session.is_active,
            "start_time": session.start_time,
            "last_activity": session.last_activity,
            "participants": session.participants,
            "transcript_segments": len(session.transcript_segments),
            "total_audio_duration": session.total_audio_duration,
            "reconnection_count": session.reconnection_count,
            "processed_for_tasks": session.processed_for_tasks
        }

# Global session manager instance
session_manager = MeetingSessionManager()
