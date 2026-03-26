#!/bin/bash
# Railway Ticketing System - User Creation Examples
# ==================================================
# Run these commands when the Catalyst server is properly configured

echo "🚀 Railway Ticketing System - User Creation Guide"
echo "=================================================="

# Server URL (update based on your setup)
SERVER_URL="http://localhost:3000/server/catalyst_backend"

echo -e "\n📋 Testing Server Health..."
curl -s "$SERVER_URL/api/health" | jq '.' 2>/dev/null || echo "Health check endpoint not responding properly"

echo -e "\n👤 Creating User Record #1 - Basic Registration"
curl -X POST "$SERVER_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "Full_Name": "Alice Johnson",
    "Email": "alice.johnson@railway.com",
    "Phone_Number": "9876543210",
    "Password": "Alice@123"
  }' | jq '.' 2>/dev/null

echo -e "\n👤 Creating User Record #2 - With Additional Details"
curl -X POST "$SERVER_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "Full_Name": "Bob Smith",
    "Email": "bob.smith@railway.com",
    "Phone_Number": "9876543211",
    "Password": "BobSecure@456",
    "Gender": "Male",
    "Address": "456 Train Lane, Mumbai, Maharashtra",
    "Date_of_Birth": "1990-05-15",
    "ID_Proof_Type": "Aadhar",
    "ID_Proof_Number": "1234-5678-9012"
  }' | jq '.' 2>/dev/null

echo -e "\n👤 Creating User Record #3 - Admin User"
curl -X POST "$SERVER_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "Full_Name": "Railway Admin",
    "Email": "admin@railway.com",
    "Phone_Number": "9876543212",
    "Password": "AdminSecure@789",
    "Role": "Admin",
    "Gender": "Male"
  }' | jq '.' 2>/dev/null

echo -e "\n🔐 Testing Login for Created User"
curl -X POST "$SERVER_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice.johnson@railway.com",
    "password": "Alice@123"
  }' | jq '.' 2>/dev/null

echo -e "\n📊 Listing All Users (Admin Required)"
curl -X GET "$SERVER_URL/api/users" \
  -H "X-User-Role: Admin" \
  -H "X-User-Email: admin@railway.com" | jq '.' 2>/dev/null

echo -e "\n✅ User creation examples completed!"
echo "Note: Install 'jq' for pretty JSON formatting: sudo apt-get install jq"