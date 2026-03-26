@echo off
setlocal enabledelayedexpansion

echo ========================================
echo CATALYST WHITE SCREEN FIX
echo ========================================
echo.

echo [1/4] Killing Node processes...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul
if !errorlevel! equ 0 (
    echo - Found Node process, terminating...
    for /f "tokens=2" %%A in ('tasklist /FI "IMAGENAME eq node.exe" ^| find /I "node.exe"') do (
        taskkill /PID %%A /F >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo ✓ Node process terminated
) else (
    echo ✓ No Node processes running
)
echo.

echo [2/4] Removing .build folder...
if exist .build (
    rd /s /q .build >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ .build removed
    ) else (
        echo ✗ Failed to remove .build (might be locked)
    )
) else (
    echo ✓ .build already clean
)
echo.

echo [3/4] Removing catalyst-frontend build...
if exist catalyst-frontend\build (
    rd /s /q catalyst-frontend\build >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ catalyst-frontend/build removed
    ) else (
        echo ✗ Failed to remove frontend build
    )
) else (
    echo ✓ catalyst-frontend/build already clean
)
echo.

echo [4/4] Starting Catalyst server...
echo ========================================
echo Server starting... (wait 30-60 seconds for full startup)
echo Navigate to: http://localhost:3000/app/
echo ========================================
echo.

catalyst serve

pause
