#!/bin/bash

# Comprehensive Groq API Key Loading Diagnosis Script
# Diagnoses all possible issues with Groq API key loading on EC2/production

set -e

echo "🔍 Comprehensive Groq API Key Loading Diagnosis"
echo "=================================================="
echo ""
echo "🎯 This script will diagnose why Groq API key may not be loading"
echo "   in your PM2/production environment"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions for colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
AI_PROCESSING_DIR="$SCRIPT_DIR/ai_processing"

echo "📁 Project Structure:"
echo "   Script location: $SCRIPT_DIR"
echo "   AI processing: $AI_PROCESSING_DIR"
echo ""

# Test 1: Check .env file locations and contents
echo "1️⃣ .env File Location & Content Analysis"
echo "==========================================="

ENV_LOCATIONS=(
    "$AI_PROCESSING_DIR/.env"
    "$PROJECT_ROOT/.env"
    "$PROJECT_ROOT/shared/.env"
    "$AI_PROCESSING_DIR/.env.prod"
    "$AI_PROCESSING_DIR/.env.production"
    "$HOME/.env"
    "/etc/environment"
)

FOUND_ENV_FILES=()
GROQ_KEYS=()

for env_file in "${ENV_LOCATIONS[@]}"; do
    if [ -f "$env_file" ]; then
        print_success "Found: $env_file"
        FOUND_ENV_FILES+=("$env_file")

        # Check permissions
        perms=$(ls -l "$env_file" | awk '{print $1}')
        echo "   Permissions: $perms"

        # Check if readable
        if [ -r "$env_file" ]; then
            print_success "   File is readable"

            # Check for GROQ_API_KEY
            if grep -q "GROQ_API_KEY" "$env_file"; then
                key=$(grep "GROQ_API_KEY" "$env_file" | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'")
                if [ -n "$key" ]; then
                    masked_key="${key:0:12}...${key: -4}"
                    print_success "   Contains GROQ_API_KEY: $masked_key"
                    GROQ_KEYS+=("$key")

                    # Validate key format
                    if [[ "$key" =~ ^gsk_ ]]; then
                        print_success "   Key format: Valid (starts with gsk_)"
                    else
                        print_warning "   Key format: Invalid (should start with gsk_)"
                    fi

                    # Check for whitespace issues
                    if [[ "$key" =~ [[:space:]] ]]; then
                        print_error "   Key contains whitespace!"
                    fi

                    # Check length
                    echo "   Key length: ${#key} characters"
                    if [ ${#key} -lt 50 ]; then
                        print_warning "   Key seems short for Groq API key"
                    fi
                else
                    print_error "   GROQ_API_KEY found but empty"
                fi
            else
                print_warning "   No GROQ_API_KEY found"
            fi
        else
            print_error "   File exists but not readable"
        fi
        echo ""
    fi
done

if [ ${#FOUND_ENV_FILES[@]} -eq 0 ]; then
    print_error "No .env files found in any standard locations!"
    echo "   Create one with: ./ai_processing/setup_groq_key_fixed.sh"
    echo ""
fi

# Test 2: Environment Variable Analysis
echo "2️⃣ Current Environment Variable Analysis"
echo "========================================"

# Check current shell environment
if [ -n "$GROQ_API_KEY" ]; then
    masked_current="${GROQ_API_KEY:0:12}...${GROQ_API_KEY: -4}"
    print_success "GROQ_API_KEY in current shell: $masked_current"
else
    print_warning "GROQ_API_KEY not in current shell environment"
fi

# Check system environment
if printenv | grep -q "GROQ_API_KEY"; then
    printenv_key=$(printenv GROQ_API_KEY)
    masked_printenv="${printenv_key:0:12}...${printenv_key: -4}"
    print_success "GROQ_API_KEY in printenv: $masked_printenv"
else
    print_warning "GROQ_API_KEY not in printenv"
fi

echo ""

# Test 3: PM2 Environment Analysis
echo "3️⃣ PM2 Environment Analysis"
echo "============================="

if command -v pm2 >/dev/null 2>&1; then
    print_success "PM2 is installed"

    # Check if PM2 processes exist
    if pm2 list 2>/dev/null | grep -q "scrumbot"; then
        print_success "ScrumBot PM2 processes found"

        # Show PM2 process list
        echo "PM2 Process Status:"
        pm2 list | grep -E "(name|scrumbot|online|stopped|errored)"

        # Check PM2 process environment for WebSocket server
        if pm2 list | grep -q "scrumbot-websocket"; then
            echo ""
            echo "📋 WebSocket PM2 Process Info:"
            pm2 show scrumbot-websocket | head -20

            # Try to get environment from PM2 process
            echo ""
            echo "🔍 Checking PM2 process environment..."

            # Get the PM2 process info and look for env variables
            pm2_env_output=$(pm2 show scrumbot-websocket 2>/dev/null || echo "Failed to get PM2 info")
            if echo "$pm2_env_output" | grep -q "GROQ_API_KEY"; then
                print_success "GROQ_API_KEY found in PM2 process environment"
            else
                print_error "GROQ_API_KEY NOT found in PM2 process environment"
            fi
        else
            print_warning "scrumbot-websocket PM2 process not found"
        fi
    else
        print_warning "No ScrumBot PM2 processes found"
        echo "   Start with: pm2 start ecosystem.config.js"
    fi
else
    print_error "PM2 not installed"
fi

echo ""

# Test 4: Python Environment Test
echo "4️⃣ Python Environment Test"
echo "=========================="

# Test Python can access the environment variable
cd "$AI_PROCESSING_DIR"

if [ -f "venv/bin/python" ]; then
    print_success "Python virtual environment found"

    # Test with virtual environment Python
    echo "🐍 Testing with venv Python:"
    ./venv/bin/python << 'EOF'
import os
from dotenv import load_dotenv

print("🔍 Python environment test:")

# Test 1: Direct environment access
groq_key = os.getenv('GROQ_API_KEY')
if groq_key:
    print(f"✅ Direct os.getenv(): {groq_key[:12]}...{groq_key[-4:]}")
else:
    print("❌ Direct os.getenv(): NOT FOUND")

# Test 2: Load .env file
try:
    load_dotenv('.env')
    groq_key_dotenv = os.getenv('GROQ_API_KEY')
    if groq_key_dotenv:
        print(f"✅ After load_dotenv(): {groq_key_dotenv[:12]}...{groq_key_dotenv[-4:]}")
    else:
        print("❌ After load_dotenv(): NOT FOUND")
except Exception as e:
    print(f"❌ load_dotenv() failed: {e}")

# Test 3: Check if .env file exists and is readable
import os.path
env_files = ['.env', '../.env', '../shared/.env']
for env_file in env_files:
    if os.path.exists(env_file):
        print(f"✅ Found env file: {env_file}")
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if 'GROQ_API_KEY' in content:
                    print(f"✅ {env_file} contains GROQ_API_KEY")
                else:
                    print(f"❌ {env_file} does not contain GROQ_API_KEY")
        except Exception as e:
            print(f"❌ Cannot read {env_file}: {e}")
    else:
        print(f"❌ No env file: {env_file}")

# Test 4: Try importing AI processor
try:
    import sys
    sys.path.append('app')
    from ai_processor import AIProcessor
    ai = AIProcessor()
    if ai.client:
        print("✅ AI Processor initialized successfully")
    else:
        print("❌ AI Processor client is None")
except Exception as e:
    print(f"❌ AI Processor initialization failed: {e}")
EOF

else
    print_error "Python virtual environment not found at venv/bin/python"
    echo "   Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

echo ""

# Test 5: Direct Groq API Test
echo "5️⃣ Direct Groq API Connection Test"
echo "==================================="

if [ ${#GROQ_KEYS[@]} -gt 0 ]; then
    # Use the first found key for testing
    TEST_KEY="${GROQ_KEYS[0]}"

    echo "🧪 Testing Groq API connectivity..."

    # Create a test script
    cat > /tmp/test_groq_direct.py << 'EOF'
import os
import sys
import json

# Get test key from environment
test_key = os.environ.get('TEST_GROQ_API_KEY')
if not test_key:
    print("❌ No test key provided")
    sys.exit(1)

try:
    import requests

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {test_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Test connection"}],
        "max_tokens": 5
    }

    print("📡 Connecting to Groq API...")
    response = requests.post(url, headers=headers, json=payload, timeout=15)

    print(f"📊 Response status: {response.status_code}")

    if response.status_code == 200:
        print("✅ Groq API connection successful!")
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            print("✅ API returned valid response")
        else:
            print("⚠️  API responded but format unexpected")
    elif response.status_code == 401:
        print("❌ API key invalid (401 Unauthorized)")
    elif response.status_code == 429:
        print("⚠️  Rate limited (429) - key is valid but usage exceeded")
    else:
        print(f"❌ API error: {response.status_code}")
        print(f"Response: {response.text}")

except ImportError:
    print("❌ Python requests library not available")
    print("   Install with: pip install requests")
except Exception as e:
    print(f"❌ Connection test failed: {e}")
EOF

    # Run the test
    TEST_GROQ_API_KEY="$TEST_KEY" python3 /tmp/test_groq_direct.py 2>/dev/null || print_error "Direct API test failed"
    rm -f /tmp/test_groq_direct.py

else
    print_warning "No Groq API keys found to test"
fi

echo ""

# Test 6: WebSocket Server Analysis
echo "6️⃣ WebSocket Server Startup Analysis"
echo "===================================="

if [ -f "$AI_PROCESSING_DIR/start_websocket_server.py" ]; then
    print_success "WebSocket server script found"

    echo "📄 Analyzing start_websocket_server.py:"

    # Check if it loads dotenv
    if grep -q "load_dotenv" "$AI_PROCESSING_DIR/start_websocket_server.py"; then
        print_success "Script contains load_dotenv() call"
    else
        print_error "Script does NOT contain load_dotenv() call"
        print_info "This is likely the main issue!"
    fi

    # Check if it checks for GROQ_API_KEY
    if grep -q "GROQ_API_KEY" "$AI_PROCESSING_DIR/start_websocket_server.py"; then
        print_success "Script references GROQ_API_KEY"
    else
        print_warning "Script does not reference GROQ_API_KEY"
    fi

else
    print_error "WebSocket server script not found"
fi

echo ""

# Test 7: File System Permissions
echo "7️⃣ File System Permissions Analysis"
echo "==================================="

echo "📁 Checking file permissions:"

# Check key files
key_files=(
    "$AI_PROCESSING_DIR/.env"
    "$AI_PROCESSING_DIR/start_websocket_server.py"
    "$AI_PROCESSING_DIR/app/ai_processor.py"
    "$AI_PROCESSING_DIR/venv/bin/python"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        perms=$(ls -la "$file" | awk '{print $1, $3, $4}')
        print_success "$(basename "$file"): $perms"
    else
        print_error "$(basename "$file"): NOT FOUND"
    fi
done

echo ""

# Summary and Recommendations
echo "📊 DIAGNOSIS SUMMARY"
echo "===================="
echo ""

# Count issues
issues_found=0
critical_issues=()

# Check for critical issues
if [ ${#FOUND_ENV_FILES[@]} -eq 0 ]; then
    critical_issues+=("No .env file found")
    ((issues_found++))
fi

if [ ${#GROQ_KEYS[@]} -eq 0 ]; then
    critical_issues+=("No GROQ_API_KEY found in any .env file")
    ((issues_found++))
fi

if [ -z "$GROQ_API_KEY" ]; then
    critical_issues+=("GROQ_API_KEY not in current environment")
    ((issues_found++))
fi

if ! grep -q "load_dotenv" "$AI_PROCESSING_DIR/start_websocket_server.py" 2>/dev/null; then
    critical_issues+=("WebSocket server doesn't load environment variables")
    ((issues_found++))
fi

# Display results
if [ $issues_found -eq 0 ]; then
    print_success "No critical issues found! Environment should be working."
else
    print_error "Found $issues_found critical issues:"
    for issue in "${critical_issues[@]}"; do
        echo "   • $issue"
    done
fi

echo ""
echo "🔧 RECOMMENDED FIXES"
echo "===================="

if [ ${#FOUND_ENV_FILES[@]} -eq 0 ] || [ ${#GROQ_KEYS[@]} -eq 0 ]; then
    echo "1. Create/fix .env file:"
    echo "   ./ai_processing/setup_groq_key_fixed.sh"
    echo ""
fi

if ! grep -q "load_dotenv" "$AI_PROCESSING_DIR/start_websocket_server.py" 2>/dev/null; then
    echo "2. Fix WebSocket server environment loading:"
    echo "   # Add to start_websocket_server.py:"
    echo "   from dotenv import load_dotenv"
    echo "   load_dotenv()"
    echo ""
fi

if pm2 list 2>/dev/null | grep -q "scrumbot"; then
    echo "3. Restart PM2 with fixed environment:"
    echo "   ./restart_pm2_with_env_fixed.sh"
    echo ""
fi

echo "4. Verify the fix:"
echo "   python test_groq_fix.py"
echo ""

print_info "Run this script again after applying fixes to verify they worked!"
