"""
Test Admin Login Flow
Run this script to test the employee login system
"""
import requests
import json

BASE_URL = "http://localhost:3000/server/smart_railway_app_function"

def test_flow():
    print("=" * 60)
    print("STEP 1: Create Admin Employee")
    print("=" * 60)
    
    # Step 1: Create admin
    create_response = requests.post(
        f"{BASE_URL}/data-seed/admin-employee",
        json={
            "email": "newadmin2@railway.com",
            "password": "Admin@123",
            "full_name": "New Admin"
        }
    )
    print(f"Status: {create_response.status_code}")
    print(f"Response: {json.dumps(create_response.json(), indent=2)}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Check if employee exists")
    print("=" * 60)
    
    # Step 2: Check employee
    check_response = requests.get(
        f"{BASE_URL}/data-seed/check-employee/newadmin2@railway.com"
    )
    print(f"Status: {check_response.status_code}")
    print(f"Response: {json.dumps(check_response.json(), indent=2)}")
    
    print("\n" + "=" * 60)
    print("STEP 3: Try Employee Login")
    print("=" * 60)
    
    # Step 3: Login
    login_response = requests.post(
        f"{BASE_URL}/session/employee/login",
        json={
            "email": "newadmin2@railway.com",
            "password": "Admin@123"
        }
    )
    print(f"Status: {login_response.status_code}")
    print(f"Response: {json.dumps(login_response.json(), indent=2)}")
    
    if login_response.status_code == 200:
        print("\n✅ LOGIN SUCCESSFUL!")
    else:
        print("\n❌ LOGIN FAILED!")
        print("\nDEBUG INFO:")
        print("- Check if Employees table has the record")
        print("- Check if password hash matches")
        print("- Check Account_Status is 'Active'")

if __name__ == "__main__":
    test_flow()
