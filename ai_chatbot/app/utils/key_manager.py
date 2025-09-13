import os
from typing import List
import random
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class GroqKeyManager:
    def __init__(self, env_prefix: str = "GROQ_API_KEY"):
        self.env_prefix = env_prefix
        self.keys = []
        self.current_key_index = 0
        self.last_rotation = datetime.now()
        self.rotation_interval = timedelta(minutes=5)
        self._load_keys()
        
    def _load_keys(self):
        """Load API keys from environment variables"""
        for i in range(1, 6):  # Load up to 5 keys
            key = os.getenv(f"{self.env_prefix}_{i}")
            if key:
                self.keys.append({"key": key, "calls": 0, "last_used": None})
        
        if not self.keys:
            # Fallback to single key
            key = os.getenv(self.env_prefix)
            if key:
                self.keys.append({"key": key, "calls": 0, "last_used": None})
            else:
                raise ValueError("No Groq API keys found in environment variables")

    async def get_key(self) -> str:
        """Get the next available API key"""
        await self._maybe_rotate()
        
        key_info = self.keys[self.current_key_index]
        key_info["calls"] += 1
        key_info["last_used"] = datetime.now()
        
        return key_info["key"]

    async def _maybe_rotate(self):
        """Rotate keys if needed"""
        now = datetime.now()
        if now - self.last_rotation >= self.rotation_interval:
            # Simple round-robin rotation
            self.current_key_index = (self.current_key_index + 1) % len(self.keys)
            self.last_rotation = now
            
            # Log rotation for monitoring
            logger.info(f"Rotating to key {self.current_key_index + 1}")
            
            # Reset calls counter for the previous key
            prev_index = (self.current_key_index - 1) % len(self.keys)
            self.keys[prev_index]["calls"] = 0

    def get_key_stats(self):
        """Get usage statistics for all keys"""
        return [{
            "key_number": i + 1,
            "calls": key["calls"],
            "last_used": key["last_used"].isoformat() if key["last_used"] else None
        } for i, key in enumerate(self.keys)]
