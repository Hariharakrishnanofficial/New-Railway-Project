# User/Employee Architecture - IMPLEMENTED ✅

## Overview

**Status:** ✅ IMPLEMENTED (April 6, 2026)  
**Last Updated:** April 8, 2026 (Session FK Migration Required)

**Architecture:** Separate tables for Users (passengers) and Employees (staff/admin) with polymorphic session management.

---

## Implemented Database Architecture

### ✅ Current Production Schema

```
┌─────────────────────────────┐
│       Users Table           │  ← Passengers ONLY
├─────────────────────────────┤
│ ROWID (PK)                  │
│ Full_Name                   │
│ Email (Unique)              │
│ Password (Argon2id Hashed)  │
│ Phone_Number                │
│ Account_Status              │
│ Role (Removed - all users   │
│      are passengers)        │
│ Created_At                  │
└─────────────────────────────┘

┌─────────────────────────────┐
│      Employees Table        │  ← Staff (Admin/Employee)
├─────────────────────────────┤
│ ROWID (PK)                  │
│ Employee_ID (Unique)        │  ← Staff ID like "EMP001"
│ Full_Name                   │
│ Email (Unique)              │
│ Password (Argon2id Hashed)  │
│ Phone_Number                │
│ Role (Admin|Employee)       │
│ Department                  │  ← Mandatory
│ Designation                 │  ← Mandatory
│ Account_Status              │
│ Last_Login                  │
│ Is_Active                   │
│ Joined_At                   │
│ Created_At                  │
└─────────────────────────────┘

┌──────────────────────────────┐
│       Sessions Table         │  ← Polymorphic session management
├──────────────────────────────┤
│ ROWID (PK)                   │
│ Session_ID (Unique)          │
│ User_ID ⚠️                   │  ← POLYMORPHIC REFERENCE
│ User_Type                    │  ← 'user' or 'employee'
│ User_Email                   │
│ User_Role                    │
│ CSRF_Token                   │
│ Expires_At                   │
│ Is_Active                    │
│ Created_At                   │
└──────────────────────────────┘

⚠️ **CRITICAL**: User_ID must NOT have Foreign Key constraint
   - Can reference Users.ROWID (if User_Type='user')
   - Can reference Employees.ROWID (if User_Type='employee')
   - Database FK cannot express "Table A OR Table B"
   - Validation enforced at application level
```

