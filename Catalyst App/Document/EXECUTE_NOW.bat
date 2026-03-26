@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo CREATING USER RECORD - LIVE EXECUTION
echo ================================================================================
echo.

echo STEP 1: Creating user via API
echo.

curl -X POST http://localhost:3000/server/catalyst_backend/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"Full_Name\":\"Test User Verification\",\"Email\":\"testuser@railway.com\",\"Password\":\"TestPassword123!\",\"Phone_Number\":\"9876543210\",\"Address\":\"Test Address, Test City\"}" ^
  -v 2>&1

echo.
echo.
echo ================================================================================
echo STEP 2: Testing Sign In
echo ================================================================================
echo.

timeout /t 2 /nobreak >nul

curl -X POST http://localhost:3000/server/catalyst_backend/api/auth/signin ^
  -H "Content-Type: application/json" ^
  -d "{\"Email\":\"testuser@railway.com\",\"Password\":\"TestPassword123!\"}" ^
  -v 2>&1

echo.
echo.
echo ================================================================================
echo STEP 3: Verifying in CloudScale
echo ================================================================================
echo.

echo Now check CloudScale:
echo 1. Open: https://creator.zoho.com/
echo 2. Go to: Tables ^> Users
echo 3. Search: testuser@railway.com
echo 4. Verify all fields are correct
echo 5. Check password is hashed (starts with $2b$12$)
echo.

pause
