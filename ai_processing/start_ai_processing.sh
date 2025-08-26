#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions for logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    log_error "This script must be run from the ai_processing directory"
    log_error "Current directory: $(pwd)"
    exit 1
fi

log_section "Starting ScrumBot AI Processing Server"

# Check Python installation
log_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    log_error "Python3 is not installed or not in PATH"
    exit 1
fi

python_version=$(python3 --version)
log_success "Found Python: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    log_success "Virtual environment created"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate || {
    log_error "Failed to activate virtual environment"
    exit 1
}

# Check and install dependencies
log_info "Checking dependencies..."
pip install -r requirements.txt > /dev/null 2>&1 || {
    log_error "Failed to install dependencies"
    exit 1
}
log_success "Dependencies are up to date"

# Check Whisper components
log_info "Checking Whisper components..."
if [ ! -f "whisper-server-package/main" ]; then
    log_error "Whisper executable not found at whisper-server-package/main"
    log_error "Please run the build_whisper.sh script first or copy from the working backend"
    exit 1
fi

if [ ! -f "whisper-server-package/models/for-tests-ggml-base.en.bin" ]; then
    log_error "Whisper model not found"
    log_error "Expected: whisper-server-package/models/for-tests-ggml-base.en.bin"
    exit 1
fi

log_success "Whisper components found"

# Check if database file exists, create if not
log_info "Checking database..."
if [ ! -f "meeting_minutes.db" ]; then
    log_warning "Database file not found, it will be created on first run"
else
    log_success "Database file found"
fi

# Check for environment file
log_info "Checking environment configuration..."
if [ ! -f ".env" ]; then
    log_warning "No .env file found. Creating default one..."
    cat > .env << EOF
# AI Processing Server Configuration
OLLAMA_HOST=http://localhost:11434

# API Keys (add your keys here)
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
# GROQ_API_KEY=your_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
EOF
    log_success "Default .env file created. Edit it to add your API keys."
else
    log_success "Environment file found"
fi

# Check if port is available
PORT=${PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warning "Port $PORT is already in use. The server might fail to start."
fi

log_section "Starting Server"

log_info "Server will be available at:"
log_info "  - Main API: http://localhost:$PORT"
log_info "  - API Documentation: http://localhost:$PORT/docs"
log_info "  - Health Check: http://localhost:$PORT/health"
log_info "  - Transcription: http://localhost:$PORT/transcribe"

log_info "Available AI providers:"
log_info "  - OpenAI (requires OPENAI_API_KEY)"
log_info "  - Anthropic Claude (requires ANTHROPIC_API_KEY)"
log_info "  - Groq (requires GROQ_API_KEY)"
log_info "  - Ollama (requires local Ollama server)"

log_info "Press Ctrl+C to stop the server"
echo

# Start the server
log_success "Starting AI Processing Server..."
exec python3 -m uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --reload
