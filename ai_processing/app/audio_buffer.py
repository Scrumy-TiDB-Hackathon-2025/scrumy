"""
Audio Buffer System for Whisper Minimum Duration Requirements

Buffers raw audio chunks until minimum duration (100ms) is reached
"""

import asyncio
import time
import wave
import tempfile
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    data: bytes
    timestamp: float
    metadata: Dict
    sample_rate: int = 16000
    channels: int = 1
    sample_width: int = 2

class SessionAudioBuffer:
    """Enhanced buffer with 3s target duration for better speech recognition"""
    
    def __init__(self, session_id: str, target_duration_ms: int = 5000):
        self.session_id = session_id
        self.target_duration_ms = target_duration_ms  # Increased to 5000ms for better context
        self.buffer = bytearray()
        self.target_samples = (target_duration_ms * 16000) // 1000  # 80000 samples for 5s
        self.last_flush = None  # Set when first chunk arrives
        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2
        self.timeout_seconds = 8.0  # Increased to 8.0s for longer context
        
        logger.info(f"Enhanced audio buffer: {session_id}, target={target_duration_ms}ms ({self.target_samples} samples)")
        
    def add_chunk(self, audio_data: bytes, timestamp: float, metadata: Dict) -> bool:
        """Add audio chunk to buffer. Returns True if ready for processing."""
        try:
            # Update parameters from first chunk
            if len(self.buffer) == 0:
                self.sample_rate = metadata.get('sampleRate', 16000)
                self.channels = metadata.get('channels', 1)
                self.sample_width = metadata.get('sampleWidth', 2)
                # Recalculate target samples with actual sample rate
                self.target_samples = (self.target_duration_ms * self.sample_rate) // 1000
                # Set timeout start time when first chunk arrives
                self.last_flush = time.time()
            
            # Append audio data to buffer
            self.buffer.extend(audio_data)
            
            # Check if ready for processing
            return self.should_process()
            
        except Exception as e:
            logger.error(f"Error adding audio chunk: {e}")
            return False
    
    def should_process(self) -> bool:
        """Process if buffer is full OR timeout reached"""
        if len(self.buffer) == 0 or self.last_flush is None:
            return False
            
        bytes_per_sample = self.sample_width * self.channels
        current_samples = len(self.buffer) // bytes_per_sample
        time_since_flush = time.time() - self.last_flush
        
        # Process if buffer is full OR timeout reached
        buffer_full = current_samples >= (self.target_samples * 0.98)  # 98% threshold
        timeout_reached = time_since_flush > self.timeout_seconds
        
        if buffer_full or timeout_reached:
            duration_ms = (current_samples / self.sample_rate) * 1000
            reason = "buffer_full" if buffer_full else "timeout"
            logger.debug(f"Buffer ready: {reason}, {duration_ms:.1f}ms, {current_samples} samples, time_since_flush={time_since_flush:.1f}s")
            return True
        
        return False
    
    def get_buffered_audio(self) -> Optional[bytes]:
        """Get current buffered audio data"""
        if len(self.buffer) == 0:
            return None
        return bytes(self.buffer)
    
    def create_wav_file(self) -> Optional[str]:
        """Create temporary WAV file from buffered audio"""
        audio_data = self.get_buffered_audio()
        if not audio_data:
            return None
            
        try:
            # Create temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Write WAV file
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            bytes_per_sample = self.sample_width * self.channels
            samples = len(audio_data) // bytes_per_sample
            duration_ms = (samples / self.sample_rate) * 1000
            
            logger.info(f"Created WAV: {temp_path} ({duration_ms:.1f}ms, {len(audio_data)} bytes)")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error creating WAV file: {e}")
            return None
    
    def clear(self):
        """Clear buffer after processing"""
        self.buffer.clear()
        # Reset last_flush to prevent repeated timeout processing
        self.last_flush = time.time()
        logger.debug(f"Audio buffer cleared for session {self.session_id}")
    
    def get_duration_ms(self) -> float:
        """Get current buffer duration in milliseconds"""
        if len(self.buffer) == 0:
            return 0.0
        bytes_per_sample = self.sample_width * self.channels
        samples = len(self.buffer) // bytes_per_sample
        return (samples / self.sample_rate) * 1000

class AudioBufferManager:
    """Manage audio buffers for multiple sessions with memory limits"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.buffers: Dict[str, SessionAudioBuffer] = {}
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.session_timeout_minutes = 5
    
    def get_buffer(self, session_id: str) -> SessionAudioBuffer:
        """Get or create audio buffer for session"""
        if session_id not in self.buffers:
            self.buffers[session_id] = SessionAudioBuffer(session_id)
            logger.info(f"Created audio buffer for session {session_id}")
            
            # Check memory usage
            self._check_memory_limits()
            
        return self.buffers[session_id]
    
    def remove_buffer(self, session_id: str):
        """Remove buffer when session ends"""
        if session_id in self.buffers:
            del self.buffers[session_id]
            logger.info(f"Removed audio buffer for session {session_id}")
    
    def _check_memory_limits(self):
        """Check and enforce memory limits"""
        total_memory = sum(len(buffer.buffer) for buffer in self.buffers.values())
        
        if total_memory > self.max_memory_bytes:
            logger.warning(f"Memory limit exceeded: {total_memory / 1024 / 1024:.1f}MB > {self.max_memory_bytes / 1024 / 1024:.1f}MB")
            
            # Remove oldest buffers
            sorted_buffers = sorted(
                self.buffers.items(),
                key=lambda x: x[1].last_flush
            )
            
            for session_id, buffer in sorted_buffers:
                if total_memory <= self.max_memory_bytes:
                    break
                    
                logger.info(f"Removing buffer {session_id} due to memory pressure")
                total_memory -= len(buffer.buffer)
                del self.buffers[session_id]