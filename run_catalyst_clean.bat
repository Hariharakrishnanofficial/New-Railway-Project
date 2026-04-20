@echo off
setlocal

echo [1/5] Stopping Python and Node processes...
REM taskkill can fail with "Access denied" in some environments; use PowerShell Stop-Process as a best-effort fallback.
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
powershell -NoProfile -Command "Get-Process python,pythonw,node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1

echo [2/5] Waiting for process shutdown...
timeout /t 2 /nobreak >nul

echo [3/5] Removing .build folder...
if exist ".build" (
  rd /s /q ".build" >nul 2>&1
)

if exist ".build" (
  echo [WARN] .build is still locked. Close editors/terminals/antivirus lock and retry.
  pause
  exit /b 1
) else (
  echo [OK] .build removed.
)

echo [4/5] Clearing Python cache...
for /d /r "functions" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [5/5] Starting Catalyst with verbose logs...
echo.
catalyst serve --verbose

endlocal
