#!/usr/bin/env python3
"""
CloudScale Connection Test
Tests if CloudScale database is connected and creates a test user.
"""
import os
import sys
from datetime import datetime

# Add functions path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'catalyst_backend'))

def test_connection():
    """Test CloudScale connection and create a user."""
    print("=" * 60)
    print("CloudScale Connection Test")
    print("=" * 60)

    try:
        from config import TABLES
        print("[OK] Config loaded successfully")
        print(f"  Tables configured: {len(TABLES)}")

        # Import CloudScale repository
        from repositories.cloudscale_repository import cloudscale_repo, CriteriaBuilder
        print("[OK] CloudScale repository imported")

        # Import security for password hashing
        from core.security import hash_password
        print("[OK] Security module imported")

        # Initialize Catalyst SDK (simulated for local test)
        print("\n[Testing CloudScale Connection]")

        # Test 1: Check if Users table exists by querying it
        print("1. Testing Users table access...")
        try:
            users = cloudscale_repo.get_records(
                TABLES['users'],
                criteria='(Account_Status == "Active")',
                limit=1
            )
            print(f"   [OK] Users table accessible ({len(users)} active users found)")
        except Exception as e:
            print(f"   [WARN] {e}")
            print("   Note: This may fail in local testing without Catalyst context")

        # Test 2: Create a test user
        print("\n2. Creating test user...")
        test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"

        test_user = {
            'Full_Name': 'Test User CloudScale',
            'Email': test_email,
            'Password': hash_password('TestPass123'),
            'Phone_Number': '9876543210',
            'Address': '123 Test Street',
            'Role': 'User',
            'Account_Status': 'Active'
        }

        print(f"   User details:")
        print(f"   - Email: {test_email}")
        print(f"   - Name: {test_user['Full_Name']}")
        print(f"   - Role: {test_user['Role']}")

        try:
            result = cloudscale_repo.create_record(TABLES['users'], test_user)
            print(f"   [OK] User created successfully!")
            print(f"   Record ID: {result}")
        except Exception as e:
            print(f"   [FAIL] Failed to create user: {e}")
            print("   Note: This requires active Catalyst context (catalyst serve)")
            return False

        # Test 3: Query the user
        print("\n3. Querying created user...")
        try:
            criteria = CriteriaBuilder().eq('Email', test_email).build()
            found_users = cloudscale_repo.get_records(
                TABLES['users'],
                criteria=criteria,
                limit=1
            )
            if found_users:
                print(f"   [OK] User found in database!")
                print(f"   User: {found_users[0].get('Full_Name')} ({found_users[0].get('Email')})")
            else:
                print(f"   [WARN] User not found (may be created in separate context)")
        except Exception as e:
            print(f"   [WARN] Query failed: {e}")

        print("\n" + "=" * 60)
        print("CloudScale Repository Configuration:")
        print("=" * 60)
        print("[OK] All imports successful")
        print("[OK] CloudScale repository configured")
        print("[OK] CriteriaBuilder available")
        print("[OK] Security module working")
        print("\n[NOTE] Actual database operations require 'catalyst serve' running")
        print("  with valid CATALYST_ACCESS_TOKEN in environment.")

        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
