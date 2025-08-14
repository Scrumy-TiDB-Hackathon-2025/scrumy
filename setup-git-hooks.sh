#!/bin/bash
# Setup script for Git hooks and team workflow

echo "🚀 Setting up ScrumBot team workflow..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Run this script from the root of the scrumy repository"
    exit 1
fi

# Create pre-commit hook
echo "📝 Creating pre-commit hook..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# ScrumBot pre-commit hook - prevents commits outside workspace

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 ScrumBot pre-commit check...${NC}"

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Only allow commits to dev branch
if [ "$BRANCH" != "dev" ]; then
    echo -e "${RED}❌ ERROR: Commits only allowed on dev branch${NC}"
    echo -e "Current branch: ${YELLOW}$BRANCH${NC}"
    echo -e "Switch to dev: ${GREEN}git checkout dev${NC}"
    exit 1
fi

# Get workspace setting
WORKSPACE=$(git config user.workspace)

if [ -z "$WORKSPACE" ]; then
    echo -e "${RED}❌ ERROR: Workspace not set${NC}"
    echo -e "Set your workspace with one of:"
    echo -e "${GREEN}git config user.workspace chrome_extension${NC}    # Dev A"
    echo -e "${GREEN}git config user.workspace ai_processing${NC}       # Dev B"
    echo -e "${GREEN}git config user.workspace ai_processing${NC}       # Dev C (tools files)"
    echo -e "${GREEN}git config user.workspace frontend_dashboard${NC}  # Dev D"
    exit 1
fi

# Get changed files
CHANGED_FILES=$(git diff --cached --name-only)

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No files staged for commit${NC}"
    exit 0
fi

echo -e "Workspace: ${GREEN}$WORKSPACE${NC}"
echo -e "Checking files:"

# Check each changed file
VIOLATIONS=0
for file in $CHANGED_FILES; do
    ALLOWED=false
    
    case $WORKSPACE in
        "chrome_extension")
            if [[ $file =~ ^chrome_extension/ ]] || [[ $file =~ ^shared/ ]] || [[ $file =~ ^assets/ ]]; then
                ALLOWED=true
            fi
            ;;
        "ai_processing")
            if [[ $file =~ ^ai_processing/ ]] || [[ $file =~ ^shared/ ]] || [[ $file =~ ^integration/ ]] || [[ $file =~ ^assets/ ]]; then
                ALLOWED=true
            fi
            ;;
        "frontend_dashboard")
            if [[ $file =~ ^frontend_dashboard/ ]] || [[ $file =~ ^shared/ ]] || [[ $file =~ ^assets/ ]]; then
                ALLOWED=true
            fi
            ;;
    esac
    
    if [ "$ALLOWED" = true ]; then
        echo -e "  ${GREEN}✅ $file${NC}"
    else
        echo -e "  ${RED}❌ $file (outside workspace)${NC}"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

# Check for sensitive files
echo -e "\n${YELLOW}🔒 Checking for sensitive data...${NC}"
SENSITIVE_PATTERNS=("password" "secret" "key" "token" "api_key")
SENSITIVE_VIOLATIONS=0

for file in $CHANGED_FILES; do
    if [ -f "$file" ]; then
        for pattern in "${SENSITIVE_PATTERNS[@]}"; do
            if grep -qi "$pattern.*=" "$file" 2>/dev/null; then
                echo -e "  ${RED}⚠️  $file may contain sensitive data (pattern: $pattern)${NC}"
                SENSITIVE_VIOLATIONS=$((SENSITIVE_VIOLATIONS + 1))
            fi
        done
    fi
done

# Final decision
if [ $VIOLATIONS -gt 0 ]; then
    echo -e "\n${RED}❌ COMMIT BLOCKED: $VIOLATIONS workspace violations${NC}"
    echo -e "You can only modify files in your workspace and shared folders"
    exit 1
fi

if [ $SENSITIVE_VIOLATIONS -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  WARNING: Potential sensitive data detected${NC}"
    echo -e "Please review your files and use environment variables for secrets"
    echo -e "Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ COMMIT CANCELLED${NC}"
        exit 1
    fi
fi

echo -e "\n${GREEN}✅ Pre-commit checks passed!${NC}"
exit 0
EOF

# Make pre-commit hook executable
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed"

# Prompt user to set workspace
echo ""
echo "🎯 Please set your workspace:"
echo "Choose your role:"
echo "1) Dev A - Chrome Extension (chrome_extension/)"
echo "2) Dev B - AI Backend (ai_processing/)"
echo "3) Dev C - Tools Integration (ai_processing/app/ tools files)"
echo "4) Dev D - Frontend Dashboard (frontend_dashboard/)"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        git config user.workspace "chrome_extension"
        echo "✅ Workspace set to: chrome_extension"
        ;;
    2)
        git config user.workspace "ai_processing"
        echo "✅ Workspace set to: ai_processing"
        ;;
    3)
        git config user.workspace "ai_processing"
        echo "✅ Workspace set to: ai_processing (focus on tools files)"
        echo "⚠️  Remember: Only modify tools-related files in ai_processing/app/"
        ;;
    4)
        git config user.workspace "frontend_dashboard"
        echo "✅ Workspace set to: frontend_dashboard"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

# Create commit message template
echo ""
echo "📝 Setting up commit message template..."
cat > .git/commit-template << 'EOF'
[EPIC-X] Brief description of changes

# Longer description (optional)
# - What was changed
# - Why it was changed
# - Any breaking changes

# Epic prefixes:
# [EPIC-A] - Chrome Extension changes
# [EPIC-B] - AI Backend changes  
# [EPIC-C] - Tools Integration changes
# [EPIC-D] - Frontend Dashboard changes
# [FIX] - Bug fixes
# [DOCS] - Documentation updates
# [INTEGRATION] - Cross-team coordination
EOF

git config commit.template .git/commit-template
echo "✅ Commit message template set"

# Set up useful git aliases
echo ""
echo "🔧 Setting up helpful git aliases..."
git config alias.st "status"
git config alias.co "checkout"
git config alias.br "branch"
git config alias.ci "commit"
git config alias.unstage "reset HEAD --"
git config alias.last "log -1 HEAD"
git config alias.visual "!gitk"
git config alias.team-log "log --oneline --graph --decorate --all -10"

echo "✅ Git aliases configured"

# Final instructions
echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure you're on the dev branch: git checkout dev"
echo "2. Pull latest changes: git pull origin dev"
echo "3. Start working in your designated folder"
echo "4. Use the commit template: git commit (without -m)"
echo ""
echo "🔍 Useful commands:"
echo "  git st                 # Check status"
echo "  git team-log          # See recent team commits"
echo "  git config user.workspace  # Check your workspace setting"
echo ""
echo "⚠️  Remember: The pre-commit hook will prevent commits outside your workspace!"
echo "If you need to modify shared files, coordinate with your team first."