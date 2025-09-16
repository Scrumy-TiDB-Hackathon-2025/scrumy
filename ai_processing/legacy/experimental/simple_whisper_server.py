#!/usr/bin/env python3
"""
Simple Whisper Server - Minimal implementation for testing
"""

import os
import subprocess
import tempfile
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Simple Whisper Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent
WHISPER_EXE = BASE_DIR / "whisper.cpp/build/bin/whisper-cli"
MODEL_FILE = BASE_DIR / "whisper.cpp/models/ggml-base.en.bin"

@app.get("/health")
def health():
    """Health check"""
    return {"status": "ok", "whisper_available": WHISPER_EXE.exists()}

@app.get("/models")
def models():
    """List available models"""
    models_dir = BASE_DIR / "whisper.cpp/models"
    model_files = list(models_dir.glob("ggml-*.bin"))
    return {"models": [m.name for m in model_files]}

@app.post("/transcribe")
def transcribe(file: UploadFile = File(...)):
    """Transcribe audio file"""
    
    if not WHISPER_EXE.exists():
        raise HTTPException(status_code=500, detail="Whisper executable not found")
    
    if not MODEL_FILE.exists():
        raise HTTPException(status_code=500, detail="Model file not found")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded file
        input_path = Path(temp_dir) / file.filename
        with open(input_path, "wb") as f:
            f.write(file.file.read())
        
        # Run whisper
        cmd = [
            str(WHISPER_EXE),
            "-m", str(MODEL_FILE),
            "-f", str(input_path),
            "--language", "en",
            "--threads", "2"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Whisper failed: {result.stderr}")
            
            return {
                "transcript": result.stdout.strip(),
                "status": "success"
            }
            
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="Transcription timed out")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🎤 Starting Simple Whisper Server on http://127.0.0.1:8178")
    uvicorn.run(app, host="127.0.0.1", port=8178, log_level="info")