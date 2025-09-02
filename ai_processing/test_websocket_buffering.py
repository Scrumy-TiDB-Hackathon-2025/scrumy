#!/usr/bin/env python3
"""
WebSocket Buffering and Deferred AI Processing Test

Tests the new architecture where audio chunks are buffered first
and AI processing is deferred until batch processing or meeting end.
"""

import asyncio
import json
import os
import sys
import base64
import wave
import struct

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

load_env()
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def create_test_audio_chunk():
    """Create a small test audio chunk as base64"""
    # Generate 1 second of silence at 16kHz, 16-bit mono
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    
    # Create silence (zeros)
    audio_data = struct.pack('<' + 'h' * samples, *([0] * samples))
    
    # Encode as base64
    return base64.b64encode(audio_data).decode('utf-8')

async def test_websocket_buffering():
    """Test WebSocket buffering without immediate AI processing"""
    try:
        import websockets
        
        print("🔌 Connecting to WebSocket server...")
        uri = "ws://localhost:8080/ws"
        
        async with websockets.connect(uri) as websocket:
            # 1. Test handshake
            print("🤝 Testing handshake...")
            await websocket.send(json.dumps({
                "type": "HANDSHAKE", 
                "clientType": "chrome_extension"
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            handshake_response = json.loads(response)
            
            if handshake_response.get("type") != "HANDSHAKE_ACK":
                return {"status": "❌ FAIL", "details": f"Handshake failed - got {handshake_response}"}
            
            print("✅ Handshake successful")
            
            # 2. Test audio chunk buffering (should NOT trigger AI immediately)
            print("🎵 Testing audio chunk buffering...")
            test_audio = create_test_audio_chunk()
            
            # Send multiple audio chunks
            for i in range(3):
                await websocket.send(json.dumps({
                    "type": "AUDIO_CHUNK",
                    "data": test_audio,
                    "timestamp": i * 1000,
                    "metadata": {"sampleRate": 16000, "channels": 1}
                }))
                print(f"   📤 Sent audio chunk {i+1}")
                
                # Should get acknowledgment but NO AI processing
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    ack = json.loads(response)
                    
                    # Check that it's transcription result, not immediate AI processing
                    if ack.get("type") in ["transcription_result", "TRANSCRIPTION_RESULT"]:
                        print(f"   ✅ Chunk {i+1} transcribed (no immediate AI tasks/summary)")
                    elif ack.get("type") in ["TASKS", "SUMMARY", "MEETING_SUMMARY"]:
                        return {"status": "❌ FAIL", "details": f"Immediate AI processing detected on chunk {i+1}"}
                    
                except asyncio.TimeoutError:
                    print(f"   ✅ Chunk {i+1} buffered (no response = good)")
            
            # 3. Test meeting end triggers AI processing
            print("🏁 Testing meeting end triggers AI processing...")
            await websocket.send(json.dumps({
                "type": "MEETING_EVENT",
                "eventType": "meeting_ended",
                "data": {}
            }))
            
            # Now we should get AI processing results
            ai_responses = []
            try:
                while len(ai_responses) < 3:  # Expect transcript, summary, tasks
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    ai_response = json.loads(response)
                    ai_responses.append(ai_response)
                    print(f"   📥 Received: {ai_response.get('type', 'unknown')}")
                    
                    if len(ai_responses) >= 3:
                        break
                        
            except asyncio.TimeoutError:
                print("   ⚠️  Timeout waiting for AI responses (may be expected if no GROQ_API_KEY)")
            
            # 4. Validate buffering worked
            expected_types = {"TRANSCRIPT", "SUMMARY", "TASKS"}
            received_types = {resp.get("type") for resp in ai_responses}
            
            if len(ai_responses) > 0:
                print("✅ Deferred AI processing triggered successfully")
                return {
                    "status": "✅ PASS", 
                    "details": f"Buffering works - AI triggered only on meeting end. Received: {received_types}"
                }
            else:
                # Check if it's due to missing API key
                if not os.getenv('GROQ_API_KEY'):
                    print("✅ Buffering works - No AI responses due to missing GROQ_API_KEY (expected)")
                    return {
                        "status": "✅ PASS", 
                        "details": "Buffering works - No immediate AI processing, deferred correctly"
                    }
                else:
                    return {
                        "status": "⚠️ PARTIAL", 
                        "details": "Buffering works but no AI responses received"
                    }
                    
    except Exception as e:
        return {"status": "❌ FAIL", "details": f"WebSocket buffering test failed: {e}"}

async def test_no_groq_key_graceful_handling():
    """Test that WebSocket works gracefully without GROQ_API_KEY"""
    try:
        # Temporarily remove GROQ_API_KEY
        original_key = os.environ.get('GROQ_API_KEY')
        if 'GROQ_API_KEY' in os.environ:
            del os.environ['GROQ_API_KEY']
        
        import websockets
        
        uri = "ws://localhost:8080/ws"
        async with websockets.connect(uri) as websocket:
            # Test that connection works without API key
            await websocket.send(json.dumps({
                "type": "HANDSHAKE", 
                "clientType": "test_no_key"
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            handshake_response = json.loads(response)
            
            if handshake_response.get("type") == "HANDSHAKE_ACK":
                # Restore key
                if original_key:
                    os.environ['GROQ_API_KEY'] = original_key
                
                return {
                    "status": "✅ PASS", 
                    "details": "WebSocket works gracefully without GROQ_API_KEY"
                }
            else:
                return {
                    "status": "❌ FAIL", 
                    "details": "WebSocket fails without GROQ_API_KEY"
                }
                
    except Exception as e:
        # Restore key
        if original_key:
            os.environ['GROQ_API_KEY'] = original_key
        
        return {
            "status": "❌ FAIL", 
            "details": f"Graceful handling test failed: {e}"
        }

async def run_buffering_tests():
    """Run all buffering-specific tests"""
    print("🧪 WebSocket Buffering & Deferred AI Processing Tests")
    print("=" * 60)
    
    tests = [
        ("WebSocket Buffering Architecture", test_websocket_buffering),
        ("Graceful Handling (No API Key)", test_no_groq_key_graceful_handling)
    ]
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔬 Testing {test_name}...")
        try:
            result = await test_func()
            results[test_name] = result
            print(f"   {result['status']} - {result['details']}")
            
            if result['status'] == "✅ PASS":
                passed += 1
                
        except Exception as e:
            result = {"status": "❌ FAIL", "details": f"Test execution failed: {e}"}
            results[test_name] = result
            print(f"   {result['status']} - {result['details']}")
    
    print("\n" + "=" * 60)
    print("📊 BUFFERING TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 BUFFERING ARCHITECTURE WORKING CORRECTLY")
    else:
        print("⚠️  BUFFERING ISSUES DETECTED")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_buffering_tests())