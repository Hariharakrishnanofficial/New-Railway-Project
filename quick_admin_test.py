#!/usr/bin/env python3
"""
Quick Admin Employee Login Test
Verifies the admin employee can be authenticated via session endpoint
"""

import requests
import json

BASE_URL = "http://localhost:3001/server/smart_railway_app_function"

def test_admin_login():
    """Test admin employee login via session endpoint"""
    
    # Admin credentials  
    admin_credentials = {
        "email": "admin@railway.com",
        "password": "AdminPassword2024!"
    }
    
    print("🔐 Testing Admin Employee Login...")
    print(f"📧 Email: {admin_credentials['email']}")
    
    try:
        # Test employee login endpoint
        response = requests.post(
            f"{BASE_URL}/session/employee/login",
            json=admin_credentials,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login Success!")
            print(f"📄 Response Data: {json.dumps(data, indent=2)}")
            
            # Extract session info
            session_id = data.get('data', {}).get('session_id')
            csrf_token = data.get('data', {}).get('csrf_token')
            user_role = data.get('data', {}).get('user_role')
            
            if session_id and csrf_token:
                print(f"🎫 Session ID: {session_id}")
                print(f"🔒 CSRF Token: {csrf_token}")
                print(f"👤 User Role: {user_role}")
                
                # Test invitation endpoint with session
                cookies = response.cookies
                headers = {
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/json"
                }
                
                print("\n🧪 Testing Employee Invitations Endpoint...")
                invite_response = requests.get(
                    f"{BASE_URL}/admin/employees/invitations",
                    cookies=cookies,
                    headers=headers
                )
                
                print(f"📡 Invitations Response: {invite_response.status_code}")
                if invite_response.status_code == 200:
                    print("✅ Admin access confirmed! Ready to test invitation creation.")
                    
                    # Test invitation creation
                    print("\n🧪 Testing Invitation Creation...")
                    create_invite_response = requests.post(
                        f"{BASE_URL}/admin/employees/invite",
                        json={
                            "email": "test@example.com",
                            "role": "Employee",
                            "department": "Test Department",
                            "designation": "Test Position"
                        },
                        cookies=cookies,
                        headers=headers
                    )
                    
                    print(f"📡 Create Invitation Response: {create_invite_response.status_code}")
                    if create_invite_response.status_code == 201:
                        print("✅ Invitation creation works!")
                        print(f"📄 Response: {json.dumps(create_invite_response.json(), indent=2)}")
                    else:
                        print(f"❌ Invitation creation failed: {create_invite_response.text}")
                    
                    return True
                else:
                    print(f"❌ Admin access failed: {invite_response.text}")
                    return False
            else:
                print("⚠️  Login succeeded but missing session data")
                return False
        else:
            print(f"❌ Login Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Error: {e}")
        return False

if __name__ == "__main__":
    success = test_admin_login()
    if success:
        print("\n🎉 Admin employee setup is working! You can now:")
        print("1. Go to http://localhost:3001/app/#/admin/employee-invitations")
        print("2. Login with admin@railway.com / AdminPassword2024!")
        print("3. Test the employee invitation system")
    else:
        print("\n⚠️  Admin employee setup needs attention.")
        print("Run the Database Expert agent result first")