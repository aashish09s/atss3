@echo off
echo ============================================
echo   Deployment Verification Script
echo ============================================
echo.

echo [1/5] Checking DNS...
echo.
nslookup ats.trihdiconsulting.com
echo.
echo ^> DNS should show your server IP address
echo.
pause

echo.
echo [2/5] Checking PM2 Status...
echo.
pm2 status
echo.
pause

echo.
echo [3/5] Checking Backend Port (8000)...
echo.
netstat -ano | findstr :8000
echo.
echo ^> Should show process listening on port 8000
echo.
pause

echo.
echo [4/5] Checking Caddy Logs (last 10 lines)...
echo.
if exist "C:\recent\hirepy\caddy\logs\access.log" (
    powershell "Get-Content C:\recent\hirepy\caddy\logs\access.log -Tail 10"
) else (
    echo Caddy logs not found - Caddy may not be running
)
echo.
pause

echo.
echo [5/5] Testing Backend Health Endpoint...
echo.
curl -k https://ats.trihdiconsulting.com/api/health 2>nul
if errorlevel 1 (
    echo.
    echo Testing localhost instead...
    curl http://localhost:8000/api/health 2>nul
)
echo.
echo.

echo ============================================
echo   Verification Complete
echo ============================================
echo.
echo Next steps:
echo   1. Visit: https://ats.trihdiconsulting.com
echo   2. Check browser console for any errors
echo   3. Try logging in to test API connection
echo.
pause

