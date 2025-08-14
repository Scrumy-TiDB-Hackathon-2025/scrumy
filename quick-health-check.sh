#!/bin/bash
# Quick health check script for ScrumBot developers

echo "🔍 ScrumBot Developer Health Check"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    echo "Make sure you're in the scrumy project root directory"
    exit 1
fi

# Check current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}📍 Current branch: $BRANCH${NC}"

if [[ ! "$BRANCH" =~ ^(dev|epic-[a-d]-.*)$ ]]; then
    echo -e "${YELLOW}⚠️  Warning: You should be on dev branch or your epic branch${NC}"
fi

# Check workspace setting
WORKSPACE=$(git config user.workspace)
if [ -n "$WORKSPACE" ]; then
    echo -e "${GREEN}🎯 Workspace set to: $WORKSPACE${NC}"
else
    echo -e "${YELLOW}⚠️  Workspace not set. Run: ./setup-git-hooks.sh${NC}"
fi

echo ""
echo "🔧 Checking Prerequisites..."

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node.js not installed${NC}"
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not installed${NC}"
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo -e "${GREEN}✅ Git: $GIT_VERSION${NC}"
else
    echo -e "${RED}❌ Git not installed${NC}"
fi

echo ""
echo "📁 Checking Project Structure..."

# Check main folders
check_folder() {
    local folder=$1
    local description=$2
    
    if [ -d "$folder" ]; then
        echo -e "${GREEN}✅ $description${NC}"
    else
        echo -e "${RED}❌ $description (missing)${NC}"
    fi
}

check_folder "chrome_extension" "Chrome Extension workspace"
check_folder "ai_processing" "AI Processing workspace"
check_folder "frontend_dashboard" "Frontend Dashboard workspace"
check_folder "shared" "Shared resources"

echo ""
echo "📋 Role-Specific Checks..."

# Determine role and run specific checks
case $WORKSPACE in
    "chrome_extension")
        echo -e "${BLUE}🔧 Dev A (Chrome Extension) Checks:${NC}"
        cd chrome_extension 2>/dev/null || { echo -e "${RED}❌ Cannot access chrome_extension folder${NC}"; exit 1; }
        
        [ -f manifest.json ] && echo -e "${GREEN}✅ manifest.json exists${NC}" || echo -e "${RED}❌ manifest.json missing${NC}"
        [ -f content.js ] && echo -e "${GREEN}✅ content.js exists${NC}" || echo -e "${RED}❌ content.js missing${NC}"
        [ -f popup.html ] && echo -e "${GREEN}✅ popup.html exists${NC}" || echo -e "${RED}❌ popup.html missing${NC}"
        [ -f popup.js ] && echo -e "${GREEN}✅ popup.js exists${NC}" || echo -e "${RED}❌ popup.js missing${NC}"
        
        cd - > /dev/null
        ;;
        
    "ai_processing")
        echo -e "${BLUE}🤖 Dev B/C (AI Backend/Tools) Checks:${NC}"
        cd ai_processing 2>/dev/null || { echo -e "${RED}❌ Cannot access ai_processing folder${NC}"; exit 1; }
        
        [ -f requirements.txt ] && echo -e "${GREEN}✅ requirements.txt exists${NC}" || echo -e "${RED}❌ requirements.txt missing${NC}"
        [ -f .env.example ] && echo -e "${GREEN}✅ .env.example exists${NC}" || echo -e "${RED}❌ .env.example missing${NC}"
        [ -f app/main.py ] && echo -e "${GREEN}✅ FastAPI main.py exists${NC}" || echo -e "${RED}❌ FastAPI main.py missing${NC}"
        
        # Check if virtual environment exists
        if [ -d "venv" ]; then
            echo -e "${GREEN}✅ Python virtual environment exists${NC}"
            
            # Check if we can activate it and import key modules
            if source venv/bin/activate 2>/dev/null && python -c "import fastapi" 2>/dev/null; then
                echo -e "${GREEN}✅ FastAPI installed in virtual environment${NC}"
            else
                echo -e "${YELLOW}⚠️  Virtual environment exists but dependencies may not be installed${NC}"
                echo "   Run: source venv/bin/activate && pip install -r requirements.txt"
            fi
            deactivate 2>/dev/null
        else
            echo -e "${YELLOW}⚠️  Python virtual environment not created${NC}"
            echo "   Run: python3 -m venv venv"
        fi
        
        # Check tools files (for Dev C)
        [ -f app/tools.py ] && echo -e "${GREEN}✅ Tools registry exists${NC}" || echo -e "${RED}❌ Tools registry missing${NC}"
        [ -f app/integrations.py ] && echo -e "${GREEN}✅ Integrations module exists${NC}" || echo -e "${RED}❌ Integrations module missing${NC}"
        
        cd - > /dev/null
        ;;
        
    "frontend_dashboard")
        echo -e "${BLUE}🖥️  Dev D (Frontend Dashboard) Checks:${NC}"
        cd frontend_dashboard 2>/dev/null || { echo -e "${RED}❌ Cannot access frontend_dashboard folder${NC}"; exit 1; }
        
        [ -f package.json ] && echo -e "${GREEN}✅ package.json exists${NC}" || echo -e "${RED}❌ package.json missing${NC}"
        [ -f app/page.js ] && echo -e "${GREEN}✅ Main page component exists${NC}" || echo -e "${RED}❌ Main page component missing${NC}"
        [ -f app/layout.js ] && echo -e "${GREEN}✅ Layout component exists${NC}" || echo -e "${RED}❌ Layout component missing${NC}"
        
        # Check if node_modules exists
        if [ -d "node_modules" ]; then
            echo -e "${GREEN}✅ Node modules installed${NC}"
        else
            echo -e "${YELLOW}⚠️  Node modules not installed${NC}"
            echo "   Run: npm install"
        fi
        
        cd - > /dev/null
        ;;
        
    *)
        echo -e "${YELLOW}⚠️  Workspace not set or unknown. Run ./setup-git-hooks.sh to set your role${NC}"
        ;;
