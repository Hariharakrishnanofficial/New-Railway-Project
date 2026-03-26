@echo off
setlocal enabledelayedexpansion

cd /d "F:\Railway Project Backend\Catalyst App"

echo ========================================
echo CATALYST SPA ROUTING FIX
echo ========================================
echo.

echo [1/4] Killing existing processes...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul
if !errorlevel! equ 0 (
    for /f "tokens=2" %%A in ('tasklist /FI "IMAGENAME eq node.exe" ^| find /I "node.exe"') do (
        taskkill /PID %%A /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo ✓ Node processes terminated
) else (
    echo ✓ No Node processes running
)
echo.

echo [2/4] Cleaning build artifacts...
if exist .build (
    rd /s /q .build >nul 2>&1
    echo ✓ .build cleaned
)
echo.

echo [3/4] Verifying frontend build...
if not exist catalyst-frontend\build\index.html (
    echo ! index.html not found, rebuilding frontend...
    cd catalyst-frontend
    npm run build >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ Frontend rebuilt
    ) else (
        echo ✗ Frontend build failed, see errors:
        npm run build
        pause
        exit /b 1
    )
    cd ..
) else (
    echo ✓ Frontend build exists
)
echo.

echo [4/4] Starting Catalyst with SPA routing...
echo ========================================
echo Server starting with SPA routing fix...
echo.
echo Routes:
echo  • /app/ → React Dashboard (SPA)
echo  • /app/auth → React Auth Page (now fixed!)
echo  • /server/catalyst_backend/* → API endpoints
echo.
echo Navigate to: http://localhost:3000/app/
echo Or test auth: http://localhost:3000/app/auth
echo ========================================
echo.

catalyst serve

pause
