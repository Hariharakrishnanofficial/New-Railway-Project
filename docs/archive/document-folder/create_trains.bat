@echo off
REM Smart Railway - Create Sample Trains
REM Creates 5 realistic Indian Railway trains

set BASE_URL=http://localhost:3000/server/smart_railway_app_function

echo Creating sample trains...
echo.

REM Train 1: Rajdhani Express
echo Creating Rajdhani Express (12301)...
curl -s -X POST "%BASE_URL%/public-seed/trains" ^
  -H "Content-Type: application/json"

echo.

REM Now create trains with realistic data via admin endpoint
REM (You need to be logged in as admin for these)

echo.
echo ==========================================
echo To create trains with specific data, use:
echo ==========================================
echo.
echo curl -X POST "%BASE_URL%/trains" ^
echo   -H "Content-Type: application/json" ^
echo   -H "Authorization: Bearer YOUR_TOKEN" ^
echo   -d "{\"trainNumber\":\"12301\",\"trainName\":\"Rajdhani Express\",\"trainType\":\"Rajdhani\",\"fromStation\":\"NDLS\",\"toStation\":\"HWH\",\"departureTime\":\"16:55\",\"arrivalTime\":\"09:55\",\"duration\":\"17h 00m\"}"
echo.
pause
