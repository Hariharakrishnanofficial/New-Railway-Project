# PowerShell CRUD Testing Script for Railway Ticketing System
param([string]$ServerUrl = "http://localhost:3000/server/catalyst_backend")

Write-Host "=== RAILWAY TICKETING SYSTEM - CRUD TESTING ===" -ForegroundColor Magenta
Write-Host "Server URL: $ServerUrl" -ForegroundColor Cyan
Write-Host "Testing CRUD operations..." -ForegroundColor Blue

# Test User Registration
Write-Host "`nTesting User Registration..." -ForegroundColor Yellow
$userData = @{
    Full_Name = "Test User PS"
    Email = "testps@railway.com"
    Phone_Number = "9876543211"
    Password = "Test@123"
    Gender = "Male"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/auth/register" -Method Post -Body $userData -ContentType "application/json"
    Write-Host "✅ User Registration: SUCCESS" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json)" -ForegroundColor Cyan
}
catch {
    Write-Host "⚠️ User Registration: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Health Check
Write-Host "`nTesting Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$ServerUrl/api/health" -Method Get
    Write-Host "✅ Health Check: SUCCESS" -ForegroundColor Green
    Write-Host "Status: $($health.status)" -ForegroundColor Cyan
}
catch {
    Write-Host "⚠️ Health Check: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 CRUD Testing completed!" -ForegroundColor Green
