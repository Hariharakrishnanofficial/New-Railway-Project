#!/usr/bin/env python3
"""
Debug script for user creation endpoint
"""
import requests
import json

print("\n" + "="*80)
print("DEBUGGING USER CREATION ENDPOINT")
print("="*80 + "\n")

# Test 1: Check if API is running
print("TEST 1: Checking if API is accessible...")
try:
    response = requests.get("http://localhost:3000/server/catalyst_backend/api/health", timeout=5)
    print(f"✅ API is running - Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
except Exception as e:
    print(f"❌ API not accessible: {e}\n")
    exit(1)

# Test 2: Try user registration with proper JSON
print("TEST 2: Testing user registration with proper JSON...")

user_data = {
    "Full_Name": "Test User",
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!"
}

print(f"Request Data: {json.dumps(user_data, indent=2)}\n")

try:
    response = requests.post(
        "http://localhost:3000/server/catalyst_backend/api/auth/register",
        json=user_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}\n")
    
    try:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}\n")
    except:
        print(f"Response (raw): {response.text}\n")
    
    if response.status_code in [200, 201]:
        print("✅ User creation successful!\n")
    else:
        print("❌ User creation failed\n")
        print("Troubleshooting:")
        print("1. Check if Catalyst backend is properly initialized")
        print("2. Check CloudScale database connectivity")
        print("3. Review backend logs for errors")
        
except Exception as e:
    print(f"❌ Request failed: {e}\n")
    print("Troubleshooting:")
    print("1. Is Catalyst server running? (catalyst serve)")
    print("2. Check network connectivity")
    print("3. Verify API endpoint is correct")
