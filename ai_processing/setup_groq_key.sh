#!/bin/bash

# GROQ API Key Setup Script
# Run this after getting your GROQ API key from https://console.groq.com/

echo "🔑 GROQ API Key Setup"
echo "====================="
echo ""
echo "1. Go to: https://console.groq.com/"
echo "2. Sign up/Login"
echo "3. Create an API Key"
echo "4. Copy the key (starts with gsk_...)"
echo ""

read -p "Enter your GROQ API key: " GROQ_KEY

if [ -z "$GROQ_KEY" ]; then
    echo "❌ No key provided. Exiting."
    exit 1
fi

# Validate key format (should start with gsk_)
if [[ ! "$GROQ_KEY" =~ ^gsk_ ]]; then
    echo "⚠️  Warning: Key doesn't start with 'gsk_' - are you sure this is correct?"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    touch .env
fi

# Check if GROQ_API_KEY already exists in .env
if grep -q "GROQ_API_KEY" .env; then
    echo "🔄 Updating existing GROQ_API_KEY in .env..."
    # Use sed to replace the line
    sed -i.bak "s/^GROQ_API_KEY=.*/GROQ_API_KEY=$GROQ_KEY/" .env
else
    echo "➕ Adding GROQ_API_KEY to .env..."
    echo "GROQ_API_KEY=$GROQ_KEY" >> .env
fi

# Export for current session
export GROQ_API_KEY="$GROQ_KEY"

echo "✅ GROQ API Key configured!"
echo ""
echo "📋 Next steps:"
echo "1. Restart PM2 with environment: ../restart_pm2_with_env.sh"
echo "2. OR restart backend directly: ./clean_start_backend.sh"
echo "3. Test complete meeting processing: python test_complete_meeting.py"
echo ""
echo "💡 The key is saved in .env and exported for this session"
echo "🔧 For PM2 deployment, use: ../restart_pm2_with_env.sh"