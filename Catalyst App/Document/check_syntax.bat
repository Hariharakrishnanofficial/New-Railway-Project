@echo off
cd /d "F:\Railway Project Backend\Catalyst App\functions\catalyst_backend"
python -m py_compile routes/auth_crud.py
if %ERRORLEVEL% EQU 0 (
    echo Auth_crud.py Syntax: OK
) else (
    echo Auth_crud.py Syntax: FAILED
)

python -m py_compile services/auth_crud_service.py
if %ERRORLEVEL% EQU 0 (
    echo Auth_crud_service.py Syntax: OK
) else (
    echo Auth_crud_service.py Syntax: FAILED
)

python -c "import routes.auth_crud; print('Import OK')" 2>&1
