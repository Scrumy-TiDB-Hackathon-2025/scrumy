#!/usr/bin/env python3
"""
Start the Whisper transcription server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Add the app directory to Python path
    app_dir = Path(__file__).parent / "app"
    sys.path.insert(0, str(app_dir))
    
    # Set environment variables
    os.environ.setdefault("WHISPER_HOST", "127.0.0.1")
    os.environ.setdefault("WHISPER_PORT", "8178")
    
    print("🎤 Starting Whisper Transcription Server...")
    print(f"   Host: {os.environ['WHISPER_HOST']}")
    print(f"   Port: {os.environ['WHISPER_PORT']}")
    print(f"   URL: http://{os.environ['WHISPER_HOST']}:{os.environ['WHISPER_PORT']}")
    print()
    
    try:
        # Import and run the server
        from app.whisper_server import app
        import uvicorn
        
        uvicorn.run(
            app,
            host=os.environ["WHISPER_HOST"],
            port=int(os.environ["WHISPER_PORT"]),
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Whisper server stopped by user")
    except Exception as e:
        print(f"❌ Error starting Whisper server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()