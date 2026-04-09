# Smart Railway System Architecture Overview

**Last Updated**: April 8, 2026  
**Status**: Production Ready (with database migration required)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Smart Railway System                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐          ┌──────────────────────┐         │
│  │   React Frontend    │◄────────►│   Flask Backend      │         │
│  │  (railway-app/)     │   HTTP   │  (functions/)        │         │
│  │                     │   /app   │                      │         │
│  │  - React 17+        │          │  - Python 3.8+       │         │
│  │  - React Router     │          │  - Flask             │         │
│  │  - Axios HTTP       │          │  - Catalyst Runtime  │         │
│  │  - Tailwind CSS     │          │                      │         │
│  └─────────────────────┘          └──────────────────────┘         │
│           │                                    │                    │
│           │                                    ▼                    │
│           │                        ┌──────────────────────┐         │
│           │                        │  Zoho CloudScale DB  │         │
│           │                        │                      │         │
│           │                        │  - Users (Passengers)│         │
│           │                        │  - Employees (Staff) │         │
│           │                        │  - Sessions          │         │
│           │                        │  - Trains/Stations   │         │
│           │                        │  - Bookings          │         │
│           │                        └──────────────────────┘         │
│           │                                                         │
│           └────────────────► Catalyst Email Service                 │
│                               (OTP, Invitations)                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dual Authentication System

### Architecture Design

The system supports **two separate user types** with distinct authentication flows:

#### 1. Passengers (Users Table)
- **Purpose**: Train ticket buyers, general public
- **Table**: `Users`
- **Login Endpoint**: `POST /session/login`
- **Session Type**: `user_type='user'`
- **Registration**: Public registration with OTP email verification

#### 2. Employees/Admins (Employees Table)
- **Purpose**: Railway staff and administrators
- **Table**: `Employees`
- **Login Endpoint**: `POST /session/employee/login`
- **Session Type**: `user_type='employee'`
- **Registration**: Invitation-only via admin

### Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                   PASSENGER AUTHENTICATION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User visits /login                                             │
│  2. Enters email + password                                         │
│  3. POST /session/login                                            │
│     │                                                               │
│     ▼                                                               │
│  4. Check Users table                                              │
│     │                                                               │
│     ├─ Found ──► Verify Argon2id password hash                     │
│     │               │                                               │
│     │               ▼                                               │
│     │            Create Session:                                    │
│     │            - User_ID: Users.ROWID                             │
│     │            - User_Type: 'user'                                │
│     │            - User_Role: 'Passenger'                           │
│     │               │                                               │
│     │               ▼                                               │
│     │            Set HttpOnly cookie                                │
│     │            Return user data + CSRF token                      │
│     │                                                               │
│     └─ Not Found ──► Return 401 Unauthorized                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   EMPLOYEE/ADMIN AUTHENTICATION                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Employee visits /admin/login                                    │
│  2. Enters email + password                                         │
│  3. POST /session/employee/login                                   │
│     │                                                               │
│     ▼                                                               │
│  4. Check Employees table ONLY                                     │
│     │                                                               │
│     ├─ Found ──► Verify Argon2id password hash                     │
│     │               │                                               │
│     │               ▼                                               │
│     │            Create Session:                                    │
│     │            - User_ID: Employees.ROWID  ⚠️                    │
│     │            - User_Type: 'employee'                            │
│     │            - User_Role: 'ADMIN' or 'EMPLOYEE'                 │
│     │               │                                               │
│     │               ▼                                               │
│     │            Set HttpOnly cookie                                │
│     │            Return employee data + CSRF token                  │
│     │                                                               │
│     └─ Not Found ──► Return 401 Unauthorized                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

⚠️ CRITICAL: User_ID can reference EITHER Users.ROWID OR Employees.ROWID
   - Determined by User_Type field ('user' vs 'employee')
   - MUST NOT have database Foreign Key constraint
   - Validation enforced at application level
```

---

## Database Schema (Polymorphic Pattern)

### Sessions Table - Polymorphic Reference

```sql
CREATE TABLE Sessions (
    ROWID BIGINT PRIMARY KEY,
    Session_ID VARCHAR(64) UNIQUE NOT NULL,
    User_ID VARCHAR(20) NOT NULL,        -- ⚠️ NO FOREIGN KEY!
    User_Type VARCHAR(20) NOT NULL,      -- 'user' or 'employee'
    User_Email VARCHAR(255) NOT NULL,
    User_Role VARCHAR(20) NOT NULL,
    CSRF_Token VARCHAR(64) NOT NULL,
    Expires_At DATETIME NOT NULL,
    Is_Active VARCHAR(10) NOT NULL,
    Created_At DATETIME NOT NULL
);
```

**Polymorphic Reference Logic**:

```python
# When User_Type = 'user'
session.User_ID references Users.ROWID

