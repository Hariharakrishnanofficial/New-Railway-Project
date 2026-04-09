#!/usr/bin/env python3
"""
Comprehensive Employee Invitation System Fix Script
Addresses all three root causes:
1. Creates missing database tables
2. Creates first admin employee
3. Verifies system integrity
"""

import sys
import os
import bcrypt
from datetime import datetime, timedelta

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

from config import TABLES, ADMIN_EMAIL
from repositories.cloudscale_repository import cloudscale_repo

def check_table_exists(table_name):
    """Check if a table exists in CloudScale"""
    try:
        result = cloudscale_repo.execute_query(f"SELECT COUNT(*) as count FROM {table_name} LIMIT 1")
        return result.get('success', False)
    except Exception:
        return False

def create_employees_table():
    """Create the Employees table with proper schema"""
    print("📋 Creating Employees table...")
    
    # Note: CloudScale may use different SQL syntax, adjust if needed
    create_sql = f"""
        CREATE TABLE {TABLES['employees']} (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            Employee_ID VARCHAR(50),
            Full_Name VARCHAR(255) NOT NULL,
            Email VARCHAR(255) UNIQUE NOT NULL,
            Password VARCHAR(255) NOT NULL,
            Role VARCHAR(50) DEFAULT 'Employee',
            Department VARCHAR(100),
            Designation VARCHAR(100),
            Phone_Number VARCHAR(20),
            Account_Status VARCHAR(20) DEFAULT 'Active',
            Is_Active INTEGER DEFAULT 1,
            Joined_At DATETIME DEFAULT CURRENT_TIMESTAMP,
            Last_Login DATETIME
        )
    """
    
    result = cloudscale_repo.execute_query(create_sql)
    
    if result.get('success'):
        print("   ✅ Employees table created successfully")
        return True
    else:
        print(f"   ❌ Failed to create Employees table: {result.get('error')}")
        return False

def create_employee_invitations_table():
    """Create the Employee_Invitations table"""
    print("📋 Creating Employee_Invitations table...")
    
    create_sql = f"""
        CREATE TABLE {TABLES['employee_invitations']} (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            Invitation_Token VARCHAR(255) UNIQUE NOT NULL,
            Email VARCHAR(255) NOT NULL,
            Role VARCHAR(50) DEFAULT 'Employee',
            Department VARCHAR(100),
            Designation VARCHAR(100),
            Invited_By INTEGER NOT NULL,
            Invited_At DATETIME DEFAULT CURRENT_TIMESTAMP,
            Expires_At DATETIME NOT NULL,
            Is_Used VARCHAR(10) DEFAULT 'false',
            Used_At DATETIME,
            Registered_Employee_Id VARCHAR(50)
        )
    """
    
    result = cloudscale_repo.execute_query(create_sql)
    
    if result.get('success'):
        print("   ✅ Employee_Invitations table created successfully")
        return True
    else:
        print(f"   ❌ Failed to create Employee_Invitations table: {result.get('error')}")
        return False

def add_user_type_column_to_sessions():
    """Add User_Type column to Sessions table if missing"""
    print("📋 Adding User_Type column to Sessions table...")
    
    # Try to add the column (will fail if it already exists)
    alter_sql = f"ALTER TABLE {TABLES['sessions']} ADD COLUMN User_Type VARCHAR(20) DEFAULT 'user'"
    
    result = cloudscale_repo.execute_query(alter_sql)
    
    if result.get('success'):
        print("   ✅ User_Type column added to Sessions table")
        return True
    else:
        # Column might already exist - check if we can select from it
        test_sql = f"SELECT User_Type FROM {TABLES['sessions']} LIMIT 1"
        test_result = cloudscale_repo.execute_query(test_sql)
        if test_result.get('success'):
            print("   ℹ️  User_Type column already exists in Sessions table")
            return True
        else:
            print(f"   ❌ Failed to add User_Type column: {result.get('error')}")
            return False

