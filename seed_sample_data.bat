@echo off
REM Smart Railway - Sample Data Seeder
REM Run this to create sample data in the system

set BASE_URL=http://localhost:3000/server/smart_railway_app_function

echo ==========================================
echo Smart Railway - Sample Data Seeder
echo ==========================================
echo.

REM Step 1: Create sample stations first
echo [1/3] Creating sample stations...
curl -s -X POST "%BASE_URL%/public-seed/stations" -H "Content-Type: application/json"
echo.
echo.

REM Step 2: Create sample trains
echo [2/3] Creating sample trains...
curl -s -X POST "%BASE_URL%/public-seed/trains" -H "Content-Type: application/json"
echo.
echo.

REM Step 3: Create sample fares
echo [3/3] Creating sample fares...
curl -s -X POST "%BASE_URL%/public-seed/fares" -H "Content-Type: application/json"
echo.
echo.

echo ==========================================
echo Sample data created successfully!
echo ==========================================
echo.
echo You can now:
echo  - View trains at /admin/trains
echo  - View stations at /admin/stations
echo  - View fares at /admin/fares
echo.
pause
