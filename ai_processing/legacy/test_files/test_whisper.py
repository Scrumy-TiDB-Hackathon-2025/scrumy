#!/usr/bin/env python3
"""
Test script for Whisper server
"""

import requests
import json
from pathlib import Path

def test_whisper_server():
    """Test the Whisper transcription server"""
    
    # Server URL
    base_url = "http://127.0.0.1:8178"
    
    print("🧪 Testing Whisper Server...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test models endpoint
    try:
        response = requests.get(f"{base_url}/models")
        if response.status_code == 200:
            models_data = response.json()
            print("✅ Models endpoint working")
            print(f"   Available models: {models_data['models']}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
        return False
    
    # Test transcription with sample file
    sample_file = Path("whisper.cpp/samples/jfk.mp3")
    if sample_file.exists():
        print(f"\n🎤 Testing transcription with {sample_file}")
        
        try:
            with open(sample_file, "rb") as f:
                files = {"file": f}
                data = {
                    "language": "en",
                    "model": "base.en"
                }
                
                response = requests.post(f"{base_url}/transcribe", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Transcription successful!")
                    print(f"   Transcript: {result['transcript']}")
                    print(f"   Processing time: {result.get('processing_time', 'N/A')} seconds")
                    return True
                else:
                    print(f"❌ Transcription failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return False
    else:
        print(f"⚠️  Sample file not found: {sample_file}")
        print("   Skipping transcription test")
        return True

if __name__ == "__main__":
    success = test_whisper_server()
    if success:
        print("\n🎉 Whisper server is working correctly!")
    else:
        print("\n💥 Whisper server test failed!")
        exit(1)