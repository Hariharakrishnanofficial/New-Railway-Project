#!/usr/bin/env python3
"""
Database Diagnostic and Fix Script
Checks if required tables exist and creates admin employee if needed
"""

import sys
import os

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

from config import TABLES
from repositories.cloudscale_repository import CloudScaleRepository

def main():
    print("=" * 80)
    print("SMART RAILWAY - DATABASE DIAGNOSTIC")
    print("=" * 80)
    
    repo = CloudScaleRepository()
    
    # 1. List all tables
    print("\n1. Checking existing tables...")
    result = repo.execute_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    
    if result.get('success'):
        tables = [row['name'] for row in result.get('data', {}).get('data', [])]
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"     - {table}")
    else:
        print(f"   ERROR: Failed to list tables: {result.get('error')}")
        return
    
    # 2. Check for required tables
    print("\n2. Checking required tables...")
    required_tables = {
        'Sessions': TABLES.get('sessions', 'Sessions'),
        'Employees': TABLES.get('employees', 'Employees'),
        'Employee_Invitations': TABLES.get('employee_invitations', 'Employee_Invitations'),
    }
    
    missing_tables = []
    for name, table_name in required_tables.items():
        if table_name in tables:
            print(f"   ✓ {name} ({table_name}) - EXISTS")
        else:
            print(f"   ✗ {name} ({table_name}) - MISSING")
            missing_tables.append(name)
    
    # 3. Check Sessions table structure
    if 'Sessions' in tables:
        print("\n3. Checking Sessions table columns...")
        result = repo.execute_query(f"PRAGMA table_info({TABLES['sessions']})")
        if result.get('success'):
            columns = [row['name'] for row in result.get('data', {}).get('data', [])]
            print(f"   Columns: {', '.join(columns)}")
            
            if 'User_Type' in columns:
                print("   ✓ User_Type column exists")
            else:
                print("   ✗ User_Type column MISSING")
        else:
            print(f"   ERROR: {result.get('error')}")
    
    # 4. Check Employees table structure
    if 'Employees' in tables:
        print("\n4. Checking Employees table columns...")
        result = repo.execute_query(f"PRAGMA table_info({TABLES['employees']})")
        if result.get('success'):
            columns = [row['name'] for row in result.get('data', {}).get('data', [])]
            print(f"   Columns: {', '.join(columns)}")
        else:
            print(f"   ERROR: {result.get('error')}")
        
        # Count employees
        result = repo.execute_query(f"SELECT COUNT(*) as count, SUM(CASE WHEN Role='Admin' THEN 1 ELSE 0 END) as admin_count FROM {TABLES['employees']}")
        if result.get('success'):
            data = result.get('data', {}).get('data', [{}])[0]
            total = data.get('count', 0)
            admin_count = data.get('admin_count', 0)
            print(f"   Total employees: {total}")
            print(f"   Admin employees: {admin_count}")
            
            if admin_count == 0:
                print("   ⚠ WARNING: No admin employees found!")
        else:
            print(f"   ERROR: {result.get('error')}")
    
    # 5. Check Employee_Invitations table structure  
    if 'Employee_Invitations' in tables:
        print("\n5. Checking Employee_Invitations table columns...")
        result = repo.execute_query(f"PRAGMA table_info({TABLES['employee_invitations']})")
        if result.get('success'):
            columns = [row['name'] for row in result.get('data', {}).get('data', [])]
            print(f"   Columns: {', '.join(columns)}")
            
            required_cols = ['Role', 'Department', 'Designation', 'Invited_By']
            missing_cols = [col for col in required_cols if col not in columns]
            if missing_cols:
                print(f"   ✗ Missing columns: {', '.join(missing_cols)}")
            else:
                print("   ✓ All required columns present")
        else:
            print(f"   ERROR: {result.get('error')}")
        
        # Count invitations
        result = repo.execute_query(f"SELECT COUNT(*) as count FROM {TABLES['employee_invitations']}")
        if result.get('success'):
            count = result.get('data', {}).get('data', [{}])[0].get('count', 0)
            print(f"   Total invitations: {count}")
        else:
            print(f"   ERROR: {result.get('error')}")
    
    # 6. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if missing_tables:
        print(f"✗ CRITICAL: Missing tables: {', '.join(missing_tables)}")
        print("\n  ACTION REQUIRED:")
        print("  1. Run database migration script to create missing tables")
        print("  2. See CRITICAL_DATABASE_MIGRATION_REQUIRED.md for instructions")
    else:
        print("✓ All required tables exist")
        
        # Check if we need an admin employee
        if 'Employees' in tables:
            result = repo.execute_query(f"SELECT COUNT(*) as count FROM {TABLES['employees']} WHERE Role='Admin'")
            if result.get('success'):
                admin_count = result.get('data', {}).get('data', [{}])[0].get('count', 0)
                if admin_count == 0:
                    print("\n✗ WARNING: No admin employee found")
                    print("\n  ACTION REQUIRED:")
                    print("  1. Create an admin employee manually in the database")
                    print("  2. Or use the employee invitation system to create one")
                    print("  3. Login with the admin employee to access admin features")
                else:
                    print("\n✓ Admin employee(s) found")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
