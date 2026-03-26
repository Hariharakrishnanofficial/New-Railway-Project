#!/usr/bin/env python3
"""
Create test user and show verification steps
Direct script for CloudScale testing
"""

import json
import sys

print("\n" + "="*80)
print(" CREATE TEST USER FOR CLOUDSCALE VERIFICATION")
print("="*80 + "\n")

# Step 1: Show what will be created
print("📝 STEP 1: User Data to Create")
print("-" * 80)

user_data = {
    "Full_Name": "Test User Verification",
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!",
    "Phone_Number": "9876543210",
    "Address": "Test Address, Test City"
}

for key, value in user_data.items():
    print(f"  {key:20} : {value}")

# Step 2: Show API call
print("\n📡 STEP 2: API Call Information")
print("-" * 80)
print("  Method    : POST")
print("  URL       : http://localhost:3000/server/catalyst_backend/api/register")
print("  Headers   : Content-Type: application/json")
print("  Body      :")
for line in json.dumps(user_data, indent=2).split('\n'):
    print(f"    {line}")

# Step 3: Try to create user
print("\n🔄 STEP 3: Creating User...")
print("-" * 80)

try:
    import requests
    
    response = requests.post(
        "http://localhost:3000/server/catalyst_backend/api/register",
        json=user_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    result = response.json()
    
    print(f"  Status Code : {response.status_code}")
    
    if response.status_code in [200, 201]:
        print("  Result      : ✅ SUCCESS\n")
        
        # Step 4: Show response
        print("📊 STEP 4: API Response")
        print("-" * 80)
        print(json.dumps(result, indent=2))
        
        # Step 5: Extract user ID
        print("\n🔍 STEP 5: Extract User Information")
        print("-" * 80)
        
        if 'data' in result:
            user_info = result['data']
            user_id = user_info.get('User_ID') or user_info.get('id')
            print(f"  User ID     : {user_id}")
            print(f"  Email       : {user_info.get('Email')}")
            print(f"  Name        : {user_info.get('Full_Name')}")
            print(f"  Role        : {user_info.get('Role')}")
            print(f"  Status      : {user_info.get('Account_Status')}")
            print(f"  Created At  : {user_info.get('Created_At')}")
        
        # Step 6: CloudScale verification steps
        print("\n☁️  STEP 6: Verify in CloudScale")
        print("-" * 80)
        print("""
  1. Open CloudScale Creator Web Console
     URL: https://creator.zoho.com/
  
  2. Select your project: "Railway Ticketing System"
  
  3. Navigate to Tables
     • Click on "Tables" in left sidebar
     • Find and open "Users" table
  
  4. Search for the new user
     • Look for email: testuser@railway.com
     • Or search in the table grid
  
  5. Verify the record contains:
     ✓ Full_Name      : Test User Verification
     ✓ Email          : testuser@railway.com
     ✓ Password_Hash  : $2b$12$... (bcrypt encrypted)
     ✓ Phone_Number   : 9876543210
     ✓ Address        : Test Address, Test City
     ✓ Role           : User
     ✓ Account_Status : Active
     ✓ Created_At     : (recent timestamp)
     ✓ Updated_At     : (recent timestamp)
  
  6. Verify password is HASHED (not plain text)
     • Click on Password_Hash field
     • Should see: $2b$12$... or similar bcrypt format
     • Should NOT see: TestPassword123!
        """)
        
        # Step 7: Testing
        print("\n🧪 STEP 7: Test Sign In with Created User")
        print("-" * 80)
        print("""
  Try signing in with these credentials:
  
  Email    : testuser@railway.com
  Password : TestPassword123!
  
  Option A: Using Browser
  • Open: http://localhost:3000/app/auth
  • Click "Sign In" tab
  • Enter email and password
  • Should redirect to dashboard
  
  Option B: Using API
  • POST http://localhost:3000/server/catalyst_backend/api/signin
  • Headers: Content-Type: application/json
  • Body:
    {
      "Email": "testuser@railway.com",
      "Password": "TestPassword123!"
    }
  • Should return JWT access_token
        """)
        
    else:
        print(f"  Result      : ❌ FAILED\n")
        print("  Response:")
        print(json.dumps(result, indent=2))
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("  ❌ CONNECTION ERROR")
    print("\n  Could not connect to Catalyst API server")
    print("  Make sure Catalyst is running:")
    print("    catalyst serve")
    sys.exit(1)
    
except ImportError:
    print("  ❌ REQUESTS LIBRARY NOT FOUND")
    print("\n  Install it with:")
    print("    pip install requests")
    print("\n  Or use: create_user_curl.bat")
    sys.exit(1)
    
except Exception as e:
    print(f"  ❌ ERROR: {str(e)}")
    sys.exit(1)

print("\n" + "="*80)
print(" ✅ USER CREATED SUCCESSFULLY")
print(" → Now check CloudScale (see STEP 6 above)")
print("="*80 + "\n")
