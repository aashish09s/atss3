# SynHireOne Backend Server Startup Script
Write-Host "Starting SynHireOne Backend Server..." -ForegroundColor Green
Write-Host ""

# Try different Python paths
$pythonPaths = @(
    "D:\hirepy (2)\hirepy (2)\hirepy\backend\venv\Scripts\python.exe",
    "C:\Users\ANSH\AppData\Local\Programs\Python\Python313\python.exe",
    "python"
)

$pythonFound = $false
$pythonPath = ""

foreach ($path in $pythonPaths) {
    try {
        if ($path -eq "python") {
            $result = & python --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pythonPath = "python"
                $pythonFound = $true
                break
            }
        } else {
            if (Test-Path $path) {
                $result = & $path --version 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $pythonPath = $path
                    $pythonFound = $true
                    break
                }
            }
        }
    } catch {
        continue
    }
}

if (-not $pythonFound) {
    Write-Host "ERROR: No working Python found!" -ForegroundColor Red
    Write-Host "Tried paths:" -ForegroundColor Yellow
    foreach ($path in $pythonPaths) {
        Write-Host "  - $path" -ForegroundColor Yellow
    }
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Using Python: $pythonPath" -ForegroundColor Green
Write-Host ""

# Start the server
Write-Host "Starting server on http://127.0.0.1:8002..." -ForegroundColor Green
Write-Host ""

try {
    & $pythonPath -c "import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8002, reload=False)"
} catch {
    Write-Host "ERROR: Failed to start server" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
}