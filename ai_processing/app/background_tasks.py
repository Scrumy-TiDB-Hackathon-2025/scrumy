"""
Background Task Manager for FastAPI WebSocket Application
Handles timeout-based audio buffer processing independently of WebSocket connections
"""

import asyncio
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._audio_buffer_manager = None
        self._websocket_manager = None

    async def start(self, audio_buffer_manager, websocket_manager):
        """Start the background task"""
        self._audio_buffer_manager = audio_buffer_manager
        self._websocket_manager = websocket_manager
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._timeout_checker_loop())
            print("🚀 Background timeout checker started")

    async def stop(self):
        """Stop the background task"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            print("🛑 Background timeout checker stopped")

    async def _timeout_checker_loop(self):
        """Background loop to check for timeout-based buffer processing"""
        print(f"🔍 Background task loop started - checking every 1s")

        while self._running:
            try:
                buffer_count = len(self._audio_buffer_manager.buffers) if self._audio_buffer_manager else 0

                if self._audio_buffer_manager and buffer_count > 0:
                    # Only log when there are buffers with content or processing needed
                    has_activity = False

                    for session_id, buffer in list(self._audio_buffer_manager.buffers.items()):
                        duration = buffer.get_duration_ms()
                        time_since_flush = time.time() - buffer.last_flush if buffer.last_flush else 0
                        buffer_len = len(buffer.buffer)

                        # Check if buffer should be processed (handles both buffer full and timeout)
                        if buffer.should_process():
                            if not has_activity:
                                print(f"🔍 [DEBUG] Background check: {buffer_count} buffers in manager")
                                has_activity = True
                            print(f"⏰ Timeout triggered for session {session_id} ({duration:.1f}ms, {time_since_flush:.1f}s)")
                            await self._process_timeout_buffer(session_id, buffer)
                        elif duration > 0 or time_since_flush < 10:  # Only log if there's recent activity
                            if not has_activity:
                                print(f"🔍 [DEBUG] Background check: {buffer_count} buffers in manager")
                                has_activity = True
                            print(f"   Buffer {session_id}: {duration:.1f}ms, {buffer_len} bytes, {time_since_flush:.1f}s since flush")
                # Skip logging when no buffers or no activity

            except Exception as e:
                print(f"❌ Error in timeout checker: {e}")
                logger.error(f"Timeout checker error: {e}")

            await asyncio.sleep(1.0)

    async def _process_timeout_buffer(self, session_id: str, buffer):
        """Process buffer due to timeout"""
        try:
            if self._websocket_manager:
                await self._websocket_manager._process_timeout_buffer(session_id, buffer)
        except Exception as e:
            print(f"❌ Error processing timeout buffer: {e}")
            logger.error(f"Error processing timeout buffer: {e}")

# Global instance
background_manager = BackgroundTaskManager()
