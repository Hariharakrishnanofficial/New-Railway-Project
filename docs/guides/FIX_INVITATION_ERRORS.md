# Fix Employee Invitation Errors

## Current Errors

### 1. **500 Internal Server Error** - GET `/admin/employees/invitations`
**Root Cause:** Database tables missing or incorrectly structured
- `Employee_Invitations` table doesn't exist OR
- `Employees` table doesn't exist OR  
- Tables have incorrect column names

### 2. **403 Forbidden** - POST `/admin/employees/invite`
**Root Cause:** Not logged in as admin employee
- You're logged in as a regular passenger/user (not an employee)
- System requires either:
  - Login with email matching `ADMIN_EMAIL` config, OR
  - Login as Employee with `Role='Admin'`

---

## Quick Fix Steps

### Step 1: Diagnose Database Issues

Run the diagnostic script:
```bash
python diagnose_and_fix_db.py
```

This will show you:
- Which tables exist
- Which tables are missing
- Whether Sessions table has User_Type column
- Whether admin employees exist

### Step 2: Fix Missing Tables

If tables are missing, you need to create them in CloudScale database.

#### Create Employees Table

```sql
CREATE TABLE IF NOT EXISTS Employees (
  ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
  Employee_ID TEXT NOT NULL UNIQUE,
  Full_Name TEXT NOT NULL,
  Email TEXT NOT NULL UNIQUE,
  Password_Hash TEXT NOT NULL,
  Role TEXT NOT NULL DEFAULT 'Employee',
  Department TEXT,
  Designation TEXT,
  Phone TEXT,
  Permissions TEXT,
  Is_Active INTEGER DEFAULT 1,
  Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  Last_Login TIMESTAMP
);
```

#### Create Employee_Invitations Table

```sql
CREATE TABLE IF NOT EXISTS Employee_Invitations (
  ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
  Email TEXT NOT NULL,
  Role TEXT NOT NULL DEFAULT 'Employee',
  Department TEXT,
  Designation TEXT,
  Invitation_Token TEXT NOT NULL UNIQUE,
  Expires_At TIMESTAMP NOT NULL,
  Is_Used INTEGER DEFAULT 0,
  Used_At TIMESTAMP,
  Registered_Employee_Id TEXT,
  Invited_By INTEGER,
  Invited_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (Invited_By) REFERENCES Employees(ROWID)
);
```

#### Add User_Type to Sessions Table

```sql
-- Check if User_Type column exists
PRAGMA table_info(Sessions);

-- If User_Type doesn't exist, add it
ALTER TABLE Sessions ADD COLUMN User_Type TEXT DEFAULT 'user';
```

### Step 3: Create First Admin Employee

Since you can't use the invitation system without an admin, you need to create the first admin manually.

#### Option A: SQL INSERT (Recommended)

```sql
-- Generate password hash for your chosen password
-- Use Python to generate bcrypt hash:
```

Run this Python script to generate password hash:

```python
import bcrypt

password = "your_admin_password_here"  # Change this!
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Password Hash: {password_hash}")
```

Then insert the admin employee:

```sql
INSERT INTO Employees (
  Employee_ID,
  Full_Name,
  Email,
  Password_Hash,
  Role,
  Department,
  Designation,
  Permissions,
  Is_Active
) VALUES (
  'ADM001',
  'System Admin',
  'admin@railway.com',  -- Change to your email
  '$2b$12$...your_hash_here...',  -- Use the hash generated above
  'Admin',
  'Administration',
  'System Administrator',
  '{"users": {"view": true, "create": true, "update": true, "delete": true}, "employees": {"view": true, "create": true, "update": true, "delete": true}, "trains": {"view": true, "create": true, "update": true, "delete": true}, "bookings": {"view": true, "manage": true}, "reports": {"view": true, "generate": true}}',
  1
);
```

#### Option B: Use Create Admin Script

Create this script `create_admin.py`:

