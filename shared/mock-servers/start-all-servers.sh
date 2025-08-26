#!/bin/bash

# Master Mock Servers Startup Script
# This script starts both the Chrome Extension WebSocket mock server
# and the Frontend Dashboard REST API mock server

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Default configuration
CHROME_EXT_HOST="localhost"
CHROME_EXT_PORT=8000
FRONTEND_HOST="0.0.0.0"
FRONTEND_PORT=3001
DEBUG_MODE=false
SETUP_ONLY=false
CHROME_ONLY=false
FRONTEND_ONLY=false

# PIDs for background processes
CHROME_EXT_PID=""
FRONTEND_PID=""

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

print_server() {
    echo -e "${PURPLE}[SERVER]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "This script starts both mock servers for ScrumBot development:"
    echo "  - Chrome Extension WebSocket Server (audio processing)"
    echo "  - Frontend Dashboard REST API Server (dashboard data)"
    echo ""
    echo "Options:"
    echo "  --chrome-host HOST     Chrome extension server host (default: localhost)"
    echo "  --chrome-port PORT     Chrome extension server port (default: 8000)"
    echo "  --frontend-host HOST   Frontend dashboard server host (default: 0.0.0.0)"
    echo "  --frontend-port PORT   Frontend dashboard server port (default: 3001)"
    echo "  --debug               Enable debug mode for both servers"
    echo "  --setup-only          Only setup environments, don't start servers"
    echo "  --chrome-only         Only start Chrome extension server"
    echo "  --frontend-only       Only start Frontend dashboard server"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Start both servers with defaults"
    echo "  $0 --debug                           # Start both with debug mode"
    echo "  $0 --chrome-only --debug             # Start only Chrome server with debug"
    echo "  $0 --frontend-port 8080              # Custom frontend port"
    echo "  $0 --setup-only                      # Just setup environments"
    echo ""
    echo "Server Details:"
    echo "  Chrome Extension WebSocket: ws://localhost:8000/ws/audio"
    echo "  Frontend Dashboard REST API: http://0.0.0.0:3001"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --chrome-host)
            CHROME_EXT_HOST="$2"
            shift 2
            ;;
        --chrome-port)
            CHROME_EXT_PORT="$2"
            shift 2
            ;;
        --frontend-host)
            FRONTEND_HOST="$2"
            shift 2
            ;;
        --frontend-port)
            FRONTEND_PORT="$2"
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
        --chrome-only)
            CHROME_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
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
echo "=================================================="
echo "       ScrumBot Mock Servers Manager"
echo "=================================================="
echo ""
echo "🤖 Chrome Extension WebSocket Mock Server"
echo "📊 Frontend Dashboard REST API Mock Server"
echo ""

# Check if directories exist
check_directories() {
    print_status "Checking server directories..."

    if [[ ! -d "chrome-extension" ]]; then
        print_error "chrome-extension directory not found"
        exit 1
    fi

    if [[ ! -d "frontend-dashboard" ]]; then
        print_error "frontend-dashboard directory not found"
        exit 1
    fi

    print_success "Server directories found"
}

# Setup Chrome extension server
setup_chrome_extension() {
    if [[ "$FRONTEND_ONLY" == true ]]; then
        return
    fi

    print_server "Setting up Chrome Extension WebSocket Server..."
    cd "$SCRIPT_DIR/chrome-extension"

    local setup_args="--setup-only --host $CHROME_EXT_HOST --port $CHROME_EXT_PORT"
    if [[ "$DEBUG_MODE" == true ]]; then
        setup_args="$setup_args --debug"
    fi

    bash start-server.sh $setup_args

    if [[ $? -eq 0 ]]; then
        print_success "Chrome extension server setup complete"
    else
        print_error "Chrome extension server setup failed"
        exit 1
    fi

    cd "$SCRIPT_DIR"
}

# Setup Frontend dashboard server
setup_frontend_dashboard() {
    if [[ "$CHROME_ONLY" == true ]]; then
        return
    fi

    print_server "Setting up Frontend Dashboard REST API Server..."
    cd "$SCRIPT_DIR/frontend-dashboard"

    local setup_args="--setup-only --host $FRONTEND_HOST --port $FRONTEND_PORT"
    if [[ "$DEBUG_MODE" == true ]]; then
        setup_args="$setup_args --debug"
    fi

    bash start-server.sh $setup_args

    if [[ $? -eq 0 ]]; then
        print_success "Frontend dashboard server setup complete"
    else
        print_error "Frontend dashboard server setup failed"
        exit 1
    fi

    cd "$SCRIPT_DIR"
}

