@echo off
setlocal

echo [1/4] Stopping Python and Node processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo [2/4] Waiting for process shutdown...
timeout /t 2 /nobreak >nul

echo [3/4] Removing .build folder...
if exist ".build" (
  rd /s /q ".build"
)

if exist ".build" (
  echo [WARN] .build is still locked. Close editors/terminals/antivirus lock and retry.
) else (
  echo [OK] .build removed.
)

echo [4/4] Starting Catalyst with verbose logs...
echo.
catalyst serve --verbose

endlocal
