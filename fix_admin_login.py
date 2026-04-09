#!/usr/bin/env python3
"""
Fix Admin Login - Emergency Fix Script
Fixes existing admin records that only exist in Employees table by creating matching Users records.
"""

import sys
import os
import json

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

from repositories.cloudscale_repository import CloudScaleRepository
from config import TABLES

def fix_admin_login():
    print("=" * 80)
    print("FIX ADMIN LOGIN - EMERGENCY REPAIR")
    print("=" * 80)
    print("\nThis will fix admin records that only exist in Employees table")
    print("by creating matching records in Users table for authentication.\n")
    
    repo = CloudScaleRepository()
    
    # Get all admin employees
    print("Looking for admin employees without Users records...")
    
    try:
        # Get all employees with Admin role
        result = repo.execute_query(
            f"SELECT ROWID, Employee_ID, Full_Name, Email, Password_Hash FROM {TABLES['employees']} WHERE Role='Admin'",
            ()
        )
        
        if not result.get('success'):
            print(f"✗ Failed to query Employees table: {result.get('error')}")
            return
            
        employees = result.get('data', {}).get('data', [])
        
        if not employees:
            print("✗ No admin employees found in Employees table")
            return
            
        print(f"Found {len(employees)} admin employee(s):")
        
        for emp in employees:
            email = emp.get('Email')
            employee_id = emp.get('Employee_ID')
            full_name = emp.get('Full_Name')
            password_hash = emp.get('Password_Hash')
            
            print(f"  - {employee_id}: {full_name} ({email})")
            
            # Check if Users record already exists
            user_result = repo.execute_query(
                f"SELECT ROWID FROM {TABLES['users']} WHERE Email=?",
                (email,)
            )
            
            if user_result.get('success') and user_result.get('data', {}).get('data'):
                print(f"    ✓ Users record already exists for {email}")
                continue
                
            # Create Users record
            if not password_hash:
                print(f"    ✗ No password hash found for {email} - skipping")
                continue
                
            print(f"    Creating Users record for {email}...")
            
            user_data = {
                'Full_Name': full_name,
                'Email': email,
                'Password': password_hash,  # Use the existing hash
                'Role': 'ADMIN',
                'Account_Status': 'Active'
            }
            
            create_result = repo.insert_record(TABLES['users'], user_data)
            
            if create_result.get('success'):
                user_id = create_result.get('data', {}).get('ROWID')
                print(f"    ✓ Users record created with ID: {user_id}")
                
                # Update Employees record to link to Users record
                update_result = repo.update_record(
                    TABLES['employees'], 
                    str(emp.get('ROWID')),
                    {'User_Id': user_id}
                )
                
                if update_result.get('success'):
                    print(f"    ✓ Employees record updated with User_Id link")
                else:
                    print(f"    ! Warning: Failed to update Employees record: {update_result.get('error')}")
                    
            else:
                print(f"    ✗ Failed to create Users record: {create_result.get('error')}")
        
        print("\n" + "=" * 80)
        print("✓ ADMIN LOGIN FIX COMPLETED!")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. Try logging in with your admin email and password")
        print("2. Use endpoint: POST /session/employee/login")
        print("3. If still failing, check the logs for specific errors")
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        fix_admin_login()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()