# Start Chrome extension server in background
start_chrome_extension() {
    if [[ "$FRONTEND_ONLY" == true ]]; then
        return
    fi

    print_server "Starting Chrome Extension WebSocket Server..."
    cd "$SCRIPT_DIR/chrome-extension"

    local start_args="--host $CHROME_EXT_HOST --port $CHROME_EXT_PORT"
    if [[ "$DEBUG_MODE" == true ]]; then
        start_args="$start_args --debug"
    fi

    # Start in background
    bash start-server.sh $start_args &
    CHROME_EXT_PID=$!

    # Wait a moment for server to start
    sleep 3

    # Check if still running
    if kill -0 $CHROME_EXT_PID 2>/dev/null; then
        print_success "Chrome Extension WebSocket Server started (PID: $CHROME_EXT_PID)"
        print_status "WebSocket endpoint: ws://$CHROME_EXT_HOST:$CHROME_EXT_PORT/ws/audio"
    else
        print_error "Chrome Extension WebSocket Server failed to start"
        exit 1
    fi

    cd "$SCRIPT_DIR"
}

# Start Frontend dashboard server in background
start_frontend_dashboard() {
    if [[ "$CHROME_ONLY" == true ]]; then
        return
    fi

    print_server "Starting Frontend Dashboard REST API Server..."
    cd "$SCRIPT_DIR/frontend-dashboard"

    local start_args="--host $FRONTEND_HOST --port $FRONTEND_PORT"
    if [[ "$DEBUG_MODE" == true ]]; then
        start_args="$start_args --debug"
    fi

    # Start in background
    bash start-server.sh $start_args &
    FRONTEND_PID=$!

    # Wait a moment for server to start
    sleep 3

    # Check if still running
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend Dashboard REST API Server started (PID: $FRONTEND_PID)"
        print_status "REST API endpoint: http://$FRONTEND_HOST:$FRONTEND_PORT"
    else
        print_error "Frontend Dashboard REST API Server failed to start"
        exit 1
    fi

    cd "$SCRIPT_DIR"
}

# Wait for servers and handle shutdown
wait_for_servers() {
    print_success "All servers started successfully!"
    echo ""
    echo "=========================================="
    echo "          Server Information"
    echo "=========================================="

    if [[ "$FRONTEND_ONLY" != true ]]; then
        echo "🤖 Chrome Extension WebSocket Server:"
        echo "   • Endpoint: ws://$CHROME_EXT_HOST:$CHROME_EXT_PORT/ws/audio"
        echo "   • PID: $CHROME_EXT_PID"
        echo "   • For: Chrome extension audio processing"
        echo ""
    fi

    if [[ "$CHROME_ONLY" != true ]]; then
        echo "📊 Frontend Dashboard REST API Server:"
        echo "   • Base URL: http://$FRONTEND_HOST:$FRONTEND_PORT"
        echo "   • PID: $FRONTEND_PID"
        echo "   • For: Frontend dashboard data"
        echo ""
        echo "   Key endpoints:"
        echo "   • GET  /health - Health check"
        echo "   • GET  /get-meetings - List meetings"
        echo "   • GET  /get-summary/<id> - Meeting summaries"
        echo "   • GET  /analytics/overview - Analytics data"
        echo ""
    fi

    echo "=========================================="
    echo ""
    print_status "Press Ctrl+C to stop all servers"
    echo ""

    # Wait for either server to exit
    if [[ "$CHROME_ONLY" == true ]]; then
        wait $CHROME_EXT_PID
    elif [[ "$FRONTEND_ONLY" == true ]]; then
        wait $FRONTEND_PID
    else
        # Wait for any server to exit
        wait -n
    fi
}

# Cleanup function
cleanup() {
    echo ""
    print_status "Shutting down all servers..."

    if [[ -n "$CHROME_EXT_PID" ]] && kill -0 $CHROME_EXT_PID 2>/dev/null; then
        print_status "Stopping Chrome Extension WebSocket Server (PID: $CHROME_EXT_PID)..."
        kill -TERM $CHROME_EXT_PID 2>/dev/null || true
        wait $CHROME_EXT_PID 2>/dev/null || true
        print_success "Chrome Extension WebSocket Server stopped"
    fi

    if [[ -n "$FRONTEND_PID" ]] && kill -0 $FRONTEND_PID 2>/dev/null; then
        print_status "Stopping Frontend Dashboard REST API Server (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID 2>/dev/null || true
        wait $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend Dashboard REST API Server stopped"
    fi

    print_success "All servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Main execution
main() {
    check_directories

    # Setup phase
    print_status "=== Setup Phase ==="
    setup_chrome_extension
    setup_frontend_dashboard

    if [[ "$SETUP_ONLY" == true ]]; then
        print_success "Environment setup complete for all servers"
        echo ""
        echo "To start servers manually:"
        if [[ "$FRONTEND_ONLY" != true ]]; then
            echo "  Chrome Extension: cd chrome-extension && bash start-server.sh"
        fi
        if [[ "$CHROME_ONLY" != true ]]; then
            echo "  Frontend Dashboard: cd frontend-dashboard && bash start-server.sh"
        fi
        echo ""
        echo "Or run this script without --setup-only to start all servers"
        exit 0
    fi

    # Start phase
    print_status "=== Server Start Phase ==="
    start_chrome_extension
    start_frontend_dashboard

    # Wait phase
    wait_for_servers
}

# Run main function
main
