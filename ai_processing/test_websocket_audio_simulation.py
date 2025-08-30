#!/usr/bin/env python3
"""
WebSocket Audio Chunk Simulation

Simulates Chrome extension sending audio chunks to AI processing WebSocket server
Uses the recorded meeting audio file and sends it in chunks
"""

import asyncio
import websockets
import json
import base64
import wave
import os
import time
from pathlib import Path

# Audio file path
AUDIO_FILE = "tests/data/meeting-test.wav"
WEBSOCKET_URL = "ws://localhost:8080/ws"

# Mock participant data
MOCK_PARTICIPANTS = [
    {"id": "1", "name": "Sarah", "status": "active", "is_host": True},
    {"id": "2", "name": "John", "status": "active", "is_host": False},
    {"id": "3", "name": "Mike", "status": "active", "is_host": False},
    {"id": "4", "name": "Lisa", "status": "active", "is_host": False}
]

async def simulate_audio_chunks():
    """Simulate Chrome extension sending audio chunks"""
    
    print("🎵 WEBSOCKET AUDIO CHUNK SIMULATION")
    print("=" * 50)
    
    # Check if audio file exists
    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Audio file not found: {AUDIO_FILE}")
        return
    
    print(f"📁 Using audio file: {AUDIO_FILE}")
    
    try:
        # Connect to WebSocket server
        print(f"🔌 Connecting to {WEBSOCKET_URL}...")
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Send handshake
            handshake = {
                "type": "HANDSHAKE",
                "clientType": "chrome-extension",
                "version": "1.0",
                "capabilities": ["audio-capture", "meeting-detection"]
            }
            await websocket.send(json.dumps(handshake))
            print("🤝 Handshake sent")
            
            # Wait for handshake response
            response = await websocket.recv()
            handshake_response = json.loads(response)
            print(f"✅ Handshake acknowledged: {handshake_response.get('status')}")
            
            # Read and chunk the audio file into smaller pieces
            print("📊 Processing audio file...")
            audio_chunks = read_audio_in_chunks(AUDIO_FILE, chunk_duration=5.0)  # 5-second chunks
            print(f"📦 Created {len(audio_chunks)} audio chunks (5 seconds each)")
            
            # Send audio chunks
            for i, chunk_data in enumerate(audio_chunks):
                print(f"📤 Sending chunk {i+1}/{len(audio_chunks)} ({len(chunk_data)} bytes)")
                
                # Encode chunk as base64
                chunk_b64 = base64.b64encode(chunk_data).decode('utf-8')
                
                # Create enhanced audio chunk message
                message = {
                    "type": "AUDIO_CHUNK_ENHANCED",
                    "data": chunk_b64,
                    "timestamp": int(time.time() * 1000),
                    "platform": "meet.google.com",
                    "meetingUrl": "https://meet.google.com/test-meeting-123",
                    "participants": MOCK_PARTICIPANTS,
                    "participant_count": len(MOCK_PARTICIPANTS),
                    "metadata": {
                        "chunk_size": len(chunk_data),
                        "sample_rate": 16000,
                        "channels": 1,
                        "format": "wav",
                        "chunk_index": i
                    }
                }
                
                # Send chunk
                await websocket.send(json.dumps(message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    result = json.loads(response)
                    
                    if result.get('type') == 'TRANSCRIPTION_RESULT':
                        transcript = result.get('data', {}).get('text', '')
                        speaker = result.get('data', {}).get('speaker', 'Unknown')
                        confidence = result.get('data', {}).get('confidence', 0.0)
                        
                        if transcript.strip():  # Only show non-empty transcripts
                            print(f"  📝 Transcript: {transcript}")
                            print(f"  👤 Speaker: {speaker}")
                            print(f"  🎯 Confidence: {confidence:.2f}")
                        else:
                            print(f"  🔇 Silent chunk (no speech detected)")
                    elif result.get('type') == 'ERROR':
                        error_msg = result.get('error', 'Unknown error')
                        print(f"  ❌ Error: {error_msg}")
                    else:
                        print(f"  📨 Response: {result.get('type')}")
                        
                except asyncio.TimeoutError:
                    print("  ⏰ No response received (timeout)")
                except Exception as e:
                    print(f"  ❌ Response error: {e}")
                
                # Delay between chunks to simulate real-time
                await asyncio.sleep(1.0)  # 1 second delay
            
            # Send meeting end event
            end_event = {
                "type": "MEETING_EVENT",
                "eventType": "meeting_ended",
                "timestamp": int(time.time() * 1000),
                "data": {
                    "meeting_duration": len(audio_chunks) * 2,
                    "total_chunks": len(audio_chunks)
                }
            }
            await websocket.send(json.dumps(end_event))
            print("🏁 Meeting end event sent")
            
            # Wait for final summary
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                result = json.loads(response)
                
                if result.get('type') == 'MEETING_SUMMARY':
                    summary_data = result.get('data', {})
                    tasks = summary_data.get('tasks', {}).get('tasks', [])
                    print(f"\n📋 MEETING SUMMARY RECEIVED:")
                    print(f"   Tasks found: {len(tasks)}")
                    for i, task in enumerate(tasks[:3], 1):
                        print(f"   {i}. {task.get('title', 'No title')}")
                else:
                    print(f"📨 Final response: {result.get('type')}")
                    
            except asyncio.TimeoutError:
                print("⏰ No summary received (timeout)")
            
            print("\n✅ Simulation completed successfully!")
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")

def read_audio_in_chunks(audio_file, chunk_duration=2.0):
    """Read audio file and split into chunks"""
    chunks = []
    
    try:
        with wave.open(audio_file, 'rb') as wav_file:
            frames_per_second = wav_file.getframerate()
            frames_per_chunk = int(frames_per_second * chunk_duration)
            
            while True:
                frames = wav_file.readframes(frames_per_chunk)
                if not frames:
                    break
                chunks.append(frames)
                
        return chunks
        
    except Exception as e:
        print(f"Error reading audio file: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(simulate_audio_chunks())