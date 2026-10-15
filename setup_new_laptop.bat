@echo off
title ClassOS ? One-Click Setup for New Laptop
echo ========================================================
echo        ClassOS: Environment & Dependency Setup
echo ========================================================
echo.

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://python.org and check "Add Python to PATH".
    pause
    exit /b 1
)
python --version

echo.
echo [2/3] Installing Backend Dependencies...
cd /d "%~dp0classos\backend"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some pip packages had issues. Continuing...
)

echo.
echo [3/3] Installing Frontend Dependencies...
cd /d "%~dp0classos\frontend"
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js LTS from https://nodejs.org
    pause
    exit /b 1
)
call npm install

echo.
echo ========================================================
echo  [SUCCESS] ClassOS is fully setup and ready to run!
echo  Double-click "start_classos.bat" to start the system.
echo ========================================================
pause
