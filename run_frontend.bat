@echo off
setlocal
title CapCheck AI - Vite Frontend Server
cd /d "%~dp0"

if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend npm packages...
    cd frontend
    call npm install
    cd ..
)

cd frontend
echo ======================================================================
echo           CapCheck AI - Frontend Server (Port 5173)
echo ======================================================================
echo Web Application URL: http://localhost:5173
echo.

call npm run dev

if %errorlevel% neq 0 (
    echo.
    echo Frontend server stopped with an error code.
    pause
)
