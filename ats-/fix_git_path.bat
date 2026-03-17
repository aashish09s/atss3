@echo off
echo ========================================
echo Git PATH Fixer - Run as Administrator
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script needs to be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo Adding Git to System PATH permanently...
echo.

REM Get current System PATH
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "SYSTEM_PATH=%%B"

REM Check if Git is already in PATH
echo %SYSTEM_PATH% | findstr /C:"Git\bin" >nul
if %errorLevel% equ 0 (
    echo Git\bin is already in System PATH.
) else (
    echo %SYSTEM_PATH% | findstr /C:"Git\cmd" >nul
    if %errorLevel% equ 0 (
        echo Git\cmd is already in System PATH.
    ) else (
        REM Add Git\bin to System PATH
        setx /M PATH "%SYSTEM_PATH%;C:\Program Files\Git\bin" >nul
        if %errorLevel% equ 0 (
            echo Successfully added Git\bin to System PATH!
        ) else (
            echo Failed to add Git to System PATH.
            pause
            exit /b 1
        )
    )
)

echo.
echo ========================================
echo IMPORTANT: Please close and reopen your terminal
echo for the changes to take effect!
echo ========================================
echo.
pause

