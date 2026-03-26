@echo off
setlocal enabledelayedexpansion

cd /d "F:\Railway Project Backend\Catalyst App"

echo ========================================
echo REBUILD & SERVE
echo ========================================
echo.

echo [1/3] Killing existing processes...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul
if !errorlevel! equ 0 (
    for /f "tokens=2" %%A in ('tasklist /FI "IMAGENAME eq node.exe" ^| find /I "node.exe"') do (
        taskkill /PID %%A /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo ✓ Processes terminated
)
echo.

echo [2/3] Rebuilding frontend...
cd catalyst-frontend
echo - Running: npm run build
npm run build >nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Frontend rebuilt successfully
) else (
    echo ✗ Frontend build failed
    echo Retrying with verbose output...
    npm run build
    pause
    exit /b 1
)
cd ..
echo.

echo [3/3] Cleaning .build folder...
if exist .build (
    rd /s /q .build >nul 2>&1
    echo ✓ .build cleaned
)
echo.

echo ========================================
echo Starting Catalyst server...
echo ========================================
echo Wait 30-60 seconds for startup
echo Then navigate to: http://localhost:3000/app/
echo.

catalyst serve

pause