# When User_Type = 'employee'  
session.User_ID references Employees.ROWID

# Database cannot enforce this with FK
# Application validates before insert
```

### Why No Foreign Key?

**Problem**: Database Foreign Keys can only point to ONE table.

```sql
-- ❌ This is what we CANNOT do in SQL:
ALTER TABLE Sessions
ADD FOREIGN KEY (User_ID) 
    REFERENCES Users(ROWID) OR Employees(ROWID);  -- NOT VALID SQL!
```

**Solution**: Remove FK constraint, validate in code.

```python
# Application-level validation (session_service.py)
def create_session(user_id, user_type, ...):
    # Validate user exists before creating session
    if user_type == 'user':
        user = get_user_by_id(user_id)
        if not user:
            raise ValueError(f"Invalid user_id: {user_id}")
    elif user_type == 'employee':
        employee = get_employee_by_id(user_id)
        if not employee:
            raise ValueError(f"Invalid employee_id: {user_id}")
    
    # Now safe to insert
    cloudscale_repo.create_record('Sessions', session_data)
```

---

## Session Management

### Session Lifecycle

```
┌───────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE                          │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  1. User/Employee Login                                       │
│     ├─► Generate Session_ID (256-bit entropy)                 │
│     ├─► Generate CSRF_Token (256-bit entropy)                 │
│     ├─► Set Expires_At (24 hours from now)                    │
│     ├─► Sign Session_ID with HMAC                             │
│     └─► Store in Sessions table                               │
│                                                               │
│  2. Session Cookie Set                                        │
│     ├─► Name: 'session_id'                                    │
│     ├─► Value: HMAC-signed Session_ID                         │
│     ├─► HttpOnly: true (no JavaScript access)                 │
│     ├─► Secure: true (HTTPS only in production)               │
│     ├─► SameSite: 'Lax' (CSRF protection)                     │
│     └─► Max-Age: 24 hours                                     │
│                                                               │
│  3. Request Validation (every request)                        │
│     ├─► Extract session_id from cookie                        │
│     ├─► Verify HMAC signature                                 │
│     ├─► Lookup in Sessions table                              │
│     ├─► Check Is_Active = 'true'                              │
│     ├─► Check Expires_At > now                                │
│     ├─► Update Last_Accessed_At (sliding window)              │
│     └─► Return user/employee data                             │
│                                                               │
│  4. Session Expiration                                        │
│     ├─► Idle timeout: 6 hours                                 │
│     ├─► Absolute timeout: 24 hours                            │
│     └─► Auto-revoke when limit reached (max 3 per user)       │
│                                                               │
│  5. Logout                                                    │
│     ├─► Set Is_Active = 'false' in database                   │
│     ├─► Clear cookie from browser                             │
│     └─► Log SESSION_REVOKED audit event                       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Security Features

1. **HMAC Cookie Signing**
   - Session IDs signed with secret key
   - Prevents tampering and forgery
   - Signature verification on every request

2. **HttpOnly Cookies**
   - Not accessible to JavaScript (XSS protection)
   - Sent automatically with every request

3. **CSRF Protection**
   - Separate CSRF token for state-changing requests
   - Must be included in request header
   - Token rotates on login

4. **Concurrent Session Limit**
   - Maximum 3 sessions per user
   - Oldest session auto-revoked when limit reached
   - Prevents account sharing

5. **Audit Logging**
   - Every session event logged
   - Login success/failure
   - Session creation/validation/expiration/revocation
   - IP address and user agent tracked

---

## Critical Migration Requirements

### ⚠️ Sessions Table FK Constraint Removal

**Before Production Deployment**:

1. Open Zoho Catalyst Console
2. Navigate to DataStore → Tables → Sessions
3. Click on User_ID column
4. Remove Foreign Key constraint (if exists)
5. Save changes

**Why Required**:
- Employee sessions store Employees.ROWID in User_ID
- FK to Users table rejects Employees.ROWID values
- Results in 500 error on employee login

**Verification**:
```bash
# Test employee login should succeed after migration
curl -X POST "http://localhost:3000/server/smart_railway_app_function/session/employee/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@railway.com", "password": "Admin@123"}'

# Expected: 200 OK with session created
# Before fix: 500 error - FK violation
```

