#!/usr/bin/env python3
"""
Backend starter script for PM2
Starts the FastAPI backend server
"""

import uvicorn
import os
from pathlib import Path

# Set working directory to ai_processing
os.chdir(Path(__file__).parent)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5167)),
        reload=False,
        log_level="info"
    )