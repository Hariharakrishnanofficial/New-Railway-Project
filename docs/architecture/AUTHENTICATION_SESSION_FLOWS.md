# Authentication & Session Flow Diagrams

**Version**: 2.0  
**Last Updated**: April 8, 2026  
**Purpose**: Visual reference for authentication, session management, and data flows

---

## Table of Contents

- [Dual Authentication System Overview](#dual-authentication-system-overview)
- [Passenger Login Flow](#passenger-login-flow)
- [Employee Login Flow](#employee-login-flow)
- [Session Creation & Validation Flow](#session-creation--validation-flow)
- [Polymorphic Reference Pattern](#polymorphic-reference-pattern)
- [Session Lifecycle](#session-lifecycle)
- [Error Handling Flows](#error-handling-flows)

---

## Dual Authentication System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Smart Railway System                         │
└────────────────────────────────────────────────────────────────┘
                            │
           ┌────────────────┴────────────────┐
           │                                 │
           ▼                                 ▼
  ┌──────────────────┐              ┌──────────────────┐
  │  Passenger Path  │              │  Employee Path   │
  └──────────────────┘              └──────────────────┘
           │                                 │
           ▼                                 ▼
  POST /session/login          POST /session/employee/login
           │                                 │
           ▼                                 ▼
  Check Users Table            Check Employees Table
  (Email, Hashed_Password)     (Email, Hashed_Password)
           │                                 │
           ▼                                 ▼
  User_Type = 'user'           User_Type = 'employee'
  User_ID = Users.ROWID        User_ID = Employees.ROWID
  User_Role = 'Passenger'      User_Role = 'Admin'/'Employee'
           │                                 │
           └────────────────┬────────────────┘
                            ▼
                   Create Session Record
                   (Sessions Table)
                            │
                            ▼
              ┌─────────────────────────────┐
              │  Session Record             │
              ├─────────────────────────────┤
              │  Session_ID: random token   │
              │  User_ID: ROWID (poly ref)  │
              │  User_Type: 'user'|'employee'│
              │  User_Email: email          │
              │  User_Role: role string     │
              │  CSRF_Token: random token   │
              │  Expires_At: now + 90 days  │
              │  Is_Active: true            │
              └─────────────────────────────┘
                            │
                            ▼
             Set HttpOnly Cookie (Session_ID)
                            │
                            ▼
                   Return User Data
```

---

## Passenger Login Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ POST /session/login
       │ {email, password}
       ▼
┌─────────────────────────────────────────────────────────┐
│                  auth.py: login()                        │
└─────────────────────────────────────────────────────────┘
       │
       │ 1. Validate request data
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│        cloudscale_repository: get_user_by_email()        │
└─────────────────────────────────────────────────────────┘
       │
       │ SELECT ROWID, Email, Hashed_Password, ... 
       │ FROM Users WHERE Email = ?
       │
       ▼
  ┌─────────┐
  │ Found?  │
  └────┬────┘
       │ No → 401 Invalid credentials
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│         verify_password(password, hashed_pwd)            │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  ┌─────────┐
  │ Valid?  │
  └────┬────┘
       │ No → 401 Invalid credentials
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│  Check Account_Status = 'Active'                         │
│  Check Email_Verified = True                             │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  ┌─────────┐
  │ Active? │
  └────┬────┘
       │ No → 403 Account inactive or not verified
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│  session_service: create_session(                        │
│    user_id=Users.ROWID,                                  │
│    user_type='user',                                     │
│    user_email=email,                                     │
│    user_role='Passenger',                                │
│    request_data...                                       │
│  )                                                       │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Set Cookie: Session_ID (HttpOnly, Secure, SameSite)     │
│  Return: {user_id, email, role, name, ...}               │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Browser   │
│ (Logged In) │
└─────────────┘
```

---

## Employee Login Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ POST /session/employee/login
       │ {email, password}
       ▼
┌─────────────────────────────────────────────────────────┐
│           session_auth.py: employee_login()              │
└─────────────────────────────────────────────────────────┘
       │
       │ 1. Validate request data
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│    employee_service: authenticate_employee(email, pwd)   │
└─────────────────────────────────────────────────────────┘
       │
       │ SELECT ROWID, Email, Hashed_Password, ...
       │ FROM Employees WHERE Email = ?
       │
       ▼
  ┌─────────┐
  │ Found?  │
  └────┬────┘
       │ No → 401 Invalid credentials
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│         verify_password(password, hashed_pwd)            │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  ┌─────────┐
  │ Valid?  │
  └────┬────┘
       │ No → 401 Invalid credentials
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│  Check Account_Status = 'Active'                         │
│  Check Email_Verified = True (if required)               │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  ┌─────────┐
  │ Active? │
  └────┬────┘
       │ No → 403 Account inactive
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│  session_service: create_session(                        │
│    user_id=Employees.ROWID,                              │
│    user_type='employee',                                 │
│    user_email=email,                                     │
│    user_role='Admin'|'Employee',                         │
│    request_data...                                       │
│  )                                                       │
└─────────────────────────────────────────────────────────┘
       │
       ▼  ⚠️ FK VIOLATION HERE (before migration)
       │
┌─────────────────────────────────────────────────────────┐
│  INSERT INTO Sessions (                                  │
│    Session_ID, User_ID ← Employees.ROWID,               │
│    User_Type='employee', ...                             │
│  )                                                       │
│                                                          │
│  ❌ FAILS if FK constraint exists:                       │
│     User_ID → Users.ROWID (expects Users table)         │
│                                                          │
│  ✅ WORKS after FK removal:                              │
│     User_ID accepts any ROWID                            │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Set Cookie: Session_ID (HttpOnly, Secure, SameSite)     │
│  Return: {user_id, email, role, name, department, ...}   │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Browser   │
│ (Logged In) │
└─────────────┘
```

---

## Session Creation & Validation Flow

### Session Creation

```
session_service.create_session()
       │
       │ 1. Generate secure Session_ID (secrets.token_urlsafe(32))
       │ 2. Generate secure CSRF_Token (secrets.token_urlsafe(32))
       │ 3. Extract request metadata (IP, User-Agent, fingerprint)
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Prepare session data:                                   │
│  {                                                       │
│    Session_ID: <random_token>,                           │
│    User_ID: <ROWID>,                                     │
│    User_Type: 'user' | 'employee',                       │
│    User_Email: <email>,                                  │
│    User_Role: <role>,                                    │
│    CSRF_Token: <random_token>,                           │
│    Expires_At: now + 90 days,                            │
│    Is_Active: true,                                      │
│    IP_Address: <client_ip>,                              │
│    User_Agent: <browser>,                                │
│    Device_Fingerprint: <hash>,                           │
│    Last_Accessed_At: now                                 │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  🛡️ Application-level validation (recommended):          │
│                                                          │
│  if user_type == 'user':                                 │
│      user = get_user_by_id(user_id)                      │
│      if not user: raise ValueError("Invalid user_id")    │
│  elif user_type == 'employee':                           │
│      employee = get_employee_by_id(user_id)              │
│      if not employee: raise ValueError("Invalid user_id")│
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  INSERT INTO Sessions (...)                              │
│  ✅ Works with polymorphic User_ID (no FK constraint)    │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  INSERT INTO Session_Audit_Log (                         │
│    Action='LOGIN',                                       │
│    User_ID=<ROWID>,                                      │
│    User_Type=<type>,                                     │
│    User_Email=<email>,                                   │
│    Status='SUCCESS',                                     │
│    ...                                                   │
│  )                                                       │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  Return (session_id, csrf_token)
```

### Session Validation

```
  API Request with Cookie: Session_ID=<token>
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  @require_session decorator / Middleware                 │
└─────────────────────────────────────────────────────────┘
       │
       │ 1. Extract Session_ID from cookie
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  session_service.validate_session(session_id)            │
└─────────────────────────────────────────────────────────┘
       │
       │ SELECT * FROM Sessions WHERE Session_ID = ?
       │
       ▼
  ┌─────────┐
  │ Found?  │
  └────┬────┘
       │ No → 401 Invalid session
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│  Validation checks:                                      │
│  1. Is_Active = true                                     │
│  2. Expires_At > now                                     │
│  3. (now - Last_Accessed_At) < 24 hours (idle timeout)   │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  ┌─────────┐
  │ Valid?  │
  └────┬────┘
       │ No → 401 Session expired/inactive
       │
       │ Yes
       ▼
┌─────────────────────────────────────────────────────────┐
│  Update Last_Accessed_At = now (sliding window)          │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Populate request context:                               │
│  g.user_id = session.User_ID                             │
│  g.user_type = session.User_Type                         │
│  g.user_email = session.User_Email                       │
│  g.user_role = session.User_Role                         │
│  g.csrf_token = session.CSRF_Token                       │
└─────────────────────────────────────────────────────────┘
       │
       ▼
  Proceed to API endpoint handler
```

---

## Polymorphic Reference Pattern

### Database Constraint (BEFORE Migration)

```
┌──────────────────┐
│  Sessions Table  │
├──────────────────┤
│ Session_ID       │
│ User_ID ─────────┼──┐ FK Constraint
│ User_Type        │  │ User_ID → Users.ROWID
│ ...              │  │
└──────────────────┘  │
                      │
      ┌───────────────┘
      │
      ▼
┌──────────────────┐
│   Users Table    │
├──────────────────┤
│ ROWID (PK)       │ ✅ Passenger sessions work
│ Email            │
│ ...              │
└──────────────────┘

┌───────────────────┐
│ Employees Table   │
├───────────────────┤
│ ROWID (PK)        │ ❌ Employee sessions fail
│ Email             │    (FK violation)
│ ...               │
└───────────────────┘
```

### Application-Level Pattern (AFTER Migration)

```
┌──────────────────┐
│  Sessions Table  │
├──────────────────┤
│ Session_ID       │
│ User_ID          │ ← Can be ANY ROWID (no FK)
│ User_Type        │ ← Indicates which table
│ ...              │
└────────┬─────────┘
         │
         │ Application logic handles reference
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────────┐  ┌───────────────────┐
│   Users Table    │  │ Employees Table   │
├──────────────────┤  ├───────────────────┤
│ ROWID (PK)       │  │ ROWID (PK)        │
│ Email            │  │ Email             │
│ ...              │  │ ...               │
└──────────────────┘  └───────────────────┘

User_Type='user'     User_Type='employee'
→ Look up Users      → Look up Employees
```

### Validation Code Pattern

```python
# Before creating session
def create_session(user_id, user_type, ...):
    # Application-level referential integrity
    if user_type == 'user':
        user = cloudscale_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Invalid user_id: {user_id}")
    elif user_type == 'employee':
        employee = cloudscale_repo.get_employee_by_id(user_id)
        if not employee:
            raise ValueError(f"Invalid employee user_id: {user_id}")
    
    # Now safe to insert
    session_data = {
        'User_ID': user_id,
        'User_Type': user_type,
        ...
    }
    cloudscale_repo.insert('Sessions', session_data)
```

---

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        Session Lifecycle                         │
└─────────────────────────────────────────────────────────────────┘

1. CREATION (Login)
   │
   ├─ Generate Session_ID (256-bit entropy)
   ├─ Generate CSRF_Token (256-bit entropy)
   ├─ Set Expires_At (now + 90 days)
   ├─ Set Is_Active = true
   ├─ Capture device metadata (IP, User-Agent, fingerprint)
   └─ INSERT INTO Sessions

2. ACTIVE USE (API Requests)
   │
   ├─ Validate session on each request
   ├─ Update Last_Accessed_At (sliding window)
   ├─ Check idle timeout (24 hours)
   └─ Populate request context (g.user_id, g.user_role, etc.)

3. EXPIRATION
   │
   ├─ Absolute: Expires_At < now (90 days)
   ├─ Idle: (now - Last_Accessed_At) > 24 hours
   └─ Manual: User logout or admin revocation

4. TERMINATION (Logout)
   │
   ├─ UPDATE Sessions SET Is_Active = false WHERE Session_ID = ?
   ├─ Clear HttpOnly cookie
   ├─ Audit log: Action='LOGOUT'
   └─ Frontend redirect to login page

5. CLEANUP (Background Job)
   │
   ├─ DELETE FROM Sessions WHERE Expires_At < (now - 30 days)
   └─ Runs daily to prevent table bloat
```

---

## Error Handling Flows

### Invalid Credentials

```
Login Request
   │
   ▼
User/Employee not found OR password mismatch
   │
   ▼
┌─────────────────────────────────────┐
│  Audit Log:                          │
│  Action = 'LOGIN_FAILED'             │
│  Status = 'INVALID_CREDENTIALS'      │
│  User_Email = <attempted_email>      │
└─────────────────────────────────────┘
   │
   ▼
Return 401 {"error": "Invalid credentials"}
```

### Account Inactive

```
Login Request
   │
   ▼
Valid credentials BUT Account_Status != 'Active'
   │
   ▼
┌─────────────────────────────────────┐
│  Audit Log:                          │
│  Action = 'LOGIN_FAILED'             │
│  Status = 'ACCOUNT_INACTIVE'         │
│  User_Email = <email>                │
└─────────────────────────────────────┘
   │
   ▼
Return 403 {"error": "Account is not active"}
```

### Session Creation Failure (FK Violation)

```
Employee Login
   │
   ▼
Valid employee authentication
   │
   ▼
Attempt to create session
   │
   ▼
INSERT INTO Sessions (User_ID = Employees.ROWID, ...)
   │
   ▼
❌ FK Constraint: User_ID → Users.ROWID
   │
   ▼
┌─────────────────────────────────────┐
│  Database Error:                     │
│  "Invalid Foreign key value for      │
│   column User_ID. ROWID of table     │
│   Users is expected"                 │
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│  Audit Log:                          │
│  Action = 'EMPLOYEE_LOGIN_FAILED'    │
│  Status = 'SESSION_CREATION_FAILED'  │
│  Error = <database_error>            │
└─────────────────────────────────────┘
   │
   ▼
Return 500 {"error": "Failed to create session"}
```

**Fix**: Remove FK constraint in CloudScale console

### Session Expired/Invalid

```
API Request with Session_ID cookie
   │
   ▼
Session not found OR Is_Active = false OR Expires_At < now
   │
   ▼
Return 401 {"error": "Session expired or invalid"}
   │
   ▼
Frontend clears local state, redirects to login
```

---

## Data Flow Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. POST /session/login OR /session/employee/login
       │    {email, password}
       ▼
┌─────────────────────────────────────────────────────────┐
│              Flask Route Handler                         │
│  (auth.py: login() OR session_auth.py: employee_login()) │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 2. Authenticate
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Authentication Service                           │
│  (user_service.py OR employee_service.py)                │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 3. Query database
                   ▼
┌─────────────────────────────────────────────────────────┐
│         CloudScale Repository                            │
│  (get_user_by_email() OR get_employee_by_email())        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 4. ZCQL Query
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Zoho CloudScale Database                         │
│  (Users Table OR Employees Table)                        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 5. Return user/employee record
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Authentication Service                           │
│  (verify password, check status)                         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 6. Create session
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Session Service                                  │
│  (session_service.py: create_session())                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 7. INSERT session record
                   ▼
┌─────────────────────────────────────────────────────────┐
│         CloudScale Repository                            │
│  (insert('Sessions', data))                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 8. ZCQL INSERT
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Zoho CloudScale Database                         │
│  (Sessions Table - polymorphic User_ID)                  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 9. Audit logging
                   ▼
┌─────────────────────────────────────────────────────────┐
│         Session_Audit_Log Table                          │
│  (Action='LOGIN', Status='SUCCESS')                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 10. Return session data
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Flask Route Handler                         │
│  (Set HttpOnly cookie, return user data)                 │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 11. HTTP Response
                   │     Set-Cookie: Session_ID=<token>
                   │     {user_id, email, role, ...}
                   ▼
┌─────────────┐
│   Browser   │
│ (Logged In) │
└─────────────┘
```

---

## Migration Impact Visualization

### Before Migration (Broken State)

```
Employee Login Attempt
         │
         ▼
┌─────────────────────┐
│ Authenticate        │ ✅ SUCCESS
│ (Employees Table)   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Create Session      │
│ User_ID = 12345     │ ← Employees.ROWID
│ User_Type='employee'│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│ INSERT INTO Sessions                         │
│   User_ID = 12345 ← FK CHECK                │
│                                              │
│ FK Constraint: User_ID → Users.ROWID        │
│ Check: Does 12345 exist in Users?           │
│ Result: NO (it's in Employees table)        │
│                                              │
│ ❌ FK VIOLATION                              │
└─────────┬───────────────────────────────────┘
          │
          ▼
   500 Internal Server Error
```

### After Migration (Working State)

```
Employee Login Attempt
         │
         ▼
┌─────────────────────┐
│ Authenticate        │ ✅ SUCCESS
│ (Employees Table)   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Create Session      │
│ User_ID = 12345     │ ← Employees.ROWID
│ User_Type='employee'│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│ INSERT INTO Sessions                         │
│   User_ID = 12345 ← NO FK CONSTRAINT        │
│                                              │
│ Application validates reference:             │
│   if user_type=='employee':                  │
│     employee = get_employee_by_id(12345)     │
│     if not employee: raise ValueError()      │
│                                              │
│ ✅ VALIDATION PASSED                         │
└─────────┬───────────────────────────────────┘
          │
          ▼
   200 OK - Session Created
```

---

**Last Updated**: April 8, 2026  
**Related Documents**:
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- [CRITICAL_DATABASE_MIGRATION_REQUIRED.md](../CRITICAL_DATABASE_MIGRATION_REQUIRED.md)
- [CLOUDSCALE_DATABASE_SCHEMA_V2.md](CLOUDSCALE_DATABASE_SCHEMA_V2.md)
