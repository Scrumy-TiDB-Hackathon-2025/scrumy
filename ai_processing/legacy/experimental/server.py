from fastapi import FastAPI
import subprocess
import sqlite3

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/transcribe")
async def transcribe(audio: dict):
    try:
        result = subprocess.run(['./whisper.cpp/build/bin/main', '-m', './whisper-server-package/models/ggml-tiny.bin', '-t', audio['data']], capture_output=True, text=True)
        conn = sqlite3.connect('./meetily.db')
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS transcripts (id INTEGER PRIMARY KEY, transcript TEXT)")
        cursor.execute("INSERT INTO transcripts (transcript) VALUES (?)", (result.stdout,))
        conn.commit()
        conn.close()
        return {"transcript": result.stdout}
    except Exception as e:
        return {"error": str(e)}