**See**: `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md`

---

## File Structure

### Backend (functions/smart_railway_app_function/)

```
routes/
├── session_auth.py          # Session endpoints
│   ├── POST /session/login            (passengers)
│   ├── POST /session/employee/login   (employees/admins)
│   ├── POST /session/logout
│   └── GET /session/validate

services/
├── session_service.py       # Session management logic
│   ├── create_session()
│   ├── validate_session()
│   ├── revoke_session()
│   └── log_audit_event()
├── employee_service.py      # Employee business logic
│   ├── authenticate_employee()
│   ├── create_employee()
│   └── get_employee_by_email()

repositories/
└── cloudscale_repository.py # Database access
    ├── get_user_by_email()
    ├── get_employee_by_email()
    ├── get_records()
    └── create_record()
```

### Frontend (railway-app/src/)

```
components/
├── AuthPage.jsx             # Login form (both types)
├── OTPVerification.jsx      # OTP entry for registration

contexts/
└── SessionAuthContext.jsx   # Authentication state
    ├── login()              (passenger)
    ├── employeeLogin()      (employee/admin)
    ├── validateSession()
    └── logout()

api/
└── sessionApi.js            # API calls
    ├── login()
    ├── employeeLogin()
    ├── validateSession()
    └── logout()
```

---

## Key Design Decisions

### 1. Separate Tables vs Single Table with Role

**Decision**: Separate Users and Employees tables ✅

**Rationale**:
- Employees need additional fields (Employee_ID, Department, Designation)
- Clear separation of concerns
- Different registration flows (public vs invitation)
- Easier to manage permissions and access control

### 2. Polymorphic Reference vs Separate Session Tables

**Decision**: Polymorphic reference with User_Type field ✅

**Rationale**:
- Single session management codebase
- User_Type field clearly indicates table reference
- No need to query two session tables
- Simpler session validation logic

**Alternative Considered**: Separate User_Sessions and Employee_Sessions tables
- **Rejected**: Duplicate code, complex queries, harder to enforce limits

### 3. Database FK vs Application Validation

**Decision**: No FK constraint, application-level validation ✅

**Rationale**:
- Database FK cannot express "Table A OR Table B"
- Application validation is more flexible
- Can add detailed error messages
- Allows polymorphic pattern

**Trade-off**: Lose database-level referential integrity
**Mitigation**: Strict validation in session_service.py before insert

---

## API Endpoints

### Passenger Authentication

```
POST /session/register        # Public registration with OTP
POST /session/verify          # Verify OTP and create account
POST /session/login           # Login (checks Users table)
POST /session/logout          # Logout (clears session)
GET  /session/validate        # Check if session is valid
```

### Employee Authentication

```
POST /session/employee/login  # Login (checks Employees table)
POST /session/logout          # Logout (clears session)
GET  /session/validate        # Check if session is valid (same endpoint)
```

### Employee Management (Admin Only)

```
POST /employees/invite        # Send invitation email
GET  /employees               # List all employees
GET  /employees/:id           # Get employee details
PUT  /employees/:id           # Update employee
DELETE /employees/:id         # Deactivate employee
```

---

## Security Best Practices Implemented

1. ✅ **Argon2id password hashing** (not bcrypt)
2. ✅ **HMAC-signed session cookies** (not plain session IDs)
3. ✅ **HttpOnly + Secure cookies** (XSS and MITM protection)
4. ✅ **CSRF tokens** (state-changing request protection)
5. ✅ **Session audit logging** (full security trail)
6. ✅ **Concurrent session limits** (max 3 per user)
7. ✅ **Sliding window expiration** (24h absolute, 6h idle)
8. ✅ **Security headers** (XSS, clickjacking, MIME sniffing)
9. ✅ **CORS hardening** (no wildcards, whitelisted origins)
10. ✅ **HTTPS enforcement** (production only)

---

## Related Documentation

- **Database Schema**: `docs/architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md`
- **User/Employee Plan**: `docs/architecture/USER_EMPLOYEE_RESTRUCTURE_PLAN.md`
- **Implementation Notes**: `docs/architecture/IMPLEMENTATION_NOTES.md`
- **Migration Guide**: `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md`
- **Security Summary**: `docs/security/SECURITY_IMPLEMENTATION_SUMMARY.md`

---

**Version**: 2.0  
**Last Updated**: April 8, 2026  
**Status**: ✅ Production Ready (after database migration)
