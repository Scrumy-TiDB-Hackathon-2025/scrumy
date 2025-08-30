#!/usr/bin/env python3
"""
Start WebSocket Server for Audio Processing

Starts the WebSocket server that handles Chrome extension audio chunks
"""

import asyncio
import logging
import os
from fastapi import FastAPI
from fastapi.websockets import WebSocket
import uvicorn
from app.websocket_server import websocket_endpoint

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')
        print(f"✅ Loaded environment from {env_path}")
    else:
        print(f"⚠️  .env file not found at {env_path}")

# Load environment at startup
load_env()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(title="ScrumBot WebSocket Server")

@app.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    """WebSocket endpoint for audio processing"""
    await websocket_endpoint(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "websocket-server"}

if __name__ == "__main__":
    print("🚀 Starting ScrumBot WebSocket Server...")
    print("📡 WebSocket endpoint: ws://localhost:8080/ws")
    print("🏥 Health check: http://localhost:8080/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )