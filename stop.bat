@echo off
setlocal enabledelayedexpansion
title Stop CapCheck AI Services

echo ======================================================================
echo                 Stopping CapCheck AI Services
echo ======================================================================
echo.

set "STOPPED=0"

:: Kill process listening on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    set "PID=%%a"
    if defined PID if "!PID!" neq "0" (
        echo Stopping Backend process [PID !PID!] on port 8000...
        taskkill /F /PID !PID! >nul 2>&1
        set "STOPPED=1"
    )
)

:: Kill process listening on port 5173 (Frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 "') do (
    set "PID=%%a"
    if defined PID if "!PID!" neq "0" (
        echo Stopping Frontend process [PID !PID!] on port 5173...
        taskkill /F /PID !PID! >nul 2>&1
        set "STOPPED=1"
    )
)

echo.
if "!STOPPED!"=="1" (
    echo [SUCCESS] CapCheck AI services have been stopped cleanly.
) else (
    echo [INFO] No active CapCheck AI processes were found running on ports 8000 or 5173.
)
echo.
timeout /t 3 >nul 2>&1
