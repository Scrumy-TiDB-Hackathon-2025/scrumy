# Whisper Custom Server

This directory contains a custom Whisper server implementation optimized for the ScrumBot AI Processing system, providing real-time audio transcription capabilities.

## 📁 Directory Overview

```
whisper-custom/
├── README.md           # This file
├── server/             # Custom Whisper server implementation
│   ├── server.cpp      # Main C++ server implementation
│   ├── httplib.h       # HTTP server library
│   ├── CMakeLists.txt  # CMake build configuration
│   ├── README.md       # Server-specific documentation
│   └── public/         # Static web assets for server UI
└── models/             # Whisper model files (not in repo)
```

## 🚀 Overview

The Whisper Custom Server is a C++ implementation that provides:
- **Real-time audio transcription** using OpenAI's Whisper models
- **HTTP/REST API** for audio processing requests
- **WebSocket support** for streaming audio transcription
- **Optimized performance** for production workloads
- **Custom integration** tailored for ScrumBot requirements

## 🛠️ Features

### Core Capabilities
- **Multiple Model Support**: Works with various Whisper model sizes
- **Real-time Processing**: Low-latency audio transcription
- **Format Flexibility**: Supports multiple audio formats (WAV, MP3, etc.)
- **Language Detection**: Automatic language identification
- **Speaker Timestamps**: Provides timing information for transcriptions
- **Custom Parameters**: Configurable transcription settings

### Performance Optimizations
- **Memory Efficient**: Optimized memory usage for large audio files
- **Multi-threading**: Parallel processing for better performance
- **Caching**: Model caching to reduce load times
- **Streaming**: Real-time audio chunk processing

## 🔧 Building the Server

### Prerequisites
```bash
# Install required dependencies
sudo apt-get update
sudo apt-get install cmake build-essential

# For macOS
brew install cmake
```

### Build Process
```bash
# Navigate to server directory
cd whisper-custom/server

# Create build directory
mkdir build && cd build

# Configure with CMake
cmake ..

# Build the server
make -j$(nproc)

# The executable will be created as 'whisper-server'
```

### Build Options
```bash
# Debug build
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release build (optimized)
cmake -DCMAKE_BUILD_TYPE=Release ..

# With CUDA support (if available)
cmake -DWHISPER_CUDA=ON ..
```

## 🚀 Running the Server

### Basic Usage
```bash
# Start the server on default port (8080)
./whisper-server

# Start on custom port
./whisper-server --port 8081

# With specific model
./whisper-server --model models/ggml-base.en.bin

# With debug logging
./whisper-server --verbose
```

### Server Configuration
```bash
# Environment variables
export WHISPER_MODEL_PATH=models/ggml-base.en.bin
export WHISPER_PORT=8080
export WHISPER_HOST=0.0.0.0
export WHISPER_THREADS=4
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
Response: {"status": "ok", "model": "base.en"}
```

### Transcribe Audio
```bash
POST /transcribe
Content-Type: multipart/form-data
Body: audio file

Response: {
  "text": "transcribed text",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello world"
    }
  ]
}
```

### WebSocket Streaming
```bash
WS /stream
Send: Binary audio chunks
Receive: {"text": "partial transcription"}
```

### Model Information
```bash
GET /info
Response: {
  "model": "base.en",
  "language": "en",
  "sample_rate": 16000
}
```

## 🔌 Integration with ScrumBot

### Python Client Integration
```python
import requests
import websocket
import json

# REST API usage
def transcribe_file(audio_file_path):
    with open(audio_file_path, 'rb') as f:
        files = {'audio': f}
        response = requests.post('http://localhost:8080/transcribe', files=files)
        return response.json()

# WebSocket streaming
def stream_audio(audio_chunks):
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:8080/stream")
    
    for chunk in audio_chunks:
        ws.send_binary(chunk)
        result = ws.recv()
        yield json.loads(result)
    
    ws.close()
```

### FastAPI Backend Integration
The main ScrumBot backend (`../server.py`) integrates with this server:
```python
# In ai_processing/app/ai_processor.py
WHISPER_SERVER_URL = "http://localhost:8080"

async def process_audio(audio_data):
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('audio', audio_data, content_type='audio/wav')
        
        async with session.post(f"{WHISPER_SERVER_URL}/transcribe", data=data) as resp:
            return await resp.json()
```

## 📊 Model Management

### Supported Models
- `ggml-tiny.bin` - Fastest, least accurate
- `ggml-base.bin` - Good balance of speed/accuracy
- `ggml-small.bin` - Better accuracy, slower
- `ggml-medium.bin` - High accuracy
- `ggml-large.bin` - Best accuracy, slowest

### Model Download
```bash
# Download base English model
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin -P models/

# Download multilingual base model
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin -P models/
```

### Model Selection Criteria
- **Development**: Use `tiny` or `base` for speed
- **Staging**: Use `base` or `small` for testing
- **Production**: Use `small` or `medium` for accuracy

## 🚨 Troubleshooting

### Build Issues
```bash
# Missing dependencies
sudo apt-get install cmake build-essential

# CMake version too old
# Install newer CMake from official website

# Missing model files
ls -la models/  # Check if model files exist
```

### Runtime Issues
```bash
# Port already in use
lsof -i :8080
kill -9 <PID>

# Model loading errors
# Verify model file integrity and path

# Memory issues
# Use smaller model or increase system memory
```

### Performance Issues
```bash
# Check CPU usage
htop

# Monitor memory usage
free -h

# Check model loading time
time ./whisper-server --model models/ggml-base.bin
```

## 🔧 Development

### Adding New Features
1. Modify `server.cpp` for new functionality
2. Update CMakeLists.txt if needed
3. Rebuild with `make`
4. Test with sample audio files
5. Update API documentation

### Code Structure
```cpp
// Main server loop
int main(int argc, char** argv);

// Audio processing
std::string transcribe_audio(const std::vector<uint8_t>& audio_data);

// WebSocket handling  
void handle_websocket(const httplib::Request& req, httplib::Response& res);

// Model management
bool load_model(const std::string& model_path);
```

### Testing
```bash
# Test with curl
curl -X POST -F "audio=@test.wav" http://localhost:8080/transcribe

# Test WebSocket with wscat
npm install -g wscat
wscat -c ws://localhost:8080/stream
```

## 📈 Performance Metrics

### Benchmarks (Base Model)
- **Audio Processing**: ~0.1x real-time (1 min audio = 6s processing)
- **Memory Usage**: ~500MB with base model loaded
- **Startup Time**: ~2-3 seconds for model loading
- **Concurrent Requests**: Supports 4-8 concurrent transcriptions

### Optimization Tips
- Use appropriate model size for your accuracy needs
- Enable GPU acceleration if available
- Adjust thread count based on CPU cores
- Use audio preprocessing to improve accuracy

## 📚 Related Documentation

- [Main AI Processing README](../README.md)
- [Server Implementation](server/README.md)
- [API Documentation](../API_DOCUMENTATION.md)
- [Integration Guide](../AI_INTEGRATION_GUIDE.md)
- [Whisper.cpp Documentation](https://github.com/ggerganov/whisper.cpp)

---

**Maintainer**: ScrumBot AI Team  
**Last Updated**: August 2025  
**Version**: 1.0.0  
**Based on**: whisper.cpp by ggerganov