**See:** `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md` for FK removal steps
│ Designation                  │  ← NEW: Pre-fill on registration
│ Invited_By                   │
│ Invited_At                   │
│ Expires_At                   │
│ Is_Used                      │
│ Used_At                      │
│ Registered_Employee_Id       │  ← Links to Employees table
│ Created_At                   │
└──────────────────────────────┘
```

## ✅ Authentication Flow - IMPLEMENTED

### Current Production Flow (April 2026)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DUAL AUTHENTICATION SYSTEM                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PASSENGER LOGIN                          EMPLOYEE/ADMIN LOGIN           │
│  └─► /session/login                       └─► /session/employee/login   │
│                                                                          │
│  User enters email/password               Employee enters email/password │
│         │                                          │                      │
│         ▼                                          ▼                      │
│  ┌─────────────────┐                      ┌──────────────────┐          │
│  │ Check Users     │──Found──► Verify     │ Check Employees  │──Found──►│
│  │ table ONLY      │           password   │ table ONLY       │  Verify  │
│  └─────────────────┘              │       └──────────────────┘  password│
│         │                         │                  │              │    │
│    Not Found                      ▼             Not Found          ▼    │
│         │                   Create session           │        Create    │
│         ▼                   User_Type='user'         ▼        session   │
│  Return 401               User_ID=Users.ROWID   Return 401  User_Type=  │
│  "Invalid credentials"    User_Role='Passenger'  "Invalid"  'employee'  │
│                                   │               credentials  │         │
│                                   │                            │         │
│                                   ▼                            ▼         │
│                            Sessions table              Sessions table    │
│                            ├─ User_ID: 1234           ├─ User_ID: 5678  │
│                            ├─ User_Type: 'user'       ├─ User_Type:     │
│                            └─ User_Role: 'Passenger'  │   'employee'    │
│                                                        └─ User_Role:     │
│                                                            'ADMIN'       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### ⚠️ CRITICAL: Polymorphic Session Management

**Sessions.User_ID** can reference **either table**:
- When `User_Type='user'` → User_ID references `Users.ROWID`
- When `User_Type='employee'` → User_ID references `Employees.ROWID`

**FK Constraint Issue**:
- ❌ DO NOT add Foreign Key constraint `User_ID → Users.ROWID`
- ❌ This breaks employee logins (FK violation)
- ✅ Remove existing FK if present (see migration guide)
- ✅ Validate references at application level using `User_Type`

**Migration Required**: See `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md`

---

## Employees Table Schema

### CloudScale Table Definition

```python
# In config.py - Add to TABLES dict
TABLES = {
    # ... existing tables ...
    'employees': 'Employees',
}
```

### Column Definitions

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `ROWID` | BIGINT | Auto | Primary key |
| `Employee_ID` | VARCHAR(20) | Yes | Unique staff ID (e.g., "EMP001", "ADM001") |
| `Full_Name` | VARCHAR(100) | Yes | Employee name |
| `Email` | VARCHAR(255) | Yes | Unique, lowercase |
| `Password` | VARCHAR(255) | Yes | Bcrypt hashed |
| `Phone_Number` | VARCHAR(20) | No | Contact number |
| `Role` | VARCHAR(20) | Yes | "Admin" or "Employee" |
| `Department` | VARCHAR(50) | No | e.g., "Operations", "Customer Service" |
| `Designation` | VARCHAR(50) | No | e.g., "Station Master", "Ticket Clerk" |
| `Permissions` | TEXT | No | JSON array of permissions |
| `Invited_By` | BIGINT | Yes | ROWID of inviting admin |
| `Invitation_Id` | BIGINT | No | Link to invitation record |
| `Joined_At` | DATETIME | Yes | When employee registered |
| `Account_Status` | VARCHAR(20) | Yes | "Active", "Inactive", "Suspended" |
| `Last_Login` | DATETIME | No | Last successful login |
| `Created_At` | DATETIME | Yes | Record creation time |
| `Updated_At` | DATETIME | No | Last update time |

### Permission System

```json
// Example Permissions JSON structure
{
  "modules": {
    "bookings": ["view", "create", "cancel"],
    "trains": ["view"],
    "stations": ["view"],
    "users": ["view"],
    "reports": ["view", "export"],
    "announcements": ["view", "create", "edit"]
  },
  "admin_access": false,
  "can_invite_employees": false
}
```

### Default Permissions by Role

| Role | Default Permissions |
|------|---------------------|
| **Admin** | Full access to all modules |
| **Employee** | Limited: bookings (view/create), stations (view), announcements (view) |

---

## Updated Employee_Invitations Table

### New Columns to Add

| Column | Type | Description |
|--------|------|-------------|
| `Role` | VARCHAR(20) | "Admin" or "Employee" - what role to assign |
| `Department` | VARCHAR(50) | Pre-filled for registration |
| `Designation` | VARCHAR(50) | Pre-filled for registration |
| `Employee_ID_Prefix` | VARCHAR(10) | Auto-generate ID like "EMP" or "ADM" |

### Updated Schema

```python
invitation_data = {
    'Email': email,
    'Invitation_Token': token,
    'Role': 'Employee',  # NEW: Admin can specify
    'Department': 'Operations',  # NEW: Optional pre-fill
    'Designation': 'Ticket Clerk',  # NEW: Optional pre-fill
    'Invited_By': admin_id,
    'Invited_At': now,
    'Expires_At': expires_at,
    'Is_Used': False,
}
```

---

## Implementation Tasks

### Phase 0: Documentation (COMPLETED ✅)

- [x] **0.1** Update `CLOUDSCALE_DATABASE_SCHEMA_V2.md` with Employees table
- [x] **0.2** Update `CLOUDSCALE_DATABASE_SCHEMA_V2.md` Employee_Invitations with new columns
- [x] **0.3** Update `SESSION_SCHEMA.md` with User_Type field
- [x] **0.4** Update relationships diagram
- [x] **0.5** Update API endpoint mapping

### Phase 1: Database & Config Setup (IN PROGRESS 🔄)

- [ ] **1.1** Create `Employees` table in CloudScale (manual - console)
- [ ] **1.2** Add new columns to `Employee_Invitations` table (manual - console)
- [x] **1.3** Update `config.py` with new table mapping ✅
- [x] **1.4** Create employee repository functions ✅

### Phase 2: Backend Services (COMPLETE ✅)

- [x] **2.1** Create `employee_service.py` for employee CRUD ✅
- [x] **2.2** Update `employee_invitation_service.py` with role/department fields ✅
- [x] **2.3** Create employee registration endpoint (with OTP) ✅
  - Updated `otp_register.py` to create Employee records when invitation token present
  - Employee creation includes Role, Department, Designation from invitation
  - Marks invitation as used with Registered_Employee_Id
  - Creates session with `user_type='employee'`
- [x] **2.4** Create separate login endpoint for employees ✅ (`/session/employee/login`)
- [x] **2.5** Update session middleware for employee authentication ✅ (user_type support)
- [x] **2.6** Fix audit logging for foreign key constraints ✅
  - User_ID only included if valid positive integer (ROWID)
  - Session_ID stored in Details.session_ref instead of FK field

### Phase 3: Admin Panel (IN PROGRESS 🔄)

- [x] **3.1** Update invitation form with Role, Department, Designation fields ✅
  - Added Role dropdown (Admin/Employee)
  - Added Department and Designation text inputs
  - Updated API call to include new fields
  - Updated invitations list to show Role, Department, Designation
- [ ] **3.2** Create Employee management page (list, view, edit)
- [ ] **3.3** Add permission editor component
- [ ] **3.4** Create employee registration page (with pre-filled data from invitation)

### Phase 4: Testing & Migration

- [ ] **4.1** Test employee invitation flow end-to-end
- [ ] **4.2** Test employee login separately from user login
- [ ] **4.3** Migrate existing employee-role users to Employees table (if any)
- [ ] **4.4** Update API documentation

---

## API Changes

### Updated Invitation Endpoint

```
POST /admin/employees/invite
{
  "email": "employee@company.com",
  "role": "Employee",          // NEW: "Admin" or "Employee"
  "department": "Operations",  // NEW: Optional
  "designation": "Clerk"       // NEW: Optional
}
```

### New Employee Login Endpoint

```
POST /session/employee/login
{
  "email": "employee@company.com",
  "password": "SecurePass123"
}

