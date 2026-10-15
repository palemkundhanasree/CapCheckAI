@echo off
setlocal
title CapCheck AI - Single-Click Launcher

:: Change directory to the folder containing this batch script safely
cd /d "%~dp0"

echo ======================================================================
echo                    CapCheck AI - One-Click Launcher
echo ======================================================================
echo [INFO] Current Directory: %~dp0
echo.

:: 1. Search for virtual environment Python in local venv
if exist "venv\Scripts\python.exe" (
    echo [INFO] Found local virtual environment at venv\Scripts\python.exe
    set "RUNNER=venv\Scripts\python.exe"
    goto :START_APP
)

:: 2. Check if python is in PATH
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Found Python in system PATH.
    set "RUNNER=python"
    goto :START_APP
)

:: 3. Check if Python Launcher (py) is in PATH
where py >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Found Python Launcher (py).
    set "RUNNER=py"
    goto :START_APP
)

:: 4. Check common Windows Python installation paths
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "RUNNER=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :START_APP
)
if exist "%ProgramFiles%\Python311\python.exe" (
    set "RUNNER=%ProgramFiles%\Python311\python.exe"
    goto :START_APP
)
if exist "%ProgramFiles%\Python312\python.exe" (
    set "RUNNER=%ProgramFiles%\Python312\python.exe"
    goto :START_APP
)

:: If Python was not found anywhere:
echo ======================================================================
echo [ERROR] Python was not found on your system!
echo.
echo Please install Python (version 3.10, 3.11, or 3.12) from:
echo https://www.python.org/downloads/
echo.
echo IMPORTANT: During installation, be sure to check the box:
echo "[X] Add python.exe to PATH"
echo ======================================================================
echo.
pause
exit /b 1

:START_APP
echo [INFO] Starting CapCheck AI using: %RUNNER%
echo.

"%RUNNER%" start_all.py

echo.
echo ======================================================================
echo [NOTICE] CapCheck AI session ended.
echo ======================================================================
echo.
pause

