#!/bin/bash

# Start backend with test environment for Groq API testing
# This script loads the test environment and starts the backend

echo "🧪 Starting ScrumBot backend with test environment..."

# Check if test environment file exists
if [ -f ".env.test" ]; then
    echo "✅ Loading test environment variables..."
    export $(cat .env.test | grep -v '^#' | xargs)
    echo "🔑 Groq API key loaded: ${GROQ_API_KEY:0:10}...${GROQ_API_KEY: -4}"
else
    echo "⚠️ No .env.test file found - using system environment"
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️ No virtual environment found - using system Python"
fi

# Test Groq integration first
echo "🧪 Testing Groq integration..."
python test_groq_integration.py

echo ""
echo "🚀 Starting backend server..."
echo "Press Ctrl+C to stop"

# Start the backend
python start_backend.py