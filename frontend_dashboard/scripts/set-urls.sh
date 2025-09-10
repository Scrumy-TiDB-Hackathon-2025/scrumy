#!/bin/bash

# Script to set API and WebSocket URLs for dev/prod environments

set_dev() {
    echo "Setting development URLs..."
    read -p "Enter API URL (default: http://localhost:8080): " api_url
    read -p "Enter WebSocket URL (default: ws://localhost:8080): " ws_url
    
    api_url=${api_url:-http://localhost:8080}
    ws_url=${ws_url:-ws://localhost:8080}
    
    cat > .env.local << EOF
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_API_URL=$api_url
NEXT_PUBLIC_WEBSOCKET_URL=$ws_url
EOF
    echo "✅ Development URLs set:"
    echo "   API: $api_url"
    echo "   WebSocket: $ws_url"
    
    # Kill any process on port 3000
    echo "Checking for processes on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    
    # Run development server
    echo "Starting development server..."
    npm run dev
}

set_prod() {
    echo "Setting production URLs..."
    read -p "Enter API URL: " api_url
    read -p "Enter WebSocket URL: " ws_url
    
    if [ -z "$api_url" ] || [ -z "$ws_url" ]; then
        echo "❌ Error: Both URLs are required for production"
        exit 1
    fi
    
    cat > .env.local << EOF
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_API_URL=$api_url
NEXT_PUBLIC_WEBSOCKET_URL=$ws_url
EOF
    echo "✅ Production URLs set:"
    echo "   API: $api_url"
    echo "   WebSocket: $ws_url"
    
    # Kill any process on port 3000
    echo "Checking for processes on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    
    # Build and start production server
    echo "Building for production..."
    npm run build
    echo "Starting production server..."
    npm run start
}

case "$1" in
    "dev")
        set_dev
        ;;
    "prod")
        set_prod
        ;;
    *)
        echo "Usage: $0 {dev|prod}"
        echo ""
        echo "Examples:"
        echo "  $0 dev    # Prompts for dev URLs with defaults"
        echo "  $0 prod   # Prompts for production URLs"
        exit 1
        ;;
esac