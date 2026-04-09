
import os
import sys
import logging
import hashlib

# Add the function directory to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'functions', 'smart_railway_app_function'))

import zcatalyst_sdk
from repositories.cloudscale_repository import init_catalyst, cloudscale_repo
from config import TABLES

# Import security to get the correct hashing instance
try:
    from core.security import ARGON2_AVAILABLE, BCRYPT_AVAILABLE, _ph
    import bcrypt
except ImportError:
    ARGON2_AVAILABLE = False
    BCRYPT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_employee_with_argon2():
    email = "test_verified_2@railway.com"
    password = "Admin@123"
    
    print("\n" + "="*60)
    print("🚀 SMART RAILWAY: SYNC ADMIN EMPLOYEE (ARGON2)")
    print("="*60)
    
    # Generate Hash based on available library
    if ARGON2_AVAILABLE:
        print("Using Argon2id for hashing...")
        # Note: _ph is already initialized in core.security
        password_hash = _ph.hash(password)
    elif BCRYPT_AVAILABLE:
        print("Argon2 not found, falling back to bcrypt...")
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
    else:
        print("⚠️ No crypto libraries found, using SHA-256 fallback...")
        password_hash = hashlib.sha256(password.encode()).hexdigest()

    print(f"Generated Hash: {password_hash[:20]}...")

    try:
        # Initialize Catalyst SDK for Local Execution
        print("Initializing Catalyst SDK locally with project context...")
        # Explicit empty dict informs the SDK to use CLI session ('catalyst login')
        # instead of the serverless request header context.
        app = zcatalyst_sdk.initialize({})
        init_catalyst(app)
        
        # Prepare data matching the provided JSON from user
        employee_data = {
            "Employee_ID": "Admin001",
            "Email": email,
            "Full_Name": "System Admin",
            "Password": password_hash,
            "Role": "Admin",
            "Account_Status": "Active",
            "Is_Active": True,
            "Designation": "ADMIN",
            "Department": "ADMIN",
            "Joined_At": "2026-04-07 17:06:55"
        }
        
        # 1. Purge any conflicting records
        print(f"Purging any conflicting records for: {email}...")
        # Check if table key is available in TABLES
        table_name = TABLES.get('employees', 'Employees')
        check_query = f"SELECT ROWID FROM {table_name} WHERE Email = '{email}'"
        conflicts = cloudscale_repo.execute_query(check_query)
        
        if conflicts.get('success') and conflicts['data'].get('data'):
            for row in conflicts['data']['data']:
                rid = row.get('ROWID')
                # Use direct datastore call to avoid repo Select* logic issue for now
                app.datastore().table(table_name).delete_row(rid)
                print(f"Deleted conflict ROWID: {rid}")
        
        # 2. Create the clean new record
        print(f"Creating record in table: {table_name}...")
        result = cloudscale_repo.create_record('employees', employee_data)
        
        if result.get('success'):
            print("\n✅ SUCCESS: Admin Employee record is now active.")
            print(f"📧 Email: {email}")
            print(f"🔑 Password: {password}")
            print(f"🆔 Employee ID: Admin001")
            print(f"🔒 Hash Type: {'Argon2id' if ARGON2_AVAILABLE else 'Bcrypt/Fallback'}")
            print("="*60)
            print("Login via the 'Employee' tab in the UI.")
        else:
            print(f"\n❌ ERROR: {result.get('error')}")

    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        print("\nFix: Run 'catalyst login' first if not already authenticated.")

if __name__ == "__main__":
    create_admin_employee_with_argon2()
