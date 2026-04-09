#!/usr/bin/env python3
"""Create a sample Employee for login testing.

Usage:
  1) Run: catalyst login
  2) From repo root: python create_sample_employee.py

This script creates (or replaces) a single employee record in CloudScale.
It is meant for development/testing only.
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Add the function directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

import zcatalyst_sdk

from repositories.cloudscale_repository import init_catalyst, cloudscale_repo, CriteriaBuilder
from config import TABLES
from core.security import hash_password

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Change these if needed
SAMPLE_EMPLOYEE_EMAIL = 'sample.employee@railway.com'
SAMPLE_EMPLOYEE_PASSWORD = 'Employee@123'
SAMPLE_EMPLOYEE_NAME = 'Sample Employee'
SAMPLE_EMPLOYEE_ROLE = 'Employee'  # 'Employee' or 'Admin'
SAMPLE_EMPLOYEE_DEPT = 'Operations'
SAMPLE_EMPLOYEE_DESIG = 'Staff'
SAMPLE_EMPLOYEE_PHONE = '+91-9000000000'


def main():
    print('\n' + '=' * 70)
    print('SMART RAILWAY - CREATE SAMPLE EMPLOYEE')
    print('=' * 70)

    try:
        app = zcatalyst_sdk.initialize({})
        init_catalyst(app)
    except Exception as exc:
        print(f'❌ Failed to initialize Catalyst SDK: {exc}')
        print("Fix: Run 'catalyst login' and try again.")
        sys.exit(1)

    table_name = TABLES.get('employees') or 'Employees'
    email = SAMPLE_EMPLOYEE_EMAIL.strip().lower()

    # Delete any existing employee with the same email (avoids unique constraint issues)
    try:
        criteria = CriteriaBuilder().eq('Email', email).build()
        query = f"SELECT ROWID, Employee_ID, Email FROM {table_name} WHERE {criteria} LIMIT 10"
        existing = cloudscale_repo.execute_query(query)

        if existing.get('success') and existing.get('data', {}).get('data'):
            rows = existing['data']['data']
            print(f"Found {len(rows)} existing record(s) for {email}. Deleting...")
            ds_table = app.datastore().table(table_name)
            for row in rows:
                rid = row.get('ROWID')
                if rid is not None:
                    ds_table.delete_row(rid)
                    print(f"  - Deleted ROWID: {rid}")
    except Exception as exc:
        print(f"⚠️  Could not check/delete existing employee: {exc}")

    # Create new employee
    employee_id = cloudscale_repo.get_next_employee_id('Admin' if SAMPLE_EMPLOYEE_ROLE.lower() == 'admin' else 'Employee')
    password_hash = hash_password(SAMPLE_EMPLOYEE_PASSWORD)
    now = datetime.now(timezone.utc).isoformat()

    employee_data = {
        'Employee_ID': employee_id,
        'Full_Name': SAMPLE_EMPLOYEE_NAME,
        'Email': email,
        'Password': password_hash,
        'Role': 'Admin' if SAMPLE_EMPLOYEE_ROLE.lower() == 'admin' else 'Employee',
        'Department': SAMPLE_EMPLOYEE_DEPT,
        'Designation': SAMPLE_EMPLOYEE_DESIG,
        'Phone_Number': SAMPLE_EMPLOYEE_PHONE,
        'Account_Status': 'Active',
        'Is_Active': True,
        'Joined_At': now,
    }

    result = cloudscale_repo.create_record('employees', employee_data)

    if result.get('success'):
        print('\n✅ Sample employee created')
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {SAMPLE_EMPLOYEE_PASSWORD}")
        print(f"🆔 Employee_ID: {employee_id}")
        print("\nLogin via the UI → Employee tab.")
    else:
        print('\n❌ Failed to create sample employee')
        print(result.get('error') or result)
        sys.exit(2)


if __name__ == '__main__':
    main()
