@echo off
setlocal enabledelayedexpansion

cd /d "F:\Railway Project Backend\Catalyst App"

echo ========================================
echo CREATE TEST USER VIA API
echo ========================================
echo.

echo Preparing user data...
set "email=testuser@railway.com"
set "name=Test User Verification"
set "password=TestPassword123!"
set "phone=9876543210"
set "address=Test Address, Test City"

echo.
echo 📝 Creating user:
echo   Email: !email!
echo   Name: !name!
echo   Password: !password!
echo.

echo 🔄 Sending request to API...
echo.

curl -X POST http://localhost:3000/server/catalyst_backend/api/register ^
  -H "Content-Type: application/json" ^
  -d "{\"Full_Name\":\"!name!\",\"Email\":\"!email!\",\"Password\":\"!password!\",\"Phone_Number\":\"!phone!\",\"Address\":\"!address!\"}" ^
  -v

echo.
echo.
echo ========================================
echo ✅ Request sent!
echo.
echo Next: Check CloudScale for new user record
echo Email: !email!
echo ========================================

pause
