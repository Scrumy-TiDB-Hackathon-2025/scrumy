# ScrumBot Team Rules (Hackathon Edition)

## 🚨 3 Simple Rules to Avoid Chaos

### 1. Branch Strategy (CRITICAL)
```
Dev A: Work on epic-a-chrome-extension branch
Dev B: Work on epic-b-ai-backend branch  
Dev C: Work on epic-c-tools-integration branch
Dev D: Work on epic-d-frontend-dashboard branch
```

### 2. Git Workflow (PROPER)
```bash
# Create your feature branch from dev
git checkout dev
git pull origin dev
git checkout -b epic-a-chrome-extension  # Use your epic name

# Work and commit on your branch
git add .
git commit -m "[EPIC-A] What you did"
git push origin epic-a-chrome-extension

# Create PR to merge into dev branch
# Go to GitHub → Create Pull Request → epic-a-chrome-extension → dev
```

### 3. Communication (ESSENTIAL)
```
Before modifying shared files: Ask in team chat
If you break something: Immediately tell the team
If you need help: Ask specific questions with error messages
```

## 🔧 Optional: Prevent Accidents
Run this once to prevent accidentally modifying other people's files:
```bash
chmod +x setup-git-hooks.sh
./setup-git-hooks.sh
```

That's it! Focus on coding, not process. 🚀