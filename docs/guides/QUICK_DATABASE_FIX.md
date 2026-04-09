# Quick Fix: Create Database Tables in CloudScale

## The Problem

You're getting:
- **500 Error** on GET `/admin/employees/invitations` → Employees or Employee_Invitations table doesn't exist
- **403 Error** on POST `/admin/employees/invite` → Not logged in as admin employee

## Solution Steps

### Step 1: Access CloudScale Database Console

1. Go to Zoho Catalyst Console
2. Navigate to **Data Store** or **CloudScale**
3. You should see a list of your tables

### Step 2: Check If Tables Exist

Look for these tables:
- ✅ **Sessions** (should already exist)
- ❓ **Employees** (probably missing)
- ❓ **Employee_Invitations** (probably missing)

### Step 3: Create Employees Table

If the **Employees** table doesn't exist, create it:

```sql
CREATE TABLE Employees (
  ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
  Employee_ID TEXT NOT NULL UNIQUE,
  Full_Name TEXT NOT NULL,
  Email TEXT NOT NULL UNIQUE,
  Password_Hash TEXT NOT NULL,
  Role TEXT NOT NULL DEFAULT 'Employee',
  Department TEXT,
  Designation TEXT,
  Phone TEXT,
  Permissions TEXT,
  Is_Active INT DEFAULT 1,
  Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  Last_Login TIMESTAMP
);
```

**Or if using CloudScale UI:**
1. Click "Create Table"
2. Table Name: `Employees`
3. Add columns:
   - `Employee_ID` - TEXT, NOT NULL, UNIQUE
   - `Full_Name` - TEXT, NOT NULL
   - `Email` - TEXT, NOT NULL, UNIQUE
   - `Password_Hash` - TEXT, NOT NULL
   - `Role` - TEXT, NOT NULL, DEFAULT 'Employee'
   - `Department` - TEXT
   - `Designation` - TEXT
   - `Phone` - TEXT
   - `Permissions` - TEXT
   - `Is_Active` - INT, DEFAULT 1
   - `Created_At` - TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
   - `Updated_At` - TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
   - `Last_Login` - TIMESTAMP

### Step 4: Create Employee_Invitations Table

```sql
CREATE TABLE Employee_Invitations (
  ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
  Email TEXT NOT NULL,
  Role TEXT NOT NULL DEFAULT 'Employee',
  Department TEXT,
  Designation TEXT,
  Invitation_Token TEXT NOT NULL UNIQUE,
  Expires_At TIMESTAMP NOT NULL,
  Is_Used INT DEFAULT 0,
  Used_At TIMESTAMP,
  Registered_Employee_Id TEXT,
  Invited_By BIGINT,
  Invited_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Or if using CloudScale UI:**
1. Click "Create Table"
2. Table Name: `Employee_Invitations`
3. Add columns:
   - `Email` - TEXT, NOT NULL
   - `Role` - TEXT, NOT NULL, DEFAULT 'Employee'
   - `Department` - TEXT
   - `Designation` - TEXT
   - `Invitation_Token` - TEXT, NOT NULL, UNIQUE
   - `Expires_At` - TIMESTAMP, NOT NULL
   - `Is_Used` - INT, DEFAULT 0
   - `Used_At` - TIMESTAMP
   - `Registered_Employee_Id` - TEXT
   - `Invited_By` - BIGINT
   - `Invited_At` - TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

### Step 5: Add User_Type Column to Sessions Table

If the Sessions table is missing the `User_Type` column:

```sql
ALTER TABLE Sessions ADD COLUMN User_Type TEXT DEFAULT 'user';
```

**Or if using CloudScale UI:**
1. Open the **Sessions** table
2. Click "Add Column"
3. Column Name: `User_Type`
4. Type: TEXT
5. Default Value: `'user'`

### Step 6: Create First Admin Employee

Once the Employees table exists, create an admin employee:

**Option A: Using Python Script**
```bash
python create_admin.py
```

**Option B: Direct SQL INSERT**

First, generate a password hash:
```bash
python generate_password_hash.py
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
  'admin@railway.com',
  '$2b$12$...your_hash_here...',  -- Replace with hash from generate_password_hash.py
  'Admin',
  'Administration',
  'System Administrator',
  '{"users": {"view": true, "create": true, "update": true, "delete": true}, "employees": {"view": true, "create": true, "update": true, "delete": true}, "trains": {"view": true, "create": true, "update": true, "delete": true}, "bookings": {"view": true, "manage": true}, "reports": {"view": true, "generate": true}}',
  1
);
```

### Step 7: Verify Tables Exist

After creating tables, verify they exist:

1. Refresh your CloudScale console
2. You should see:
   - Sessions
   - Employees (with 1 record - the admin)
   - Employee_Invitations (empty initially)

### Step 8: Login as Admin

1. **Logout** from your current session (if logged in as passenger)
2. **Login** using the admin employee credentials:
   - URL: `POST http://localhost:3000/server/smart_railway_app_function/session/employee/login`
   - Body: `{ "email": "admin@railway.com", "password": "your_password" }`

### Step 9: Test Employee Invitations

Now try the invitation endpoints again:
1. GET `/admin/employees/invitations` → Should return 200 with empty list
2. POST `/admin/employees/invite` → Should return 201 and create invitation

---

## Troubleshooting

### "Table already exists" error
- The table exists but might have wrong structure
- Drop the table and recreate it, OR
- Use ALTER TABLE to add missing columns

### "Cannot access CloudScale console"
- You might need admin access to your Catalyst project
- Ask your team admin to grant you Data Store permissions

### "Still getting 500 errors after creating tables"
- Check column names match exactly (case-sensitive!)
- Verify Invited_By column type is BIGINT (not TEXT)
- Check that ROWID is set as PRIMARY KEY with AUTO_INCREMENT

### "Still getting 403 errors after creating admin"
- Make sure you logged out first
- Use `/session/employee/login` endpoint (NOT `/session/login`)
- Verify admin employee exists: `SELECT * FROM Employees WHERE Role='Admin'`
- Check session validation: `GET /session/validate` should show `user_type: 'employee'`

---

## Alternative: Use CloudScale Web Interface

If SQL is not working, you can use the CloudScale web interface:

1. Go to Catalyst Console → Data Store → CloudScale
2. Click "Create Table" button
3. Enter table name
4. Add columns one by one using the UI
5. Set column types, default values, constraints
6. Save table

This is easier but slower than SQL.

---

## Quick Verification Checklist

After completing all steps, verify:

- [ ] Employees table exists with correct columns
- [ ] Employee_Invitations table exists with correct columns
- [ ] Sessions table has User_Type column
- [ ] At least one admin employee exists (Role='Admin')
- [ ] Can login as admin via `/session/employee/login`
- [ ] Session validation shows `user_type: 'employee'` and `user_role: 'Admin'`
- [ ] GET `/admin/employees/invitations` returns 200
- [ ] POST `/admin/employees/invite` returns 201

---

## Need More Help?

If you're still stuck after following these steps:

1. Share a screenshot of your CloudScale tables list
2. Share the exact error message from backend logs
3. Share the result of GET `/session/validate` to verify your login
4. I'll help debug further!
