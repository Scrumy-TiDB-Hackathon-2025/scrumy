#!/usr/bin/env python3
"""
WebSocket server starter script for PM2
Starts the WebSocket server for Chrome extension
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from app.websocket_server import start_server

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
    print(f"Starting WebSocket server on port {port}")
    try:
        asyncio.run(start_server(port=port))
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise
