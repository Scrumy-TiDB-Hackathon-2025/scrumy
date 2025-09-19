"""
Epic C Tools Integration Package
Production-ready integrations with Notion, Slack, and ClickUp
"""

from .integrations import NotionIntegration, SlackIntegration, ClickUpIntegration, integration_manager
from .tools import tools
from .ai_agent import AIAgent
from .tidb_manager import tidb_manager

__version__ = "1.0.0"
__author__ = "ScrumBot Team"

__all__ = [
    "NotionIntegration",
    "SlackIntegration", 
    "ClickUpIntegration",
    "integration_manager",
    "tools",
    "AIAgent",
    "tidb_manager"
]