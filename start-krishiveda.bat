@echo off
REM Double-click this file to start KrishiVeda (backend + frontend) and open it in your browser.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [!] Python environment not found. Run setup-krishiveda.bat first.
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo [!] Frontend packages not found. Run setup-krishiveda.bat first.
  pause
  exit /b 1
)

echo Starting backend on http://localhost:8000 ...
start "KrishiVeda Backend" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000"

echo Starting frontend on http://localhost:5173 ...
start "KrishiVeda Frontend" cmd /k "cd frontend && npm run dev"

REM Give both servers a few seconds to start, then open the app
ping -n 9 127.0.0.1 >nul
start http://localhost:5173
echo.
echo KrishiVeda is running. Close the two black windows to stop it.
