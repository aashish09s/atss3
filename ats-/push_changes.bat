@echo off
REM Add Git to PATH for this session
set "PATH=%PATH%;C:\Program Files\Git\bin;C:\Program Files\Git\cmd"

REM Verify Git is accessible
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not accessible. Please check your Git installation.
    pause
    exit /b 1
)

git config --global core.pager ""
git add -A
git commit -m "Add new panels and features - superadmin routes, updated routes and models, frontend components"
git push origin main

