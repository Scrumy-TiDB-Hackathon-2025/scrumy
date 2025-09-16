#!/usr/bin/env python3
"""
Final Whisper server test - comprehensive validation
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_whisper_complete():
    """Complete test of Whisper functionality"""
    
    print("🎤 Final Whisper Server Test")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8178"
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health: {health_data}")
            if not health_data.get("whisper_available"):
                print("   ❌ Whisper not available")
                return False
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Models endpoint
    print("2. Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            print(f"   ✅ Models: {models_data}")
        else:
            print(f"   ❌ Models endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Models endpoint error: {e}")
        return False
    
    # Test 3: Transcription
    print("3. Testing transcription...")
    sample_file = Path("whisper.cpp/samples/jfk.mp3")
    
    if not sample_file.exists():
        print(f"   ❌ Sample file not found: {sample_file}")
        return False
    
    try:
        with open(sample_file, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{base_url}/transcribe", files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                transcript = result.get("transcript", "")
                print(f"   ✅ Transcription successful!")
                print(f"   📝 Transcript: {transcript[:100]}...")
                
                # Verify it contains expected content
                if "fellow Americans" in transcript and "ask not what" in transcript:
                    print("   ✅ Transcript content verified!")
                    return True
                else:
                    print("   ⚠️  Transcript content unexpected")
                    return False
            else:
                print(f"   ❌ Transcription failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Transcription error: {e}")
        return False

def main():
    """Main test function"""
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:8178/health", timeout=2)
        server_running = response.status_code == 200
    except:
        server_running = False
    
    if not server_running:
        print("❌ Whisper server not running on port 8178")
        print("💡 Start it with: python simple_whisper_server.py")
        return False
    
    success = test_whisper_complete()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED! Whisper server is fully functional!")
        print("\n📋 Summary:")
        print("   ✅ Health endpoint working")
        print("   ✅ Models endpoint working") 
        print("   ✅ Transcription working")
        print("   ✅ Audio processing successful")
        print("\n🚀 Your Whisper server is ready for integration!")
        return True
    else:
        print("💥 Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)