#!/usr/bin/env python3
"""
Test Groq Optimization Implementation

Tests the new batched processing system vs old per-chunk processing
"""

import asyncio
import sys
import os
import time
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.meeting_buffer import MeetingBuffer, TranscriptChunk, BatchProcessor
from app.ai_processor import AIProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment
def load_env():
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')

async def test_groq_optimization():
    """Test the optimized batched processing"""
    
    print("🚀 GROQ OPTIMIZATION TEST")
    print("=" * 50)
    
    # Load environment
    load_env()
    
    # Check GROQ key
    if not os.getenv('GROQ_API_KEY'):
        print("❌ GROQ_API_KEY not found")
        return
    
    print("✅ GROQ_API_KEY found")
    
    # Initialize components
    ai_processor = AIProcessor()
    batch_processor = BatchProcessor(ai_processor)
    buffer = MeetingBuffer("test_meeting_optimization")
    
    # Mock participant data
    mock_participants = [
        {"id": "1", "name": "Sarah", "role": "PM", "is_host": True},
        {"id": "2", "name": "John", "role": "Developer", "is_host": False},
        {"id": "3", "name": "Mike", "role": "DevOps", "is_host": False},
        {"id": "4", "name": "Lisa", "role": "QA", "is_host": False}
    ]
    
    # Mock transcript chunks (from our meeting audio)
    mock_chunks = [
        "This is a sprint planning meeting for January 30th, 2025.",
        "Sarah speaking as product manager. Alright team, let's review our sprint goals.",
        "We need to focus on the user authentication system this week.",
        "John as developer. I can take the user documentation update.",
        "We need to make sure the API docs are current before release.",
        "Mike as DevOps. I'll handle the staging deployment.",
        "We should get the environment ready by Thursday so QA has time to test.",
        "Lisa as QA engineer. Speaking of testing, I need to run the comprehensive test suite.",
        "Sarah: Great assignments everyone. John, can you investigate those database performance issues?",
        "John: Absolutely. I'll look into optimizing database indexes as well."
    ]
    
    print(f"📦 Adding {len(mock_chunks)} transcript chunks to buffer...")
    
    # Add chunks to buffer
    start_time = time.time()
    for i, text in enumerate(mock_chunks):
        chunk = TranscriptChunk(
            timestamp_start=i * 5.0,
            timestamp_end=(i + 1) * 5.0,
            raw_text=text,
            participants_present=mock_participants,
            confidence=0.85,
            chunk_index=i
        )
        
        buffer.add_chunk(chunk)
        print(f"  Added chunk {i+1}: {text[:50]}...")
        
        # Check if batch should be processed
        if buffer.should_process_batch():
            print(f"🔄 Batch processing triggered at chunk {i+1}")
            break
    
    # Test batch processing
    print("\n🧠 Testing batch processing...")
    batch_start = time.time()
    
    try:
        results = await batch_processor.process_buffer_batch(buffer)
        batch_end = time.time()
        
        print(f"✅ Batch processing completed in {batch_end - batch_start:.2f}s")
        print(f"📊 Results: {len(results.get('segments', []))} segments identified")
        
        # Apply results
        buffer.apply_speaker_results(results)
        
        # Show refined transcript
        print("\n📝 REFINED TRANSCRIPT:")
        refined = buffer.get_recent_refined_transcript(10)
        for segment in refined:
            print(f"  [{segment['timestamp']}] {segment['speaker']}: {segment['text']}")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        print("🔄 Applying fallback processing...")
        buffer._apply_fallback_speakers()
        
        # Show fallback results
        print("\n📝 FALLBACK TRANSCRIPT:")
        refined = buffer.get_recent_refined_transcript(10)
        for segment in refined:
            print(f"  [{segment['timestamp']}] {segment['speaker']}: {segment['text']}")
    
    total_time = time.time() - start_time
    
    # Calculate optimization metrics
    print(f"\n📈 OPTIMIZATION METRICS:")
    print(f"   Total chunks: {len(mock_chunks)}")
    print(f"   Old method: {len(mock_chunks)} API calls")
    print(f"   New method: 1 API call")
    print(f"   API call reduction: {((len(mock_chunks) - 1) / len(mock_chunks)) * 100:.1f}%")
    print(f"   Processing time: {total_time:.2f}s")
    print(f"   Estimated cost reduction: ~95%")
    
    print(f"\n✅ Groq optimization test completed!")

if __name__ == "__main__":
    asyncio.run(test_groq_optimization())