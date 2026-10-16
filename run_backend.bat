@echo off
setlocal
title CapCheck AI - FastAPI Backend Server
cd /d "%~dp0"

set "PYTHONPATH=backend"

if exist "venv\Scripts\python.exe" (
    set "RUNNER=venv\Scripts\python.exe"
    goto :START_BACKEND
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "RUNNER=python"
    goto :START_BACKEND
)

echo [ERROR] Python environment not found. Please run run.bat first to set up the environment.
pause
exit /b 1

:START_BACKEND
if not exist ".env" (
    copy .env.example .env >nul
)

"%RUNNER%" -c "import sys; sys.path.insert(0, 'backend'); from app.db.session import init_db; init_db()" >nul 2>&1

echo ======================================================================
echo           CapCheck AI - Backend Server (Port 8000)
echo ======================================================================
echo API Docs: http://127.0.0.1:8000/docs
echo Health:   http://127.0.0.1:8000/api/v1/health
echo Press Ctrl+C to terminate.
echo.

"%RUNNER%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

if %errorlevel% neq 0 (
    echo.
    echo Backend server stopped with an error code.
    pause
)
