#!/usr/bin/env python3
"""
Full Audio-to-Tasks Pipeline Test
Tests the complete workflow: Audio File → Transcription → AI Processing → Task Extraction
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5167"
AUDIO_FILE = "temp_jfk.mp3"  # Using existing test audio file

def test_full_pipeline():
    """Test the complete audio-to-tasks pipeline"""
    
    print("🎯 Testing Full Audio-to-Tasks Pipeline")
    print("=" * 50)
    
    # Check if audio file exists
    audio_path = Path(AUDIO_FILE)
    if not audio_path.exists():
        print(f"❌ Audio file not found: {AUDIO_FILE}")
        return False
    
    print(f"📁 Using audio file: {AUDIO_FILE}")
    print(f"📏 File size: {audio_path.stat().st_size} bytes")
    
    try:
        # Step 1: Upload and transcribe audio
        print("\n🎤 Step 1: Transcribing audio...")
        
        with open(AUDIO_FILE, 'rb') as f:
            files = {'file': (AUDIO_FILE, f, 'audio/mpeg')}
            response = requests.post(f"{BASE_URL}/transcribe", files=files, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ Transcription failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        transcription_data = response.json()
        transcript = transcription_data.get('transcript', '')
        
        print(f"✅ Transcription successful!")
        print(f"📝 Transcript length: {len(transcript)} characters")
        print(f"📄 Transcript preview: {transcript[:200]}...")
        
        # Step 2: Process meeting (AI analysis)
        print("\n🤖 Step 2: AI Processing...")
        
        meeting_data = {
            "text": transcript,
            "model": "groq",
            "model_name": "llama-3.1-70b-versatile",
            "meeting_id": "pipeline-test-001"
        }
        
        response = requests.post(f"{BASE_URL}/process-complete-meeting", json=meeting_data, timeout=60)
        
        if response.status_code != 200:
            print(f"❌ AI processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        processing_result = response.json()
        
        print(f"✅ AI Processing successful!")
        print(f"📊 Summary length: {len(processing_result.get('summary', ''))} characters")
        print(f"🎯 Key points: {len(processing_result.get('key_points', []))}")
        print(f"📋 Tasks found: {len(processing_result.get('tasks', []))}")
        
        # Step 3: Extract tasks specifically
        print("\n📋 Step 3: Task Extraction...")
        
        task_data = {"transcript": transcript}
        response = requests.post(f"{BASE_URL}/extract-tasks", json=task_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Task extraction failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        task_result = response.json()
        tasks = task_result.get('tasks', [])
        
        print(f"✅ Task extraction successful!")
        print(f"📝 Tasks extracted: {len(tasks)}")
        
        # Display results
        print("\n" + "=" * 50)
        print("🎉 PIPELINE RESULTS")
        print("=" * 50)
        
        print(f"\n📄 TRANSCRIPT:")
        print(f"{transcript}")
        
        print(f"\n📊 SUMMARY:")
        print(f"{processing_result.get('summary', 'No summary generated')}")
        
        print(f"\n🎯 KEY POINTS:")
        for i, point in enumerate(processing_result.get('key_points', []), 1):
            print(f"{i}. {point}")
        
        print(f"\n📋 TASKS FROM PROCESSING:")
        for i, task in enumerate(processing_result.get('tasks', []), 1):
            print(f"{i}. {task}")
        
        print(f"\n📋 TASKS FROM EXTRACTION:")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task}")
        
        # Performance metrics
        print(f"\n⚡ PERFORMANCE:")
        print(f"Audio file: {AUDIO_FILE}")
        print(f"File size: {audio_path.stat().st_size} bytes")
        print(f"Transcript length: {len(transcript)} characters")
        print(f"Tasks found (processing): {len(processing_result.get('tasks', []))}")
        print(f"Tasks found (extraction): {len(tasks)}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Full Audio-to-Tasks Pipeline Test")
    print("=" * 50)
    
    # Check backend status
    if not check_backend_status():
        print("❌ Backend not running! Please start with:")
        print("   ./clean_start_backend.sh")
        exit(1)
    
    print("✅ Backend is running")
    
    # Run the test
    success = test_full_pipeline()
    
    if success:
        print("\n🎉 Full pipeline test completed successfully!")
    else:
        print("\n❌ Pipeline test failed!")
        exit(1)