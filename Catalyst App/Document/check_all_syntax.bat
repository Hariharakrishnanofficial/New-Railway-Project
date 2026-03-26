@echo off
setlocal enabledelayedexpansion

echo Testing Python syntax in key files...

set "backend_dir=F:\Railway Project Backend\Catalyst App\functions\catalyst_backend"

echo.
echo 1. Checking core/exceptions.py
python -m py_compile "%backend_dir%\core\exceptions.py"
if !errorlevel! equ 0 (
    echo    ✓ Syntax OK
) else (
    echo    ✗ SYNTAX ERROR
    exit /b 1
)

echo.
echo 2. Checking services/auth_crud_service.py  
python -m py_compile "%backend_dir%\services\auth_crud_service.py"
if !errorlevel! equ 0 (
    echo    ✓ Syntax OK
) else (
    echo    ✗ SYNTAX ERROR
    exit /b 1
)

echo.
echo 3. Checking routes/auth_crud.py
python -m py_compile "%backend_dir%\routes\auth_crud.py"
if !errorlevel! equ 0 (
    echo    ✓ Syntax OK
) else (
    echo    ✗ SYNTAX ERROR
    exit /b 1
)

echo.
echo ✅ All syntax checks passed!
