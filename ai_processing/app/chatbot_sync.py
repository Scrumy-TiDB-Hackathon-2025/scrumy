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
        """Add live transcript chunks for real-time context"""
        try:
            if not transcript.strip() or len(transcript) < 10:
                return  # Skip short/empty transcripts
                
            content = f"Live transcript from meeting {meeting_id} - {speaker}: {transcript}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    self.knowledge_endpoint,
                    json={
                        "content": content,
                        "metadata": {
                            "type": "live_transcript",
                            "meeting_id": meeting_id,
                            "speaker": speaker,
                            "category": "live"
                        }
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to sync live transcript: {e}")  # Non-critical
    
    async def add_meeting_participants(self, meeting_id: str, participants: List[str]):
        """Add participant context for better responses"""
        try:
            if not participants:
                return
                
            content = f"Meeting {meeting_id} participants: {', '.join(participants)}"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    self.knowledge_endpoint,
                    json={
                        "content": content,
                        "metadata": {
                            "type": "participants",
                            "meeting_id": meeting_id,
                            "category": "meeting"
                        }
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to sync participants: {e}")

# Global instance for use in WebSocket server
chatbot_sync = ChatbotSync()