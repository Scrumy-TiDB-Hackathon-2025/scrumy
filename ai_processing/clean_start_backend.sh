#!/bin/bash

# Exit on error
set -e

# Color codes and emojis
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="whisper-server-package"
MODEL_DIR="$PACKAGE_NAME/models"

# Whisper.cpp configuration (what the backend actually uses)
WHISPER_CPP_DIR="whisper.cpp"
WHISPER_EXECUTABLE="$WHISPER_CPP_DIR/build/bin/whisper-cli"
WHISPER_MODEL_DIR="$WHISPER_CPP_DIR/models"

# Helper functions for logging
log_info() {
    echo -e "${BLUE}ℹ️  [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}❌ [ERROR]${NC} $1"
    return 1
}

log_section() {
    echo -e "\n${PURPLE}🔄 === $1 ===${NC}\n"
}

# Error handling function
handle_error() {
    local error_msg="$1"
    log_error "$error_msg"
    cleanup
    exit 1
}

# Cleanup function
cleanup() {
    log_section "Cleanup"
    if [ -n "$WHISPER_PID" ]; then
        log_info "Stopping Whisper server..."
        if kill -0 $WHISPER_PID 2>/dev/null; then
            kill -9 $WHISPER_PID 2>/dev/null || log_warning "Failed to kill Whisper server process"
            pkill -9 -f "whisper-server" 2>/dev/null || log_warning "Failed to kill remaining whisper-server processes"
        fi
        log_success "Whisper server stopped"
    fi
    if [ -n "$PYTHON_PID" ]; then
        log_info "Stopping Python backend..."
        if kill -0 $PYTHON_PID 2>/dev/null; then
            kill -9 $PYTHON_PID 2>/dev/null || log_warning "Failed to kill Python backend process"
        fi
        log_success "Python backend stopped"
    fi
}

# Set up trap for cleanup on script exit, interrupt, or termination
trap cleanup EXIT INT TERM

# Check if required directories and files exist
log_section "Environment Check"

# Check for Whisper (what the backend actually uses)
WHISPER_AVAILABLE=false
if [ -f "$WHISPER_EXECUTABLE" ] && [ -d "$WHISPER_MODEL_DIR" ]; then
    # Check if we have at least one model
    if ls "$WHISPER_MODEL_DIR"/ggml-*.bin >/dev/null 2>&1; then
        log_success "Whisper.cpp executable and models found"
        WHISPER_AVAILABLE=true
    else
        log_warning "Whisper.cpp executable found but no models available"
        log_info "Models directory: $WHISPER_MODEL_DIR"
    fi
elif [ -f "$WHISPER_EXECUTABLE" ]; then
    log_warning "Whisper.cpp executable found but models directory missing"
    log_info "Expected models at: $WHISPER_MODEL_DIR"
else
    log_warning "Whisper.cpp not built. Transcription will not be available."
    log_info "To enable Whisper: build whisper.cpp first"
fi

# Check for Python backend (required)
if [ ! -d "app" ]; then
    handle_error "Python backend directory not found. Please check your installation"
fi

if [ ! -f "app/main.py" ]; then
    handle_error "Python backend main.py not found. Please check your installation"
fi

# Check for virtual environment (create if needed)
if [ ! -d "venv" ]; then
    log_warning "Virtual environment not found. Creating one..."
    log_info "Running: python -m venv venv"
    
    if ! python -m venv venv; then
        handle_error "Failed to create virtual environment. Please ensure Python is installed."
    fi
    
    log_success "Virtual environment created successfully"
    
    # Activate and install dependencies
    log_info "Activating virtual environment and installing dependencies..."
    if ! source venv/bin/activate; then
        handle_error "Failed to activate virtual environment"
    fi
    
    if [ -f "requirements.txt" ]; then
        log_info "Installing requirements from requirements.txt..."
        if ! pip install -r requirements.txt; then
            handle_error "Failed to install requirements"
        fi
        log_success "Requirements installed successfully"
    else
        log_warning "requirements.txt not found, installing basic dependencies..."
        if ! pip install fastapi uvicorn python-multipart; then
            handle_error "Failed to install basic dependencies"
        fi
        log_success "Basic dependencies installed"
    fi
else
    log_success "Virtual environment found"
fi

# Kill any existing whisper-server processes
log_section "Initial Cleanup"

log_info "Checking for existing whisper servers..."
if pkill -f "whisper-server" 2>/dev/null; then
    log_success "Existing whisper servers terminated"
else
    log_warning "No existing whisper servers found"
fi
sleep 1  # Give processes time to terminate

# Check and kill if backend app in port 5167 is running
log_section "Backend App Check"

log_info "Checking for processes on port 5167..."
PORT=5167
if lsof -i :$PORT | grep -q LISTEN; then
    log_warning "Backend app is running on port $PORT"
    read -p "$(echo -e "${YELLOW}🤔 Kill it? (y/N)${NC} ")" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        handle_error "User chose not to terminate existing backend app"
    fi

    log_info "Terminating backend app..."
    if ! kill -9 $(lsof -t -i :$PORT) 2>/dev/null; then
        handle_error "Failed to terminate backend app"
    fi
    log_success "Backend app terminated"
    sleep 1  # Give processes time to terminate
