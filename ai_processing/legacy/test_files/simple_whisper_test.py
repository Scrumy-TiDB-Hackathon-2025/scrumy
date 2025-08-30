#!/usr/bin/env python3
"""
Simple Whisper server test - quick validation
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def test_whisper_direct():
    """Test whisper.cpp directly without server"""
    print("🔧 Testing whisper.cpp directly...")
    
    whisper_exe = Path("whisper.cpp/build/bin/whisper-cli")
    model_file = Path("whisper.cpp/models/ggml-base.en.bin")
    sample_file = Path("whisper.cpp/samples/jfk.mp3")
    
    if not whisper_exe.exists():
        print(f"❌ Whisper executable not found: {whisper_exe}")
        return False
    
    if not model_file.exists():
        print(f"❌ Model file not found: {model_file}")
        return False
    
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return False
    
    try:
        cmd = [
            str(whisper_exe),
            "-m", str(model_file),
            "-f", str(sample_file),
            "--language", "en",
            "--threads", "2"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Direct whisper.cpp test passed!")
            print(f"Output: {result.stdout[:200]}...")
            return True
        else:
            print(f"❌ Direct whisper.cpp test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Direct whisper.cpp test timed out")
        return False
    except Exception as e:
        print(f"❌ Direct whisper.cpp test error: {e}")
        return False

def test_server_quick():
    """Quick server test with timeout"""
    print("\n🚀 Testing Whisper server...")
    
    # Start server in background
    try:
        server_process = subprocess.Popen([
            sys.executable, "start_whisper_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Quick health check with timeout
        try:
            response = requests.get("http://127.0.0.1:8178/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server health check passed!")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Server connection failed: {e}")
            return False
        finally:
            # Always cleanup
            server_process.terminate()
            server_process.wait(timeout=5)
            
    except Exception as e:
        print(f"❌ Server test error: {e}")
        return False

def main():
    print("🧪 Simple Whisper Test Suite")
    print("=" * 40)
    
    # Test 1: Direct whisper.cpp
    direct_ok = test_whisper_direct()
    
    # Test 2: Server (only if direct works)
    server_ok = False
    if direct_ok:
        server_ok = test_server_quick()
    else:
        print("\n⚠️  Skipping server test due to direct test failure")
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   Direct whisper.cpp: {'✅ PASS' if direct_ok else '❌ FAIL'}")
    print(f"   Whisper server: {'✅ PASS' if server_ok else '❌ FAIL'}")
    
    if direct_ok and server_ok:
        print("\n🎉 All tests passed! Whisper is working correctly.")
        return True
    elif direct_ok:
        print("\n⚠️  Whisper.cpp works but server needs fixing.")
        return False
    else:
        print("\n💥 Whisper.cpp setup needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)