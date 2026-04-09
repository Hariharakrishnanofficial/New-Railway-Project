# Implementation Notes - User/Employee Separation

**Last Updated:** April 8, 2026  
**Status:** ✅ Phase 1-3 Complete, ⚠️ Database Migration Required

---

## 🚨 URGENT: Database Migration Required (April 8, 2026)

### Sessions Table Foreign Key Constraint

**Issue**: Sessions.User_ID has FK constraint to Users.ROWID, blocking employee logins.

**Error Symptom**:
```
POST /session/employee/login → 500 Internal Server Error
ERROR: Invalid Foreign key value for column User_ID. ROWID of table Users is expected
```

**Required Action**: Remove FK constraint in CloudScale console.

**See**: `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md` for step-by-step instructions.

---

## Recent Code Changes

### 1. Sessions Table Polymorphic Reference (April 8, 2026)

**Problem**: Sessions.User_ID needs to reference either Users.ROWID or Employees.ROWID.

**Solution**: 
- Use `User_Type` field to distinguish table ('user' or 'employee')
- Remove database FK constraint
- Enforce referential integrity at application level

**Code Location**: `services/session_service.py:136-140`

```python
session_data = {
    "User_ID": str(user_id),      # Can be Users.ROWID or Employees.ROWID
    "User_Type": user_type,       # 'user' or 'employee'
    "User_Email": user_email,
    "User_Role": user_role,
}
```

**Validation** (Application Level):
```python
# Before creating session, validate user exists
if user_type == 'user':
    user = cloudscale_repo.get_user_by_id(user_id)
    if not user:
        raise ValueError(f"Invalid user_id: {user_id}")
elif user_type == 'employee':
    employee = cloudscale_repo.get_employee_by_id(user_id)
    if not employee:
        raise ValueError(f"Invalid employee user_id: {user_id}")
```

---

### 2. Employee Registration with OTP (April 6, 2026)

**File:** `functions/smart_railway_app_function/routes/otp_register.py`

**Changes:**
- Modified `verify_registration()` endpoint to detect employee invitations
- When `invitation_token` is present and valid:
  - Creates **Employee** record instead of User record
  - Calls `create_employee()` from employee_service
  - Includes Role, Department, Designation from invitation
  - Marks invitation as used with `Registered_Employee_Id`
  - Creates session with `user_type='employee'`
  
**Code Flow:**
```python
# Lines 460-545
if is_employee:
    # Re-verify invitation token
    is_valid, invitation_data = verify_invitation_token(token)
    
    # Extract employee details from invitation
    role = invitation_data.get('Role', 'Employee')
    department = invitation_data.get('Department')
    designation = invitation_data.get('Designation')
    
    # Create employee record
    employee_result = create_employee(
        full_name=...,
        email=...,
        role=role,
        department=department,
        designation=designation,
        invited_by=invitation_data.get('Invited_By'),
        invitation_id=invitation_data.get('ROWID')
    )
    
    user_type = 'employee'
else:
    # Create regular user (passenger)
    cloudscale_repo.create_record('Users', user_data)
    user_type = 'user'

# Create session with appropriate user_type
create_session(..., user_type=user_type)
```

**Impact:**
- Employee invitation → registration → creates Employee record (not User)
- Employees and passengers now stored in separate tables
- Session management handles both types via `user_type` field

---

### 2. Audit Logging Foreign Key Fix (April 6, 2026)

**File:** `functions/smart_railway_app_function/services/session_service.py`

**Problem:**
- Session_Audit_Log.User_ID is a **foreign key** to Users/Employees.ROWID
- Foreign keys cannot accept:
  - Empty strings (`""`)
  - Zero or negative integers
  - Invalid/non-integer values
- Previous code tried to set `User_ID = ""` for failed logins → Error

**Solution (Lines 731-746):**
```python
# Build audit data WITHOUT User_ID initially
audit_data = {
    "Event_Type": event_type,
    "User_Email": user_email or "",
    "IP_Address": ip_address or "",
    "Details": json.dumps(event_details),
    "Event_Timestamp": datetime.now(timezone.utc).isoformat(),
    "Severity": severity,
}

# Only add User_ID if valid positive integer
if user_id and str(user_id).strip():
    try:
        user_id_int = int(user_id)
        if user_id_int > 0:
            audit_data["User_ID"] = user_id_int  # ✅ Include
        else:
            # Skip - FK requires positive ROWID
            logger.debug(f"Skipping User_ID={user_id_int}")
    except (ValueError, TypeError):
        # Skip - not valid integer
        logger.debug(f"Skipping invalid User_ID: {user_id}")
```

