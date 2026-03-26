import requests
import json
import sys

def test_crud_operations(base_url="http://localhost:9000"):
    """Test CRUD operations for Railway Ticketing System"""
    
    print("=" * 60)
    print("RAILWAY TICKETING SYSTEM - CRUD TESTING")
    print("=" * 60)
    print(f"Server URL: {base_url}")
    print(f"Testing CRUD operations...\n")
    
    # Test data
    test_user = {
        "Full_Name": "Test CRUD User",
        "Email": "testcrud@railway.com",
        "Phone_Number": "9876543210",
        "Password": "TestCRUD@123",
        "Gender": "Male",
        "Role": "User"
    }
    
    test_station = {
        "Station_Name": "Test Junction",
        "Station_Code": "TSTJ",
        "State": "Tamil Nadu",
        "Zone": "SR"
    }
    
    admin_headers = {
        "Content-Type": "application/json",
        "X-User-Role": "Admin",
        "X-User-Email": "admin@railway.com",
        "X-User-ID": "1"
    }
    
    # Test 1: Server Health Check
    print("1. Testing Server Health...")
    try:
        health_endpoints = [
            f"{base_url}/api/health",
            f"{base_url}/server/catalyst_backend/api/health"
        ]
        
        server_running = False
        for endpoint in health_endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    print(f"   SUCCESS: Server responding at {endpoint}")
                    try:
                        data = response.json()
                        print(f"   Version: {data.get('version', 'Unknown')}")
                        print(f"   Status: {data.get('status', 'Unknown')}")
                    except:
                        print("   Health endpoint accessible")
                    server_running = True
                    break
            except:
                continue
        
        if not server_running:
            print("   ERROR: Server not responding")
            print("   Please start the server with: catalyst serve")
            return False
            
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Test 2: CREATE User (Registration)
    print("\n2. Testing User Registration (CREATE)...")
    try:
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=test_user,
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code in [200, 201]:
            print("   SUCCESS: User registration successful")
        else:
            print("   WARNING: Registration returned non-success status")
            
    except Exception as e:
        print(f"   ERROR: User registration failed - {e}")
    
    # Test 3: User Login (Authentication)
    print("\n3. Testing User Login (Authentication)...")
    try:
        login_data = {
            "email": test_user["Email"],
            "password": test_user["Password"]
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('access_token'):
                print("   SUCCESS: Login successful")
                auth_token = data['access_token']
                print(f"   Token: {auth_token[:30]}...")
            else:
                print("   WARNING: Login successful but no token returned")
        else:
            print(f"   WARNING: Login returned status {response.status_code}")
            
    except Exception as e:
        print(f"   ERROR: Login failed - {e}")
    
    # Test 4: CREATE Station
    print("\n4. Testing Station Creation (CREATE)...")
    try:
        response = requests.post(
            f"{base_url}/api/stations",
            json=test_station,
            headers=admin_headers,
            timeout=10
        )
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code in [200, 201]:
            print("   SUCCESS: Station creation successful")
        else:
            print("   WARNING: Station creation returned non-success status")
            
    except Exception as e:
        print(f"   ERROR: Station creation failed - {e}")
    
    # Test 5: READ Operations
    print("\n5. Testing READ Operations...")
    endpoints = [
        "/api/stations",
        "/api/trains", 
        "/api/users",
        "/api/bookings"
    ]
    
    for endpoint in endpoints:
        print(f"   Testing GET {endpoint}...")
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=admin_headers,
                timeout=10
            )
            print(f"     Status: {response.status_code}")
            
            if response.status_code == 200:
                print("     SUCCESS: Read operation successful")
                try:
                    data = response.json()
                    if 'data' in data and 'data' in data['data']:
                        count = len(data['data']['data'])
                        print(f"     Records: {count}")
                except:
                    pass
            else:
                print(f"     WARNING: Status {response.status_code}")
                
        except Exception as e:
            print(f"     ERROR: {e}")
    
    # Test 6: API Endpoints
    print("\n6. Testing API Endpoints...")
    api_tests = [
        ("GET", "/api/health", "Health Check"),
        ("GET", "/api/analytics/overview", "Analytics Overview")
    ]
    
    for method, endpoint, description in api_tests:
        print(f"   Testing {method} {endpoint} - {description}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"     Status: {response.status_code}")
            
            if response.status_code < 500:
                print("     SUCCESS: Endpoint accessible")
            else:
                print("     WARNING: Server error")
                
        except Exception as e:
            print(f"     ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("CRUD TESTING COMPLETED")
    print("=" * 60)
    print("All tests executed. Check individual results above.")
    return True

if __name__ == "__main__":
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9000"
    test_crud_operations(server_url)
