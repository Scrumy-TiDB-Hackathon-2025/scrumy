import os
import logging
from typing import Optional
from .pipeline_logger import PipelineLogger

class DebugLoggerManager:
    """Manages conditional debug logging to avoid production overhead"""
    
    def __init__(self):
        self.debug_enabled = os.getenv('DEBUG_LOGGING', 'false').lower() == 'true'
        self.logger_cache = {}
        
    def get_logger(self, session_id: str) -> Optional[PipelineLogger]:
        """Get logger only if debug mode enabled"""
        if not self.debug_enabled:
            return None
            
        if session_id not in self.logger_cache:
            self.logger_cache[session_id] = PipelineLogger(session_id)
            
        return self.logger_cache[session_id]
    
    def cleanup_logger(self, session_id: str):
        """Remove logger from cache to free memory"""
        if session_id in self.logger_cache:
            del self.logger_cache[session_id]

# Global instance
debug_manager = DebugLoggerManager()