#!/bin/bash

echo "🔍 Groq API Setup Verification"
echo "=============================="
echo ""

# Get the correct project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_PROCESSING_DIR="$PROJECT_DIR/ai_processing"

echo "📁 Project directory: $PROJECT_DIR"
echo "📁 AI processing directory: $AI_PROCESSING_DIR"
echo ""

# Load environment from .env file for testing
if [ -f "$AI_PROCESSING_DIR/.env" ]; then
    set -a
    source "$AI_PROCESSING_DIR/.env"
    set +a
fi

# Check if .env exists and contains GROQ_API_KEY
echo "1. Checking .env file..."
if [ -f "$AI_PROCESSING_DIR/.env" ]; then
    echo "✅ .env file exists at $AI_PROCESSING_DIR/.env"
    if grep -q "GROQ_API_KEY" "$AI_PROCESSING_DIR/.env"; then
        echo "✅ GROQ_API_KEY found in .env"
        # Show key (masked)
        key=$(grep "GROQ_API_KEY" "$AI_PROCESSING_DIR/.env" | cut -d'=' -f2)
        if [ -n "$key" ]; then
            masked_key="${key:0:8}...${key: -4}"
            echo "   Key: $masked_key"
        else
            echo "❌ GROQ_API_KEY is empty in .env"
        fi
    else
        echo "❌ GROQ_API_KEY not found in .env"
    fi
else
    echo "❌ .env file not found at $AI_PROCESSING_DIR/.env"
    echo "   Run: cd ai_processing && ./setup_groq_key.sh"
fi

echo ""

# Check if key is in environment
echo "2. Checking environment variable..."
if [ -n "$GROQ_API_KEY" ]; then
    masked_env_key="${GROQ_API_KEY:0:8}...${GROQ_API_KEY: -4}"
    echo "✅ GROQ_API_KEY in environment: $masked_env_key"
else
    echo "❌ GROQ_API_KEY not in environment"
    echo "   Try: source ai_processing/.env"
fi

echo ""

# Check PM2 process environment
echo "3. Checking PM2 process environment..."
if command -v pm2 &> /dev/null; then
    echo "✅ PM2 is available"
    pm2 describe scrumbot-websocket > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ scrumbot-websocket process found"
        echo "   Checking process environment..."
        pm2 show scrumbot-websocket | grep -A 5 "env:"
    else
        echo "❌ scrumbot-websocket process not found"
        echo "   Available processes:"
        pm2 list
    fi
else
    echo "❌ PM2 not available"
fi

echo ""

# Test Groq API connection
echo "4. Testing Groq API connection..."
if [ -n "$GROQ_API_KEY" ]; then
    echo "   Testing API key..."
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer $GROQ_API_KEY" \
        -H "Content-Type: application/json" \
        "https://api.groq.com/openai/v1/models")
    
    if [ "$response" = "200" ]; then
        echo "✅ Groq API key is valid"
    else
        echo "❌ Groq API key test failed (HTTP $response)"
    fi
else
    echo "⚠️  Cannot test - no API key in environment"
fi

echo ""
echo "📋 Recommendations:"
if [ -f "$AI_PROCESSING_DIR/.env" ] && [ -z "$GROQ_API_KEY" ]; then
    echo "1. Load environment: source ai_processing/.env"
    echo "2. Restart PM2: ./restart_pm2_with_env.sh"
elif [ -z "$GROQ_API_KEY" ]; then
    echo "1. Setup API key: cd ai_processing && ./setup_groq_key.sh"
    echo "2. Restart PM2: ./restart_pm2_with_env.sh"
else
    echo "1. Environment looks good!"
    echo "2. If PM2 issues persist: ./restart_pm2_with_env.sh"
fi
echo "3. If API test fails: regenerate key at https://console.groq.com/"
echo "4. Check server logs: pm2 logs scrumbot-backend --lines 10"