fi



# Check for existing model (only if Whisper is available)
if [ "$WHISPER_AVAILABLE" = true ]; then
    log_section "Model Check"

    log_info "Checking for Whisper models..."
    EXISTING_MODELS=$(find "$WHISPER_MODEL_DIR" -name "ggml-*.bin" -type f 2>/dev/null)

    if [ -n "$EXISTING_MODELS" ]; then
        log_success "Found existing models:"
        echo -e "${BLUE}$EXISTING_MODELS${NC}"
    else
        log_warning "No existing models found in $WHISPER_MODEL_DIR"
    fi
fi

# Backend uses hardcoded model path: whisper.cpp/models/ggml-base.en.bin
if [ "$WHISPER_AVAILABLE" = true ]; then
    REQUIRED_MODEL="$WHISPER_MODEL_DIR/ggml-base.en.bin"
    if [ -f "$REQUIRED_MODEL" ]; then
        log_success "Required model found: $REQUIRED_MODEL"
    else
        log_warning "Required model not found: $REQUIRED_MODEL"
        log_info "Backend will show error if transcription is attempted"
    fi
fi

log_section "Starting Services"

# Note: Backend uses whisper.cpp directly, no separate server needed
if [ "$WHISPER_AVAILABLE" = true ]; then
    log_info "Whisper.cpp ready for transcription 🎙️"
else
    log_info "Whisper.cpp not available - transcription disabled"
fi
WHISPER_PID=""

# Start the Python backend in background
log_info "Starting Python backend... 🚀"
# Start venv if not active
if [ -z "$VIRTUAL_ENV" ]; then
    log_info "Activating virtual environment..."
    if ! source venv/bin/activate; then
        handle_error "Failed to activate virtual environment"
    fi
fi

# Check if required Python packages are installed
if ! pip show fastapi >/dev/null 2>&1; then
    handle_error "FastAPI not found. Please install dependencies first"
fi

# Start the backend with auto-restart feature
log_info "Starting backend with auto-restart on file changes..."
if command -v watchdog >/dev/null 2>&1; then
    log_info "Using watchdog for auto-restart"
    PYTHONPATH=. watchdog --patterns="*.py" --recursive --auto-restart -- python app/main.py > backend.log 2>&1 &
    PYTHON_PID=$!
elif pip show watchdog >/dev/null 2>&1; then
    log_info "Using watchdog for auto-restart"
    PYTHONPATH=. python -m watchdog --patterns="*.py" --recursive --auto-restart -- python app/main.py > backend.log 2>&1 &
    PYTHON_PID=$!
else
    log_warning "Watchdog not installed. Installing for auto-restart feature..."
    pip install watchdog
    log_info "Using watchdog for auto-restart"
    PYTHONPATH=. python -m watchdog --patterns="*.py" --recursive --auto-restart -- python app/main.py > backend.log 2>&1 &
    PYTHON_PID=$!
fi

# Wait for backend to start and check if it's running
sleep 10
if ! kill -0 $PYTHON_PID 2>/dev/null; then
    handle_error "Python backend failed to start"
fi

# Check if the port is actually listening
if ! lsof -i :$PORT | grep -q LISTEN; then
    handle_error "Python backend is not listening on port $PORT"
fi

log_success "🎉 Services started successfully with auto-restart!"

echo -e "${GREEN}🐍 Python Backend (PID: $PYTHON_PID) - Port: 5167${NC}"
echo -e "${BLUE}  📄 Backend logs: backend.log${NC}"
echo -e "${BLUE}  🔄 Auto-restart: Enabled (watches *.py files)${NC}"

if [ "$WHISPER_AVAILABLE" = true ]; then
    echo -e "${GREEN}🎙️ Whisper.cpp: Ready for transcription${NC}"
    echo -e "${BLUE}  📍 Executable: $WHISPER_EXECUTABLE${NC}"
    echo -e "${BLUE}  📁 Models: $WHISPER_MODEL_DIR${NC}"
else
    echo -e "${YELLOW}🎙️ Whisper.cpp: Not available${NC}"
fi

echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Show available endpoints
echo -e "\n${BLUE}📡 Available Endpoints:${NC}"
echo -e "${BLUE}  - API Documentation: http://localhost:5167/docs${NC}"
echo -e "${BLUE}  - Process Complete Meeting: POST http://localhost:5167/process-complete-meeting${NC}"

if [ "$WHISPER_AVAILABLE" = true ]; then
    echo -e "${GREEN}  - Audio Transcription: POST http://localhost:5167/transcribe${NC}"
else
    echo -e "${YELLOW}  - Audio Transcription: Unavailable (Whisper.cpp not built)${NC}"
fi

# Show log monitoring commands
echo -e "\n${BLUE}📊 Monitor Logs:${NC}"
echo -e "${BLUE}  - Backend: tail -f backend.log${NC}"

# Keep the script running and wait for processes
if [ "$WHISPER_AVAILABLE" = true ] && [ -n "$WHISPER_PID" ]; then
    wait $WHISPER_PID $PYTHON_PID || handle_error "One of the services crashed"
else
    wait $PYTHON_PID || handle_error "Python backend crashed"
fi
