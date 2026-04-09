# Postman Collection Updated - Session & Employee Endpoints

## ✅ Update Complete

Your Postman collection has been successfully updated with new session-based authentication and employee management endpoints.

**File:** `functions/smart_railway_app_function/docs/Smart_Railway_API.postman_collection.json`  
**Backup:** `functions/smart_railway_app_function/docs/Smart_Railway_API.postman_collection.backup.json`

---

## 📦 What's New

### **New Collection Variables (5)**
| Variable | Purpose |
|----------|---------|
| `sessionId` | Current session ID |
| `csrfToken` | CSRF token for state-changing requests |
| `employeeId` | Current employee ID (for employee sessions) |
| `invitationId` | Last created invitation ID |
| `invitationToken` | Invitation token for registration |

### **New Folder: 01A. Session Auth (4 endpoints)**

1. **Passenger Login** - `POST /session/login`
   - Login as passenger user
   - Sets HttpOnly session cookie
   - Auto-saves: `csrfToken`, `userId`

2. **Employee Login** - `POST /session/employee/login`
   - Login as employee/admin
   - Sets HttpOnly session cookie
   - Auto-saves: `csrfToken`, `employeeId`

3. **Validate Session** - `GET /session/validate`
   - Validate current session
   - Returns user/employee data

4. **Logout** - `POST /session/logout`
   - Destroy session
   - Clears session cookie

### **New Folder: 02A. Employees (8 endpoints)**

1. **Send Invitation** - `POST /admin/employees/invite`
   - Create employee invitation
   - Requires: Admin session + CSRF token
   - Body: `{ email, role, department, designation }`
   - Auto-saves: `invitationId`, `invitationToken`

2. **List Invitations** - `GET /admin/employees/invitations`
   - List all employee invitations
   - Requires: Admin session
   - Query params: `limit=50`

3. **Refresh Invitation** - `POST /admin/employees/invitations/:id/refresh`
   - Extend invitation expiry
   - Requires: Admin session + CSRF token

4. **Reinvite Employee** - `POST /admin/employees/invitations/:id/reinvite`
   - Resend invitation email
   - Requires: Admin session + CSRF token

5. **Get All Employees** - `GET /admin/employees`
   - List all employees
   - Requires: Admin session

6. **Get Employee by ID** - `GET /admin/employees/:id`
   - Get employee details
   - Requires: Admin session

7. **Update Employee** - `PUT /admin/employees/:id`
   - Update employee details
   - Requires: Admin session + CSRF token
   - Body: `{ full_name, department, designation }`

8. **Deactivate Employee** - `POST /admin/employees/:id/deactivate`
   - Deactivate employee account
   - Requires: Admin session + CSRF token

---

## 🚀 How to Use

### **Step 1: Import Collection**

Open Postman and import the updated collection:
```
File > Import > functions/smart_railway_app_function/docs/Smart_Railway_API.postman_collection.json
```

### **Step 2: Configure Base URL**

Set the `baseUrl` variable:
- **Development:** `http://localhost:3000`
- **Production:** `https://your-production-url.com`

Go to: Collection > Variables > `baseUrl` > Set current value

### **Step 3: Test Employee Login Flow**

#### 3.1 Create Admin Employee (One-time)

First, create an admin employee using the script:
```bash
python create_admin.py
```

#### 3.2 Login as Admin

1. Open: **01A. Session Auth > Employee Login**
2. Update body with your admin credentials:
   ```json
   {
       "email": "admin@railway.com",
       "password": "your_admin_password"
   }
   ```
3. Click **Send**
4. ✅ Session cookie is automatically saved
5. ✅ `csrfToken` and `employeeId` are auto-saved to variables

#### 3.3 Send Employee Invitation

1. Open: **02A. Employees > Send Invitation**
2. Body is already populated:
   ```json
   {
       "email": "employee@example.com",
       "role": "Employee",
       "department": "Operations",
       "designation": "Station Master"
   }
   ```
3. Click **Send**
4. ✅ `invitationId` and `invitationToken` are auto-saved
5. ✅ Invitation email sent (check server logs)

#### 3.4 List Invitations

1. Open: **02A. Employees > List Invitations**
2. Click **Send**
3. ✅ See all invitations with details

---

## 🔐 Authentication Flow

### **Session-Based (New - Recommended)**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Login (Passenger or Employee)                           │
│     POST /session/login or /session/employee/login          │
│     ↓                                                        │
│  2. Server sets HttpOnly cookie (automatic)                 │
│     Set-Cookie: railway_session=abc123; HttpOnly; Secure    │
│     ↓                                                        │
│  3. CSRF token saved to collection variable                 │
│     {{csrfToken}} = xyz789                                  │
│     ↓                                                        │
│  4. All subsequent requests include:                        │
│     - Session cookie (automatic via browser/Postman)        │
│     - X-CSRF-Token header (for POST/PUT/DELETE)            │
└─────────────────────────────────────────────────────────────┘
```

### **JWT-Based (Old - Still Supported)**

```
┌─────────────────────────────────────────────────────────────┐
│  1. Login via /auth/login                                   │
│     ↓                                                        │
│  2. Get JWT token                                           │
│     {{authToken}} = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... │
│     ↓                                                        │
│  3. All requests include:                                   │
│     Authorization: Bearer {{authToken}}                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Testing Checklist

