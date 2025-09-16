#!/usr/bin/env python3
"""
Whisper Server - Standalone audio transcription service
Handles audio file uploads and returns transcriptions using whisper.cpp
"""

import os
import subprocess
import tempfile
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscriptionRequest(BaseModel):
    """Request model for transcription settings"""
    language: Optional[str] = "en"
    model: Optional[str] = "base.en"
    output_format: Optional[str] = "json"

class TranscriptionResponse(BaseModel):
    """Response model for transcription results"""
    transcript: str
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    segments: Optional[list] = None

class WhisperServer:
    """Whisper transcription server using whisper.cpp"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.whisper_executable = self.base_dir / "whisper.cpp/build/bin/whisper-cli"
        self.models_dir = self.base_dir / "whisper.cpp/models"
        
        # Validate setup
        self._validate_setup()
    
    def _validate_setup(self):
        """Validate that whisper.cpp is properly built and models exist"""
        if not self.whisper_executable.exists():
            raise RuntimeError(f"Whisper executable not found at {self.whisper_executable}")
        
        if not self.models_dir.exists():
            raise RuntimeError(f"Models directory not found at {self.models_dir}")
        
        # Check for at least one model
        model_files = list(self.models_dir.glob("ggml-*.bin"))
        if not model_files:
            raise RuntimeError(f"No Whisper models found in {self.models_dir}")
        
        logger.info(f"Whisper server initialized with {len(model_files)} models")
        for model in model_files:
            logger.info(f"  - {model.name}")
    
    def _preprocess_audio(self, input_path: str, output_path: str) -> bool:
        """Convert audio to whisper.cpp format (16kHz, mono, 16-bit PCM WAV)"""
        try:
            cmd = [
                "ffmpeg", "-i", input_path,
                "-ar", "16000",      # 16kHz sample rate
                "-ac", "1",          # Mono
                "-c:a", "pcm_s16le", # 16-bit PCM
                "-y",                # Overwrite output
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Audio preprocessing timed out")
            return False
        except Exception as e:
            logger.error(f"Audio preprocessing error: {e}")
            return False
    
    def _get_model_path(self, model_name: str) -> Path:
        """Get the full path to a model file"""
        # Handle both short names (base.en) and full names (ggml-base.en.bin)
        if not model_name.startswith("ggml-"):
            model_name = f"ggml-{model_name}"
        if not model_name.endswith(".bin"):
            model_name = f"{model_name}.bin"
        
        model_path = self.models_dir / model_name
        
        if not model_path.exists():
            # Try to find a similar model
            available_models = list(self.models_dir.glob("ggml-*.bin"))
            if available_models:
                logger.warning(f"Model {model_name} not found, using {available_models[0].name}")
                return available_models[0]
            else:
                raise FileNotFoundError(f"No models available in {self.models_dir}")
        
        return model_path
    
    async def transcribe_audio(self, audio_file: UploadFile, settings: TranscriptionRequest) -> TranscriptionResponse:
        """Transcribe audio file using whisper.cpp"""
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            try:
                # Save uploaded file
                input_file = temp_dir_path / f"input_{audio_file.filename}"
                with open(input_file, "wb") as f:
                    content = await audio_file.read()
                    f.write(content)
                
                logger.info(f"Saved audio file: {input_file} ({len(content)} bytes)")
                
                # Get model path
                try:
                    model_path = self._get_model_path(settings.model)
                    logger.info(f"Using model: {model_path}")
                except FileNotFoundError as e:
                    raise HTTPException(status_code=400, detail=str(e))
                
                # Simple whisper command - minimal options for reliability
                whisper_cmd = [
                    str(self.whisper_executable),
                    "-m", str(model_path),
                    "-f", str(input_file),
                    "--output-txt",
                    "--output-file", str(temp_dir_path / "output"),
                    "--language", settings.language,
                    "--threads", "2"
                ]
                
                logger.info(f"Running whisper command: {' '.join(whisper_cmd)}")
                
                # Run with shorter timeout for testing
                result = await asyncio.create_subprocess_exec(
                    *whisper_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)
                except asyncio.TimeoutError:
                    result.kill()
                    raise HTTPException(status_code=408, detail="Transcription timed out")
                
                processing_time = time.time() - start_time
                
                if result.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.error(f"Whisper failed (code {result.returncode}): {error_msg}")
                    raise HTTPException(status_code=500, detail=f"Transcription failed: {error_msg}")
                
                # Read output file
                output_file = temp_dir_path / "output.txt"
                transcript_text = ""
                
                if output_file.exists():
                    transcript_text = output_file.read_text().strip()
                    logger.info(f"Transcription result: {transcript_text[:100]}...")
                else:
                    # Fallback to stdout
                    transcript_text = stdout.decode().strip() if stdout else ""
                    logger.warning("Output file not found, using stdout")
                
                if not transcript_text:
                    logger.warning("Empty transcript received")
                    transcript_text = "[No speech detected]"
                
                return TranscriptionResponse(
                    transcript=transcript_text,
                    processing_time=processing_time,
                    segments=None
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Transcription error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

# Create FastAPI app
app = FastAPI(
    title="Whisper Transcription Server",
    description="Audio transcription service using whisper.cpp",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize whisper server
try:
    whisper_server = WhisperServer()
except Exception as e:
    logger.error(f"Failed to initialize Whisper server: {e}")
    whisper_server = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if whisper_server is None:
        raise HTTPException(status_code=503, detail="Whisper server not initialized")
    return {"status": "healthy", "service": "whisper-transcription"}

@app.get("/models")
async def list_models():
    """List available Whisper models"""
    if whisper_server is None:
        raise HTTPException(status_code=503, detail="Whisper server not initialized")
    
    models = list(whisper_server.models_dir.glob("ggml-*.bin"))
    return {
        "models": [model.name for model in models],
        "count": len(models)
    }

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_endpoint(
    file: UploadFile = File(...),
    language: str = "en",
    model: str = "base.en",
    output_format: str = "json"
):
    """Transcribe audio file"""
    if whisper_server is None:
        raise HTTPException(status_code=503, detail="Whisper server not initialized")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith(('audio/', 'video/')):
        logger.warning(f"Unexpected content type: {file.content_type}, proceeding anyway")
    
    settings = TranscriptionRequest(
        language=language,
        model=model,
        output_format=output_format
    )
    
    return await whisper_server.transcribe_audio(file, settings)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("WHISPER_PORT", 8178))
    host = os.getenv("WHISPER_HOST", "127.0.0.1")
    
    logger.info(f"Starting Whisper server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)