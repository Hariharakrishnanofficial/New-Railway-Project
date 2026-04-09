# Phase 1 Deployment Guide - User/Employee Separation

## ⚠️ CRITICAL: Database Updates Required

Before deploying the latest code, you **MUST** update your CloudScale database tables in the Zoho Catalyst Console.

---

## 🔧 Required Database Changes

### 1. Update Sessions Table

Add the `User_Type` column to the Sessions table:

**Go to:** Catalyst Console → CloudScale → Data Store → Sessions table

**Add Column:**
- **Column Name:** `User_Type`
- **Data Type:** `text`
- **Required:** Yes
- **Default Value:** `user`

**After adding, update existing records:**
```sql
UPDATE Sessions SET User_Type = 'user' WHERE User_Type IS NULL OR User_Type = ''
```

---

### 2. Create Employees Table

**Go to:** Catalyst Console → CloudScale → Data Store → Create New Table

**Table Name:** `Employees`

**Columns:**

| Column Name | Data Type | Required | Default | Description |
|------------|-----------|----------|---------|-------------|
| ROWID | bigint | Auto | - | Primary key (auto) |
| Employee_ID | text | Yes | - | Unique ID (EMP001, ADM001) |
| Full_Name | text | Yes | - | Employee name |
| Email | text | Yes | - | Unique email |
| Password | text | Yes | - | Bcrypt hashed password |
| Phone_Number | text | No | - | Contact number |
| Role | text | Yes | - | 'Admin' or 'Employee' |
| Department | text | No | - | e.g., 'Operations' |
| Designation | text | No | - | e.g., 'Station Master' |
| Permissions | text | No | - | JSON permissions |
| Invited_By | bigint | Yes | - | ROWID of inviting admin |
| Invitation_Id | bigint | No | - | Link to invitation |
| Joined_At | text | Yes | - | ISO timestamp |
| Account_Status | text | Yes | 'Active' | 'Active', 'Inactive', 'Suspended' |
| Last_Login | text | No | - | ISO timestamp |
| Created_At | text | Yes | - | ISO timestamp |
| Updated_At | text | No | - | ISO timestamp |

**Indexes to create:**
- `Employee_ID` (Unique)
- `Email` (Unique)
- `Role`
- `Account_Status`

---

### 3. Update Employee_Invitations Table

**Go to:** Catalyst Console → CloudScale → Data Store → Employee_Invitations table

**Add these columns:**

| Column Name | Data Type | Required | Default | Description |
|------------|-----------|----------|---------|-------------|
| Role | text | Yes | 'Employee' | 'Admin' or 'Employee' |
| Department | text | No | - | Pre-fill for employee |
| Designation | text | No | - | Pre-fill for employee |

**Rename column:**
- Change `Registered_User_Id` to `Registered_Employee_Id`
- Or add new column `Registered_Employee_Id` and keep old one for compatibility

**Update Invited_By reference:**
- This column should now reference `Employees.ROWID` instead of `Users.ROWID`
- **Important:** You'll need to create at least one admin employee first before using invitations

---

## 🚀 Deployment Steps

### Step 1: Update Database Schema (FIRST!)

1. Log into Zoho Catalyst Console
2. Navigate to CloudScale → Data Store
3. Make all the database changes listed above
4. Verify the changes are saved

### Step 2: Configure Environment Variables

**Critical for Production:** Add CORS configuration to Catalyst environment variables.

1. Go to Catalyst Console → Settings → Environment Variables
2. Add the following variable:

**Variable Name:** `CORS_ALLOWED_ORIGINS`

**Variable Value:** 
```
https://smart-railway-app-60066581545.development.catalystserverless.in
```

**Important Notes:**
- Include **ONLY** your production domain (no trailing slash)
- For multiple domains, separate with commas: `https://domain1.com,https://domain2.com`
- The value is case-sensitive and must match exactly
- Without this, CORS will block all API requests from your frontend

### Step 3: Create First Admin Employee (Manual)

Since the invitation system now requires an existing admin employee, you need to create one manually:

**Option A: Use CloudScale Console**
1. Go to Employees table
2. Click "Add Row"
3. Fill in:
   - Employee_ID: `ADM001`
   - Full_Name: `Your Name`
   - Email: `your-email@domain.com`
   - Password: Generate bcrypt hash (use online tool or Python: `bcrypt.hashpw(b"yourpassword", bcrypt.gensalt())`)
   - Role: `Admin`
   - Department: `Administration`
   - Designation: `System Administrator`
   - Permissions: `{"admin_access": true, "can_invite_employees": true}`
   - Account_Status: `Active`
   - Joined_At: Current ISO timestamp
   - Created_At: Current ISO timestamp
   - Invited_By: `1` (self-reference)

