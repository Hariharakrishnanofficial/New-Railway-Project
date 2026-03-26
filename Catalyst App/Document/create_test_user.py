#!/usr/bin/env python3
"""
Create test user in CloudScale via API
"""

import requests
import json
import sys

# API endpoint
api_url = "http://localhost:3000/server/catalyst_backend/api/register"

# Test user data
user_data = {
    "Full_Name": "Test User Verification",
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!",
    "Phone_Number": "9876543210",
    "Address": "Test Address, Test City"
}

print("=" * 80)
print("CREATING USER IN CLOUDSCALE")
print("=" * 80)
print()
print("📝 User Data:")
print(json.dumps(user_data, indent=2))
print()

try:
    print("🔄 Sending request to:", api_url)
    print()
    
    response = requests.post(
        api_url,
        json=user_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"📊 Response Status: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    print()
    
    result = response.json()
    
    if response.status_code in [200, 201]:
        print("✅ USER CREATED SUCCESSFULLY!")
        print()
        print("Response Data:")
        print(json.dumps(result, indent=2))
        print()
        
        # Extract user ID if available
        if isinstance(result, dict):
            if 'data' in result and isinstance(result['data'], dict):
                user_id = result['data'].get('User_ID') or result['data'].get('id')
                if user_id:
                    print(f"📌 User ID: {user_id}")
            elif 'User_ID' in result:
                print(f"📌 User ID: {result['User_ID']}")
    else:
        print("❌ ERROR CREATING USER")
        print()
        print("Response Data:")
        print(json.dumps(result, indent=2))
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR")
    print("⚠️  Could not connect to API server")
    print("Make sure Catalyst is running: catalyst serve")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)

print()
print("=" * 80)
print("✅ USER CREATION COMPLETE")
print()
print("Next Steps:")
print("1. Check CloudScale database for the user record")
print("2. Email: testuser@railway.com")
print("3. Verify password is hashed (not plain text)")
print("=" * 80)
