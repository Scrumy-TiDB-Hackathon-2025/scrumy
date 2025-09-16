#!/bin/bash

# GROQ API Key Setup Script (FIXED VERSION)
# Enhanced with validation, multiple location support, and EC2 compatibility

set -e

echo "🔑 GROQ API Key Setup (Enhanced)"
echo "================================="
echo ""

# Function to validate API key format
validate_groq_key() {
    local key="$1"

    if [ -z "$key" ]; then
        echo "❌ Key is empty"
        return 1
    fi

    if [[ ${#key} -lt 50 ]]; then
        echo "⚠️  Key seems too short (${#key} chars)"
        return 1
    fi

    if [[ ! "$key" =~ ^gsk_ ]]; then
        echo "⚠️  Key doesn't start with 'gsk_' - this may be incorrect"
        echo "    Valid Groq API keys start with 'gsk_'"
        return 1
    fi

    if [[ "$key" =~ [[:space:]] ]]; then
        echo "❌ Key contains whitespace - check for copy/paste errors"
        return 1
    fi

    echo "✅ Key format looks valid"
    return 0
}

# Function to test API key with actual Groq API
test_groq_key() {
    local key="$1"
    echo "🧪 Testing key with Groq API..."

    # Create temp test script
    cat > /tmp/test_groq.py << 'EOF'
import os
import sys
try:
    import requests
    import json
except ImportError:
    print("❌ Python requests library not available")
    sys.exit(1)

api_key = os.environ.get('TEST_GROQ_KEY')
if not api_key:
    print("❌ No test key provided")
    sys.exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 10
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    if response.status_code == 200:
        print("✅ API key works!")
        sys.exit(0)
    elif response.status_code == 401:
        print("❌ API key invalid (401 Unauthorized)")
        sys.exit(1)
    elif response.status_code == 429:
        print("⚠️  Rate limited, but key seems valid")
        sys.exit(0)
    else:
        print(f"⚠️  Unexpected response: {response.status_code}")
        sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"⚠️  Network error (key format OK): {e}")
    sys.exit(0)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
EOF

    # Test the key
    TEST_GROQ_KEY="$key" python3 /tmp/test_groq.py
    local test_result=$?
    rm -f /tmp/test_groq.py

    return $test_result
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Project root: $PROJECT_ROOT"

# Show current API key status if exists
echo ""
echo "🔍 Checking current API key status..."

# Check multiple possible .env locations
ENV_LOCATIONS=(
    "$SCRIPT_DIR/.env"
    "$PROJECT_ROOT/.env"
    "$PROJECT_ROOT/shared/.env"
    "$SCRIPT_DIR/.env.prod"
)

CURRENT_ENV_FILE=""
CURRENT_KEY=""

for env_file in "${ENV_LOCATIONS[@]}"; do
    if [ -f "$env_file" ]; then
        echo "   Found .env: $env_file"
        if grep -q "GROQ_API_KEY" "$env_file"; then
            CURRENT_ENV_FILE="$env_file"
            CURRENT_KEY=$(grep "GROQ_API_KEY" "$env_file" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
            break
        fi
    fi
done

if [ -n "$CURRENT_KEY" ]; then
    masked_key="${CURRENT_KEY:0:10}...${CURRENT_KEY: -4}"
    echo "   Current key: $masked_key"
    echo "   Location: $CURRENT_ENV_FILE"

    # Validate current key
    if validate_groq_key "$CURRENT_KEY"; then
        echo ""
        read -p "🤔 Key exists and looks valid. Replace it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "✅ Keeping existing key"
            echo ""
            echo "🧪 Testing existing key..."
            if test_groq_key "$CURRENT_KEY"; then
                echo "🎉 Existing key works perfectly!"
                exit 0
            else
                echo "❌ Existing key failed test - continuing with replacement..."
            fi
        fi
    fi
else
    echo "   No existing GROQ_API_KEY found"
fi

echo ""
echo "📋 How to get your GROQ API key:"
echo "1. Go to: https://console.groq.com/"
echo "2. Sign up/Login with GitHub, Google, or email"
echo "3. Go to 'API Keys' section"
echo "4. Click 'Create API Key'"
echo "5. Copy the key (starts with gsk_...)"
echo ""

# Get the API key
while true; do
    read -p "🔑 Enter your GROQ API key: " GROQ_KEY

    if [ -z "$GROQ_KEY" ]; then
        echo "❌ No key provided. Please enter a valid key or Ctrl+C to exit."
        continue
    fi

    # Validate the key
    if validate_groq_key "$GROQ_KEY"; then
        break
    else
        echo ""
        read -p "🤔 Use this key anyway? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            break
        fi
    fi
done

# Test the API key
echo ""
if test_groq_key "$GROQ_KEY"; then
    echo "🎉 API key validated successfully!"
else
    echo ""
    read -p "⚠️  API key test failed. Save anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Aborted. Please check your key and try again."
        exit 1
    fi
fi

# Determine where to save the .env file
if [ -n "$CURRENT_ENV_FILE" ]; then
    ENV_FILE="$CURRENT_ENV_FILE"
else
    ENV_FILE="$SCRIPT_DIR/.env"
fi

echo ""
echo "📝 Saving to: $ENV_FILE"

# Create .env file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    echo "📄 Creating new .env file..."
    touch "$ENV_FILE"
fi

# Backup existing .env file
if [ -f "$ENV_FILE" ] && [ -s "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backed up existing .env file"
fi

# Update or add GROQ_API_KEY
if grep -q "GROQ_API_KEY" "$ENV_FILE"; then
    echo "🔄 Updating existing GROQ_API_KEY..."
    # Use a more reliable sed replacement
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/^GROQ_API_KEY=.*/GROQ_API_KEY=$GROQ_KEY/" "$ENV_FILE"
    else
        # Linux
        sed -i "s/^GROQ_API_KEY=.*/GROQ_API_KEY=$GROQ_KEY/" "$ENV_FILE"
    fi
else
    echo "➕ Adding GROQ_API_KEY to .env..."
    echo "GROQ_API_KEY=$GROQ_KEY" >> "$ENV_FILE"
fi

# Set proper permissions
chmod 600 "$ENV_FILE"

# Export for current session
export GROQ_API_KEY="$GROQ_KEY"

echo "✅ GROQ API Key configured successfully!"
echo ""
echo "📋 Configuration summary:"
echo "   Key length: ${#GROQ_KEY} characters"
echo "   Key prefix: ${GROQ_KEY:0:10}..."
echo "   Saved to: $ENV_FILE"
echo "   Permissions: $(ls -l "$ENV_FILE" | awk '{print $1}')"
echo ""

# Show next steps based on environment
if command -v pm2 >/dev/null 2>&1 && pm2 list >/dev/null 2>&1; then
    echo "🔧 PM2 detected - Next steps for production:"
    echo "   1. Restart PM2 with environment:"
    echo "      $PROJECT_ROOT/restart_pm2_with_env_fixed.sh"
    echo "   2. Check PM2 status:"
    echo "      pm2 status"
    echo "   3. Monitor logs:"
    echo "      pm2 logs scrumbot-websocket --lines 10"
elif [ -f "$SCRIPT_DIR/start_websocket_server.py" ]; then
    echo "🔧 Development environment - Next steps:"
    echo "   1. Test WebSocket server:"
    echo "      cd $SCRIPT_DIR && python start_websocket_server.py"
    echo "   2. Test complete pipeline:"
    echo "      cd $PROJECT_ROOT && python test_groq_fix.py"
fi

echo ""
echo "🧪 Verify installation:"
echo "   cd $SCRIPT_DIR"
echo "   python -c \"import os; print('GROQ_API_KEY:', os.getenv('GROQ_API_KEY', 'NOT_FOUND')[:15] + '...')\""
echo ""
echo "💡 Tips:"
echo "   - Keep your API key secret"
echo "   - Monitor usage at https://console.groq.com/"
echo "   - Set up rate limiting if needed"
echo "   - The key is now in your environment for this session"
