"""
Status Adapter for Task Management Integrations

This module provides status mapping between different task management platforms
(ClickUp, Notion, etc.) to ensure consistent status handling across integrations.
"""

import logging
from typing import Dict, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class StandardStatus(Enum):
    """Standardized status values used internally"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class StatusAdapter:
    """Adapter to map status values between different platforms"""

    # ClickUp status mappings (based on actual API format - lowercase)
    CLICKUP_STATUS_MAP = {
        # Standard -> ClickUp (API format)
        StandardStatus.NOT_STARTED: "to do",
        StandardStatus.IN_PROGRESS: "in progress",
        StandardStatus.DONE: "complete",
        # Fallback mappings for unsupported statuses
        StandardStatus.BLOCKED: "in progress",  # Map to closest available
        StandardStatus.REVIEW: "in progress",   # Map to closest available
        StandardStatus.CANCELLED: "to do"  # Map to closest available
    }

    # Reverse mapping: ClickUp -> Standard
    CLICKUP_REVERSE_MAP = {
        "to do": StandardStatus.NOT_STARTED,
        "in progress": StandardStatus.IN_PROGRESS,
        "complete": StandardStatus.DONE,
        # Handle UI case variations (for future compatibility)
        "Not Started": StandardStatus.NOT_STARTED,
        "In Progress": StandardStatus.IN_PROGRESS,
        "Done": StandardStatus.DONE
    }

    # Notion status mappings (common Notion status values)
    NOTION_STATUS_MAP = {
        # Standard -> Notion
        StandardStatus.NOT_STARTED: "Not started",
        StandardStatus.IN_PROGRESS: "In progress",
        StandardStatus.BLOCKED: "Blocked",
        StandardStatus.REVIEW: "Review",
        StandardStatus.DONE: "Done",
        StandardStatus.CANCELLED: "Cancelled"
    }

    # Reverse mapping: Notion -> Standard
    NOTION_REVERSE_MAP = {
        "Not started": StandardStatus.NOT_STARTED,
        "In progress": StandardStatus.IN_PROGRESS,
        "Blocked": StandardStatus.BLOCKED,
        "Review": StandardStatus.REVIEW,
        "Done": StandardStatus.DONE,
        "Cancelled": StandardStatus.CANCELLED
    }

    # Priority mappings for different platforms
    CLICKUP_PRIORITY_MAP = {
        "urgent": 1,
        "high": 2,
        "normal": 3,
        "medium": 3,  # Alias for normal
        "low": 4
    }

    NOTION_PRIORITY_MAP = {
        "urgent": "High",
        "high": "High",
        "normal": "Medium",
        "medium": "Medium",
        "low": "Low"
    }

    @classmethod
    def to_clickup_status(cls, standard_status: str) -> str:
        """Convert standard status to ClickUp status"""
        try:
            # Try to parse as StandardStatus enum
            if isinstance(standard_status, str):
                # Handle common input variations
                normalized = standard_status.lower().replace(" ", "_")
                std_status = StandardStatus(normalized)
            else:
                std_status = standard_status

            clickup_status = cls.CLICKUP_STATUS_MAP.get(std_status)
            if clickup_status:
                logger.debug(f"Mapped status '{standard_status}' -> ClickUp '{clickup_status}'")
                return clickup_status
            else:
                logger.warning(f"No ClickUp mapping for status '{standard_status}', using default 'Not Started'")
                return "Not Started"

        except (ValueError, KeyError):
            # If we can't parse as enum, try direct string mapping
            direct_mappings = {
                "todo": "to do",
                "open": "to do",
                "doing": "in progress",
                "complete": "complete",
                "completed": "complete",
                "closed": "complete",
                "done": "complete"
            }

            normalized = standard_status.lower().strip()
            if normalized in direct_mappings:
                result = direct_mappings[normalized]
                logger.debug(f"Direct mapped status '{standard_status}' -> ClickUp '{result}'")
                return result

            logger.warning(f"Unknown status '{standard_status}', using default 'to do'")
            return "to do"

    @classmethod
    def from_clickup_status(cls, clickup_status: str) -> StandardStatus:
        """Convert ClickUp status to standard status"""
        std_status = cls.CLICKUP_REVERSE_MAP.get(clickup_status)
        if std_status:
            return std_status

        # Try case-insensitive lookup
        for cu_status, std_status in cls.CLICKUP_REVERSE_MAP.items():
            if cu_status.lower() == clickup_status.lower():
                return std_status

        logger.warning(f"Unknown ClickUp status '{clickup_status}', defaulting to NOT_STARTED")
        return StandardStatus.NOT_STARTED

    @classmethod
    def to_notion_status(cls, standard_status: str) -> str:
        """Convert standard status to Notion status"""
        try:
            if isinstance(standard_status, str):
                normalized = standard_status.lower().replace(" ", "_")
                std_status = StandardStatus(normalized)
            else:
                std_status = standard_status

            notion_status = cls.NOTION_STATUS_MAP.get(std_status)
            if notion_status:
                logger.debug(f"Mapped status '{standard_status}' -> Notion '{notion_status}'")
                return notion_status
            else:
                logger.warning(f"No Notion mapping for status '{standard_status}', using default 'Not started'")
                return "Not started"

        except (ValueError, KeyError):
            # Direct string mappings for common variations
            direct_mappings = {
                "todo": "Not started",
                "to do": "Not started",
                "open": "Not started",
                "doing": "In progress",
                "complete": "Done",
                "completed": "Done",
                "closed": "Done"
            }

            normalized = standard_status.lower().strip()
            if normalized in direct_mappings:
                result = direct_mappings[normalized]
                logger.debug(f"Direct mapped status '{standard_status}' -> Notion '{result}'")
                return result

            logger.warning(f"Unknown status '{standard_status}', using default 'Not started'")
            return "Not started"

    @classmethod
    def from_notion_status(cls, notion_status: str) -> StandardStatus:
        """Convert Notion status to standard status"""
        std_status = cls.NOTION_REVERSE_MAP.get(notion_status)
        if std_status:
            return std_status

        logger.warning(f"Unknown Notion status '{notion_status}', defaulting to NOT_STARTED")
        return StandardStatus.NOT_STARTED

    @classmethod
    def to_clickup_priority(cls, priority: str) -> int:
        """Convert priority string to ClickUp priority number (1=urgent, 4=low)"""
        return cls.CLICKUP_PRIORITY_MAP.get(priority.lower(), 3)  # Default to normal

    @classmethod
    def to_notion_priority(cls, priority: str) -> str:
        """Convert priority string to Notion priority"""
        return cls.NOTION_PRIORITY_MAP.get(priority.lower(), "Medium")  # Default to Medium

    @classmethod
    def get_supported_statuses(cls, platform: str) -> List[str]:
        """Get list of supported statuses for a platform"""
        if platform.lower() == "clickup":
            return ["to do", "in progress", "complete"]  # Actual API format
        elif platform.lower() == "notion":
            return list(cls.NOTION_STATUS_MAP.values())
        else:
            return [status.value for status in StandardStatus]

    @classmethod
    def validate_status(cls, status: str, platform: str) -> tuple[bool, str]:
        """Validate if a status is supported by the platform"""
        supported = cls.get_supported_statuses(platform)

        if status in supported:
            return True, f"Status '{status}' is supported by {platform}"

        # Try case-insensitive match
        for supported_status in supported:
            if supported_status.lower() == status.lower():
                return True, f"Status '{status}' matches '{supported_status}' (case-insensitive)"

        return False, f"Status '{status}' is not supported by {platform}. Supported: {supported}"

    @classmethod
    def normalize_task_data(cls, task_data: Dict, target_platform: str) -> Dict:
        """Normalize task data for a specific platform"""
        normalized = task_data.copy()

        if target_platform.lower() == "clickup":
            # Convert status
            if "status" in normalized:
                normalized["status"] = cls.to_clickup_status(normalized["status"])

            # Convert priority
            if "priority" in normalized:
                normalized["priority"] = cls.to_clickup_priority(normalized["priority"])

        elif target_platform.lower() == "notion":
            # Convert status
            if "status" in normalized:
                normalized["status"] = cls.to_notion_status(normalized["status"])

            # Convert priority
            if "priority" in normalized:
                normalized["priority"] = cls.to_notion_priority(normalized["priority"])

        logger.debug(f"Normalized task data for {target_platform}: {normalized}")
        return normalized


def get_status_adapter() -> StatusAdapter:
    """Factory function to get a StatusAdapter instance"""
    return StatusAdapter()


# Convenience functions for common operations
def map_status_to_clickup(status: str) -> str:
    """Quick function to map any status to ClickUp format"""
    return StatusAdapter.to_clickup_status(status)


def map_status_to_notion(status: str) -> str:
    """Quick function to map any status to Notion format"""
    return StatusAdapter.to_notion_status(status)


def normalize_task_for_platform(task_data: Dict, platform: str) -> Dict:
    """Quick function to normalize task data for a platform"""
    return StatusAdapter.normalize_task_data(task_data, platform)
