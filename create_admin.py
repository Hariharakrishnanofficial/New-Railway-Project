#!/usr/bin/env python3
"""
Create Admin Employee Script
Creates the first admin employee in the database
"""

import sys
import os
import bcrypt
import json

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

from repositories.cloudscale_repository import CloudScaleRepository
from config import TABLES

def create_admin():
    print("=" * 80)
    print("CREATE ADMIN EMPLOYEE")
    print("=" * 80)
    print("\nThis will create the first admin employee in your database.")
    print("You'll need this to access admin features like employee invitations.\n")
    
    # Get admin details
    email = input("Admin email: ").strip().lower()
    if not email or '@' not in email:
        print("✗ Invalid email address")
        return
    
    full_name = input("Full name: ").strip()
    if not full_name:
        print("✗ Full name is required")
        return
    
    password = input("Password (min 8 characters): ").strip()
    if len(password) < 8:
        print("✗ Password must be at least 8 characters")
        return
    
    confirm_password = input("Confirm password: ").strip()
    if password != confirm_password:
        print("✗ Passwords do not match")
        return
    
    print("\nGenerating secure password hash...")
    # Generate password hash using bcrypt (supported by backend verify_password)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

    # Also generate Argon2 hash (preferred). If SDK init fails, user can paste this into CloudScale.
    argon2_hash = None
    try:
        from core.security import hash_password  # pylint: disable=import-outside-toplevel
        argon2_hash = hash_password(password)
    except Exception:
        argon2_hash = None
    
    # Default admin permissions
    permissions = {
        "users": {"view": True, "create": True, "update": True, "delete": True},
        "employees": {"view": True, "create": True, "update": True, "delete": True},
        "trains": {"view": True, "create": True, "update": True, "delete": True},
        "bookings": {"view": True, "manage": True},
        "reports": {"view": True, "generate": True}
    }
    
    def _print_manual_fallback() -> None:
        # Don't print plaintext password. Provide hashes + ZCQL templates.
        def _esc(s: str) -> str:
            return (s or '').replace("'", "''")

        print("\n⚠️  Manual fallback (CloudScale Console)")
        print("If this script cannot initialize Catalyst locally, you can create/update the admin by pasting these values into CloudScale.")
        print("\nEmployees.Password (bcrypt):")
        print(password_hash)
        if argon2_hash:
            print("\nEmployees.Password (argon2id preferred):")
            print(argon2_hash)

        emp_table = TABLES['employees']
        user_table = TABLES['users']
        safe_email = _esc(email)
        safe_name = _esc(full_name)
        chosen_hash = _esc(argon2_hash or password_hash)

        print("\n--- ZCQL (preferred: UPDATE if row exists) ---")
        print(f"UPDATE {emp_table} SET Password='{chosen_hash}', Role='Admin', Account_Status='Active' WHERE Email='{safe_email}';")
        print(f"UPDATE {user_table} SET Password='{chosen_hash}', Role='ADMIN', Account_Status='Active' WHERE Email='{safe_email}';")

        print("\n--- ZCQL (INSERT if no row exists yet) ---")
        print(
            f"INSERT INTO {emp_table} (Employee_ID, Full_Name, Email, Password, Role, Department, Designation, Account_Status, Is_Active) "
            f"VALUES ('ADM001', '{safe_name}', '{safe_email}', '{chosen_hash}', 'Admin', 'Administration', 'System Administrator', 'Active', true);"
        )
        print(
            f"INSERT INTO {user_table} (Full_Name, Email, Password, Role, Account_Status) "
            f"VALUES ('{safe_name}', '{safe_email}', '{chosen_hash}', 'ADMIN', 'Active');"
        )

    # Create Catalyst SDK client
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        from repositories.cloudscale_repository import init_catalyst
        init_catalyst(app)
    except Exception as e:
        print(f"\n✗ Failed to initialize Catalyst SDK: {e}")
        print("\nFix:")
        print("1) Run: catalyst login")
        print("2) Then run this script again from the same terminal")
        _print_manual_fallback()
        return

    repo = CloudScaleRepository()
    
    # Check if Employees table exists
    print("\nChecking if Employees table exists...")
    # CloudScale doesn't use sqlite_master. We'll skip this check or use ZCQL.
    # result = repo.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
    #                             (TABLES.get('employees', 'Employees'),))
    
    # if not result.get('success') or not result.get('data', {}).get('data'):
    #    print(f"\n✗ ERROR: Employees table doesn't exist!")
    #    print("\n  You need to create the Employees table first.")
    #    print("  See FIX_INVITATION_ERRORS.md for table creation SQL.")
    #    return
    
    # Check if admin already exists
    print("Checking for existing admin employees...")
    # Fix: execute_query takes 1 argument (the full query string).
    # ZCQL doesn't support parameterized queries with ? in the same way sqlite3 does in this implementation.
    check_query = f"SELECT Email FROM {TABLES['employees']} WHERE Email='{email}' OR Role='Admin'"
    result = repo.execute_query(check_query)
    
    if result.get('success'):
        existing = result.get('data', {}).get('data', [])
        if existing:
            print(f"\n✗ WARNING: Admin or user with this email already exists:")
            for emp in existing:
                print(f"  - {emp.get('Email')}")
            
            overwrite = input("\nOverwrite? (yes/no): ").strip().lower()
            if overwrite != 'yes':
                print("Aborted.")
                return
    
    # First, create user record (required for authentication)
    print("\nCreating admin user record...")
    user_data = {
        'Full_Name': full_name,
        'Email': email,
        'Password': password_hash,  # Correct field name for Users table
        'Role': 'ADMIN',  # Use ADMIN role for Users table
        'Account_Status': 'Active'
    }
    
    user_result = repo.create_record(TABLES['users'], user_data)
    
    if not user_result.get('success'):
        print(f"\n✗ Failed to create admin user:")
        print(f"   Error: {user_result.get('error')}")
        return
    
    user_id = user_result.get('data', {}).get('ROWID')
    print(f"✓ Admin user created with ID: {user_id}")
    
    # Now create employee profile record
    print("Creating admin employee profile...")
    employee_data = {
        'Employee_ID': 'ADM001',
        'Full_Name': full_name,
        'Email': email,
        'User_Id': user_id,  # Link to Users table
        'Password': password_hash,  # Required for /session/employee/login (auths against Employees table)
        'Role': 'Admin',  # Employee role
        'Department': 'Administration',
        'Designation': 'System Administrator',
        'Permissions': json.dumps(permissions),
        'Account_Status': 'Active'
    }
    
    result = repo.create_record(TABLES['employees'], employee_data)
    
    if result.get('success'):
        print("\n" + "=" * 80)
        print("✓ ADMIN EMPLOYEE CREATED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\nUser ID:      {user_id}")
        print(f"Employee ID:  ADM001")
        print(f"Full Name:    {full_name}")
        print(f"Email:        {email}")
        print(f"Role:         Admin")
        print(f"Department:   Administration")
        print(f"Designation:  System Administrator")
        print("\nNext Steps:")
        print("1. Login to the app using this email and password")
        print("2. Use the employee login endpoint: POST /session/employee/login")
        print("3. You should now have access to admin features")
        print("4. Try accessing /admin/employees/invitations")
        print("\n" + "=" * 80)
    else:
        print(f"\n✗ Failed to create admin employee profile:")
        print(f"   Error: {result.get('error')}")
        print("\nTroubleshooting:")
        print("- Check if the Employees table has the correct structure")
        print("- Verify database connection is working")
        print("- See FIX_INVITATION_ERRORS.md for more help")

if __name__ == '__main__':
    try:
        create_admin()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
