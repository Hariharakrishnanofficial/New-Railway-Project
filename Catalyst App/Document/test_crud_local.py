#!/usr/bin/env python3
"""
LOCAL CRUD TESTING SCRIPT for Railway Ticketing System
=========================================================

This script tests all CRUD operations locally without requiring
the full Catalyst CloudScale environment.

Usage: python test_crud_local.py
"""

import sys
import os
import json
import requests
import time
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'catalyst_backend'))

# Test data
TEST_USER_DATA = {
    "Full_Name": "Test CRUD User",
    "Email": "testcrud@railway.com",
    "Phone_Number": "9876543210",
    "Password": "TestCRUD@123",
    "Gender": "Male",
    "Role": "User",
    "Address": "123 Test Street, Chennai"
}

TEST_STATION_DATA = {
    "Station_Name": "Test Junction",
    "Station_Code": "TSTJ",
    "State": "Tamil Nadu",
    "Zone": "SR",
    "Division": "MAS"
}

COLOR = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}

def print_header(text):
    print(f"\n{COLOR['HEADER']}{COLOR['BOLD']}{'='*60}")
    print(f"{text.center(60)}")
    print(f"{'='*60}{COLOR['ENDC']}")

def print_test(text):
    print(f"\n{COLOR['BLUE']}🧪 {text}{COLOR['ENDC']}")

def print_success(text):
    print(f"{COLOR['GREEN']}✅ {text}{COLOR['ENDC']}")

def print_error(text):
    print(f"{COLOR['RED']}❌ {text}{COLOR['ENDC']}")

def print_warning(text):
    print(f"{COLOR['YELLOW']}⚠️  {text}{COLOR['ENDC']}")

def print_info(text):
    print(f"{COLOR['CYAN']}ℹ️  {text}{COLOR['ENDC']}")


class CRUDTester:
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.admin_headers = {
            'Content-Type': 'application/json',
            'X-User-Role': 'Admin',
            'X-User-Email': 'admin@railway.com',
            'X-User-ID': '1'
        }

    def test_server_health(self):
        """Test if server is responding"""
        print_test("Testing server health...")
        try:
            # Try different possible endpoints
            endpoints_to_try = [
                f"{self.base_url}/api/health",
                f"{self.base_url}/server/catalyst_backend/api/health",
                f"{self.base_url}/"
            ]

            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        print_success(f"Server responding at: {endpoint}")
                        if 'health' in endpoint:
                            data = response.json()
                            print_info(f"Version: {data.get('version', 'Unknown')}")
                            print_info(f"Status: {data.get('status', 'Unknown')}")
                        return True
                except:
                    continue

            print_error("Server not responding on any endpoint")
            return False

        except Exception as e:
            print_error(f"Server health check failed: {e}")
            return False

    def test_user_crud(self):
        """Test User CRUD operations"""
        print_header("USER CRUD OPERATIONS")

        # Test 1: CREATE User
        print_test("CREATE User via Registration")
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=TEST_USER_DATA,
                timeout=10
            )
            print_info(f"Status: {response.status_code}")
            print_info(f"Response: {response.text[:200]}...")

            if response.status_code in [201, 200]:
                print_success("User registration successful")
                data = response.json()
                user_id = data.get('user_id') or data.get('data', {}).get('ID')
                if user_id:
                    print_info(f"Created user ID: {user_id}")
                    return user_id
            else:
                print_warning(f"Registration returned {response.status_code}")
                return None

        except Exception as e:
            print_error(f"User registration failed: {e}")
            return None

    def test_auth_login(self):
        """Test authentication and get JWT token"""
        print_test("LOGIN Authentication")
        try:
            login_data = {
                "email": TEST_USER_DATA["Email"],
                "password": TEST_USER_DATA["Password"]
            }

            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                timeout=10
            )

            print_info(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('access_token'):
                    self.auth_token = data['access_token']
                    print_success("Login successful")
                    print_info(f"Token: {self.auth_token[:30]}...")
                    return True

            print_warning("Login failed or no token returned")
            return False

        except Exception as e:
            print_error(f"Login failed: {e}")
            return False

    def test_stations_crud(self):
        """Test Station CRUD operations"""
        print_header("STATIONS CRUD OPERATIONS")

        # Test CREATE Station
        print_test("CREATE Station")
        try:
            response = self.session.post(
                f"{self.base_url}/api/stations",
                json=TEST_STATION_DATA,
                headers=self.admin_headers,
                timeout=10
            )

            print_info(f"Status: {response.status_code}")
            print_info(f"Response: {response.text[:200]}...")

            if response.status_code in [201, 200]:
                print_success("Station created successfully")
                data = response.json()
                station_id = data.get('data', {}).get('ID')
                return station_id
            else:
                print_warning(f"Station creation returned {response.status_code}")

        except Exception as e:
            print_error(f"Station creation failed: {e}")

        return None

    def test_read_operations(self):
        """Test READ operations"""
        print_header("READ OPERATIONS")

        endpoints_to_test = [
            "/api/stations",
            "/api/trains",
            "/api/users",
            "/api/bookings"
        ]

        for endpoint in endpoints_to_test:
            print_test(f"GET {endpoint}")
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.admin_headers,
                    timeout=10
                )

                print_info(f"Status: {response.status_code}")

                if response.status_code == 200:
                    print_success(f"{endpoint} - READ successful")
                    try:
                        data = response.json()
                        if isinstance(data, dict) and 'data' in data:
                            count = len(data['data'].get('data', []))
                            print_info(f"Records returned: {count}")
                    except:
                        pass
                else:
                    print_warning(f"{endpoint} - Status {response.status_code}")

            except Exception as e:
                print_error(f"{endpoint} failed: {e}")

    def test_api_endpoints(self):
        """Test various API endpoints structure"""
        print_header("API ENDPOINTS TESTING")

        endpoints = [
            ("GET", "/api/health", "Health Check"),
            ("GET", "/api/analytics/overview", "Analytics Overview"),
            ("POST", "/api/ai/search", "AI Search"),
        ]

        for method, endpoint, description in endpoints:
            print_test(f"{method} {endpoint} - {description}")
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json={"query": "test"},
                        timeout=10
                    )

                print_info(f"Status: {response.status_code}")

                if response.status_code < 500:
                    print_success(f"{description} - Endpoint accessible")
                else:
                    print_warning(f"{description} - Server error")

            except Exception as e:
                print_error(f"{description} failed: {e}")

    def run_comprehensive_test(self):
        """Run all CRUD tests"""
        print_header("RAILWAY TICKETING SYSTEM - CRUD TESTING")
        print_info("Testing all CRUD operations locally\n")

        # 1. Test server health
        if not self.test_server_health():
            print_error("Server not accessible. Please ensure the server is running.")
            print_info("Start server with: catalyst serve")
            return False

        # 2. Test User CRUD
        user_id = self.test_user_crud()

        # 3. Test Authentication
        self.test_auth_login()

        # 4. Test Stations CRUD
        self.test_stations_crud()

        # 5. Test READ operations
        self.test_read_operations()

        # 6. Test API endpoints
        self.test_api_endpoints()

        print_header("CRUD TESTING COMPLETED")
        print_success("All tests executed successfully!")
        print_info("Check individual test results above for detailed status")

        return True


def main():
    """Main function"""
    # Check if server URL is provided
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000"

    print_header("RAILWAY TICKETING SYSTEM CRUD TESTER")
    print_info(f"Server URL: {server_url}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tester = CRUDTester(server_url)
    success = tester.run_comprehensive_test()

    if success:
        print_success("\n🎉 CRUD testing completed!")
    else:
        print_error("\n💥 CRUD testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()