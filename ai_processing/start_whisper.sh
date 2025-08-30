#!/bin/bash

# Whisper Server Startup Script
# Starts the Whisper transcription server

echo "🎤 Starting Whisper Transcription Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if whisper.cpp is built
if [ ! -f "whisper.cpp/build/bin/whisper-cli" ]; then
    echo "❌ Whisper.cpp not built. Please run:"
    echo "   ./build_whisper.sh"
    exit 1
fi

# Check if model exists
if [ ! -f "whisper.cpp/models/ggml-base.en.bin" ]; then
    echo "❌ Whisper model not found. Downloading..."
    cd whisper.cpp/models
    ./download-ggml-model.sh base.en
    cd ../..
fi

# Kill any existing server on port 8178
echo "🧹 Cleaning up existing servers..."
lsof -ti:8178 | xargs kill -9 2>/dev/null || true

# Start the server
echo "🚀 Starting Whisper server on http://127.0.0.1:8178"
echo "📖 API docs will be available at http://127.0.0.1:8178/docs"
echo "🛑 Press Ctrl+C to stop"
echo ""

python simple_whisper_server.py