Use this checklist to verify all endpoints work:

### Session Auth
- [ ] Passenger Login works and saves `csrfToken`
- [ ] Employee Login works and saves `csrfToken` + `employeeId`
- [ ] Validate Session returns correct user data
- [ ] Logout clears session

### Employee Management (Requires Admin Session)
- [ ] Send Invitation works and saves `invitationId`
- [ ] List Invitations returns all invitations
- [ ] Refresh Invitation extends expiry
- [ ] Reinvite sends new email
- [ ] Get All Employees returns employee list
- [ ] Get Employee by ID returns employee details
- [ ] Update Employee modifies employee data
- [ ] Deactivate Employee sets Is_Active to 0

---

## 🛠️ Troubleshooting

### **403 Forbidden on Admin Endpoints**

**Problem:** Not logged in as admin employee

**Solution:**
1. Logout: **Session Auth > Logout**
2. Login as admin: **Session Auth > Employee Login**
3. Verify session: **Session Auth > Validate Session** (should show `user_type: 'employee'` and `user_role: 'Admin'`)

### **500 Internal Server Error on Invitations**

**Problem:** Database tables missing

**Solution:**
1. Run diagnostic: `python diagnose_and_fix_db.py`
2. Create missing tables (see `FIX_INVITATION_ERRORS.md`)
3. Verify tables exist before testing

### **CSRF Token Error**

**Problem:** Missing or invalid CSRF token

**Solution:**
1. Make sure you've logged in first (CSRF token is returned on login)
2. Check that `{{csrfToken}}` variable is populated
3. Verify the `X-CSRF-Token` header is present in state-changing requests

### **Session Cookie Not Sent**

**Problem:** Postman not including session cookie

**Solution:**
1. Make sure cookies are enabled in Postman: Settings > General > Cookies
2. Check cookie jar: Cookies icon (top right) > Manage Cookies
3. Verify domain matches `baseUrl`

---

## 📁 File Structure

```
functions/smart_railway_app_function/docs/
├── Smart_Railway_API.postman_collection.json       ← Updated collection
├── Smart_Railway_API.postman_collection.backup.json ← Backup (original)
└── API_SPECIFICATION.json                          ← API spec
```

---

## 🔄 Importing to Postman

### Option 1: Import File
```
Postman > File > Import > Select file > Open
```

### Option 2: Import URL (if hosted)
```
Postman > File > Import > Link > Paste URL > Continue
```

### Option 3: Drag and Drop
```
Drag the .json file into Postman window
```

---

## 📊 Collection Stats

| Metric | Value |
|--------|-------|
| **Total Folders** | 18 |
| **Total Endpoints** | 80+ |
| **New Session Endpoints** | 4 |
| **New Employee Endpoints** | 8 |
| **Collection Variables** | 15 |
| **Authentication Types** | 2 (Session + JWT) |

---

## 📝 Notes

1. **HttpOnly Cookies:** Session cookies are automatically managed by Postman. You don't need to manually copy/paste them.

2. **CSRF Protection:** All state-changing requests (POST/PUT/DELETE) require the `X-CSRF-Token` header, which is auto-populated from `{{csrfToken}}` variable.

3. **Auto-Save Scripts:** Test scripts automatically save important IDs to collection variables for easy reuse across requests.

4. **Backward Compatibility:** Old JWT-based endpoints still work. You can use either authentication method.

5. **Base URL:** Default is `http://localhost:9000` but should be changed to `http://localhost:3000` for your setup.

---

## 🎯 Next Steps

1. **Import** the updated collection to Postman
2. **Set** the `baseUrl` to `http://localhost:3000`
3. **Create** an admin employee with `python create_admin.py`
4. **Login** as admin via **Session Auth > Employee Login**
5. **Test** employee invitation flow
6. **Verify** all endpoints work as expected

---

## 📚 Related Documentation

- **Fix Guide:** `FIX_INVITATION_ERRORS.md` - How to fix 500/403 errors
- **Summary:** `INVITATION_ERROR_SUMMARY.md` - Error analysis and solutions
- **Scripts:** `create_admin.py`, `diagnose_and_fix_db.py` - Database tools
- **API Spec:** `functions/smart_railway_app_function/docs/API_SPECIFICATION.json`

---

**Happy Testing! 🚀**
