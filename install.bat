@echo off
setlocal
title CapCheck AI - Installer
cd /d "%~dp0"

echo ======================================================================
echo                     CapCheck AI - Installer
echo ======================================================================
echo.

if exist "venv\Scripts\python.exe" (
    set "RUNNER=venv\Scripts\python.exe"
    goto :RUN_INSTALL
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "RUNNER=python"
    goto :RUN_INSTALL
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "RUNNER=py"
    goto :RUN_INSTALL
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :RUN_INSTALL
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :RUN_INSTALL
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :RUN_INSTALL
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :RUN_INSTALL
)

echo [ERROR] Python was not found. Please install Python 3.10+ from https://www.python.org/
pause
exit /b 1

:RUN_INSTALL
echo [INFO] Running environment setup using: %RUNNER%
"%RUNNER%" -c "import sys, subprocess, os; from pathlib import Path; root = Path('.'); venv = root / 'venv'; sys.exit(0) if (venv / 'Scripts' / 'python.exe').exists() else subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])"
if exist "venv\Scripts\pip.exe" (
    echo [INFO] Installing backend requirements...
    venv\Scripts\pip.exe install -r backend\requirements.txt
)
if exist "frontend\package.json" (
    echo [INFO] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)
if not exist ".env" (
    copy .env.example .env >nul
)
if exist "venv\Scripts\python.exe" (
    echo [INFO] Initializing database...
    venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); from app.db.session import init_db; init_db()"
)

echo.
echo ======================================================================
echo [SUCCESS] CapCheck AI is fully installed and ready!
echo Double-click run.bat to launch the application.
echo ======================================================================
echo.
pause
