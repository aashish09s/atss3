@echo off
REM Quick deployment script
echo.
echo ============================================
echo   HirePy Quick Deployment
echo   Domain: ats.trihdiconsulting.com
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Building frontend...
cd frontend
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [2/4] Starting backend with PM2...
if not exist "logs" mkdir logs
pm2 delete hirepy-backend 2>nul
pm2 start ecosystem.config.js
pm2 save

echo.
echo [3/4] PM2 Status:
pm2 status

echo.
echo [4/4] Deployment Complete!
echo.
echo Next steps:
echo   1. Make sure Caddy is running: caddy run --config C:\recent\hirepy\Caddyfile
echo   2. Visit: https://ats.trihdiconsulting.com
echo.
echo Useful commands:
echo   pm2 logs            - View backend logs
echo   pm2 restart all     - Restart application
echo   pm2 monit           - Monitor processes
echo.
pause