**Option B: Use a migration script** (create later if needed)

### Step 4: Deploy Backend Code

1. Deploy the updated backend code to Catalyst
2. The code now includes:
   - `user_type` support in sessions
   - Employee service and repository functions
   - Employee login endpoint: `/session/employee/login`
   - Updated session validation

### Step 5: Test

1. **Test Passenger Registration:**
   - Go to `/app/#/register`
   - Complete registration with OTP
   - Login should work normally
   - Session validate should return `type: 'user'`

2. **Test Employee Login:**
   - Use employee credentials
   - Login at `/session/employee/login` endpoint
   - Session validate should return `type: 'employee'`

3. **Test Invitations:**
   - Admin can send employee invitations
   - Invitations now include Role, Department, Designation
   - Registration creates employee record (not user)

---

## 🐛 Troubleshooting

### Issue: CORS Blocked - Failed to load resource

**Symptoms:**
```
WARNING CORS: Blocked origin: https://smart-railway-app-60066581545.development.catalystserverless.in
```

**Cause:** `CORS_ALLOWED_ORIGINS` environment variable not set in production

**Fix:** 
1. Go to Catalyst Console → Settings → Environment Variables
2. Add variable: `CORS_ALLOWED_ORIGINS`
3. Set value: `https://smart-railway-app-60066581545.development.catalystserverless.in`
4. Redeploy the function

### Issue: Audit log failed - Invalid input value for User_ID

**Symptoms:**
```
ERROR Create record error in Session_Audit_Log: 'Invalid input value for User_ID. bigint value expected'
WARNING Audit log failed: {...}
```

**Cause:** User_ID is a foreign key field in Session_Audit_Log table. It cannot accept:
- Empty strings (`""`)
- Zero or negative integers  
- Non-integer values

It must be either:
- A valid positive ROWID (integer > 0) from Users/Employees table
- Completely omitted from the data (since Is Mandatory = false)

**Fix:** 
Code has been updated to:
1. Check if user_id exists and is not empty
2. Convert to integer
3. Only include in audit_data if integer > 0
4. Otherwise, completely omit User_ID from the record

**To apply:**
- Redeploy the updated `session_service.py`
- Check logs for debug messages: `"Audit log: Skipping User_ID..."` to see what values are being filtered

### Issue: 401 Unauthorized on /session/validate

**Cause:** User_Type column not added to Sessions table

**Fix:** 
1. Add User_Type column to Sessions table
2. Set default value to 'user'
3. Update existing records

### Issue: Employee login fails

**Cause:** Employees table not created

**Fix:** Create Employees table as specified above

### Issue: Can't send invitations

**Cause:** No admin employee exists, or Invited_By references old Users table

**Fix:** Create first admin employee manually (see Step 2)

### Issue: Redirect loop on /app/

**Cause:** This is a known issue with HashRouter and Catalyst hosting

**Fix:** 
- Access the app via `/app/#/` (with hash)
- Or update client routing to handle this better

---

## 📝 Code Changes Summary

**Files Modified:**
1. `config.py` - Added employees table mapping
2. `cloudscale_repository.py` - Added employee repository functions
3. `employee_service.py` - NEW: Employee CRUD and authentication
4. `employee_invitation_service.py` - Updated with Role/Department/Designation
5. `session_service.py` - Added user_type parameter support
6. `session_middleware.py` - Added get_current_user_type()
7. `session_auth.py` - Added employee login endpoint, updated validate
8. `otp_register.py` - Added user_type='user' to session creation

**New Endpoints:**
- `POST /session/employee/login` - Employee login
- `GET /session/validate` - Now returns user_type

**Database Changes:**
- Sessions: Added User_Type column
- Employees: New table
- Employee_Invitations: Added Role, Department, Designation

---

## ✅ Verification Checklist

- [ ] Sessions table has User_Type column
- [ ] Employees table created with all columns
- [ ] Employee_Invitations table has new columns
- [ ] At least one admin employee exists
- [ ] Passenger registration works
- [ ] Passenger login works
- [ ] Employee login works
- [ ] Session validation returns correct user_type
- [ ] Invitations include role/department/designation

---

## 🔄 Rollback Plan

If issues occur:

1. **Keep User_Type column** - Set default to 'user' for backward compatibility
2. **Employees table** - Can remain empty; system still works for passengers
3. **Code rollback** - The user_type parameter has a default value of 'user', so old sessions still work

---

## 📞 Support

If you encounter issues:
1. Check CloudScale console for error logs
2. Verify database schema matches this guide
3. Check that User_Type column exists in Sessions table
4. Ensure at least one admin employee record exists
