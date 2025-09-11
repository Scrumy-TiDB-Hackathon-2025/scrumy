#!/usr/bin/env python3
"""
Quick WebSocket test - just check connection and send one small audio chunk
"""

import asyncio
import websockets
import json
import base64
import os
from datetime import datetime

async def quick_test():
    """Test with real test-meeting.wav file"""
    
    wav_file_path = "../test-meeting.wav"
    
    if not os.path.exists(wav_file_path):
        print(f"❌ Audio file not found: {wav_file_path}")
        return
    
    print(f"🎵 Loading {wav_file_path}...")
    
    # Read WAV file
    import wave
    with wave.open(wav_file_path, 'rb') as wav_file:
        frames = wav_file.readframes(-1)
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
    
    print(f"📊 Audio: {len(frames)} bytes, {sample_rate}Hz, {channels}ch")
    
    try:
        # Connect to WebSocket server
        uri = "ws://localhost:8080/ws"
        
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send handshake
            handshake = {"type": "HANDSHAKE", "clientVersion": "1.0.0"}
            await websocket.send(json.dumps(handshake))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            result = json.loads(response)
            print(f"📨 Handshake: {result.get('type')}")
            
            # Send audio in chunks
            chunk_size = 8192  # 8KB chunks
            total_chunks = len(frames) // chunk_size + (1 if len(frames) % chunk_size else 0)
            
            print(f"📦 Sending {min(5, total_chunks)} audio chunks (first 5 only)...")
            
            for i in range(0, min(len(frames), chunk_size * 5), chunk_size):  # Send first 5 chunks only
                chunk = frames[i:i + chunk_size]
                chunk_base64 = base64.b64encode(chunk).decode('utf-8')
                
                audio_message = {
                    "type": "AUDIO_CHUNK_ENHANCED",
                    "data": chunk_base64,
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "platform": "test",
                    "meetingUrl": "test://test-meeting-wav",
                    "participants": [{"id": "test-1", "name": "Test User", "status": "active", "is_host": True}],
                    "participant_count": 1,
                    "metadata": {"chunk_size": len(chunk), "sample_rate": sample_rate, "channels": channels}
                }
                
                await websocket.send(json.dumps(audio_message))
                chunk_num = (i // chunk_size) + 1
                print(f"📤 Sent chunk {chunk_num} ({len(chunk)} bytes)")
                
                # Check for responses
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    result = json.loads(response)
                    msg_type = result.get('type')
                    
                    if msg_type == 'TRANSCRIPTION_RESULT':
                        text = result.get('data', {}).get('text', '')
                        if text and text not in ['[BLANK_AUDIO]', '[SILENCE_DETECTED]']:
                            print(f"📝 Transcription: '{text}'")
                    elif msg_type == 'SESSION_REGISTERED':
                        print(f"✅ Session registered")
                        
                except asyncio.TimeoutError:
                    pass
                
                await asyncio.sleep(0.1)  # Small delay
            
            # Send meeting end
            end_message = {
                "type": "MEETING_EVENT",
                "eventType": "meeting_ended",
                "data": {"bufferFlushComplete": True}
            }
            await websocket.send(json.dumps(end_message))
            print("🏁 Sent meeting end")
            
            # Wait for final processing
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                result = json.loads(response)
                print(f"📨 Final: {result.get('type')}")
            except asyncio.TimeoutError:
                print("⏰ No final response")
            
            print("✅ Test completed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def check_db_quick():
    """Quick database check"""
    print("\n🔍 Quick database check...")
    
    import sys
    sys.path.append(os.path.dirname(__file__))
    from app.sqlite_database import SQLiteDatabase
    
    db = SQLiteDatabase("meeting_minutes.db")
    meetings = await db.get_all_meetings()
    
    print(f"📋 Total meetings: {len(meetings)}")
    
    # Check for test meetings
    test_meetings = [m for m in meetings if 'test' in m['id'].lower()]
    print(f"🧪 Test meetings: {len(test_meetings)}")
    
    if test_meetings:
        latest = test_meetings[-1]
        print(f"   Latest: {latest['id']} - {latest['title']}")
        
        # Check transcript
        transcript_data = await db.get_meeting_transcript(latest['id'])
        if transcript_data:
            chunks = len(transcript_data.get('transcript_chunks', []))
            print(f"   Transcript chunks: {chunks}")

if __name__ == "__main__":
    async def run():
        await quick_test()
        await check_db_quick()
    
    asyncio.run(run())