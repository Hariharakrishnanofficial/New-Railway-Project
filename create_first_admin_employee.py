#!/usr/bin/env python3
"""
Create First Admin Employee - Smart Railway Ticketing System
Comprehensive script to set up the first admin employee for the employee invitation system.

This script will:
1. Check if required tables exist and create them if needed
2. Create the first admin employee with proper credentials
3. Ensure the system is ready for employee invitations
4. Use proper CloudScale/ZCQL syntax
"""

import sys
import os
import bcrypt
import logging
from datetime import datetime, timedelta

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

try:
    import zcatalyst_sdk
    from repositories.cloudscale_repository import init_catalyst, cloudscale_repo
    from config import TABLES, ADMIN_EMAIL
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def init_catalyst_app():
    """Initialize Catalyst SDK"""
    try:
        # Initialize empty dict for local CLI session
        app = zcatalyst_sdk.initialize({})
        init_catalyst(app)
        logger.info("Catalyst SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Catalyst SDK: {e}")
        return False

def check_table_exists(table_name):
    """Check if a table exists in CloudScale"""
    try:
        # Try to query the table with LIMIT 1 to check existence
        result = cloudscale_repo.execute_query(f"SELECT ROWID FROM {table_name} LIMIT 1")
        return result.get('success', False)
    except Exception as e:
        logger.debug(f"Table {table_name} does not exist or query failed: {e}")
        return False

def create_users_table():
    """Create the Users table with proper CloudScale schema"""
    print("📋 Creating Users table...")
    
    # CloudScale/ZCQL compatible CREATE TABLE statement
    create_sql = f"""
        CREATE TABLE {TABLES['users']} (
            Full_Name VARCHAR(255) NOT NULL,
            Email VARCHAR(255) UNIQUE NOT NULL,
            Password VARCHAR(255) NOT NULL,
            Phone_Number VARCHAR(20),
            Date_of_Birth VARCHAR(10),
            Gender VARCHAR(10),
            Aadhaar_Number VARCHAR(12),
            PAN_Number VARCHAR(10),
            Role VARCHAR(20) DEFAULT 'USER',
            Account_Status VARCHAR(20) DEFAULT 'Active',
            Email_Verified BOOLEAN DEFAULT FALSE,
            Phone_Verified BOOLEAN DEFAULT FALSE,
            Is_Active BOOLEAN DEFAULT TRUE,
            Last_Login DATETIME,
            Profile_Picture_URL TEXT,
            Preferred_Language VARCHAR(10) DEFAULT 'en',
            Notification_Preferences TEXT,
            Privacy_Settings TEXT
        )
    """
    
    result = cloudscale_repo.execute_query(create_sql)
    
    if result.get('success'):
        print("   ✅ Users table created successfully")
        return True
    else:
        print(f"   ❌ Failed to create Users table: {result.get('error')}")
        return False

