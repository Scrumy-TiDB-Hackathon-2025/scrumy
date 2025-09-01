#!/usr/bin/env python3
"""
WebSocket server starter script for PM2
Starts the WebSocket server for Chrome extension
"""

import asyncio
import os
from pathlib import Path
from app.websocket_server import start_server

# Set working directory to ai_processing
os.chdir(Path(__file__).parent)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Starting WebSocket server on port {port}")
    asyncio.run(start_server(port=port))