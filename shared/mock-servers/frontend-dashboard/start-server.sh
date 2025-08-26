#!/bin/bash

# Frontend Dashboard REST API Mock Server Startup Script
# This script sets up and starts the REST API mock server for frontend dashboard testing

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT=3001
VENV_DIR="venv"
PYTHON_VERSION="python3"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --host HOST        Server host (default: 0.0.0.0)"
    echo "  --port PORT        Server port (default: 3001)"
    echo "  --debug           Enable debug mode"
    echo "  --setup-only      Only setup environment, don't start server"
    echo "  --no-venv         Don't use virtual environment"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with defaults"
    echo "  $0 --host localhost --port 8080      # Custom host and port"
    echo "  $0 --debug                           # Enable debug mode"
    echo "  $0 --setup-only                      # Just setup environment"
}

# Parse command line arguments
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
DEBUG_MODE=false
SETUP_ONLY=false
USE_VENV=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Banner
echo ""
echo "==========================================="
echo "  Frontend Dashboard REST API Mock Server"
echo "==========================================="
echo ""

# Check Python availability
check_python() {
    print_status "Checking Python availability..."

    if ! command -v "$PYTHON_VERSION" &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VER=$("$PYTHON_VERSION" --version 2>&1 | cut -d' ' -f2)
    print_success "Found Python $PYTHON_VER"
}

# Setup virtual environment
setup_venv() {
    if [[ "$USE_VENV" == true ]]; then
        print_status "Setting up virtual environment..."

        if [[ ! -d "$VENV_DIR" ]]; then
            print_status "Creating virtual environment..."
            "$PYTHON_VERSION" -m venv "$VENV_DIR"
            print_success "Virtual environment created"
        else
            print_status "Virtual environment already exists"
        fi

        # Activate virtual environment
        source "$VENV_DIR/bin/activate"
        print_success "Virtual environment activated"

        # Upgrade pip
        pip install --upgrade pip > /dev/null 2>&1
        print_status "Upgraded pip to latest version"
    else
        print_warning "Skipping virtual environment setup"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."

    if [[ -f "requirements.txt" ]]; then
        if [[ "$USE_VENV" == true ]]; then
            pip install -r requirements.txt
        else
            pip3 install -r requirements.txt
        fi
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Verify server script exists
check_server_script() {
    if [[ ! -f "rest-api-mock-server.py" ]]; then
        print_error "rest-api-mock-server.py not found"
        exit 1
    fi
    print_success "Server script found"
}

# Verify mock data exists
check_mock_data() {
    MOCK_DATA_PATH="../shared/mock-meetings-data.json"
    if [[ ! -f "$MOCK_DATA_PATH" ]]; then
        print_error "Mock data file not found: $MOCK_DATA_PATH"
        exit 1
    fi
    print_success "Mock data file found"
}

# Check if port is available
check_port() {
    print_status "Checking if port $PORT is available..."

    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port $PORT is already in use"
        print_status "Use --port option to specify a different port"
        exit 1
    fi

    print_success "Port $PORT is available"
}

# Start the server
start_server() {
    print_status "Starting REST API Mock Server..."
    print_status "Host: $HOST"
    print_status "Port: $PORT"
    print_status "Debug: $DEBUG_MODE"
    echo ""

    # Build command
    CMD_ARGS="--host $HOST --port $PORT"

    if [[ "$DEBUG_MODE" == true ]]; then
        CMD_ARGS="$CMD_ARGS --debug"
    fi

    # Start server with proper Python interpreter
    if [[ "$USE_VENV" == true ]]; then
        python rest-api-mock-server.py $CMD_ARGS
    else
        python3 rest-api-mock-server.py $CMD_ARGS
    fi
}

# Test API endpoints
test_endpoints() {
    print_status "Testing API endpoints..."

    local BASE_URL="http://$HOST:$PORT"

    # Test health endpoint
    if command -v curl &> /dev/null; then
        if curl -s --max-time 5 "$BASE_URL/health" > /dev/null; then
            print_success "Health endpoint working"
        else
            print_warning "Health endpoint test failed"
        fi

        if curl -s --max-time 5 "$BASE_URL/get-meetings" > /dev/null; then
            print_success "Meetings endpoint working"
        else
            print_warning "Meetings endpoint test failed"
        fi
    else
        print_warning "curl not available, skipping endpoint tests"
    fi
}

# Cleanup function
cleanup() {
    echo ""
    print_status "Shutting down server..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_python
    setup_venv
    install_dependencies
    check_server_script
    check_mock_data

    if [[ "$SETUP_ONLY" == true ]]; then
        print_success "Environment setup complete"
        echo ""
        echo "To start the server manually:"
        if [[ "$USE_VENV" == true ]]; then
            echo "  source venv/bin/activate"
        fi
        echo "  python$(if [[ "$USE_VENV" == false ]]; then echo "3"; fi) rest-api-mock-server.py --host $HOST --port $PORT"
        echo ""
        echo "Available endpoints:"
        echo "  - GET  http://$HOST:$PORT/health"
        echo "  - GET  http://$HOST:$PORT/get-meetings"
        echo "  - GET  http://$HOST:$PORT/get-summary/<meeting_id>"
        echo "  - GET  http://$HOST:$PORT/get-transcripts/<meeting_id>"
        echo "  - GET  http://$HOST:$PORT/get-tasks"
        echo "  - GET  http://$HOST:$PORT/get-participants/<meeting_id>"
        echo "  - POST http://$HOST:$PORT/process-transcript"
        echo "  - POST http://$HOST:$PORT/process-transcript-with-tools"
        echo "  - GET  http://$HOST:$PORT/available-tools"
        echo "  - GET  http://$HOST:$PORT/analytics/overview"
        exit 0
    fi

    check_port

    print_success "Setup complete! Starting server..."
    echo ""
    echo "API Base URL: http://$HOST:$PORT"
    echo "Available endpoints:"
    echo "  - GET  /health                           - Server health check"
    echo "  - GET  /get-meetings                     - List all meetings"
    echo "  - GET  /get-summary/<meeting_id>         - Get meeting summary"
    echo "  - GET  /get-transcripts/<meeting_id>     - Get meeting transcripts"
    echo "  - GET  /get-tasks                        - List all tasks"
    echo "  - GET  /get-participants/<meeting_id>    - Get meeting participants"
    echo "  - POST /process-transcript               - Process transcript text"
    echo "  - POST /process-transcript-with-tools    - Process with AI tools"
    echo "  - GET  /available-tools                  - List available tools"
    echo "  - GET  /analytics/overview               - Analytics dashboard"
    echo ""
    echo "Update your frontend dashboard API_URL to: http://$HOST:$PORT"
    echo "Press Ctrl+C to stop the server"
    echo ""

    start_server
}

# Run main function
main