def create_employees_table():
    """Create the Employees table with proper CloudScale schema"""
    print("📋 Creating Employees table...")
    
    # CloudScale/ZCQL compatible CREATE TABLE statement
    create_sql = f"""
        CREATE TABLE {TABLES['employees']} (
            Employee_ID VARCHAR(50) UNIQUE NOT NULL,
            Full_Name VARCHAR(255) NOT NULL,
            Email VARCHAR(255) UNIQUE NOT NULL,
            Password VARCHAR(255) NOT NULL,
            Role VARCHAR(50) DEFAULT 'Employee',
            Department VARCHAR(100),
            Designation VARCHAR(100),
            Phone_Number VARCHAR(20),
            Account_Status VARCHAR(20) DEFAULT 'Active',
            Is_Active BOOLEAN DEFAULT TRUE,
            Joined_At DATETIME,
            Last_Login DATETIME,
            Permissions TEXT,
            User_Id VARCHAR(20)
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
            Invitation_Token VARCHAR(255) UNIQUE NOT NULL,
            Email VARCHAR(255) NOT NULL,
            Role VARCHAR(50) DEFAULT 'Employee',
            Department VARCHAR(100),
            Designation VARCHAR(100),
            Invited_By VARCHAR(20) NOT NULL,
            Invited_At DATETIME,
            Expires_At DATETIME NOT NULL,
            Is_Used BOOLEAN DEFAULT FALSE,
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

def create_sessions_table():
    """Create the Sessions table with User_Type column"""
    print("📋 Creating Sessions table...")
    
    create_sql = f"""
        CREATE TABLE {TABLES['sessions']} (
            Session_ID VARCHAR(255) UNIQUE NOT NULL,
            User_ID VARCHAR(20),
            Employee_ID VARCHAR(20),
            User_Type VARCHAR(20) DEFAULT 'user',
            Session_Data TEXT,
            IP_Address VARCHAR(45),
            User_Agent TEXT,
            Created_At DATETIME,
            Last_Activity DATETIME,
            Expires_At DATETIME,
            Is_Active BOOLEAN DEFAULT TRUE,
            CSRF_Token VARCHAR(255)
        )
    """
    
    result = cloudscale_repo.execute_query(create_sql)
    
    if result.get('success'):
        print("   ✅ Sessions table created successfully")
        return True
    else:
        print(f"   ❌ Failed to create Sessions table: {result.get('error')}")
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
    
    # Admin credentials
    admin_email = ADMIN_EMAIL
    admin_password = "AdminPassword2024!"
    admin_name = "System Administrator"
    admin_employee_id = "ADM001"
    
    # Generate secure password hash
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    # Check if admin already exists in Employees table
    check_query = f"SELECT ROWID, Email FROM {TABLES['employees']} WHERE Role = 'Admin' OR Email = '{admin_email}' LIMIT 1"
    check_result = cloudscale_repo.execute_query(check_query)
    
    if check_result.get('success'):
        existing_data = check_result.get('data', {}).get('data', [])
        if existing_data:
            print("   ℹ️  Admin employee already exists")
            for emp in existing_data:
                print(f"   📧 Email: {emp.get('Email')}")
            return True
    
    # Create employee record (this is the main one needed for auth)
    employee_data = {
        'Employee_ID': admin_employee_id,
        'Full_Name': admin_name,
        'Email': admin_email,
        'Password': password_hash,
        'Role': 'Admin',
        'Department': 'Administration',
        'Designation': 'System Administrator',
        'Phone_Number': '+1-800-RAILWAY',
        'Account_Status': 'Active',
        'Is_Active': True,
        'Joined_At': datetime.now().isoformat(),
        'Permissions': '{"all": true}'  # Full admin permissions
    }
    
    result = cloudscale_repo.create_record('employees', employee_data)
    
    if result.get('success'):
        print("   ✅ Admin employee created successfully!")
        print(f"   📧 Email: {admin_email}")
        print(f"   🔑 Password: {admin_password}")
        print(f"   🆔 Employee ID: {admin_employee_id}")
        print(f"   🏷️  Role: Admin")
        
        # Also create a Users record for backward compatibility if needed
        user_data = {
            'Full_Name': admin_name,
            'Email': admin_email,
            'Password': password_hash,
            'Role': 'ADMIN',
            'Account_Status': 'Active',
            'Email_Verified': True,
            'Is_Active': True
        }
        
        # Try to create user record (ignore if it fails - employee record is primary)
        user_result = cloudscale_repo.create_record('users', user_data)
        if user_result.get('success'):
            print("   ✅ Admin user record also created")
        else:
            print("   ℹ️  Admin user record creation skipped (employee record is sufficient)")
        
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
    
    if admin_result.get('success'):
        admin_data = admin_result.get('data', {}).get('data', [])
        if admin_data:
            admin = admin_data[0]
            print(f"   ✅ Admin employee exists: {admin.get('Email')}")
        else:
            print("   ❌ No admin employee found")
            all_tables_exist = False
    else:
        print("   ❌ Cannot verify admin employee")
        all_tables_exist = False
    
    # Check Sessions table has User_Type column
    sessions_query = f"SELECT User_Type FROM {TABLES['sessions']} LIMIT 1"
    sessions_result = cloudscale_repo.execute_query(sessions_query)
    
    if sessions_result.get('success'):
        print("   ✅ Sessions table has User_Type column")
    else:
        print("   ⚠️  Sessions table may be missing User_Type column")
    
    return all_tables_exist

def main():
    print("=" * 80)
    print("🚀 SMART RAILWAY - CREATE FIRST ADMIN EMPLOYEE")
    print("=" * 80)
    print()
    print("This script will:")
    print("1. Initialize Catalyst SDK")
    print("2. Create missing database tables")
    print("3. Create the first admin employee")
    print("4. Verify system integrity")
    print()
    
    # Initialize Catalyst SDK
    print("🔧 STEP 1: Initializing Catalyst SDK")
    if not init_catalyst_app():
        print("❌ Failed to initialize Catalyst SDK")
        print("\nTroubleshooting:")
        print("1. Make sure you've run 'catalyst login'")
        print("2. Verify you're in the correct project directory")
        print("3. Check your internet connection")
        return False
    
    try:
        # Step 2: Create missing tables
        print("\n🏗️  STEP 2: Creating missing database tables")
        
        # Users table
        if not check_table_exists(TABLES['users']):
            if not create_users_table():
                print("❌ Failed to create Users table - aborting")
                return False
        else:
            print("   ℹ️  Users table already exists")
        
        # Employees table
        if not check_table_exists(TABLES['employees']):
            if not create_employees_table():
                print("❌ Failed to create Employees table - aborting")
                return False
        else:
            print("   ℹ️  Employees table already exists")
        
        # Employee_Invitations table
        if not check_table_exists(TABLES['employee_invitations']):
            if not create_employee_invitations_table():
                print("❌ Failed to create Employee_Invitations table - aborting")
                return False
        else:
            print("   ℹ️  Employee_Invitations table already exists")
        
        # Sessions table
        if not check_table_exists(TABLES['sessions']):
            if not create_sessions_table():
                print("❌ Failed to create Sessions table - aborting")
                return False
        else:
            print("   ℹ️  Sessions table already exists")
            # Try to add User_Type column if missing
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
            print("\n📋 LOGIN CREDENTIALS:")
            print(f"   📧 Email: {ADMIN_EMAIL}")
            print("   🔑 Password: AdminPassword2024!")
            print("   🆔 Employee ID: ADM001")
            print("   🏷️  Role: Admin")
            print("\n📋 NEXT STEPS:")
            print("1. Go to your Railway app at: http://localhost:3001/app/")
            print("2. Click on 'Employee Login' tab")
            print("3. Login using the credentials above")
            print("4. You should now have access to admin features")
            print("5. Test employee invitation at: /admin/employee-invitations")
            print("6. Change the default password after first login")
            return True
        else:
            print("\n❌ System verification failed - manual review required")
            return False
            
    except Exception as exc:
        print(f"\n💥 CRITICAL ERROR: {exc}")
        print("\nThis error suggests a problem with:")
        print("- Database connectivity")
        print("- CloudScale table permissions")
        print("- ZCQL syntax compatibility")
        print("\nPlease check the CloudScale console for more details.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n" + "=" * 80)
            print("✅ SETUP COMPLETE - You can now test employee invitations!")
            print("=" * 80)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)