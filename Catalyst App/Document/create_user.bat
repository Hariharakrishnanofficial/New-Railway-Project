@echo off
setlocal enabledelayedexpansion

cd /d "F:\Railway Project Backend\Catalyst App"

echo ========================================
echo CREATE TEST USER IN CLOUDSCALE
echo ========================================
echo.

echo Checking if Python is available...
python --version >nul 2>&1
if !errorlevel! equ 0 (
    echo ✓ Python found
    echo.
    echo Running user creation script...
    echo.
    python create_test_user.py
    
    if !errorlevel! equ 0 (
        echo.
        echo ✅ SUCCESS - Check CloudScale for the new user!
    ) else (
        echo.
        echo ❌ Script failed
    )
) else (
    echo ✗ Python not found in PATH
    echo.
    echo Trying with python3...
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ Python3 found
        echo.
        python3 create_test_user.py
    ) else (
        echo ✗ Python3 also not found
        echo.
        echo Please ensure Python is installed and added to PATH
    )
)

echo.
pause
