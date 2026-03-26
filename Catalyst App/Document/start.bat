@echo off
echo Cleaning up...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
rd /s /q .build >nul 2>&1
timeout /t 1 /nobreak >nul
echo Starting Catalyst...
catalyst serve
