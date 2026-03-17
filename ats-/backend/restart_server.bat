@echo off
echo Stopping any existing server...
taskkill /f /im python.exe 2>nul
echo Starting FastAPI server...
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause

