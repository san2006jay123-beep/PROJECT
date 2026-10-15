@echo off
title ClassOS ? Starting Smart Classroom System
echo ========================================================
echo        ClassOS: Launching Backend and Frontend
echo ========================================================
echo.

set ROOT_DIR=%~dp0

echo [1/2] Starting FastAPI AI Backend on http://localhost:8000 ...
start "ClassOS Backend Engine" cmd /k "cd /d %ROOT_DIR% && python -m uvicorn app.main:app --app-dir classos\backend --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Vite Frontend Dashboard on https://localhost:5173 ...
start "ClassOS Frontend UI" cmd /k "cd /d %ROOT_DIR%classos\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ========================================================
echo  [LIVE] ClassOS is now running!
echo  Opening browser at https://localhost:5173 ...
echo ========================================================
start https://localhost:5173/

