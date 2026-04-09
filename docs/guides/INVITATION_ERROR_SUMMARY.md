# Employee Invitation System - Error Resolution Guide

## Problem Summary

Your employee invitation system has two errors:

1. **500 Internal Server Error** - Cannot fetch invitations list
2. **403 Forbidden** - Cannot create new invitations

## Root Causes Identified

### 500 Error: Missing Database Tables
The backend code tries to query `Employees` and `Employee_Invitations` tables that either:
- Don't exist in your CloudScale database, OR
- Exist but have incorrect column structure

**Code Location:** `employee_invitation_service.py` lines 400-417
```python
query = f"""
    SELECT i.*, e.Full_Name as Invited_By_Name, e.Employee_ID as Invited_By_Emp_ID
    FROM Employee_Invitations i
    LEFT JOIN Employees e ON i.Invited_By = e.ROWID
    ...
"""
```

### 403 Error: Not Logged In as Admin
The `@require_session_admin` decorator requires you to be logged in as an **admin employee**, but you're currently logged in as a regular passenger/user.

**Code Location:** `session_middleware.py` lines 211-227
```python
# Admin check logic:
is_admin_email = email == ADMIN_EMAIL or email.endswith("@" + ADMIN_DOMAIN)
is_admin_role = role == "admin"

if not is_admin_email and not is_admin_role:
    return 403 Forbidden  # ← You're hitting this
```

## Solution Path

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Diagnose Database                                  │
│  Run: python diagnose_and_fix_db.py                         │
│  This shows which tables exist and what's missing           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Create Missing Tables                              │
│  Run SQL CREATE TABLE statements for:                       │
│  - Employees                                                 │
│  - Employee_Invitations                                      │
│  - Add User_Type column to Sessions (if missing)            │
│  See: FIX_INVITATION_ERRORS.md                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Create First Admin Employee                        │
│  Option A: Run create_admin.py (recommended)                │
│  Option B: Generate hash with generate_password_hash.py     │
│            Then run SQL INSERT manually                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Login as Admin                                     │
│  1. Logout from current passenger session                   │
│  2. Login with admin email/password                         │
│  3. Use employee login endpoint:                            │
│     POST /session/employee/login                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Test Employee Invitations                          │
│  - GET /admin/employees/invitations → should return 200     │
│  - POST /admin/employees/invite → should return 201         │
└─────────────────────────────────────────────────────────────┘
```

## Files Created to Help You

| File | Purpose |
|------|---------|
| `FIX_INVITATION_ERRORS.md` | Complete step-by-step fix guide with SQL statements |
| `diagnose_and_fix_db.py` | Diagnostic script to check database state |
| `create_admin.py` | Interactive script to create first admin employee |
| `generate_password_hash.py` | Generate bcrypt hash for manual SQL INSERT |
| `INVITATION_ERROR_SUMMARY.md` | This file - overview and solution path |

## Quick Start

### If you know tables are missing:

```bash
# 1. Create tables (run these SQL statements in CloudScale)
#    See FIX_INVITATION_ERRORS.md for full SQL

# 2. Create admin employee
python create_admin.py

# 3. Login as admin and test
```

### If you're not sure what's wrong:

```bash
# 1. Run diagnostic
python diagnose_and_fix_db.py

# 2. Follow the recommendations in the output

# 3. Create admin
python create_admin.py

# 4. Login and test
```

## Understanding the Employee System

### Two Types of Users

| Aspect | Passenger/User | Employee |
|--------|----------------|----------|
| **Table** | `Users` | `Employees` |
| **Login Endpoint** | `/session/login` | `/session/employee/login` |
| **Session Type** | `user_type='user'` | `user_type='employee'` |
| **Roles** | Always "User" | "Admin" or "Employee" |
| **Permissions** | Book tickets, view bookings | Manage system, invite employees |

### Admin Requirements

To access admin endpoints (like employee invitations), you must:

**EITHER:**
- Be logged in with email matching `ADMIN_EMAIL` config
- Be logged in with email ending with `@ADMIN_DOMAIN`

**OR:**
- Be logged in as Employee with `Role='Admin'`

**Current Issue:** You're logged in as a passenger, not an employee.

## Common Mistakes to Avoid

1. ❌ **Trying to use passenger login for admin access**
   - ✓ Use `/session/employee/login` instead

2. ❌ **Creating User record instead of Employee record**
   - ✓ Admin must be in `Employees` table, not `Users` table

3. ❌ **Setting user_role='Admin' for passengers**
   - ✓ Admin role only works for employees (user_type='employee')

4. ❌ **Using plaintext password in database**
   - ✓ Must use bcrypt hash (starts with `$2b$`)

5. ❌ **Forgetting to logout before switching user types**
   - ✓ Logout from passenger session before logging in as employee

## Testing Checklist

After following the fix steps, verify:

- [ ] Diagnostic script shows all required tables exist
- [ ] At least one employee with Role='Admin' exists
- [ ] Can login as admin employee (POST `/session/employee/login`)
- [ ] Session validation shows `user_type: 'employee'` and `user_role: 'Admin'`
- [ ] GET `/admin/employees/invitations` returns 200 (even if empty list)
- [ ] POST `/admin/employees/invite` works (returns 201)
- [ ] Frontend UI shows invitation form without errors

## If You Still Have Issues

1. **Check backend logs** for detailed error messages
2. **Verify table structure** with `PRAGMA table_info(Employees)`
3. **Test session** with GET `/session/validate`
4. **Check admin status** with GET `/session/user`

## Related Documentation

- `CRITICAL_DATABASE_MIGRATION_REQUIRED.md` - Full database migration guide
- `SESSION_ARCHITECTURE_GUIDE.md` - Session system design
- `docs/architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md` - Complete schema
- `docs/architecture/IMPLEMENTATION_NOTES.md` - Technical implementation details

---

**Need Help?**
- Run `python diagnose_and_fix_db.py` to see what's missing
- Check `FIX_INVITATION_ERRORS.md` for detailed SQL statements
- Verify you're logged in as admin employee, not passenger