Response:
{
  "status": "success",
  "data": {
    "employee": {
      "id": "123",
      "employeeId": "EMP001",
      "fullName": "John Staff",
      "email": "employee@company.com",
      "role": "Employee",
      "department": "Operations",
      "designation": "Clerk",
      "permissions": {...}
    },
    "csrfToken": "..."
  }
}
```

### Updated Session Validation

```
GET /session/validate

Response (for employees):
{
  "status": "success",
  "data": {
    "type": "employee",  // NEW: "user" or "employee"
    "employee": {
      "id": "123",
      "employeeId": "EMP001",
      "role": "Employee",
      "permissions": {...}
    }
  }
}
```

---

## Security Considerations

1. **Separate Authentication**: Employees have their own table, reducing risk of role escalation
2. **Permission Granularity**: JSON permissions allow fine-grained access control
3. **Audit Trail**: `Invited_By` tracks who added each employee
4. **Account Control**: Admins can suspend/deactivate employee accounts independently

---

## Migration Strategy

### For Existing Users with Role="Employee" or "Admin"

```python
# Migration script (one-time)
def migrate_existing_employees():
    # 1. Query Users where Role in ('Employee', 'Admin')
    # 2. For each: Create record in Employees table
    # 3. Delete from Users table (or mark as migrated)
    # 4. Update any foreign key references
    pass
```

### Backward Compatibility

During transition:
- Login checks Employees table first, then Users table
- Session middleware supports both table types
- Frontend detects user type from session response

---

## Open Questions

1. **Employee ID Format**: Should it be auto-generated (EMP001) or manual entry?
2. **Department List**: Fixed options or free-text?
3. **Permission Inheritance**: Should Employee inherit from a base template?
4. **Multi-role Support**: Can one person be both User (passenger) and Employee?

---

## Files to Create/Modify

### New Files
- `services/employee_service.py` - Employee CRUD operations
- `routes/employee_routes.py` - Employee management endpoints
- `pages/admin/EmployeeManagement.jsx` - Employee list/edit UI

### Modified Files
- `config.py` - Add Employees table mapping
- `employee_invitation_service.py` - Add role/department fields
- `employee_invitation_routes.py` - Update invitation endpoint
- `otp_register.py` - Separate employee registration flow
- `session_middleware.py` - Support employee sessions
- `session_service.py` - Detect user type on login
- `EmployeeInvitation.jsx` - Add role/department form fields
