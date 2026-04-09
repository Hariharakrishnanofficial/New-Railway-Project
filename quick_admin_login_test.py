#!/usr/bin/env python3
"""
Quick Admin Login Test Script
Tests just the admin login functionality to diagnose the 401 issue
"""

import requests
import json
import urllib3

# Disable SSL warnings for localhost testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test configuration
BASE_URL = "http://localhost:3001/server/smart_railway_app_function"
ADMIN_CREDENTIALS = {
    "email": "admin@admin.com",  # Updated to match .env file
    "password": "SecureRailwayAdmin2024!"  # Updated to match fix script
}

def test_admin_login():
    """Test admin login step by step."""
    print("🔍 Testing Admin Login Flow")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Get CSRF token
    print("1. Getting CSRF token...")
    try:
        csrf_response = session.get(f"{BASE_URL}/csrf-token")
        print(f"   Status: {csrf_response.status_code}")
        
        if csrf_response.status_code == 200:
            csrf_data = csrf_response.json()
            csrf_token = csrf_data.get('csrf_token')
            print(f"   ✅ CSRF token: {csrf_token[:10]}...")
        else:
            print(f"   ❌ Failed to get CSRF token: {csrf_response.text}")
            csrf_token = None
            
    except Exception as e:
        print(f"   ❌ Error getting CSRF token: {e}")
        csrf_token = None
    
    # Step 2: Test employee login endpoint
    print("\n2. Testing employee login...")
    try:
        headers = {'Content-Type': 'application/json'}
        if csrf_token:
            headers['X-CSRF-Token'] = csrf_token
        
        login_url = f"{BASE_URL}/session/employee/login"
        print(f"   URL: {login_url}")
        print(f"   Credentials: {ADMIN_CREDENTIALS}")
        print(f"   Headers: {headers}")
        
        response = session.post(login_url, 
                              json=ADMIN_CREDENTIALS, 
                              headers=headers)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            login_data = response.json()
            if login_data.get('status') == 'success':
                print("   ✅ Login successful!")
                return session, csrf_token
            else:
                print(f"   ❌ Login failed: {login_data.get('message')}")
                return None, None
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Error during login: {e}")
        return None, None

def test_admin_endpoints(session, csrf_token):
    """Test admin endpoints."""
    if not session:
        print("❌ No valid session for endpoint testing")
        return
    
    print("\n3. Testing admin endpoints...")
    
    # Test invitations endpoint
    headers = {}
    if csrf_token:
        headers['X-CSRF-Token'] = csrf_token
    
    invitations_url = f"{BASE_URL}/admin/employees/invitations"
    print(f"   Testing: {invitations_url}")
    
    try:
        response = session.get(invitations_url, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("   ✅ Admin endpoint accessible!")
        elif response.status_code == 401:
            print("   ❌ 401 UNAUTHORIZED - This is the issue!")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing endpoint: {e}")

def main():
    print("🚀 QUICK ADMIN LOGIN TEST")
    print("Testing the 401 UNAUTHORIZED issue")
    print()
    
    # Test the login flow
    session, csrf_token = test_admin_login()
    
    # Test admin endpoints
    test_admin_endpoints(session, csrf_token)
    
    print("\n" + "=" * 50)
    if session:
        print("✅ Admin login is working")
        print("If you're still getting 401 errors, the issue is likely:")
        print("1. Session not being properly stored in browser cookies")
        print("2. CSRF token mismatch")
        print("3. CORS configuration issues")
    else:
        print("❌ Admin login is failing")
        print("This needs to be fixed first with the fix script")

if __name__ == "__main__":
    main()