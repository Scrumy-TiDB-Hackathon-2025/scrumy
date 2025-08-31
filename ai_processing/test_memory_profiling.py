#!/usr/bin/env python3
"""
Memory Profiling Test for MeetingBuffer Scalability

Tests memory usage patterns for concurrent meetings to assess scalability.
"""

import asyncio
import psutil
import os
import sys
import gc
from datetime import datetime
from typing import List, Dict

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.meeting_buffer import MeetingBuffer, TranscriptChunk

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
        'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
        'percent': process.memory_percent(),
        'available_mb': psutil.virtual_memory().available / 1024 / 1024
    }

def create_test_meeting_buffer(meeting_id: str, chunk_count: int = 100) -> MeetingBuffer:
    """Create a test meeting buffer with simulated data"""
    buffer = MeetingBuffer(meeting_id)
    
    # Simulate participants
    participants = [
        {"id": f"p{i}", "name": f"User{i}", "role": "participant", "is_host": i==0}
        for i in range(4)
    ]
    
    # Add transcript chunks
    for i in range(chunk_count):
        chunk = TranscriptChunk(
            timestamp_start=i * 5.0,
            timestamp_end=(i + 1) * 5.0,
            raw_text=f"This is test transcript chunk {i} with some content to simulate real meeting data.",
            participants_present=participants,
            confidence=0.9,
            chunk_index=i
        )
        buffer.add_chunk(chunk)
    
    return buffer

async def test_single_meeting_memory():
    """Test memory usage for a single meeting"""
    print("🧪 Testing single meeting memory usage...")
    
    initial_memory = get_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")
    
    # Create meeting buffer
    buffer = create_test_meeting_buffer("test_meeting_1", chunk_count=360)  # 1 hour meeting
    
    after_creation = get_memory_usage()
    memory_per_meeting = after_creation['rss_mb'] - initial_memory['rss_mb']
    
    print(f"After creating meeting: {after_creation['rss_mb']:.2f} MB")
    print(f"Memory per meeting: {memory_per_meeting:.2f} MB")
    
    # Cleanup
    del buffer
    gc.collect()
    
    after_cleanup = get_memory_usage()
    print(f"After cleanup: {after_cleanup['rss_mb']:.2f} MB")
    
    return memory_per_meeting

async def test_concurrent_meetings_memory(meeting_count: int = 10):
    """Test memory usage for concurrent meetings"""
    print(f"\n🧪 Testing {meeting_count} concurrent meetings...")
    
    initial_memory = get_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")
    
    buffers = []
    memory_snapshots = []
    
    # Create meetings incrementally
    for i in range(meeting_count):
        buffer = create_test_meeting_buffer(f"concurrent_meeting_{i}", chunk_count=100)
        buffers.append(buffer)
        
        current_memory = get_memory_usage()
        memory_snapshots.append(current_memory['rss_mb'])
        
        if i % 5 == 0:
            print(f"  Meeting {i+1}: {current_memory['rss_mb']:.2f} MB")
    
    final_memory = get_memory_usage()
    total_memory_used = final_memory['rss_mb'] - initial_memory['rss_mb']
    memory_per_meeting = total_memory_used / meeting_count
    
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Total memory used: {total_memory_used:.2f} MB")
    print(f"Average memory per meeting: {memory_per_meeting:.2f} MB")
    
    # Test memory growth pattern
    memory_growth = [snapshots - initial_memory['rss_mb'] for snapshots in memory_snapshots]
    linear_growth = all(
        abs(memory_growth[i] - (memory_per_meeting * (i + 1))) < 0.5 
        for i in range(len(memory_growth))
    )
    
    print(f"Memory growth pattern: {'Linear' if linear_growth else 'Non-linear'}")
    
    # Cleanup
    for buffer in buffers:
        del buffer
    gc.collect()
    
    after_cleanup = get_memory_usage()
    print(f"After cleanup: {after_cleanup['rss_mb']:.2f} MB")
    
    return {
        'total_memory_mb': total_memory_used,
        'memory_per_meeting_mb': memory_per_meeting,
        'linear_growth': linear_growth,
        'cleanup_effective': after_cleanup['rss_mb'] < final_memory['rss_mb'] * 0.9
    }

