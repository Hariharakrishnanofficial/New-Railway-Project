# Railway Ticketing System - User Creation PowerShell Examples
# ===========================================================

param(
    [string]$ServerUrl = "http://localhost:3000/server/catalyst_backend"
)

Write-Host "🚀 Railway Ticketing System - User Creation Guide" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Test server health
Write-Host "`n📋 Testing Server Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$ServerUrl/api/health" -Method Get
    Write-Host "Server Status: $($health.status)" -ForegroundColor Green
}
catch {
    Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# User Creation Example 1: Basic Registration
Write-Host "`n👤 Creating User Record #1 - Basic Registration" -ForegroundColor Blue
$user1 = @{
    Full_Name = "Alice Johnson"
    Email = "alice.johnson@railway.com"
    Phone_Number = "9876543210"
    Password = "Alice@123"
}

try {
    $response1 = Invoke-RestMethod -Uri "$ServerUrl/api/auth/register" -Method Post -Body ($user1 | ConvertTo-Json) -ContentType "application/json"
    Write-Host "✅ User 1 Created Successfully!" -ForegroundColor Green
    Write-Host "Response: $($response1 | ConvertTo-Json -Depth 3)" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ User 1 Creation Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# User Creation Example 2: With Additional Details
Write-Host "`n👤 Creating User Record #2 - With Additional Details" -ForegroundColor Blue
$user2 = @{
    Full_Name = "Bob Smith"
    Email = "bob.smith@railway.com"
    Phone_Number = "9876543211"
    Password = "BobSecure@456"
    Gender = "Male"
    Address = "456 Train Lane, Mumbai, Maharashtra"
    Date_of_Birth = "1990-05-15"
    ID_Proof_Type = "Aadhar"
    ID_Proof_Number = "1234-5678-9012"
}

try {
    $response2 = Invoke-RestMethod -Uri "$ServerUrl/api/auth/register" -Method Post -Body ($user2 | ConvertTo-Json) -ContentType "application/json"
    Write-Host "✅ User 2 Created Successfully!" -ForegroundColor Green
    Write-Host "User ID: $($response2.user_id)" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ User 2 Creation Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# User Creation Example 3: Admin User
Write-Host "`n👤 Creating User Record #3 - Admin User" -ForegroundColor Blue
$adminUser = @{
    Full_Name = "Railway Admin"
    Email = "admin@railway.com"
    Phone_Number = "9876543212"
    Password = "AdminSecure@789"
    Role = "Admin"
    Gender = "Male"
}

try {
    $response3 = Invoke-RestMethod -Uri "$ServerUrl/api/auth/register" -Method Post -Body ($adminUser | ConvertTo-Json) -ContentType "application/json"
    Write-Host "✅ Admin User Created Successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Admin User Creation Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test Login
Write-Host "`n🔐 Testing Login for Created User" -ForegroundColor Blue
$loginData = @{
    email = "alice.johnson@railway.com"
    password = "Alice@123"
}

try {
    $loginResponse = Invoke-RestMethod -Uri "$ServerUrl/api/auth/login" -Method Post -Body ($loginData | ConvertTo-Json) -ContentType "application/json"
    Write-Host "✅ Login Successful!" -ForegroundColor Green
    if ($loginResponse.access_token) {
        Write-Host "Access Token: $($loginResponse.access_token.Substring(0, 30))..." -ForegroundColor Cyan
    }
}
catch {
    Write-Host "❌ Login Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# List Users (Admin)
Write-Host "`n📊 Listing All Users (Admin Required)" -ForegroundColor Blue
$adminHeaders = @{
    "X-User-Role" = "Admin"
    "X-User-Email" = "admin@railway.com"
}

try {
    $allUsers = Invoke-RestMethod -Uri "$ServerUrl/api/users" -Method Get -Headers $adminHeaders
    Write-Host "✅ Retrieved Users Successfully!" -ForegroundColor Green
    Write-Host "Total Users: $($allUsers.data.data.Count)" -ForegroundColor Cyan
}
catch {
    Write-Host "❌ Failed to retrieve users: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ User creation examples completed!" -ForegroundColor Green
Write-Host "🎉 Check the Zoho Creator Users table to verify records!" -ForegroundColor Magenta