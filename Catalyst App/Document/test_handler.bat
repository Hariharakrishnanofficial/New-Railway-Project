@echo off
setlocal enabledelayedexpansion

cd /d "F:\Railway Project Backend\Catalyst App\functions\catalyst_backend"

echo Testing if modules can be imported...
echo.

python -c "from app import handler; print('✓ App handler loaded successfully')" 2>&1

if !errorlevel! equ 0 (
    echo.
    echo ✅ SUCCESS: Function should work
) else (
    echo.
    echo ❌ FAILED: There's an import error
)

pause
