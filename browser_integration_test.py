#!/usr/bin/env python3
"""
Browser Integration Test for Employee Invitation System
Tests the complete browser flow at http://localhost:3001/app/#/admin/employee-invitations
"""

import requests
import json
import time

class EmployeeInvitationBrowserTest:
    def __init__(self):
        self.base_url = "http://localhost:3001/server/smart_railway_app_function"
        self.app_url = "http://localhost:3001/app"
        self.admin_email = "admin@admin.com"  # From .env ADMIN_EMAIL
        self.admin_password = "SecureRailwayAdmin2024!"  # From fix script
        self.session = requests.Session()
        self.csrf_token = None
        
    def test_app_loading(self):
        """Test if the React app loads correctly"""
        print("🌐 Testing App Loading...")
        try:
            response = requests.get(f"{self.app_url}/")
            if response.status_code == 200:
                print("✅ App loads successfully")
                if 'id="root"' in response.text:
                    print("✅ React root element found")
                else:
                    print("⚠️  React root element missing")
                return True
            else:
                print(f"❌ App failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"💥 App loading error: {e}")
            return False
    
    def test_admin_login_api(self):
        """Test admin login via API to get session cookie"""
        print("\n🔐 Testing Admin Login API...")
        
        login_data = {
            "email": self.admin_email,
            "password": self.admin_password
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/session/employee/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📡 Login Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Admin login successful!")
                
                # Extract session data
                session_data = data.get('data', {})
                self.csrf_token = session_data.get('csrf_token')
                user_role = session_data.get('user_role')
                user_type = session_data.get('user_type')
                
                print(f"👤 User Role: {user_role}")
                print(f"🏷️  User Type: {user_type}")
                print(f"🔒 CSRF Token: {self.csrf_token[:20]}..." if self.csrf_token else "❌ No CSRF token")
                
                # Check cookies
                cookies = dict(self.session.cookies)
                print(f"🍪 Cookies: {list(cookies.keys())}")
                
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"💥 Login error: {e}")
            return False
    
    def test_invitations_api(self):
        """Test invitations API endpoints"""
        print("\n📋 Testing Invitations API...")
        
        if not self.csrf_token:
            print("❌ No CSRF token - skipping API tests")
            return False
        
        headers = {
            "X-CSRF-Token": self.csrf_token,
            "Content-Type": "application/json"
        }
        
        try:
            # Test GET invitations
            response = self.session.get(
                f"{self.base_url}/admin/employees/invitations",
                headers=headers
            )
            
            print(f"📡 GET Invitations Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Can access invitations endpoint")
                invitations = data.get('data', {}).get('invitations', [])
                print(f"📊 Current invitations: {len(invitations)}")
                
                # Test POST invite
                print("\n📤 Testing Invitation Creation...")
                invite_data = {
                    "email": f"test{int(time.time())}@example.com",
                    "role": "Employee",
                    "department": "Test Department",
                    "designation": "Test Position"
                }
                
                invite_response = self.session.post(
                    f"{self.base_url}/admin/employees/invite",
                    json=invite_data,
                    headers=headers
                )
                
                print(f"📡 POST Invite Status: {invite_response.status_code}")
                
                if invite_response.status_code == 201:
                    print("✅ Invitation created successfully!")
                    invite_result = invite_response.json()
                    print(f"📧 Invited: {invite_result.get('data', {}).get('email')}")
                    return True
                else:
                    print(f"❌ Invitation failed: {invite_response.text}")
                    return False
                    
            else:
                print(f"❌ Cannot access invitations: {response.text}")
                return False
                
        except Exception as e:
            print(f"💥 API test error: {e}")
            return False
    
    def test_frontend_api_integration(self):
        """Test how frontend would interact with the API"""
        print("\n🔗 Testing Frontend API Integration...")
        
        # Simulate how the React app makes requests
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add CSRF token if available
        if self.csrf_token:
            headers["X-CSRF-Token"] = self.csrf_token
        
        try:
            # Test session validation (what frontend does on load)
            response = self.session.get(
                f"{self.base_url}/session/validate",
                headers=headers
            )
            
            print(f"📡 Session Validation: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Session validation works - frontend should show admin UI")
                return True
            else:
                print(f"❌ Session validation failed - frontend will redirect to login")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"💥 Frontend integration error: {e}")
            return False
    
    def generate_browser_test_instructions(self, api_success):
        """Generate instructions for manual browser testing"""
        print("\n" + "="*60)
        print("🌐 BROWSER TESTING INSTRUCTIONS")
        print("="*60)
        
        if api_success:
            print("✅ API tests passed - browser testing should work!")
            print("\nSteps to test in browser:")
            print("1. Open: http://localhost:3001/app/")
            print("2. Look for 'Employee Login' or 'Admin Login' option")
            print("3. Login with:")
            print(f"   - Email: {self.admin_email}")
            print(f"   - Password: {self.admin_password}")
            print("4. Navigate to: /admin/employee-invitations")
            print("5. Try creating an invitation")
            
            print("\n📊 Expected Results:")
            print("- ✅ Login should succeed")
            print("- ✅ Admin dashboard should be accessible")
            print("- ✅ Employee invitation page should load")
            print("- ✅ No 401 UNAUTHORIZED errors")
            
        else:
            print("❌ API tests failed - fix backend issues first!")
            print("\n🔧 Required Fixes:")
            print("1. Run: python fix_invitation_system.py")
            print("2. Ensure backend is running on port 3001")
            print("3. Check database tables exist")
            print("4. Verify admin employee was created")
            
        print("\n🛠️  Browser Developer Tools:")
        print("- Check Network tab for API calls")
        print("- Look for 401/403 errors in Console")
        print("- Verify cookies are set after login")
        print("- Check CSRF token headers on POST requests")
    
    def run_all_tests(self):
        """Run all browser integration tests"""
        print("🚀 EMPLOYEE INVITATION BROWSER INTEGRATION TEST")
        print("="*60)
        
        # Test 1: App loading
        app_loads = self.test_app_loading()
        
        # Test 2: Admin login
        login_success = self.test_admin_login_api()
        
        # Test 3: API access
        api_success = False
        if login_success:
            api_success = self.test_invitations_api()
        
        # Test 4: Frontend integration
        frontend_success = False
        if login_success:
            frontend_success = self.test_frontend_api_integration()
        
        # Results summary
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"🌐 App Loading: {'✅' if app_loads else '❌'}")
        print(f"🔐 Admin Login: {'✅' if login_success else '❌'}")
        print(f"📋 API Access: {'✅' if api_success else '❌'}")
        print(f"🔗 Frontend Integration: {'✅' if frontend_success else '❌'}")
        
        overall_success = all([app_loads, login_success, api_success, frontend_success])
        print(f"\n🎯 Overall Success: {'✅' if overall_success else '❌'}")
        
        # Browser testing instructions
        self.generate_browser_test_instructions(overall_success)
        
        return overall_success

if __name__ == "__main__":
    tester = EmployeeInvitationBrowserTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Browser integration should work.")
    else:
        print("\n⚠️  Some tests failed. Fix issues before browser testing.")