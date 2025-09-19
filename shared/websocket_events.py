"""
WebSocket Events Constants
Centralized event type definitions for consistent communication across the ScrumBot system.
"""

from typing import Optional

class WebSocketEventTypes:
    """Standard WebSocket event types used across the ScrumBot system."""

    # Connection Events
    HANDSHAKE = "HANDSHAKE"
    HANDSHAKE_ACK = "HANDSHAKE_ACK"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    # Audio Processing Events
    AUDIO_CHUNK = "AUDIO_CHUNK"
    AUDIO_BUFFER_FULL = "AUDIO_BUFFER_FULL"
    AUDIO_PROCESSING_START = "AUDIO_PROCESSING_START"
    AUDIO_PROCESSING_COMPLETE = "AUDIO_PROCESSING_COMPLETE"

    # Transcription Events (STANDARDIZED - uppercase only)
    TRANSCRIPTION_RESULT = "TRANSCRIPTION_RESULT"
    TRANSCRIPTION_ERROR = "TRANSCRIPTION_ERROR"
    TRANSCRIPTION_TIMEOUT = "TRANSCRIPTION_TIMEOUT"

    # Meeting Events
    MEETING_EVENT = "MEETING_EVENT"
    MEETING_STARTED = "MEETING_STARTED"
    MEETING_ENDED = "MEETING_ENDED"
    MEETING_UPDATE = "MEETING_UPDATE"
    MEETING_PROCESSED = "MEETING_PROCESSED"

    # Participant Events
    PARTICIPANT_JOINED = "PARTICIPANT_JOINED"
    PARTICIPANT_LEFT = "PARTICIPANT_LEFT"
    PARTICIPANT_UPDATED = "PARTICIPANT_UPDATED"

    # Processing Status Events
    PROCESSING_STATUS = "PROCESSING_STATUS"
    PROCESSING_START = "PROCESSING_START"
    PROCESSING_COMPLETE = "PROCESSING_COMPLETE"
    PROCESSING_ERROR = "PROCESSING_ERROR"

    # System Events
    ERROR = "ERROR"
    WARNING = "WARNING"
    SYSTEM_STATUS = "SYSTEM_STATUS"

    # Authentication Events
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    AUTH_FAILURE = "AUTH_FAILURE"


class WebSocketEventData:
    """Standard data structures for WebSocket events."""

    @staticmethod
    def transcription_result(text: str, confidence: float, timestamp: str,
                           speaker: str = "Unknown", chunk_id: Optional[int] = None,
                           is_final: bool = False, **kwargs) -> dict:
        """Standard transcription result event data structure."""
        return {
            "text": text,
            "confidence": confidence,
            "timestamp": timestamp,
            "speaker": speaker,
            "chunkId": chunk_id,
            "is_final": is_final,
            **kwargs
        }

    @staticmethod
    def meeting_event(meeting_id: str, event_type: str, timestamp: str,
                     data: Optional[dict] = None) -> dict:
        """Standard meeting event data structure."""
        return {
            "meetingId": meeting_id,
            "eventType": event_type,
            "timestamp": timestamp,
            "data": data or {}
        }

    @staticmethod
    def processing_status(meeting_id: str, status: str, progress: Optional[float] = None,
                         message: Optional[str] = None, **kwargs) -> dict:
        """Standard processing status event data structure."""
        return {
            "meetingId": meeting_id,
            "status": status,
            "progress": progress,
            "message": message,
            **kwargs
        }

    @staticmethod
    def error_event(error_type: str, message: str, details: Optional[dict] = None) -> dict:
        """Standard error event data structure."""
        return {
            "errorType": error_type,
            "message": message,
            "details": details or {},
            "timestamp": None  # Will be set by sender
        }


class WebSocketMessageTypes:
    """Message type constants for client identification."""

    CHROME_EXTENSION = "chrome_extension"
    FRONTEND_DASHBOARD = "frontend_dashboard"
    INTEGRATION_SERVICE = "integration_service"
    AI_PROCESSOR = "ai_processor"


class WebSocketEventValidator:
    """Validator for WebSocket event structures."""

    REQUIRED_FIELDS = {
        WebSocketEventTypes.TRANSCRIPTION_RESULT: ["text", "confidence", "timestamp"],
        WebSocketEventTypes.MEETING_EVENT: ["meetingId", "eventType", "timestamp"],
        WebSocketEventTypes.PROCESSING_STATUS: ["meetingId", "status"],
        WebSocketEventTypes.ERROR: ["errorType", "message"],
        WebSocketEventTypes.HANDSHAKE: ["clientType"],
    }

    @classmethod
    def validate_event(cls, event_type: str, data: dict) -> tuple[bool, str]:
        """
        Validate event data structure.

        Args:
            event_type: The event type to validate
            data: The event data dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        if event_type not in cls.REQUIRED_FIELDS:
            return True, ""  # No validation rules defined

        required_fields = cls.REQUIRED_FIELDS[event_type]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        return True, ""


# Deprecated event names (for migration reference)
DEPRECATED_EVENT_NAMES = {
    "transcription_result": WebSocketEventTypes.TRANSCRIPTION_RESULT,  # Use uppercase
    "meeting_update": WebSocketEventTypes.MEETING_UPDATE,
    "processing_complete": WebSocketEventTypes.PROCESSING_COMPLETE,
}

# Export commonly used constants
__all__ = [
    'WebSocketEventTypes',
    'WebSocketEventData',
    'WebSocketMessageTypes',
    'WebSocketEventValidator',
    'DEPRECATED_EVENT_NAMES'
]
