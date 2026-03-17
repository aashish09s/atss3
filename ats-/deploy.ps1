# Deployment script for ats.trihdiconsulting.com
# This script builds the frontend, sets up PM2, and reloads Caddy

Write-Host "🚀 Starting deployment..." -ForegroundColor Cyan

# Navigate to project directory
$projectRoot = "C:\recent\hirepy\hirepy"
Set-Location $projectRoot

# Step 1: Build Frontend
Write-Host "`n📦 Building frontend..." -ForegroundColor Yellow
Set-Location frontend

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Gray
    npm install
}

# Build for production
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Frontend built successfully" -ForegroundColor Green
Set-Location ..

# Step 2: Check if PM2 is installed
Write-Host "`n🔍 Checking PM2 installation..." -ForegroundColor Yellow
$pm2Installed = Get-Command pm2 -ErrorAction SilentlyContinue

if (-not $pm2Installed) {
    Write-Host "PM2 not found. Installing PM2 globally..." -ForegroundColor Yellow
    npm install -g pm2
}

# Step 3: Setup PM2
Write-Host "`n⚙️  Setting up PM2..." -ForegroundColor Yellow
Set-Location $projectRoot

# Create logs directory if it doesn't exist
$logsDir = Join-Path $projectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Stop existing processes
Write-Host "Stopping existing PM2 processes..." -ForegroundColor Gray
pm2 delete all 2>$null

# Start backend with PM2
Write-Host "Starting backend with PM2..." -ForegroundColor Gray
pm2 start ecosystem.config.js

# Save PM2 process list
pm2 save

# Setup PM2 startup script
Write-Host "Setting up PM2 startup script..." -ForegroundColor Gray
pm2 startup
pm2 save

# Step 4: Reload Caddy
Write-Host "`n🔄 Reloading Caddy..." -ForegroundColor Yellow

# Check if Caddy is running
$caddyProcess = Get-Process caddy -ErrorAction SilentlyContinue

if ($caddyProcess) {
    # Reload Caddy configuration
    $caddyAdminApi = Get-Content "C:\recent\hirepy\caddy\admin.json" -ErrorAction SilentlyContinue
    if ($caddyAdminApi) {
        Write-Host "Reloading Caddy configuration..." -ForegroundColor Gray
        curl -X POST "http://localhost:2019/load" -H "Content-Type: application/json" -d "@C:\recent\hirepy\Caddyfile" 2>$null
    } else {
        Write-Host "Restarting Caddy service..." -ForegroundColor Gray
        Restart-Service caddy -ErrorAction SilentlyContinue
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Could not restart Caddy service. Please restart it manually." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠️  Caddy is not running. Please start Caddy manually:" -ForegroundColor Yellow
    Write-Host "   caddy run --config C:\recent\hirepy\Caddyfile" -ForegroundColor Cyan
}

# Step 5: Show status
Write-Host "`n✅ Deployment completed!" -ForegroundColor Green
Write-Host "`n📊 PM2 Status:" -ForegroundColor Cyan
pm2 status

Write-Host "`n🔗 Application URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: https://ats.trihdiconsulting.com" -ForegroundColor White
Write-Host "   Backend API: https://ats.trihdiconsulting.com/api" -ForegroundColor White

Write-Host "`n📝 Useful PM2 commands:" -ForegroundColor Cyan
Write-Host "   pm2 status          - View process status" -ForegroundColor White
Write-Host "   pm2 logs            - View logs" -ForegroundColor White
Write-Host "   pm2 restart all     - Restart all processes" -ForegroundColor White
Write-Host "   pm2 monit           - Monitor processes" -ForegroundColor White

