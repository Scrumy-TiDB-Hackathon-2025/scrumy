#!/usr/bin/env python3
"""
WebSocket server starter script with auto-restart
Starts the WebSocket server for Chrome extension with file watching
"""

import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# Set working directory to ai_processing
os.chdir(Path(__file__).parent)

# Load environment variables
load_dotenv()
print(f"✅ Loaded environment from .env")

# Verify critical environment variables
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    print(f"✅ Groq API key loaded: {groq_key[:10]}...")
else:
    print("⚠️ No Groq API key found in environment")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting WebSocket server on port {port} with auto-restart")
    
    uvicorn.run(
        "app.websocket_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["./app"],
        log_level="info"
    )
