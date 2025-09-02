#!/usr/bin/env python3
"""
Direct test of MeetingBuffer logger initialization
Tests the exact code path that's failing on EC2
"""

import os
import sys

# Load environment like EC2
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared', '.tidb.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_meeting_buffer_initialization():
    """Test MeetingBuffer initialization directly"""
    try:
        print("🧪 Testing MeetingBuffer initialization...")
        
        from app.meeting_buffer import MeetingBuffer
        
        # Create buffer like WebSocket server does
        meeting_id = "test_meeting_123"
        buffer = MeetingBuffer(meeting_id)
        
        print(f"✅ MeetingBuffer created: {buffer}")
        print(f"📝 Logger type: {type(buffer.logger)}")
        print(f"📝 Logger value: {buffer.logger}")
        
        if buffer.logger is None:
            print("❌ FAIL: Logger is None")
            return False
        
        # Test the exact method that's failing
        test_data = {
            "audio_data": "test_data",
            "participant": "Test User",
            "chunk_id": 1,
            "meeting_id": meeting_id
        }
        
        buffer.logger.log_audio_chunk(test_data)
        print("✅ log_audio_chunk() works")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test all imports that MeetingBuffer needs"""
    try:
        print("\n🧪 Testing imports...")
        
        print("  - Importing pipeline_logger...")
        from app.pipeline_logger import PipelineLogger
        print("  ✅ PipelineLogger imported")
        
        print("  - Testing PipelineLogger creation...")
        logger = PipelineLogger("test_session")
        print(f"  ✅ PipelineLogger created: {logger}")
        
        print("  - Trying debug_logger import...")
        try:
            from app.debug_logger import debug_manager
            print("  ✅ debug_manager imported")
        except ImportError as e:
            print(f"  ⚠️  debug_manager not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Direct MeetingBuffer Logger Test")
    print("=" * 50)
    
    imports_ok = test_imports()
    buffer_ok = test_meeting_buffer_initialization()
    
    print("\n" + "=" * 50)
    if imports_ok and buffer_ok:
        print("🎉 ALL TESTS PASSED - Logger should work on EC2")
    else:
        print("❌ TESTS FAILED - Logger initialization has issues")