async def test_memory_leak_detection(duration_minutes: int = 5):
    """Test for memory leaks over time"""
    print(f"\n🧪 Testing memory leaks over {duration_minutes} minutes...")
    
    initial_memory = get_memory_usage()
    print(f"Initial memory: {initial_memory['rss_mb']:.2f} MB")
    
    meeting_counter = 0
    start_time = datetime.now()
    memory_samples = []
    
    while (datetime.now() - start_time).total_seconds() < duration_minutes * 60:
        # Create and destroy meetings continuously
        buffer = create_test_meeting_buffer(f"leak_test_{meeting_counter}", chunk_count=50)
        meeting_counter += 1
        
        # Sample memory every 10 meetings
        if meeting_counter % 10 == 0:
            current_memory = get_memory_usage()
            memory_samples.append(current_memory['rss_mb'])
            print(f"  Meeting {meeting_counter}: {current_memory['rss_mb']:.2f} MB")
        
        del buffer
        
        # Force garbage collection every 20 meetings
        if meeting_counter % 20 == 0:
            gc.collect()
        
        await asyncio.sleep(0.1)  # Small delay to simulate real usage
    
    final_memory = get_memory_usage()
    
    # Analyze memory trend
    if len(memory_samples) > 2:
        memory_trend = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
        leak_detected = memory_trend > 0.1  # More than 0.1 MB growth per sample
    else:
        memory_trend = 0
        leak_detected = False
    
    print(f"Final memory: {final_memory['rss_mb']:.2f} MB")
    print(f"Total meetings processed: {meeting_counter}")
    print(f"Memory trend: {memory_trend:.3f} MB per sample")
    print(f"Memory leak detected: {'Yes' if leak_detected else 'No'}")
    
    return {
        'meetings_processed': meeting_counter,
        'memory_trend_mb': memory_trend,
        'leak_detected': leak_detected,
        'final_memory_mb': final_memory['rss_mb']
    }

async def estimate_production_capacity():
    """Estimate production capacity based on memory tests"""
    print("\n📊 Estimating production capacity...")
    
    # Run single meeting test
    single_meeting_memory = await test_single_meeting_memory()
    
    # Run concurrent meetings test
    concurrent_results = await test_concurrent_meetings_memory(10)
    
    # Calculate capacity estimates
    memory_per_meeting = max(single_meeting_memory, concurrent_results['memory_per_meeting_mb'])
    
    # EC2 instance capacities (assuming 80% memory utilization)
    instance_capacities = {
        't3.medium (4GB)': int((4 * 1024 * 0.8) / memory_per_meeting),
        'c5.large (4GB)': int((4 * 1024 * 0.8) / memory_per_meeting),
        'c5.xlarge (8GB)': int((8 * 1024 * 0.8) / memory_per_meeting),
        'c5.2xlarge (16GB)': int((16 * 1024 * 0.8) / memory_per_meeting)
    }
    
    print(f"\n📈 Production Capacity Estimates:")
    print(f"Memory per meeting: {memory_per_meeting:.2f} MB")
    
    for instance, capacity in instance_capacities.items():
        print(f"  {instance}: ~{capacity} concurrent meetings")
    
    return {
        'memory_per_meeting_mb': memory_per_meeting,
        'instance_capacities': instance_capacities
    }

async def main():
    """Run all memory profiling tests"""
    print("🚀 Starting Memory Profiling Tests")
    print("=" * 50)
    
    # Test 1: Single meeting
    single_result = await test_single_meeting_memory()
    
    # Test 2: Concurrent meetings
    concurrent_result = await test_concurrent_meetings_memory(10)
    
    # Test 3: Memory leak detection (short duration for demo)
    leak_result = await test_memory_leak_detection(1)
    
    # Test 4: Production capacity estimation
    capacity_result = await estimate_production_capacity()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 MEMORY PROFILING SUMMARY")
    print("=" * 50)
    print(f"Single meeting memory: {single_result:.2f} MB")
    print(f"Concurrent meetings memory: {concurrent_result['memory_per_meeting_mb']:.2f} MB")
    print(f"Memory growth pattern: {'✅ Linear' if concurrent_result['linear_growth'] else '❌ Non-linear'}")
    print(f"Memory cleanup: {'✅ Effective' if concurrent_result['cleanup_effective'] else '❌ Ineffective'}")
    print(f"Memory leak detected: {'❌ Yes' if leak_result['leak_detected'] else '✅ No'}")
    
    print(f"\n🏭 Production Recommendations:")
    print(f"  - Memory per meeting: {capacity_result['memory_per_meeting_mb']:.2f} MB")
    print(f"  - Recommended instance: c5.large (4GB) for ~{capacity_result['instance_capacities']['c5.large (4GB)']} meetings")
    print(f"  - Enable debug logging: Only in development")
    print(f"  - Session cleanup: Every 2 hours")

if __name__ == "__main__":
    asyncio.run(main())