"""
Minimal chatbot synchronization for real-time meeting context
Maintains current working conditions while enhancing chatbot access
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ChatbotSync:
    """Lightweight sync service for chatbot meeting context"""
    
    def __init__(self, chatbot_url: str = "http://127.0.0.1:8001"):
        self.chatbot_url = chatbot_url
        self.knowledge_endpoint = f"{chatbot_url}/knowledge/add"
    
    async def add_live_transcript_chunk(self, meeting_id: str, transcript: str, speaker: str = "Unknown"):
        """Add live transcript chunks for real-time context - DISABLED to prevent infinite API calls"""
        # DISABLED: Individual /knowledge/add calls during recording cause infinite loops
        # Vector store is now populated efficiently via bulk /meetings/populate-vector-store after meeting ends
        logger.debug(f"Live transcript sync disabled - using bulk population after meeting ends")
        return
    
    async def add_meeting_participants(self, meeting_id: str, participants: List[str]):
        """Add participant context for better responses - DISABLED to prevent infinite API calls"""
        # DISABLED: Individual /knowledge/add calls during recording cause infinite loops
        # Participant data is now populated efficiently via bulk /meetings/populate-vector-store after meeting ends
        logger.debug(f"Participant sync disabled - using bulk population after meeting ends")
        return

# Global instance for use in WebSocket server
chatbot_sync = ChatbotSync()