**Key Points:**
- User_ID completely **omitted** from audit_data if:
  - user_id is None, empty string, or whitespace
  - user_id is zero or negative
  - user_id cannot be converted to integer
- This allows logging events like:
  - Failed login attempts (user doesn't exist → no User_ID)
  - Session validation failures (invalid session → no User_ID)
  - System events not tied to specific user

**Session_ID Handling:**
- Session_ID is also a foreign key (to Sessions.ROWID)
- Always omitted from direct insertion
- Instead, session token stored in `Details.session_ref` field
- Allows tracking session events even when Sessions.ROWID unknown

---

### 3. Audit Logging Polymorphic Reference Update (April 8, 2026)

**File:** `functions/smart_railway_app_function/services/session_service.py`

**Update**: Session_Audit_Log.User_ID also uses polymorphic pattern (no FK constraint).

**Previous Understanding (April 6)**:
- Thought User_ID was a foreign key to Users/Employees
- Implemented strict validation to prevent FK violations

**Current Reality (April 8)**:
- User_ID should NOT have FK constraint (same as Sessions.User_ID)
- Polymorphic reference: can be Users.ROWID or Employees.ROWID
- User_Type not stored in audit log (inferred from event type or stored in Details)

**Code Still Valid**:
```python
# User_ID validation remains good practice
if user_id and str(user_id).strip():
    try:
        user_id_int = int(user_id)
        if user_id_int > 0:
            audit_data["User_ID"] = user_id_int  # ✅ Include
    except (ValueError, TypeError):
        logger.debug(f"Skipping invalid User_ID: {user_id}")
```

**Key Points:**
- User_ID completely **omitted** from audit_data if:
  - user_id is None, empty string, or whitespace
  - user_id is zero or negative
  - user_id cannot be converted to integer
- This allows logging events like:
  - Failed login attempts (user doesn't exist → no User_ID)
  - Session validation failures (invalid session → no User_ID)
  - System events not tied to specific user
- Event_Type distinguishes user vs employee events:
  - `USER_LOGIN_SUCCESS` / `USER_LOGIN_FAILED` → User_ID from Users table
  - `EMPLOYEE_LOGIN_SUCCESS` / `EMPLOYEE_LOGIN_FAILED` → User_ID from Employees table

**Session_ID Handling:**
- Session_ID is also a foreign key (to Sessions.ROWID)
- Always omitted from direct insertion
- Instead, session token stored in `Details.session_ref` field
- Allows tracking session events even when Sessions.ROWID unknown

---

### 4. Employee Invitation Form Updates (April 6, 2026)

**File:** `railway-app/src/pages/admin/EmployeeInvitation.jsx`

**Changes:**
- Updated form to include:
  - **Role** dropdown: Admin or Employee (default: Employee)
  - **Department** text input: e.g., "Operations", "Customer Service"
  - **Designation** text input: e.g., "Station Manager", "Ticket Inspector"
  
- Form validation:
  - Email required and validated
  - Department required
  - Designation required
  
- Updated API call:
  ```javascript
  api.post('/admin/employees/invite', {
    email: formData.email,
    role: formData.role,
    department: formData.department,
    designation: formData.designation
  })
  ```

- Updated invitations table display:
  - Shows Role with color-coded badge
  - Shows Department and Designation columns
  - Admin roles highlighted in blue, Employee in green

**Impact:**
- Admins now specify full employee details at invitation time
- Employee registration pre-fills these details from invitation
- Better role-based access control foundation

---

## Environment Configuration Requirements

### Production Deployment Checklist

#### 1. CORS Configuration (CRITICAL)

**Environment Variable Required:**
```bash
CORS_ALLOWED_ORIGINS=https://smart-railway-app-60066581545.development.catalystserverless.in
```

**Where to Set:**
- Catalyst Console → Settings → Environment Variables
- Variable Name: `CORS_ALLOWED_ORIGINS`
- Variable Value: Your production domain (no trailing slash)

**Without this:**
- All API requests from frontend will be blocked
- Console shows: `WARNING CORS: Blocked origin: ...`

#### 2. Email Configuration

**Required Variables:**
```bash
CATALYST_FROM_EMAIL=noreply@yourdomain.com
CATALYST_FROM_NAME=Smart Railway Ticketing
```

#### 3. Database Schema Updates

**Required Tables:**
1. **Employees** table (create new)
2. **Employee_Invitations** table (add columns):
   - Role (text, required, default: 'Employee')
   - Department (text, optional)
   - Designation (text, optional)
   - Registered_Employee_Id (bigint, optional)
3. **Sessions** table (add column):
   - User_Type (text, required, default: 'user')

**See:** `PHASE1_DEPLOYMENT_GUIDE.md` for detailed schema

---

## Data Flow Diagrams

### Employee Invitation Flow

```
┌─────────────┐
│   Admin     │
│   Panel     │
└──────┬──────┘
       │ POST /admin/employees/invite
       │ {email, role, dept, desig}
       ▼
┌─────────────────────┐
│ Employee Invitation │
│     Service         │
├─────────────────────┤
│ 1. Create invitation│
│    record           │
│ 2. Generate token   │
│ 3. Send email with  │
│    registration link│
└──────┬──────────────┘
       │
       │ Email with link:
       │ /register?invitation=TOKEN
       ▼
┌─────────────────────┐
│  Employee clicks    │
│  registration link  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Registration Page   │
│ (with token)        │
├─────────────────────┤
│ 1. Verify token     │
│ 2. Show form        │
│ 3. User fills data  │
│ 4. Submit           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ OTP Registration    │
│    Initiate         │
├─────────────────────┤
│ 1. Validate token   │
│ 2. Store invite data│
│ 3. Send OTP email   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  User enters OTP    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ OTP Verify +        │
│ Employee Creation   │
├─────────────────────┤
│ 1. Verify OTP       │
│ 2. Create Employee  │
│    record (not User)│
│ 3. Mark invitation  │
│    as used          │
│ 4. Create session   │
│    (type=employee)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Employee Dashboard  │
│   (logged in)       │
└─────────────────────┘
```

### Session Audit Logging Flow

```
┌─────────────────────┐
│   Any Session       │
│   Event Occurs      │
│ (login, logout,     │
│  validation, etc.)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────────┐
│ log_audit_event()           │
│ Parameters:                 │
│ - event_type                │
│ - user_email (optional)     │
│ - user_id (optional)        │
│ - session_id (optional)     │
│ - ip_address (optional)     │
│ - details (JSON, optional)  │
│ - severity                  │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ _log_session_event()        │
│                             │
│ Builds audit_data dict:     │
│ - Event_Type ✅ (always)    │
│ - User_Email ✅ (always)    │
│ - IP_Address ✅ (always)    │
│ - Details ✅ (always)       │
│ - Event_Timestamp ✅        │
│ - Severity ✅ (always)      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Validate User_ID (FK)       │
│                             │
│ if user_id exists:          │
│   try:                      │
│     int_id = int(user_id)   │
│     if int_id > 0:          │
│       ✅ Add to audit_data  │
│     else:                   │
│       ❌ Skip (not positive)│
│   except:                   │
│     ❌ Skip (not integer)   │
│ else:                       │
│   ❌ Skip (empty/None)      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Insert to CloudScale        │
│ Session_Audit_Log table     │
│                             │
│ User_ID included ONLY if:   │
│ - Valid positive integer    │
│ - References Users/Employees│
│                             │
│ User_ID omitted when:       │
│ - Failed login (no user)    │
│ - System events             │
│ - Invalid session           │
└─────────────────────────────┘
```

---

## Testing Checklist

### Employee Registration Flow

- [ ] Admin sends invitation with Role, Department, Designation
- [ ] Employee receives email with registration link
- [ ] Registration page loads with invitation token
- [ ] Employee fills form and submits
- [ ] OTP email received
- [ ] OTP verification succeeds
- [ ] **Employee record created** (check Employees table, NOT Users)
- [ ] Invitation marked as used with Registered_Employee_Id
- [ ] Session created with `user_type='employee'`
- [ ] Employee can access admin panel (if role=Admin)

### Audit Logging

- [ ] Failed login (user not found) → Audit log created WITHOUT User_ID
- [ ] Successful login → Audit log created WITH User_ID
- [ ] Session validation → Audit log created WITH User_ID
- [ ] No errors about "Invalid input value for User_ID"
- [ ] Query audit logs by User_ID (should work for valid references)

### CORS

- [ ] Frontend can make API requests in production
- [ ] No "CORS blocked" warnings in logs
- [ ] Environment variable `CORS_ALLOWED_ORIGINS` is set

---

## Code Patterns & Best Practices

### Foreign Key Handling in CloudScale

**Problem:** CloudScale foreign keys are strict - they require valid ROWIDs or NULL.

**Solution Pattern:**
```python
# ❌ DON'T: Include FK field with empty/invalid value
data = {
    "Name": "John",
    "User_ID": ""  # ERROR: Foreign key can't be empty string
}

# ✅ DO: Omit FK field entirely if no valid reference
data = {
    "Name": "John"
    # User_ID not included - CloudScale treats as NULL
}

# ✅ DO: Validate before including
if user_id and int(user_id) > 0:
    data["User_ID"] = int(user_id)
```

### Session Type Handling

**Pattern for dual user types:**
```python
# In session creation
if is_employee_invitation:
    user_type = 'employee'
    # Look up in Employees table
else:
    user_type = 'user'
    # Look up in Users table

session_id, csrf = create_session(
    user_id=user_id,
    user_type=user_type  # Critical: determines which table to reference
)
```

**In session validation:**
```python
session_data = validate_session(session_id)
user_type = session_data.get('user_type', 'user')

if user_type == 'employee':
    user = get_employee_by_id(session_data['user_id'])
else:
    user = get_user_by_id(session_data['user_id'])
```

### Invitation Token Validation

**Best Practice:**
```python
# Verify token early and often
if invitation_token:
    is_valid, invitation_data = verify_invitation_token(token)
    
    if not is_valid:
        return error_response("Invalid invitation")
    
    # Verify email matches
    if invitation_data['Email'] != submitted_email:
        return error_response("Email mismatch")
    
    # Use invitation data to pre-fill employee details
    role = invitation_data.get('Role', 'Employee')
    department = invitation_data.get('Department')
    ...
```

---

## Common Issues & Solutions

### Issue: "Invalid input value for User_ID. bigint expected"

**Cause:** Trying to insert empty string or invalid value into foreign key field

**Solution:** Only include User_ID if it's a valid positive integer, otherwise omit completely

**Code Location:** `services/session_service.py` lines 731-746

---

### Issue: CORS blocked in production

**Cause:** `CORS_ALLOWED_ORIGINS` environment variable not set

**Solution:** Add variable in Catalyst Console with production domain

**Code Location:** `config.py` lines 390-410, `core/cors_config.py`

---

### Issue: Employee registration creates User record instead of Employee

**Cause:** Invitation token not passed or not validated

**Solution:** Ensure invitation token passed as query param: `/register?invitation=TOKEN`

**Code Location:** `routes/otp_register.py` lines 269-292, 462-545

---

## Migration Notes

### Existing Users with Employee Role

If you have users in the Users table with `Role='Employee'` or `Role='Admin'`:

**Option 1: Manual Migration**
1. Export employee users from Users table
2. Create corresponding records in Employees table
3. Update any references (sessions, bookings, etc.)
4. Delete from Users table

**Option 2: Migration Script** (to be created)
- Script should:
  - Query Users where Role IN ('Employee', 'Admin')
  - For each, create Employee record
  - Copy relevant data
  - Preserve ROWID mapping for foreign keys
  - Update Sessions.User_Type for existing employee sessions

---

## Future Enhancements

### Planned Features

1. **Employee Management UI** (Phase 3.2)
   - List all employees
   - Filter by role, department, status
   - Edit employee details
   - Manage permissions
   - Deactivate/suspend employees

2. **Permission System** (Phase 3.3)
   - Fine-grained permission editor
   - Role-based default permissions
   - Permission inheritance
   - Audit log for permission changes

3. **Department/Designation Management**
   - Predefined dropdown options
   - Department hierarchy
   - Designation levels
   - Assignment history

4. **Employee Analytics**
   - Login frequency
   - Action logs
   - Performance metrics
   - Department-wise reports

---

## Documentation Files Updated

This implementation required updates to:

1. ✅ `PHASE1_DEPLOYMENT_GUIDE.md` - Added CORS config, audit log fix
2. ✅ `SESSION_SCHEMA.md` - Updated User_ID/Session_ID as foreign keys
3. ✅ `SESSION_MANAGEMENT_GUIDE.md` - Updated audit logging section
4. ✅ `USER_EMPLOYEE_RESTRUCTURE_PLAN.md` - Marked Phase 2 & 3.1 complete
5. ✅ `IMPLEMENTATION_NOTES.md` - This file (comprehensive change log)

---

**For questions or issues, refer to:**
- Technical details: This file
- Deployment steps: `PHASE1_DEPLOYMENT_GUIDE.md`
- Database schema: `SESSION_SCHEMA.md`, `CLOUDSCALE_DATABASE_SCHEMA_V2.md`
- Session management: `SESSION_MANAGEMENT_GUIDE.md`
