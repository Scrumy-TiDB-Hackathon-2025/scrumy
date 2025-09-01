#!/usr/bin/env python3
"""
Chrome Extension Readiness Analysis

Tests all components needed for Chrome extension integration to determine success rate.
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime

# Load environment
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

    local_env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(local_env_path):
        with open(local_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    os.environ[key] = value

load_env()
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_websocket_server():
    """Test WebSocket server availability"""
    try:
        import websockets
        uri = "ws://localhost:8080/ws"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"type": "HANDSHAKE", "clientType": "test"}))
            response = await websocket.recv()
            return {"status": "✅ PASS", "details": "WebSocket server responding"}
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"WebSocket server not available: {e}"}

async def test_whisper_transcription():
    """Test Whisper transcription capability"""
    try:
        from app.ai_processor import AIProcessor
        audio_file = "tests/data/meeting-test.wav"
        
        if not os.path.exists(audio_file):
            return {"status": "⚠️ SKIP", "details": "Test audio file not found"}
        
        # Test whisper executable
        whisper_executable = os.getenv('WHISPER_EXECUTABLE', './whisper.cpp/build/bin/whisper-cli')
        if not os.path.exists(whisper_executable):
            return {"status": "❌ FAIL", "details": "Whisper executable not found"}
        
        return {"status": "✅ PASS", "details": "Whisper transcription ready"}
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"Whisper test failed: {e}"}

async def test_groq_api():
    """Test Groq API connectivity"""
    try:
        from app.ai_processor import AIProcessor
        ai_processor = AIProcessor()
        
        response = await ai_processor.call_ollama("Test message", "You are a test assistant. Respond with 'OK'.")
        
        if response and "ok" in response.lower():
            return {"status": "✅ PASS", "details": "Groq API responding correctly"}
        else:
            return {"status": "⚠️ PARTIAL", "details": f"Groq API responding but unexpected response: {response[:50]}"}
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"Groq API failed: {e}"}

async def test_task_extraction():
    """Test task extraction functionality"""
    try:
        from app.task_extractor import TaskExtractor
        from app.ai_processor import AIProcessor
        
        ai_processor = AIProcessor()
        task_extractor = TaskExtractor(ai_processor)
        
        test_transcript = "John will update the documentation by Friday. Sarah needs to deploy the staging environment."
        
        result = await task_extractor.extract_comprehensive_tasks(test_transcript, {"participants": ["John", "Sarah"]})
        
        if result and result.get("tasks") and len(result["tasks"]) > 0:
            return {"status": "✅ PASS", "details": f"Extracted {len(result['tasks'])} tasks successfully"}
        else:
            return {"status": "❌ FAIL", "details": "No tasks extracted from test transcript"}
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"Task extraction failed: {e}"}

async def test_integration_systems():
    """Test integration with external systems"""
    try:
        from app.integration_bridge import create_integration_bridge
        
        bridge = create_integration_bridge()
        
        if not bridge.enabled:
            return {"status": "⚠️ PARTIAL", "details": "Integration bridge disabled or not configured"}
        
        # Test with mock task
        test_tasks = [{"title": "Test task", "description": "Test description", "assignee": "Test", "priority": "medium"}]
        
        result = await bridge.create_tasks_from_ai_results(test_tasks, {"meeting_id": "test"})
        
        if result.get("tasks_created", 0) > 0:
            return {"status": "✅ PASS", "details": f"Created {result['tasks_created']} tasks in {len(result.get('successful_integrations', []))} platforms"}
        else:
            return {"status": "❌ FAIL", "details": "No tasks created in external systems"}
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"Integration test failed: {e}"}

async def test_meeting_buffer():
    """Test meeting buffer and optimization"""
    try:
        from app.meeting_buffer import MeetingBuffer, TranscriptChunk
        
        buffer = MeetingBuffer("test_meeting")
        
        # Add test chunks
        for i in range(5):
            chunk = TranscriptChunk(
                timestamp_start=i * 5.0,
                timestamp_end=(i + 1) * 5.0,
                raw_text=f"Test transcript chunk {i}",
                participants_present=[],
                confidence=0.9,
                chunk_index=i
            )
            buffer.add_chunk(chunk)
        
        if len(buffer.chunks) == 5:
            return {"status": "✅ PASS", "details": "Meeting buffer working correctly"}
        else:
            return {"status": "❌ FAIL", "details": "Meeting buffer not storing chunks correctly"}
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"Meeting buffer test failed: {e}"}

async def run_readiness_analysis():
    """Run complete readiness analysis"""
    print("🔍 Chrome Extension Readiness Analysis")
    print("=" * 50)
    
    tests = [
        ("WebSocket Server", test_websocket_server),
        ("Whisper Transcription", test_whisper_transcription),
        ("Groq API", test_groq_api),
        ("Task Extraction", test_task_extraction),
        ("Integration Systems", test_integration_systems),
        ("Meeting Buffer", test_meeting_buffer)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        try:
            result = await test_func()
            results[test_name] = result
            print(f"   {result['status']} - {result['details']}")
            
            if result['status'] == "✅ PASS":
                passed_tests += 1
        except Exception as e:
            result = {"status": "❌ FAIL", "details": f"Test execution failed: {e}"}
            results[test_name] = result
            print(f"   {result['status']} - {result['details']}")
    
    # Calculate success rate
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 50)
    print("📊 READINESS SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 READY FOR CHROME EXTENSION TESTING")
        readiness = "READY"
    elif success_rate >= 60:
        print("⚠️  PARTIALLY READY - Some issues need attention")
        readiness = "PARTIAL"
    else:
        print("❌ NOT READY - Critical issues must be fixed")
        readiness = "NOT_READY"
    
    print(f"\n📋 Recommendations:")
    for test_name, result in results.items():
        if result['status'] == "❌ FAIL":
            print(f"  🔧 Fix: {test_name}")
        elif result['status'] == "⚠️ PARTIAL" or result['status'] == "⚠️ SKIP":
            print(f"  ⚠️  Check: {test_name}")
    
    return {
        "success_rate": success_rate,
        "readiness": readiness,
        "results": results,
        "passed_tests": passed_tests,
        "total_tests": total_tests
    }

if __name__ == "__main__":
    asyncio.run(run_readiness_analysis())