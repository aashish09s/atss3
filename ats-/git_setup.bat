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

echo Git is now available in this terminal session.
echo You can now run git commands like: git fetch, git push, etc.
echo.
echo Current git version:
git --version
echo.

REM Keep the terminal open
cmd /k