esac

echo ""
echo "🔗 Checking Integration Points..."

# Check shared resources
[ -f shared/data-models/meeting-models.js ] && echo -e "${GREEN}✅ JavaScript data models exist${NC}" || echo -e "${RED}❌ JavaScript data models missing${NC}"
[ -f shared/api-contracts/audio-api.md ] && echo -e "${GREEN}✅ API contracts exist${NC}" || echo -e "${RED}❌ API contracts missing${NC}"

echo ""
echo "📖 Available Documentation..."

# Check if key guides exist
[ -f Epic_A_Chrome_Extension_Guide.md ] && echo -e "${GREEN}✅ Epic A Guide${NC}" || echo -e "${RED}❌ Epic A Guide missing${NC}"
[ -f Epic_B_AI_Processing_Guide.md ] && echo -e "${GREEN}✅ Epic B Guide${NC}" || echo -e "${RED}❌ Epic B Guide missing${NC}"
[ -f Epic_C_Tools_Integration_Guide.md ] && echo -e "${GREEN}✅ Epic C Guide${NC}" || echo -e "${RED}❌ Epic C Guide missing${NC}"
[ -f Epic_D_Frontend_Deployment_Guide.md ] && echo -e "${GREEN}✅ Epic D Guide${NC}" || echo -e "${RED}❌ Epic D Guide missing${NC}"
[ -f Project_Structure_Guide.md ] && echo -e "${GREEN}✅ Project Structure Guide${NC}" || echo -e "${RED}❌ Project Structure Guide missing${NC}"

echo ""
echo "🎯 Next Steps Based on Your Role:"

case $WORKSPACE in
    "chrome_extension")
        echo -e "${BLUE}Dev A (Chrome Extension):${NC}"
        echo "1. Read Epic_A_Chrome_Extension_Guide.md"
        echo "2. Load extension in Chrome for testing"
        echo "3. Start with Day 1: Basic extension structure"
        ;;
    "ai_processing")
        echo -e "${BLUE}Dev B (AI Backend) or Dev C (Tools):${NC}"
        echo "1. Read your respective Epic guide (B or C)"
        echo "2. Set up .env file with API keys and database connection"
        echo "3. Test FastAPI server: uvicorn app.main:app --reload"
        echo "4. Coordinate with your counterpart (B ↔ C)"
        ;;
    "frontend_dashboard")
        echo -e "${BLUE}Dev D (Frontend Dashboard):${NC}"
        echo "1. Read Epic_D_Frontend_Deployment_Guide.md"
        echo "2. Test development server: npm run dev"
        echo "3. Start building dashboard components"
        ;;
    *)
        echo -e "${YELLOW}Run ./setup-git-hooks.sh to set your role and get specific instructions${NC}"
        ;;
esac

echo ""
echo "✅ Health check complete!"
echo ""
echo "🆘 If you see any ❌ errors above:"
echo "1. Follow the setup instructions in DEVELOPER_SETUP_GUIDE.md"
echo "2. Check the troubleshooting section"
echo "3. Ask for help in team chat with specific error messages"