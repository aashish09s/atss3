# Quick Fix for Git "not recognized" Error

## Problem
When you open a new terminal and run `git fetch` or other git commands, you get:
```
'git' is not recognized as an internal or external command
```

## Solution Options

### Option 1: Quick Fix (Works Immediately)
Run this command in your terminal **every time** you open a new terminal:
```cmd
set "PATH=%PATH%;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"
```

Or in PowerShell:
```powershell
$env:Path += ";C:\Program Files\Git\bin;C:\Program Files\Git\cmd"
```

### Option 2: Use the Setup Script (Recommended)
1. Double-click `git_setup.bat` - This will open a terminal with Git already configured
2. Then you can run any git commands

### Option 3: Permanent Fix (Requires Admin)
1. Right-click `fix_git_path.bat` and select "Run as administrator"
2. Follow the prompts
3. **Close and reopen your terminal** (or restart your computer)

### Option 4: Manual Fix via Windows Settings
1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", find and select "Path", then click "Edit"
5. Click "New" and add: `C:\Program Files\Git\bin`
6. Click "New" again and add: `C:\Program Files\Git\cmd`
7. Click "OK" on all windows
8. **Close and reopen your terminal** (or restart your computer)

## Verify It Works
After applying any fix, test with:
```cmd
git --version
```

You should see: `git version 2.51.2.windows.1` (or similar)

## Note
- Git is already installed on your system at `C:\Program Files\Git\`
- The issue is just that it's not in your PATH for new terminal sessions
- Once fixed, you won't need to do this again