```python
#!/usr/bin/env python3
import sys
import os
import bcrypt
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions', 'smart_railway_app_function'))

from repositories.cloudscale_repository import CloudScaleRepository
from config import TABLES

def create_admin():
    email = input("Admin email: ").strip().lower()
    full_name = input("Full name: ").strip()
    password = input("Password: ").strip()
    
    # Generate password hash
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Default admin permissions
    permissions = {
        "users": {"view": True, "create": True, "update": True, "delete": True},
        "employees": {"view": True, "create": True, "update": True, "delete": True},
        "trains": {"view": True, "create": True, "update": True, "delete": True},
        "bookings": {"view": True, "manage": True},
        "reports": {"view": True, "generate": True}
    }
    
    repo = CloudScaleRepository()
    
    # Insert admin employee
    insert_data = {
        'Employee_ID': 'ADM001',
        'Full_Name': full_name,
        'Email': email,
        'Password_Hash': password_hash,
        'Role': 'Admin',
        'Department': 'Administration',
        'Designation': 'System Administrator',
        'Permissions': json.dumps(permissions),
        'Is_Active': 1
    }
    
    result = repo.insert_record(TABLES['employees'], insert_data)
    
    if result.get('success'):
        print(f"\n✓ Admin employee created successfully!")
        print(f"  Email: {email}")
        print(f"  Employee ID: ADM001")
        print(f"\nYou can now login with this email and password.")
    else:
        print(f"\n✗ Failed to create admin: {result.get('error')}")

if __name__ == '__main__':
    create_admin()
```

Run it:
```bash
python create_admin.py
```

### Step 4: Login as Admin Employee

1. **Logout** from your current passenger session
2. **Login** using the admin email and password you just created
3. The system should now recognize you as admin (Role='Admin')

### Step 5: Verify Admin Access

Try accessing the employee invitation page again:
- GET `/admin/employees/invitations` should return 200 with empty list
- POST `/admin/employees/invite` should work now

---

## Understanding Admin Authentication

The `require_session_admin` decorator checks for admin in this order:

```python
# From session_middleware.py lines 211-227
email = session_data.get("user_email").lower()
role = session_data.get("user_role").lower()

is_admin_email = (
    email == ADMIN_EMAIL.lower() or           # Config-based admin
    email.endswith("@" + ADMIN_DOMAIN)        # Domain-based admin
)
is_admin_role = role == "admin"               # Role-based admin

if not is_admin_email and not is_admin_role:
    return 403 Forbidden  # Admin access required
```

**You need EITHER:**
- **Email matches config** (`ADMIN_EMAIL` or `@ADMIN_DOMAIN`), OR
- **Role is "Admin"** (from Employees table)

---

## Troubleshooting

### "Table doesn't exist" errors
- Run the SQL CREATE TABLE statements above
- Verify tables exist: `SELECT name FROM sqlite_master WHERE type='table'`

### Still getting 403 after creating admin
- Verify you're logged in as the admin employee (not a passenger)
- Check session: GET `/session/validate` should return `user_type: 'employee'` and `user_role: 'Admin'`
- Try logging out completely and logging back in

### Still getting 500 errors
- Check server logs for actual error message
- Verify all required columns exist in tables
- Ensure Employees table has at least one record

### Can't login as admin employee
- Verify Employee record exists: `SELECT * FROM Employees WHERE Email='your_email'`
- Verify password hash is correct (bcrypt format: starts with `$2b$`)
- Use employee login endpoint: POST `/session/employee/login`

---

## Related Files

- **Database Schema:** `docs/architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md`
- **Migration Guide:** `CRITICAL_DATABASE_MIGRATION_REQUIRED.md`
- **Session Architecture:** `SESSION_ARCHITECTURE_GUIDE.md`
- **Employee Service:** `functions/smart_railway_app_function/services/employee_service.py`
- **Session Middleware:** `functions/smart_railway_app_function/core/session_middleware.py`
