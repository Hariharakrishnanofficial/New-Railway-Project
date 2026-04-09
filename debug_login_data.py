
import os
import sys
import logging
import json

# Add the function directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'functions', 'smart_railway_app_function'))

from repositories.cloudscale_repository import cloudscale_repo
from core.security import verify_password, hash_password
from config import TABLES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_employee_login():
    email = "test_verified_2@railway.com"
    password = "Admin@123"
    
    print(f"\n--- DEBUGGING EMPLOYEE LOGIN: {email} ---")
    
    try:
        # Check if record exists in Employees table
        employee = cloudscale_repo.get_employee_by_email(email)
        
        if not employee:
            print(f"ERROR: No record found in {TABLES['employees']} for {email}")
            return

        print(f"SUCCESS: Found employee record.")
        print(f"  ROWID: {employee.get('ROWID')}")
        print(f"  Role: {employee.get('Role')}")
        print(f"  Account_Status: {employee.get('Account_Status')}")
        
        # Check Account Status
        status = employee.get('Account_Status', 'Active')
        if status != 'Active':
            print(f"ERROR: Account_Status is '{status}', but code requires exactly 'Active'.")

        # Check Password
        stored_hash = employee.get('Password')
        if not stored_hash:
            print("ERROR: Password field is empty in database.")
            return

        is_match = verify_password(password, stored_hash)
        print(f"Password Match ('{password}'): {is_match}")
        
        if not is_match:
            print("\nUpdating Password for test account...")
            new_hash = hash_password(password)
            update_result = cloudscale_repo.update_record(TABLES['employees'], str(employee.get('ROWID')), {
                'Password': new_hash,
                'Account_Status': 'Active'
            })
            if update_result.get('success'):
                print(f"SUCCESS: Password updated. New Hash: {new_hash}")
                print("Try logging in again now.")
            else:
                print(f"ERROR: Failed to update password: {update_result.get('error')}")

    except Exception as e:
        print(f"EXCEPTION: {str(e)}")

if __name__ == "__main__":
    # Note: This tool runs without the Catalyst App Context. 
    # It might fail if the repo strictly requires it, but will show us exactly where it fails.
    debug_employee_login()
