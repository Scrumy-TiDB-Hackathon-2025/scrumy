# Team Migration Instructions - Clean Git History Update

## 🚨 IMPORTANT: Repository History Has Been Cleaned

The main repository has been updated with a clean git history for hackathon submission. All Meetily prehistory has been removed, but **ALL your hackathon work is preserved**.

## For Teammates Who Already Have the Repo Cloned

### Step 1: Save Your Current Work
```bash
# Check if you have uncommitted changes
git status

# If you have uncommitted changes, save them
git add .
git commit -m "WIP: save current work before migration"

# Note which branch you're currently working on
git branch --show-current
```

### Step 2: Backup Your Local Work (Safety First)
```bash
# Create a backup branch of your current work
git branch backup-my-work-$(date +%Y%m%d)

# Verify backup was created
git branch | grep backup
```

### Step 3: Update Remote URL (If Needed)
```bash
# Check current remote
git remote -v

# If it shows the old repo, update to hackathon organization
git remote set-url origin git@github.com:Scrumy-TiDB-Hackathon-2025/scrumy.git
```

### Step 4: Fetch the Clean History
```bash
# Fetch the new clean branches
git fetch origin

# You'll see warnings about force-updates - this is expected
```

### Step 5: Reset Your Local Branches
```bash
# Reset main to match the clean version
git checkout main
git reset --hard origin/main

# Reset dev to match the clean version  
git checkout dev
git reset --hard origin/dev
```

### Step 6: Migrate Your Work to Clean Branch
```bash
# Create a new feature branch from clean dev
git checkout dev
git checkout -b feature/your-feature-name

# If you had work on a feature branch, cherry-pick your commits
# First, find your commits from the backup branch
git log backup-my-work-$(date +%Y%m%d) --oneline --since="2025-08-08"

# Cherry-pick your commits (replace COMMIT_HASH with actual hashes)
git cherry-pick COMMIT_HASH_1
git cherry-pick COMMIT_HASH_2
# ... continue for all your commits

# Alternative: If cherry-pick is complex, manually copy your changes
# 1. Check out your backup branch
# 2. Copy your modified files
# 3. Check out your new feature branch  
# 4. Paste and commit your changes
```

### Step 7: Verify Everything Works
```bash
# Check that your work is present
git log --oneline

# Test your application/code to ensure functionality
# Run any tests you have

# Check git status
git status
```

### Step 8: Push Your Clean Work
```bash
# Push your new feature branch
git push origin feature/your-feature-name

# Create PR to dev branch when ready
```

## Alternative: Fresh Clone Approach (Simpler)

If the above seems complex, you can start fresh:

### Option A: Fresh Clone
```bash
# Navigate to parent directory
cd ..

# Rename your old repo folder
mv scrumy scrumy-old-backup

# Fresh clone with clean history
git clone git@github.com:Scrumy-TiDB-Hackathon-2025/scrumy.git

# Copy your work files from backup
cp -r scrumy-old-backup/your-work-files scrumy/

# Commit your work to new clean repo
cd scrumy
git checkout dev
git checkout -b feature/your-feature-name
git add your-work-files
git commit -m "feat: add my hackathon work"
git push origin feature/your-feature-name
```

## What Changed in the Repository

### Before (Old Version):
- 90+ commits including 8 months of Meetily history
- Multiple branches with old timeline
- Confusing commit history for hackathon judges

### After (Clean Version):
- **main**: 1 clean commit with complete hackathon project
- **dev**: Same clean commit, ready for development
- **Timeline**: Only August 14, 2025 (hackathon appropriate)
- **All your work preserved**: Chrome extension, backend, frontend - everything is there

## Branch Strategy Going Forward

```
main (protected)
├── dev (development base)
    ├── feature/teammate1-work
    ├── feature/teammate2-work
    └── feature/your-work
```

## Need Help?

If you encounter issues:
1. **Don't panic** - your work is backed up
2. **Check your backup branch** - `git branch | grep backup`
3. **Ask for help** - share the specific error message
4. **Worst case**: Use the fresh clone approach

## Verification Checklist

- [ ] Remote URL updated to hackathon organization
- [ ] Local main and dev branches reset to clean versions
- [ ] Your work migrated to new feature branch
- [ ] Application/code still works correctly
- [ ] New feature branch pushed to origin
- [ ] Old backup branch preserved locally

Your work is safe and the repository is now ready for professional hackathon submission! 🚀