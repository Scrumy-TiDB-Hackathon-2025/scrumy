#!/bin/bash

echo "🔍 Groq API Setup Verification"
echo "=============================="
echo ""

# Check if .env exists and contains GROQ_API_KEY (check both locations)
echo "1. Checking .env file..."
if [ -f "ai_processing/.env" ]; then
    echo "✅ .env file exists in ai_processing/"
    if grep -q "GROQ_API_KEY" ai_processing/.env; then
        echo "✅ GROQ_API_KEY found in ai_processing/.env"
        # Show key (masked)
        key=$(grep "GROQ_API_KEY" ai_processing/.env | cut -d'=' -f2)
        masked_key="${key:0:8}...${key: -4}"
        echo "   Key: $masked_key"
    else
        echo "❌ GROQ_API_KEY not found in ai_processing/.env"
    fi
elif [ -f ".env" ]; then
    echo "✅ .env file exists in root"
    if grep -q "GROQ_API_KEY" .env; then
        echo "✅ GROQ_API_KEY found in .env"
        # Show key (masked)
        key=$(grep "GROQ_API_KEY" .env | cut -d'=' -f2)
        masked_key="${key:0:8}...${key: -4}"
        echo "   Key: $masked_key"
    else
        echo "❌ GROQ_API_KEY not found in .env"
    fi
else
    echo "❌ .env file not found in either location"
fi

echo ""

# Check if key is in environment
echo "2. Checking environment variable..."
if [ -n "$GROQ_API_KEY" ]; then
    masked_env_key="${GROQ_API_KEY:0:8}...${GROQ_API_KEY: -4}"
    echo "✅ GROQ_API_KEY in environment: $masked_env_key"
else
    echo "❌ GROQ_API_KEY not in environment"
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
echo "1. If .env exists but environment is empty: source .env"
echo "2. If PM2 process doesn't have key: restart PM2 with ecosystem file"
echo "3. If API test fails: regenerate key at https://console.groq.com/"
echo "4. Check server logs for Groq-related errors"