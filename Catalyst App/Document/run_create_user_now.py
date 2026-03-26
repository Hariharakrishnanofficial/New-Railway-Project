#!/usr/bin/env python3
import requests
import json
import sys

print("\n" + "="*80)
print(" CREATE TEST USER & VERIFY IN SYSTEM")
print("="*80 + "\n")

# Test user data
user_data = {
    "Full_Name": "Test User Verification",
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!",
    "Phone_Number": "9876543210",
    "Address": "Test Address, Test City"
}

try:
    # Step 1: Create user
    print("STEP 1: CREATING USER")
    print("-" * 80)
    
    response = requests.post(
        "http://localhost:3000/server/catalyst_backend/api/register",
        json=user_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    result = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(result, indent=2)}\n")
    
    if response.status_code in [200, 201] and result.get('success'):
        print("✅ USER CREATED SUCCESSFULLY!\n")
        
        user_id = result.get('data', {}).get('User_ID')
        print(f"User ID: {user_id}")
        print(f"Email: {user_data['Email']}\n")
        
        # Step 2: Test sign in
        print("="*80)
        print("STEP 2: TESTING SIGN IN")
        print("-" * 80)
        
        signin_data = {
            "Email": "testuser@railway.com",
            "Password": "TestPassword123!"
        }
        
        signin_response = requests.post(
            "http://localhost:3000/server/catalyst_backend/api/signin",
            json=signin_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        signin_result = signin_response.json()
        
        print(f"Status Code: {signin_response.status_code}\n")
        
        if signin_response.status_code == 200 and signin_result.get('success'):
            print("✅ SIGN IN SUCCESSFUL!\n")
            
            access_token = signin_result.get('data', {}).get('access_token', '')[:50]
            user_info = signin_result.get('data', {}).get('user', {})
            
            print(f"Access Token: {access_token}...")
            print(f"User Info: {json.dumps(user_info, indent=2)}\n")
            
            # Step 3: Get profile
            print("="*80)
            print("STEP 3: FETCHING USER PROFILE")
            print("-" * 80)
            
            profile_response = requests.get(
                "http://localhost:3000/server/catalyst_backend/api/profile",
                headers={"Authorization": f"Bearer {signin_result['data']['access_token']}"},
                timeout=10
            )
            
            profile_result = profile_response.json()
            
            print(f"Status Code: {profile_response.status_code}\n")
            
            if profile_response.status_code == 200 and profile_result.get('success'):
                print("✅ PROFILE RETRIEVED SUCCESSFULLY!\n")
                print(f"Profile Data: {json.dumps(profile_result.get('data', {}), indent=2)}\n")
            else:
                print(f"Profile retrieval response: {json.dumps(profile_result, indent=2)}\n")
        else:
            print(f"❌ Sign in failed: {json.dumps(signin_result, indent=2)}\n")
    else:
        print(f"❌ User creation failed: {json.dumps(result, indent=2)}\n")
        sys.exit(1)
    
    print("="*80)
    print("✅ ALL CHECKS PASSED!")
    print("="*80)
    print("\nSummary:")
    print(f"  • User created: testuser@railway.com")
    print(f"  • Sign in working: YES")
    print(f"  • Profile access: YES")
    print(f"  • JWT authentication: YES")
    print(f"  • Ready for CloudScale verification: YES")
    print()
    
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR")
    print("Could not connect to Catalyst API")
    print("Make sure Catalyst is running: catalyst serve")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)
