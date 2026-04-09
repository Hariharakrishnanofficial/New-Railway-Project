# 🚨 CRITICAL: Multiple Database Tables Missing

**Current Errors:** 
- `Invalid input value for column name` when creating sessions
- `500 Internal Server Error` on employee invitations
- `403 Forbidden` on admin endpoints

**Date:** April 6, 2026

---

## ⛔ Current Issues

**You CANNOT login, register, or use admin features** until ALL database tables are created!

### Error Messages:
```
1. ERROR Create record error in Sessions: 
   {'code': 'INVALID_INPUT', 'message': 'Invalid input value for column name'}

2. 500 Internal Server Error on /admin/employees/invitations
   
3. ZCQL query error: {'code': 'ZCQL QUERY ERROR', 
   'message': 'Unknown Table Trains or Unknown Column Is_Active'}
```

### Root Cause:
**THREE missing database schema updates:**

1. ❌ **Sessions table** missing `User_Type` column → Login/registration fails
2. ❌ **Employees table** doesn't exist → Admin features fail  
3. ❌ **Employee_Invitations table** missing columns → Invitation system fails

---

## ✅ COMPLETE DATABASE FIX - 15 MINUTES

### Step 1: Fix Sessions Table (BLOCKING LOGIN)

1. **Go to:** Catalyst Console → CloudScale → Data Store → Sessions table
2. **Add column:**
   ```
   Column Name:  User_Type
   Data Type:    text
   Required:     ✅ Yes
   Default:      user
   ```
3. **Save changes**

**Test:** Try to login - should work after this step

---

### Step 2: Create Employees Table

1. **Go to:** Catalyst Console → CloudScale → Data Store
2. **Click:** "Create New Table" 
3. **Table Name:** `Employees`
4. **Add these columns:**

| Column Name | Data Type | Required | Default | Unique |
|------------|-----------|----------|---------|--------|
| ROWID | bigint | Auto PK | - | Yes |
| Employee_ID | text | Yes | - | Yes |
| Full_Name | text | Yes | - | No |
| Email | text | Yes | - | Yes |
| Password | text | Yes | - | No |
| Phone_Number | text | No | - | No |
| Role | text | Yes | Employee | No |
| Department | text | No | - | No |
| Designation | text | No | - | No |
| Permissions | text | No | - | No |
| Invited_By | bigint | Yes | - | No |
| Invitation_Id | bigint | No | - | No |
| Joined_At | text | Yes | - | No |
| Account_Status | text | Yes | Active | No |
| Last_Login | text | No | - | No |
| Created_At | text | Yes | - | No |
| Updated_At | text | No | - | No |

5. **Save table**

---

### Step 3: Update Employee_Invitations Table

**Check if table exists:**
- Go to Data Store → Look for "Employee_Invitations" table

**If table exists:** Add these columns:
- Role (text, required, default: 'Employee')
- Department (text, optional)  
- Designation (text, optional)

**If table doesn't exist:** Create new table with all columns from PHASE1_DEPLOYMENT_GUIDE.md

---

### Step 4: Create First Admin Employee

**After creating Employees table:**

1. **Go to:** Employees table → Add Row
2. **Fill in:**
   ```
   Employee_ID: ADM001
   Full_Name: Your Name
   Email: your-admin@email.com
   Password: [Generate bcrypt hash - see guide]
   Role: Admin
   Department: Administration
   Designation: System Administrator
   Permissions: {"admin_access": true, "can_invite_employees": true}
   Account_Status: Active
   Joined_At: [Current ISO timestamp]
   Created_At: [Current ISO timestamp]
   Invited_By: 1
   ```
3. **Save record**

---

## 🔍 Verification Checklist

### After Step 1 (Sessions):
- [ ] Try login → Should work
- [ ] Try registration → Should work
- [ ] No "Invalid input value for column name" errors

### After Step 2 (Employees table):
- [ ] Go to Data Store → See "Employees" table listed
- [ ] Table has all required columns
- [ ] First admin record exists

### After Step 3 (Employee_Invitations):
- [ ] Admin panel loads without errors
- [ ] Can access /admin/employees/invitations page
- [ ] No 500 errors on invitation endpoints

### Complete Success:
- [ ] Can login as passenger
- [ ] Can login as admin employee  
- [ ] Admin panel loads
- [ ] Employee invitation page works
- [ ] Can send employee invitations

---

## 📖 Detailed Instructions

**See:** `PHASE1_DEPLOYMENT_GUIDE.md` for:
- Complete table schemas with exact column specifications
- SQL scripts for data migration
- Bcrypt password generation
- ISO timestamp examples
- Troubleshooting guide

---

## 🚨 Order Matters!

**Do these in order:**

1. **FIRST:** Sessions table (fixes login)
2. **SECOND:** Employees table (enables admin)  
3. **THIRD:** Employee_Invitations columns (enables invitations)
4. **FOURTH:** Create first admin (enables full system)

**DON'T:** Try to use admin features until all tables exist

---

## ⚡ Quick Commands

**Get current timestamp (ISO format):**
```
2026-04-06T11:04:03.000Z
```

**Generate bcrypt hash (online tool or Python):**
```python
import bcrypt
password_hash = bcrypt.hashpw(b"YourPassword123!", bcrypt.gensalt()).decode('utf-8')
print(password_hash)
```

**Admin permissions JSON:**
```json
{"admin_access": true, "can_invite_employees": true, "modules": {"bookings": ["view", "create", "cancel"], "trains": ["view"], "users": ["view"], "employees": ["view", "invite", "edit"], "reports": ["view", "export"], "announcements": ["view", "create", "edit"]}}
```

---

## 🆘 If Still Getting Errors

1. **Refresh Catalyst Console** after making changes
2. **Check table names match exactly:**
   - Sessions (with User_Type column)
   - Employees (new table)
   - Employee_Invitations (updated columns)
3. **Check column names are case-sensitive**
4. **Verify first admin employee exists**
5. **Clear browser cache** if admin panel still shows errors

---

**NEXT ACTIONS:**
1. Add User_Type column to Sessions table NOW ← **THIS FIXES LOGIN**
2. Create Employees table  
3. Update/Create Employee_Invitations table
4. Add first admin employee record
5. Test full system
