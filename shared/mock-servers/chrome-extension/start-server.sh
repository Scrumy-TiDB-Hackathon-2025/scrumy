#!/bin/bash

# Chrome Extension WebSocket Mock Server Startup Script
# This script sets up and starts the WebSocket mock server for Chrome extension testing

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
DEFAULT_HOST="localhost"
DEFAULT_PORT=8000
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
    echo "  --host HOST        Server host (default: localhost)"
    echo "  --port PORT        Server port (default: 8000)"
    echo "  --debug           Enable debug logging"
    echo "  --setup-only      Only setup environment, don't start server"
    echo "  --no-venv         Don't use virtual environment"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start with defaults"
    echo "  $0 --host 0.0.0.0 --port 8080       # Custom host and port"
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
echo "=========================================="
echo "  Chrome Extension WebSocket Mock Server"
echo "=========================================="
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
    if [[ ! -f "websocket-mock-server.py" ]]; then
        print_error "websocket-mock-server.py not found"
        exit 1
    fi
    print_success "Server script found"
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
    print_status "Starting WebSocket Mock Server..."
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
        python websocket-mock-server.py $CMD_ARGS
    else
        python3 websocket-mock-server.py $CMD_ARGS
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

    if [[ "$SETUP_ONLY" == true ]]; then
        print_success "Environment setup complete"
        echo ""
        echo "To start the server manually:"
        if [[ "$USE_VENV" == true ]]; then
            echo "  source venv/bin/activate"
        fi
        echo "  python$(if [[ "$USE_VENV" == false ]]; then echo "3"; fi) websocket-mock-server.py --host $HOST --port $PORT"
        exit 0
    fi

    check_port

    print_success "Setup complete! Starting server..."
    echo ""
    echo "Connect your Chrome extension to: ws://$HOST:$PORT/ws/audio"
    echo "Press Ctrl+C to stop the server"
    echo ""

    start_server
}

# Run main function
main
