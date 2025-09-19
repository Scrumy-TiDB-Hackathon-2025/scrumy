import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class PipelineLogger:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path("pipeline_logs") / self.session_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def log_audio_chunk(self, chunk_data: Dict[str, Any]):
        """Log audio chunk reception"""
        log_file = self.log_dir / "01_audio_chunks.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "chunk_size": len(chunk_data.get("audio_data", "")),
                "participant": chunk_data.get("participant"),
                "chunk_id": chunk_data.get("chunk_id"),
                "meeting_id": chunk_data.get("meeting_id")
            }) + "\n")
    
    def log_transcript_chunk(self, transcript: str, speaker: str = None):
        """Log individual transcript chunks"""
        log_file = self.log_dir / "02_transcript_chunks.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "transcript": transcript,
                "speaker": speaker,
                "length": len(transcript)
            }) + "\n")
    
    def log_batch_processing(self, chunks: List[Dict], batch_transcript: str):
        """Log batch processing input and combined transcript"""
        log_file = self.log_dir / "03_batch_processing.json"
        with open(log_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "chunk_count": len(chunks),
                "chunks": chunks,
                "combined_transcript": batch_transcript,
                "total_length": len(batch_transcript)
            }, f, indent=2)
    
    def log_groq_request(self, prompt: str, model: str):
        """Log Groq API request"""
        log_file = self.log_dir / "04_groq_request.json"
        with open(log_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "prompt": prompt,
                "prompt_length": len(prompt)
            }, f, indent=2)
    
    def log_groq_response(self, response: str, usage_stats: Dict = None):
        """Log Groq API response"""
        log_file = self.log_dir / "05_groq_response.json"
        with open(log_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "response": response,
                "response_length": len(response),
                "usage_stats": usage_stats
            }, f, indent=2)
    
    def log_task_extraction(self, extracted_data: Dict):
        """Log extracted tasks and summary"""
        log_file = self.log_dir / "06_task_extraction.json"
        with open(log_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "extracted_data": extracted_data,
                "task_count": len(extracted_data.get("tasks", [])),
                "has_summary": bool(extracted_data.get("summary"))
            }, f, indent=2)
    
    def log_task_creation(self, platform: str, task_data: Dict, result: Dict):
        """Log task creation attempts and results"""
        log_file = self.log_dir / "07_task_creation.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "task_data": task_data,
                "result": result,
                "success": result.get("success", False),
                "task_url": result.get("url")
            }) + "\n")
    
    def log_pipeline_summary(self, summary: Dict):
        """Log overall pipeline summary"""
        log_file = self.log_dir / "00_pipeline_summary.json"
        with open(log_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "summary": summary
            }, f, indent=2)
    
    def get_log_directory(self) -> str:
        """Return the log directory path"""
        return str(self.log_dir)