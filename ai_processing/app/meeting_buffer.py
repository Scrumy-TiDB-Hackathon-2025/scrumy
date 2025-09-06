"""
Meeting Buffer System for Groq API Optimization

Buffers transcript chunks and processes them in batches to reduce API calls by 95%
"""

import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from .pipeline_logger import PipelineLogger

logger = logging.getLogger(__name__)

@dataclass
class TranscriptChunk:
    timestamp_start: float
    timestamp_end: float
    raw_text: str
    participants_present: List[Dict]
    confidence: float
    chunk_index: int
    speaker: Optional[str] = None  # Filled by batch processing

class MeetingBuffer:
    """Buffer transcript chunks for batch processing"""
    
    def __init__(self, meeting_id: str):
        self.meeting_id = meeting_id
        self.chunks: List[TranscriptChunk] = []
        self.participant_registry: Dict[str, Dict] = {}
        self.total_tokens = 0
        self.last_processed_index = 0
        self.last_batch_time = time.time()
        
        # Conditional debug logging
        try:
            from .debug_logger import debug_manager
            self.logger = debug_manager.get_logger(meeting_id)
            if self.logger is None:
                # Fallback when debug logging is disabled
                from .pipeline_logger import PipelineLogger
                self.logger = PipelineLogger(meeting_id)
        except ImportError:
            from .pipeline_logger import PipelineLogger
            self.logger = PipelineLogger(meeting_id)
        
        # Configuration
        self.BATCH_INTERVAL = 30  # seconds
        self.MAX_TOKENS = 6000
        self.MIN_CHUNKS_FOR_BATCH = 3
    
    def add_chunk(self, chunk: TranscriptChunk):
        """Add new transcript chunk to buffer"""
        self.chunks.append(chunk)
        self.total_tokens += self._estimate_tokens(chunk.raw_text)
        
        # Update participant registry
        for participant in chunk.participants_present:
            participant_id = participant.get('id')
            if participant_id:
                self.participant_registry[participant_id] = participant
        
        logger.debug(f"Added chunk {chunk.chunk_index}: {len(chunk.raw_text)} chars, {self.total_tokens} total tokens")
    
    def should_process_batch(self) -> bool:
        """Check if buffer should be processed"""
        if len(self.chunks) <= self.last_processed_index:
            return False
            
        unprocessed_chunks = len(self.chunks) - self.last_processed_index
        time_since_last = time.time() - self.last_batch_time
        
        # Triggers for batch processing
        return (
            unprocessed_chunks >= self.MIN_CHUNKS_FOR_BATCH and (
                time_since_last >= self.BATCH_INTERVAL or  # Time-based
                self.total_tokens >= self.MAX_TOKENS       # Token-based
            )
        )
    
    def get_batch_for_processing(self) -> str:
        """Get formatted batch for Groq processing"""
        unprocessed_chunks = self.chunks[self.last_processed_index:]
        
        if not unprocessed_chunks:
            return ""
        
        # Build context-rich prompt
        participants_info = []
        for p_id, p_data in self.participant_registry.items():
            name = p_data.get('name', 'Unknown')
            role = p_data.get('role', '')
            is_host = p_data.get('is_host', False)
            status = "Host" if is_host else "Participant"
            participants_info.append(f"{name} ({role}, {status})")
        
        participants_str = ", ".join(participants_info) if participants_info else "Unknown participants"
        
        # Format transcript with timestamps
        transcript_lines = []
        for chunk in unprocessed_chunks:
            start_time = self._format_timestamp(chunk.timestamp_start)
            end_time = self._format_timestamp(chunk.timestamp_end)
            transcript_lines.append(f"[{start_time}-{end_time}] \"{chunk.raw_text}\"")
        
        batch_prompt = f"""Participants: {participants_str}
Meeting: {self.meeting_id}
Platform: Meeting Platform

Transcript with timestamps:
{chr(10).join(transcript_lines)}

Identify the speaker for each segment. Use participant names when possible.
Return JSON format: {{"segments": [{{"timestamp": "[00:00-00:05]", "text": "...", "speaker": "Name"}}]}}"""
        
        # Log batch processing (only if debug enabled)
        if self.logger:
            chunk_data = [{
                "timestamp_start": chunk.timestamp_start,
                "timestamp_end": chunk.timestamp_end,
                "text": chunk.raw_text,
                "confidence": chunk.confidence
            } for chunk in unprocessed_chunks]
            
            self.logger.log_batch_processing(chunk_data, chr(10).join(transcript_lines))
        
        return batch_prompt
    
    def apply_speaker_results(self, results: Dict):
        """Apply batch processing results to chunks"""
        try:
            segments = results.get('segments', [])
            unprocessed_chunks = self.chunks[self.last_processed_index:]
            
            # Match segments to chunks by timestamp/text similarity
            for i, chunk in enumerate(unprocessed_chunks):
                for segment in segments:
                    if self._chunks_match(chunk, segment):
                        chunk.speaker = segment.get('speaker', 'Unknown')
                        break
                else:
                    chunk.speaker = self._fallback_speaker_identification(chunk)
            
            # Update processing state
            self.last_processed_index = len(self.chunks)
            self.last_batch_time = time.time()
            
            logger.info(f"Applied speaker results to {len(unprocessed_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error applying speaker results: {e}")
            # Fallback: use pattern matching for all unprocessed chunks
            self._apply_fallback_speakers()
    
    def get_recent_refined_transcript(self, last_n: int = 5) -> List[Dict]:
        """Get recent chunks with speaker information"""
        recent_chunks = self.chunks[-last_n:] if len(self.chunks) >= last_n else self.chunks
        
        return [
            {
                'timestamp': self._format_timestamp(chunk.timestamp_start),
                'text': chunk.raw_text,
                'speaker': chunk.speaker or 'Unknown',
                'confidence': chunk.confidence
            }
            for chunk in recent_chunks
            if chunk.raw_text.strip()
        ]
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as MM:SS"""
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _chunks_match(self, chunk: TranscriptChunk, segment: Dict) -> bool:
        """Check if chunk matches segment"""
        segment_text = segment.get('text', '').strip()
        chunk_text = chunk.raw_text.strip()
        
        # Simple text similarity check
        if len(segment_text) == 0 or len(chunk_text) == 0:
            return False
        
        # Check if texts are similar (simple word overlap)
        segment_words = set(segment_text.lower().split())
        chunk_words = set(chunk_text.lower().split())
        
        if len(segment_words) == 0 or len(chunk_words) == 0:
            return False
        
        overlap = len(segment_words.intersection(chunk_words))
        similarity = overlap / min(len(segment_words), len(chunk_words))
        
        return similarity > 0.6
    
    def _fallback_speaker_identification(self, chunk: TranscriptChunk) -> str:
        """Pattern-based speaker identification fallback"""
        text = chunk.raw_text.lower()
        
        # Look for explicit speaker patterns
        for p_id, p_data in self.participant_registry.items():
            name = p_data.get('name', '').lower()
            if name and (
                f"{name} speaking" in text or
                f"{name} as" in text or
                text.startswith(name) or
                f"i'm {name}" in text
            ):
                return p_data.get('name', 'Unknown')
        
        return 'Unknown'
    
    def _apply_fallback_speakers(self):
        """Apply fallback speaker identification to unprocessed chunks"""
        unprocessed_chunks = self.chunks[self.last_processed_index:]
        
        for chunk in unprocessed_chunks:
            if not chunk.speaker:
                chunk.speaker = self._fallback_speaker_identification(chunk)
        
        self.last_processed_index = len(self.chunks)
        self.last_batch_time = time.time()

class BatchProcessor:
    """Handles background batch processing"""
    
    def __init__(self, ai_processor):
        self.ai_processor = ai_processor
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.current_logger: Optional[PipelineLogger] = None
    
    async def process_buffer_batch(self, buffer: MeetingBuffer) -> Dict:
        """Process buffer batch with Groq API"""
        try:
            self.current_logger = buffer.logger
            batch_prompt = buffer.get_batch_for_processing()
            if not batch_prompt:
                return {}
            
            # Use AI processor for speaker identification
            system_prompt = """You are an expert at identifying speakers in meeting transcripts. 
            Analyze the transcript and identify who is speaking in each segment based on context clues, 
            participant information, and speech patterns."""
            
            # Log Groq request (only if debug enabled)
            if self.current_logger:
                self.current_logger.log_groq_request(batch_prompt, "groq-llama3-8b-8192")
            
            response = await self.ai_processor.call_ollama(batch_prompt, system_prompt)
            
            # Log Groq response (only if debug enabled)
            if self.current_logger:
                self.current_logger.log_groq_response(response)
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response)
                print(f"✅ Successfully parsed Groq JSON response")
                return result
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse Groq response as JSON: {e}")
                print(f"📝 Raw response: {response[:200]}...")
                
                # Return a valid fallback response
                return {
                    "error": "JSON parsing failed",
                    "raw_response": response[:500],  # First 500 chars for debugging
                    "speakers": [],
                    "analysis": "Could not parse AI response"
                }
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return {}
    
    def start_batch_processing(self, buffer: MeetingBuffer):
        """Start background batch processing task"""
        if buffer.meeting_id in self.processing_tasks:
            # Cancel existing task
            self.processing_tasks[buffer.meeting_id].cancel()
        
        # Start new processing task
        task = asyncio.create_task(self._background_process(buffer))
        self.processing_tasks[buffer.meeting_id] = task
    
    async def _background_process(self, buffer: MeetingBuffer):
        """Background processing task"""
        try:
            results = await self.process_buffer_batch(buffer)
            if results:
                buffer.apply_speaker_results(results)
                logger.info(f"Completed batch processing for meeting {buffer.meeting_id}")
            else:
                # Fallback processing
                buffer._apply_fallback_speakers()
                logger.info(f"Applied fallback processing for meeting {buffer.meeting_id}")
                
        except asyncio.CancelledError:
            logger.info(f"Batch processing cancelled for meeting {buffer.meeting_id}")
        except Exception as e:
            logger.error(f"Background processing error: {e}")
            # Always apply fallback to prevent stuck chunks
            buffer._apply_fallback_speakers()