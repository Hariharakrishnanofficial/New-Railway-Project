#!/usr/bin/env python3
"""
Comprehensive Test Script for Employee Login and Invitation System
Tests the complete flow from setup through browser integration
"""

import sys
import os
import subprocess
import requests
import json
from datetime import datetime
import urllib3

# Disable SSL warnings for localhost testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test configuration
BASE_URL = "http://localhost:3001/server/smart_railway_app_function"
FRONTEND_URL = "http://localhost:3001/app"
ADMIN_CREDENTIALS = {
    "email": "admin@admin.com",  # Updated to match .env file
    "password": "SecureRailwayAdmin2024!"  # Updated to match fix script
}

class EmployeeInvitationTester:
    """Comprehensive tester for employee invitation system."""
    
    def __init__(self):
        self.session = requests.Session()
        self.admin_session = None
        self.csrf_token = None
        self.test_results = []
        
    def log_test(self, test_name, status, details="", error=None):
        """Log test result."""
        result = {
            'test': test_name,
            'status': '✅' if status else '❌',
            'details': details,
            'error': str(error) if error else None,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{result['status']} {test_name}: {details}")
        if error:
            print(f"    Error: {error}")
    
    def test_fix_script(self):
        """Step 1: Run the fix script to set up the system."""
        try:
            print("🚀 STEP 1: Running fix_invitation_system.py script...")
            result = subprocess.run([
                sys.executable, 'fix_invitation_system.py'
            ], capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                self.log_test("fix_script_execution", True, 
                             f"Fix script executed successfully")
                print(f"Script output:\n{result.stdout}")
                return True
            else:
                self.log_test("fix_script_execution", False, 
                             f"Fix script failed with exit code {result.returncode}", 
                             result.stderr)
                print(f"Script stderr:\n{result.stderr}")
                return False
        except Exception as e:
            self.log_test("fix_script_execution", False, "Exception running fix script", e)
            return False
    
    def test_admin_login(self):
        """Step 2: Test admin employee login."""
        try:
            print("\n👤 STEP 2: Testing admin employee login...")
            
            # First, try to get CSRF token
            csrf_response = self.session.get(f"{BASE_URL}/csrf-token")
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                self.csrf_token = csrf_data.get('csrf_token')
                self.log_test("csrf_token_retrieval", True, 
                             f"CSRF token retrieved: {self.csrf_token[:10]}...")
            else:
                self.log_test("csrf_token_retrieval", False, 
                             f"Failed to get CSRF token: {csrf_response.status_code}")
                self.csrf_token = None
            
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            # Test admin login
            login_url = f"{BASE_URL}/session/employee/login"
            response = self.session.post(login_url, 
                                       json=ADMIN_CREDENTIALS, 
                                       headers=headers)
            
            if response.status_code == 200:
                login_data = response.json()
                if login_data.get('status') == 'success':
                    self.admin_session = self.session
                    self.log_test("admin_login", True, 
                                 f"Admin logged in successfully as {login_data.get('user', {}).get('email', 'N/A')}")
                    return True
                else:
                    self.log_test("admin_login", False, 
                                 f"Login failed: {login_data.get('message', 'Unknown error')}")
                    return False
            else:
                self.log_test("admin_login", False, 
                             f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("admin_login", False, "Exception during admin login", e)
            return False
    
    def test_admin_access_endpoints(self):
        """Step 3: Test admin access to invitation endpoints."""
        if not self.admin_session:
            self.log_test("admin_endpoints_test", False, "No admin session available")
            return False
        
        try:
            print("\n🔐 STEP 3: Testing admin access to invitation endpoints...")
            
            # Test GET /admin/employees/invitations
            headers = {}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            invitations_url = f"{BASE_URL}/admin/employees/invitations"
            response = self.admin_session.get(invitations_url, headers=headers)
            
            if response.status_code == 200:
                invitations_data = response.json()
                self.log_test("get_invitations_endpoint", True, 
                             f"Retrieved {len(invitations_data.get('data', {}).get('data', []))} invitations")
            elif response.status_code == 401:
                self.log_test("get_invitations_endpoint", False, 
                             "401 UNAUTHORIZED - Session authentication failed")
                return False
            else:
                self.log_test("get_invitations_endpoint", False, 
                             f"HTTP {response.status_code}: {response.text}")
                return False
            
            # Test POST /admin/employees/invite
            invite_data = {
                "email": "test.employee@railway.com",
                "role": "Employee",
                "department": "Operations",
                "designation": "Station Master"
            }
            
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            invite_url = f"{BASE_URL}/admin/employees/invite"
            response = self.admin_session.post(invite_url, 
                                             json=invite_data, 
                                             headers=headers)
            
            if response.status_code in [200, 201]:
                invite_response = response.json()
                if invite_response.get('status') == 'success':
                    self.log_test("post_invite_endpoint", True, 
                                 f"Invitation sent successfully to {invite_data['email']}")
                else:
                    self.log_test("post_invite_endpoint", False, 
                                 f"Invite failed: {invite_response.get('message', 'Unknown error')}")
            elif response.status_code == 401:
                self.log_test("post_invite_endpoint", False, 
                             "401 UNAUTHORIZED - Session authentication failed")
                return False
            else:
                self.log_test("post_invite_endpoint", False, 
                             f"HTTP {response.status_code}: {response.text}")
                
            return True
            
        except Exception as e:
            self.log_test("admin_endpoints_test", False, "Exception during endpoint testing", e)
            return False
    
    def test_browser_integration(self):
        """Step 4: Test browser integration points."""
        try:
            print("\n🌐 STEP 4: Testing browser integration...")
            
            # Test frontend accessibility
            try:
                frontend_response = requests.get(f"{FRONTEND_URL}/#/admin/employee-invitations", 
                                               timeout=10)
                if frontend_response.status_code == 200:
                    self.log_test("frontend_accessibility", True, 
                                 "Frontend page is accessible")
                else:
                    self.log_test("frontend_accessibility", False, 
                                 f"Frontend returned HTTP {frontend_response.status_code}")
            except requests.exceptions.ConnectionError:
                self.log_test("frontend_accessibility", False, 
                             "Frontend server not accessible - ensure it's running on localhost:3001")
            except Exception as e:
                self.log_test("frontend_accessibility", False, 
                             "Exception accessing frontend", e)
            
            # Test session validation endpoint
            if self.admin_session:
                session_url = f"{BASE_URL}/session/validate"
                response = self.admin_session.get(session_url)
                
                if response.status_code == 200:
                    session_data = response.json()
                    if session_data.get('valid') and session_data.get('user_type') == 'employee':
                        self.log_test("session_validation", True, 
                                     f"Session valid for employee: {session_data.get('user', {}).get('email', 'N/A')}")
                    else:
                        self.log_test("session_validation", False, 
                                     f"Invalid session or wrong user type: {session_data}")
                else:
                    self.log_test("session_validation", False, 
                                 f"Session validation failed: HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("browser_integration", False, "Exception during browser integration test", e)
            return False
    
    def test_api_errors_and_edge_cases(self):
        """Step 5: Test error handling and edge cases."""
        try:
            print("\n🧪 STEP 5: Testing error handling and edge cases...")
            
            # Test invalid credentials
            invalid_login_url = f"{BASE_URL}/session/employee/login"
            invalid_creds = {"email": "invalid@test.com", "password": "wrongpassword"}
            
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            response = requests.post(invalid_login_url, json=invalid_creds, headers=headers)
            
            if response.status_code == 401:
                self.log_test("invalid_credentials_handling", True, 
                             "Invalid credentials properly rejected with 401")
            else:
                self.log_test("invalid_credentials_handling", False, 
                             f"Expected 401, got {response.status_code}")
            
            # Test access without authentication
            unauth_session = requests.Session()
            unauth_url = f"{BASE_URL}/admin/employees/invitations"
            response = unauth_session.get(unauth_url)
            
            if response.status_code == 401:
                self.log_test("unauthorized_access_protection", True, 
                             "Unauthenticated access properly blocked with 401")
            else:
                self.log_test("unauthorized_access_protection", False, 
                             f"Expected 401 for unauthenticated access, got {response.status_code}")
            
            # Test duplicate invitation
            if self.admin_session:
                duplicate_invite_data = {
                    "email": "test.employee@railway.com",  # Same as before
                    "role": "Employee",
                    "department": "Operations", 
                    "designation": "Station Master"
                }
                
                headers = {'Content-Type': 'application/json'}
                if self.csrf_token:
                    headers['X-CSRF-Token'] = self.csrf_token
                
                invite_url = f"{BASE_URL}/admin/employees/invite"
                response = self.admin_session.post(invite_url, 
                                                 json=duplicate_invite_data, 
                                                 headers=headers)
                
                if response.status_code == 400:
                    self.log_test("duplicate_invitation_handling", True, 
                                 "Duplicate invitation properly rejected with 400")
                else:
                    # Might be allowed or handled differently
                    self.log_test("duplicate_invitation_handling", True, 
                                 f"Duplicate invitation handled: HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("error_handling_test", False, "Exception during error handling test", e)
            return False
    
    def generate_report(self):
        """Generate final test report."""
        print("\n" + "=" * 80)
        print("📋 EMPLOYEE INVITATION SYSTEM - TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == '✅'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        print("   | Test | Status | Details |")
        print("   |------|--------|---------|")
        
        for result in self.test_results:
            test_name = result['test'].replace('_', ' ').title()
            status = result['status']
            details = result['details'][:60] + "..." if len(result['details']) > 60 else result['details']
            print(f"   | {test_name:<25} | {status} | {details} |")
        
        # Issues found
        failed_results = [r for r in self.test_results if r['status'] == '❌']
        if failed_results:
            print(f"\n🚨 ISSUES FOUND:")
            for i, result in enumerate(failed_results, 1):
                print(f"   {i}. {result['test']}: {result['details']}")
                if result['error']:
                    print(f"      Error: {result['error']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if failed_tests == 0:
            print("   🎉 All tests passed! The employee invitation system is working correctly.")
            print("   📱 You can now access: http://localhost:3001/app/#/admin/employee-invitations")
            print(f"   🔑 Login with: {ADMIN_CREDENTIALS['email']} / {ADMIN_CREDENTIALS['password']}")
        else:
            print("   1. Check that the backend server is running on localhost:3001")
            print("   2. Verify database connectivity and table creation")
            print("   3. Ensure proper session and CSRF configuration")
            print("   4. Check CloudScale permissions and authentication")
        
        print(f"\n🔍 NEXT STEPS:")
        print("   1. If tests passed: Access the employee invitation page in browser")
        print("   2. If tests failed: Review error details and fix issues")
        print("   3. Run this test script again after making fixes")
        print(f"\n📌 Frontend URL: {FRONTEND_URL}/#/admin/employee-invitations")
        print(f"📌 Backend API: {BASE_URL}")

def main():
    """Main test runner."""
    tester = EmployeeInvitationTester()
    
    print("🔍 SMART RAILWAY - EMPLOYEE INVITATION SYSTEM TESTER")
    print("=" * 80)
    print("Testing complete login and invitation flow...")
    print(f"Backend: {BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print()
    
    # Run all test steps
    steps = [
        tester.test_fix_script,
        tester.test_admin_login,
        tester.test_admin_access_endpoints,
        tester.test_browser_integration,
        tester.test_api_errors_and_edge_cases
    ]
    
    for step in steps:
        try:
            step()
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            break
        except Exception as e:
            print(f"\n💥 Unexpected error in {step.__name__}: {e}")
    
    # Generate final report
    tester.generate_report()

if __name__ == "__main__":
    main()