def create_admin_employee():
    """Create the first admin employee"""
    print("👤 Creating admin employee...")
    
    # Generate secure password
    password = "SecureRailwayAdmin2024!"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Check if admin already exists
    check_query = f"SELECT ROWID FROM {TABLES['employees']} WHERE Role = 'Admin' LIMIT 1"
    check_result = cloudscale_repo.execute_query(check_query)
    
    if check_result.get('success') and check_result.get('data', {}).get('data'):
        print("   ℹ️  Admin employee already exists")
        return True
    
    admin_data = {
        'Employee_ID': 'ADM001',
        'Full_Name': 'System Administrator',
        'Email': ADMIN_EMAIL,  # Use the admin email from config
        'Password': password_hash,
        'Role': 'Admin',
        'Department': 'Administration',
        'Designation': 'System Administrator',
        'Phone_Number': '+1-800-RAILWAY',
        'Account_Status': 'Active',
        'Is_Active': 1,
        'Joined_At': datetime.now().isoformat()
    }
    
    result = cloudscale_repo.create_record(TABLES['employees'], admin_data)
    
    if result.get('success'):
        print("   ✅ Admin employee created successfully!")
        print(f"   📧 Email: {ADMIN_EMAIL}")
        print(f"   🔑 Password: {password}")
        print(f"   🆔 Employee ID: ADM001")
        print(f"   🏷️  Role: Admin")
        return True
    else:
        print(f"   ❌ Failed to create admin employee: {result.get('error')}")
        return False

def verify_system():
    """Verify the system is working correctly"""
    print("🔍 Verifying system integrity...")
    
    # Check all required tables exist
    tables_to_check = [
        ('Users', TABLES['users']),
        ('Sessions', TABLES['sessions']),
        ('Employees', TABLES['employees']),
        ('Employee_Invitations', TABLES['employee_invitations'])
    ]
    
    all_tables_exist = True
    for name, table_name in tables_to_check:
        if check_table_exists(table_name):
            print(f"   ✅ {name} table exists")
        else:
            print(f"   ❌ {name} table missing")
            all_tables_exist = False
    
    # Check admin employee exists
    admin_query = f"SELECT ROWID, Email, Role FROM {TABLES['employees']} WHERE Role = 'Admin'"
    admin_result = cloudscale_repo.execute_query(admin_query)
    
    if admin_result.get('success') and admin_result.get('data', {}).get('data'):
        admin_data = admin_result['data']['data'][0]
        print(f"   ✅ Admin employee exists: {admin_data.get('Email')}")
    else:
        print("   ❌ No admin employee found")
        all_tables_exist = False
    
    return all_tables_exist

def main():
    print("=" * 80)
    print("🚀 EMPLOYEE INVITATION SYSTEM - COMPREHENSIVE FIX")
    print("=" * 80)
    print()
    print("This script will:")
    print("1. Create missing database tables")
    print("2. Add User_Type column to Sessions table")
    print("3. Create the first admin employee")
    print("4. Verify system integrity")
    print()
    
    try:
        # Step 1: Create missing tables
        print("🏗️  STEP 1: Creating missing database tables")
        
        if not check_table_exists(TABLES['employees']):
            if not create_employees_table():
                print("❌ Failed to create Employees table - aborting")
                return False
        else:
            print("   ℹ️  Employees table already exists")
        
        if not check_table_exists(TABLES['employee_invitations']):
            if not create_employee_invitations_table():
                print("❌ Failed to create Employee_Invitations table - aborting")
                return False
        else:
            print("   ℹ️  Employee_Invitations table already exists")
        
        # Step 2: Add User_Type column
        print("\n🔧 STEP 2: Updating Sessions table schema")
        add_user_type_column_to_sessions()
        
        # Step 3: Create admin employee
        print("\n👤 STEP 3: Creating admin employee")
        if not create_admin_employee():
            print("❌ Failed to create admin employee - manual creation required")
            return False
        
        # Step 4: Verify system
        print("\n🔍 STEP 4: System verification")
        if verify_system():
            print("\n🎉 SUCCESS! Employee invitation system is now ready!")
            print("\n📋 NEXT STEPS:")
            print("1. Logout from current passenger session")
            print("2. Login using employee credentials:")
            print(f"   - Endpoint: POST /session/employee/login")
            print(f"   - Email: {ADMIN_EMAIL}")
            print("   - Password: (see above)")
            print("3. Test employee invitation at: /admin/employee-invitations")
            return True
        else:
            print("\n❌ System verification failed - manual review required")
            return False
            
    except Exception as exc:
        print(f"\n💥 CRITICAL ERROR: {exc}")
        print("Manual database setup required through CloudScale console")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)