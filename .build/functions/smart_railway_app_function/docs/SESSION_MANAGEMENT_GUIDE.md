# Session Management System - Detailed Technical Guide
**Smart Railway Ticketing System**

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication Flow](#authentication-flow)
4. [Security Features](#security-features)
5. [Session Lifecycle](#session-lifecycle)
6. [CSRF Protection](#csrf-protection)
7. [API Interaction](#api-interaction)
8. [Frontend Integration](#frontend-integration)
9. [Session Limits & Concurrency](#session-limits--concurrency)
10. [Audit Logging](#audit-logging)

---

## Overview

### What is Session Management?

Session management is a **server-side authentication system** that replaces client-side JWT tokens. Instead of storing authentication credentials in the browser (vulnerable to XSS attacks), the server maintains session state in the database and issues only a **session ID** to the client via an **HttpOnly cookie**.

### Why Replace JWT?

**Old System (JWT-based):**
- ❌ JWT tokens stored in localStorage (XSS vulnerable)
- ❌ No logout - tokens valid until expiry even after "logout"
- ❌ Can't revoke compromised tokens
- ❌ No concurrent session control
- ❌ Rate limiting lost on server restart (in-memory)

**New System (Session-based):**
- ✅ HttpOnly cookies (JavaScript cannot access)
- ✅ Real logout - session revoked immediately
- ✅ Can revoke sessions anytime (e.g., stolen session)
- ✅ Max 3 concurrent sessions per user
- ✅ CSRF protection on state-changing requests
- ✅ Full audit trail of session events

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                        │
├─────────────────────────────────────────────────────────────────┤
│  SessionAuthContext.jsx  ←→  sessionApi.js  ←→  SessionMgmt.jsx │
│    (Auth state mgmt)        (API client)        (UI component)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Requests with:
                             │ • Cookie: railway_sid=<session_id>
                             │ • X-CSRF-Token: <csrf_token>
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      BACKEND (Flask/Python)                      │
├─────────────────────────────────────────────────────────────────┤
│  session_auth.py          session_middleware.py                  │
│  (Auth routes)            (@require_session decorator)           │
│                                    │                             │
│                                    ▼                             │
│                          session_service.py                      │
│                     (Session CRUD operations)                    │
│                                    │                             │
└────────────────────────────────────┼─────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUDSCALE DATABASE (ZCQL)                     │
├─────────────────────────────────────────────────────────────────┤
│  • Sessions table (active sessions)                              │
│  • Session_Audit_Log table (security events)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow

### 1️⃣ Registration Flow

```
User                    Frontend                Backend              Database
 │                         │                       │                     │
 │ Fill registration form  │                       │                     │
 ├────────────────────────>│                       │                     │
 │                         │ POST /session/register│                     │
 │                         │ {email, password, ...}│                     │
 │                         ├──────────────────────>│                     │
 │                         │                       │ Hash password        │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │                     │
 │                         │                       │ INSERT INTO Users   │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ User created        │
 │                         │                       │                     │
 │                         │                       │ Generate session ID │
 │                         │                       │ (256-bit entropy)   │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │                     │
 │                         │                       │ Generate CSRF token │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │                     │
 │                         │                       │ INSERT INTO Sessions│
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ Session created     │
 │                         │                       │                     │
 │                         │ Set-Cookie: railway_sid│                    │
 │                         │ HttpOnly, Secure      │                     │
 │                         │ {user, csrfToken}     │                     │
 │                         │<──────────────────────┤                     │
 │                         │                       │                     │
 │                         │ Store csrfToken in    │                     │
 │                         │ memory (not localStorage)                   │
 │                         ├──────┐                │                     │
 │                         │<─────┘                │                     │
 │                         │                       │                     │
 │ Redirect to dashboard   │                       │                     │
 │<────────────────────────┤                       │                     │
```

**Key Points:**
- Password is hashed with SHA-256 before storage
- Session ID is a 43-character URL-safe token (256-bit entropy)
- Session cookie is **HttpOnly** (JavaScript cannot read it)
- CSRF token is returned in response body, stored in frontend memory
- Session record includes device info (IP, User-Agent) for security

---

### 2️⃣ Login Flow

```
User                    Frontend                Backend              Database
 │                         │                       │                     │
 │ Enter credentials       │                       │                     │
 ├────────────────────────>│                       │                     │
 │                         │ POST /session/login   │                     │
 │                         │ {email, password}     │                     │
 │                         ├──────────────────────>│                     │
 │                         │                       │                     │
 │                         │                       │ SELECT FROM Users   │
 │                         │                       │ WHERE Email = ?     │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ User record         │
 │                         │                       │                     │
 │                         │                       │ Verify password     │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │ ✓ Match             │
 │                         │                       │                     │
 │                         │                       │ Check active sessions│
 │                         │                       │ for this user       │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ Found 3 sessions    │
 │                         │                       │                     │
 │                         │                       │ Revoke oldest session│
 │                         │                       │ (limit = 3)         │
 │                         │                       ├────────────────────>│
 │                         │                       │ UPDATE Sessions     │
 │                         │                       │ SET Is_Active=false │
 │                         │                       │<────────────────────┤
 │                         │                       │                     │
 │                         │                       │ Create new session  │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │                     │
 │                         │ Set-Cookie + user data│                     │
 │                         │<──────────────────────┤                     │
 │ Logged in successfully  │                       │                     │
 │<────────────────────────┤                       │                     │
```

**Key Points:**
- Max 3 concurrent sessions enforced - oldest revoked automatically
- Each session gets a unique CSRF token
- Session cookie has 24-hour expiry with sliding window

---

### 3️⃣ Request Flow (Protected Route)

```
User                    Frontend                Backend              Database
 │                         │                       │                     │
 │ Click "My Bookings"     │                       │                     │
 ├────────────────────────>│                       │                     │
 │                         │ GET /bookings         │                     │
 │                         │ Cookie: railway_sid   │                     │
 │                         ├──────────────────────>│                     │
 │                         │                       │                     │
 │                         │                       │ @require_session    │
 │                         │                       │ decorator extracts  │
 │                         │                       │ session_id from cookie
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │                     │
 │                         │                       │ SELECT FROM Sessions│
 │                         │                       │ WHERE Session_ID=?  │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ Session record      │
 │                         │                       │                     │
 │                         │                       │ Validate:           │
 │                         │                       │ • Is_Active = true  │
 │                         │                       │ • Not expired       │
 │                         │                       │ • Not idle too long │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │ ✓ Valid             │
 │                         │                       │                     │
 │                         │                       │ UPDATE Last_Accessed│
 │                         │                       ├────────────────────>│
 │                         │                       │ (sliding timeout)   │
 │                         │                       │                     │
 │                         │                       │ Execute route handler│
 │                         │                       │ (fetch bookings)    │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │                     │
 │                         │ {status: success, ...}│                     │
 │                         │<──────────────────────┤                     │
 │ Display bookings        │                       │                     │
 │<────────────────────────┤                       │                     │
```

**Key Points:**
- Every protected request validates session before executing
- Session validation is automatic via `@require_session` decorator
- Last accessed time updated → sliding window timeout (6 hours idle)

---

### 4️⃣ State-Changing Request (with CSRF)

```
User                    Frontend                Backend              Database
 │                         │                       │                     │
 │ Update profile          │                       │                     │
 ├────────────────────────>│                       │                     │
 │                         │ PUT /session/profile  │                     │
 │                         │ Cookie: railway_sid   │                     │
 │                         │ X-CSRF-Token: abc123  │                     │
 │                         │ {fullName: "New Name"}│                     │
 │                         ├──────────────────────>│                     │
 │                         │                       │                     │
 │                         │                       │ @require_session    │
 │                         │                       │ validates session   │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ Session valid       │
 │                         │                       │                     │
 │                         │                       │ Validate CSRF token │
 │                         │                       │ X-CSRF-Token header │
 │                         │                       │ matches session's   │
 │                         │                       │ CSRF_Token field    │
 │                         │                       ├──────┐              │
 │                         │                       │<─────┘              │
 │                         │                       │ ✓ CSRF valid        │
 │                         │                       │                     │
 │                         │                       │ UPDATE Users        │
 │                         │                       │ SET Full_Name=?     │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │                     │
 │                         │ {status: success, ...}│                     │
 │                         │<──────────────────────┤                     │
 │ Profile updated         │                       │                     │
 │<────────────────────────┤                       │                     │
```

**CSRF Protection:**
- POST/PUT/DELETE/PATCH requests **require** valid CSRF token
- CSRF token sent in `X-CSRF-Token` header
- Protects against cross-site request forgery attacks

---

### 5️⃣ Logout Flow

```
User                    Frontend                Backend              Database
 │                         │                       │                     │
 │ Click "Log Out"         │                       │                     │
 ├────────────────────────>│                       │                     │
 │                         │ POST /session/logout  │                     │
 │                         │ Cookie: railway_sid   │                     │
 │                         │ X-CSRF-Token: abc123  │                     │
 │                         ├──────────────────────>│                     │
 │                         │                       │                     │
 │                         │                       │ UPDATE Sessions     │
 │                         │                       │ SET Is_Active=false │
 │                         │                       │ WHERE Session_ID=?  │
 │                         │                       ├────────────────────>│
 │                         │                       │<────────────────────┤
 │                         │                       │ Session revoked     │
 │                         │                       │                     │
 │                         │                       │ INSERT audit log    │
 │                         │                       │ SESSION_REVOKED     │
 │                         │                       ├────────────────────>│
 │                         │                       │                     │
 │                         │ Set-Cookie: railway_sid│                    │
 │                         │ expires=0 (clear)     │                     │
 │                         │<──────────────────────┤                     │
 │                         │                       │                     │
 │                         │ Clear CSRF token      │                     │
 │                         │ Clear user state      │                     │
 │                         ├──────┐                │                     │
 │                         │<─────┘                │                     │
 │                         │                       │                     │
 │ Redirected to login     │                       │                     │
 │<────────────────────────┤                       │                     │
```

**Key Points:**
- Session immediately invalidated in database (Is_Active=false)
- Cookie cleared from browser
- User cannot make authenticated requests with this session anymore
- **Soft delete** - session record kept for audit trail

---

## Security Features

### 🔒 1. HttpOnly Cookies

**Configuration:**
```python
# Backend - session_auth.py
response.set_cookie(
    'railway_sid',           # Cookie name
    session_id,              # 43-char secure token
    httponly=True,           # ⭐ Cannot access via JavaScript
    secure=True,             # ⭐ HTTPS only (production)
    samesite='Strict',       # ⭐ Prevents CSRF attacks
    max_age=86400,           # 24 hours
    path='/'
)
```

**Why HttpOnly?**
- Even if attacker injects malicious JavaScript (XSS), they **cannot** read the session cookie
- Compare to JWT in localStorage: trivial to steal via `localStorage.getItem('token')`

**Browser Behavior:**
- Browser automatically includes cookie in requests to the domain
- JavaScript code (including malicious scripts) **cannot** access it
- Only the browser and server can read/write it

---

### 🔒 2. CSRF Protection

**What is CSRF?**
Cross-Site Request Forgery - attacker tricks user's browser into making authenticated requests.

**Example Attack (Without CSRF Protection):**
```html
<!-- Malicious website -->
<img src="https://railway-app.com/api/session/profile" 
     onload="fetch('https://railway-app.com/api/bookings', {
       method: 'POST',
       credentials: 'include',  ← Browser sends session cookie
       body: JSON.stringify({...})
     })">
```

Browser sends session cookie → request succeeds → attacker creates booking!

**How We Prevent It:**

1. **Server generates CSRF token** unique per session
2. **Frontend stores CSRF token** in memory (not cookie)
3. **Frontend sends CSRF token** in custom header (`X-CSRF-Token`)
4. **Server validates** CSRF token matches session's token

**Flow:**
```
Login → Server returns { user, csrfToken: "abc123..." }
       → Frontend stores: sessionApi.csrfToken = "abc123..."

POST request → Frontend adds header: X-CSRF-Token: abc123...
             → Server checks: X-CSRF-Token == session.CSRF_Token
             → If match: ✓ proceed
             → If mismatch: ✗ 403 Forbidden
```

**Code Example:**

```javascript
// Frontend - sessionApi.js
async request(endpoint, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  
  // Add CSRF token for state-changing requests
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method)) {
    headers['X-CSRF-Token'] = csrfToken;  // ⭐ Custom header
  }
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'include',  // Include session cookie
  });
}
```

```python
# Backend - session_middleware.py
def require_session(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Validate session from cookie
        session_data = validate_session(session_id)
        
        # 2. Validate CSRF for state-changing requests
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            csrf_from_header = request.headers.get('X-CSRF-Token')
            csrf_from_session = session_data.get('CSRF_Token')
            
            if csrf_from_header != csrf_from_session:
                return jsonify({'error': 'CSRF validation failed'}), 403
        
        # 3. Execute route handler
        return f(*args, **kwargs)
    return decorated
```

**Why This Works:**
- Attacker's website **cannot** read CSRF token (stored in memory, not cookie)
- Attacker's website **cannot** set custom headers on cross-origin requests
- Browser blocks reading responses from cross-origin requests (CORS)

---

### 🔒 3. Session Token Generation

**Method:**
```python
import secrets

def generate_session_id():
    return secrets.token_urlsafe(32)  # 32 bytes = 256 bits
    # Returns: "dGhpc2lzYXNlY3VyZXRva2VuYW5kaXRpc3Zlcnlsb25n"
```

**Security Properties:**
- **256-bit entropy** - astronomically hard to guess (2^256 possibilities)
- **URL-safe** - can be used in URLs if needed
- **Cryptographically secure random** - uses OS entropy source
- **Unique** - collision probability is negligible

**Compare to weak session IDs:**
- ❌ Sequential IDs: `session_12345` → attacker tries 12346, 12347...
- ❌ Short tokens: `a7b3c9` → only ~16M possibilities (brute-forceable)
- ✅ Our tokens: 43 characters, 2^256 possibilities

---

### 🔒 4. Concurrent Session Limiting

**Problem:** User logs in from 5 different devices. If one is compromised, attacker has unlimited access.

**Solution:** Limit to 3 concurrent sessions per user.

**Implementation:**
```python
def _enforce_session_limit(user_id: str):
    """Enforce max concurrent sessions per user."""
    # Count active sessions
    query = f"""
        SELECT COUNT(ROWID) as count 
        FROM {TABLES['sessions']} 
        WHERE User_ID = '{user_id}' AND Is_Active = true
    """
    result = cloudscale_repo.execute_query(query)
    count = result.get('data', {}).get('data', [{}])[0].get('count', 0)
    
    # If at limit, revoke oldest session
    if count >= MAX_CONCURRENT_SESSIONS:
        query = f"""
            SELECT ROWID, Session_ID 
            FROM {TABLES['sessions']} 
            WHERE User_ID = '{user_id}' AND Is_Active = true 
            ORDER BY Created_At ASC 
            LIMIT 1
        """
        oldest = cloudscale_repo.execute_query(query)
        oldest_rowid = oldest['data']['data'][0]['ROWID']
        
        # Revoke it
        cloudscale_repo.update_record(
            TABLES['sessions'], 
            str(oldest_rowid), 
            {'Is_Active': False}
        )
        
        # Audit log
        _log_session_event(
            event_type="SESSION_LIMIT_ENFORCED",
            user_id=user_id,
            details={"reason": "max_sessions_exceeded"}
        )
```

**User Experience:**
- User logs in from laptop, phone, tablet → 3 sessions ✓
- User logs in from work computer (4th device) → laptop session revoked
- Laptop gets 401 Unauthorized on next request → redirected to login

---

## Session Lifecycle

### State Transitions

```
┌─────────────────────────────────────────────────────────────────┐
│                        SESSION LIFECYCLE                         │
└─────────────────────────────────────────────────────────────────┘

     [User logs in]
           │
           ▼
    ┌─────────────┐
    │   CREATED   │  Is_Active = true
    │             │  Expires_At = now + 24h
    └──────┬──────┘
           │
           │ [User makes requests]
           ▼
    ┌─────────────┐
    │   ACTIVE    │  Last_Accessed_At updated on each request
    │  (in use)   │  Sliding timeout: Expires_At extended
    └──────┬──────┘
           │
           │ Three exit paths:
           │
    ┌──────┴──────┬──────────────┬──────────────┐
    │             │              │              │
    ▼             ▼              ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ LOGOUT  │  │ EXPIRED │  │ REVOKED │  │ LIMITED │
│         │  │         │  │         │  │         │
│ User    │  │ 24h or  │  │ Admin   │  │ Max 3   │
│ clicks  │  │ 6h idle │  │ or user │  │ sessions│
│ logout  │  │ passed  │  │ revoked │  │ exceeded│
└─────────┘  └─────────┘  └─────────┘  └─────────┘
    │             │              │              │
    └─────────────┴──────────────┴──────────────┘
                     │
                     ▼
              ┌─────────────┐
              │  INACTIVE   │  Is_Active = false
              │             │  Session record kept for audit
              └─────────────┘
```

### Timeouts

**1. Absolute Timeout (24 hours)**
```python
SESSION_TIMEOUT_HOURS = 24
expires_at = now + timedelta(hours=24)
```
- Session expires 24 hours after creation, regardless of activity
- User must log in again after 24 hours

**2. Idle Timeout (6 hours)**
```python
SESSION_IDLE_TIMEOUT_HOURS = 6

def validate_session(session_id):
    session = get_session_from_db(session_id)
    
    # Check if expired
    if now > session['Expires_At']:
        return None  # Expired
    
    # Check if idle too long
    last_accessed = parse(session['Last_Accessed_At'])
    idle_duration = now - last_accessed
    
    if idle_duration > timedelta(hours=SESSION_IDLE_TIMEOUT_HOURS):
        return None  # Idle timeout
    
    # Valid - update last accessed (sliding window)
    update_last_accessed(session_id, now)
    return session
```

**Sliding Window:**
- Every request updates `Last_Accessed_At`
- As long as user is active, session stays alive (up to 24h max)
- If user inactive for 6 hours → session expires

---

## CSRF Protection

### Double Submit Cookie Pattern

We use a **synchronizer token pattern** (not double submit):

**Traditional Double Submit:**
- CSRF token in cookie + request body
- Vulnerable if attacker can set cookies

**Our Approach (Synchronizer Token):**
- CSRF token stored **server-side** in Sessions table
- CSRF token sent to client in response body (not cookie)
- Client stores in **memory** (not localStorage or cookie)
- Client sends in **custom header** on state-changing requests
- Server compares header value with database value

**Why This is Secure:**

1. **Attacker cannot get CSRF token:**
   - Not in cookie → cannot read it
   - Not in localStorage → not accessible cross-domain
   - Only stored in memory of legit frontend

2. **Attacker cannot forge custom headers:**
   - Browsers block custom headers on cross-origin requests (unless CORS allows)
   - Our CORS policy doesn't allow arbitrary origins

3. **Even if attacker tricks user's browser:**
   ```html
   <!-- Attacker's site -->
   <form action="https://railway-app.com/session/profile" method="POST">
     <input name="fullName" value="Hacked">
   </form>
   <script>document.forms[0].submit();</script>
   ```
   - Browser sends session cookie ✓
   - But **no X-CSRF-Token header** ✗
   - Server rejects request with 403 Forbidden

---

## API Interaction

### Backend API Endpoints

**Authentication:**
```python
POST   /session/register     # Register new user
POST   /session/login        # Login with credentials
POST   /session/logout       # Logout (revoke session)
GET    /session/validate     # Validate current session
GET    /session/csrf-token   # Get/refresh CSRF token
```

**Profile Management:**
```python
PUT    /session/profile           # Update user profile (CSRF required)
POST   /session/change-password   # Change password (revokes all sessions)
```

**Session Management:**
```python
GET    /session/sessions              # List user's active sessions
POST   /session/sessions/{id}/revoke  # Revoke specific session
POST   /session/sessions/revoke-all   # Revoke all except current
```

**Admin Endpoints:**
```python
GET    /session/admin/sessions           # List all active sessions
POST   /session/admin/sessions/{id}/revoke # Admin revoke any session
GET    /session/admin/stats              # Session statistics
POST   /session/admin/cleanup-expired    # Manually trigger cleanup
```

---

### Request/Response Examples

#### Login Request
```http
POST /session/login HTTP/1.1
Host: railway-app.com
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

#### Login Response
```http
HTTP/1.1 200 OK
Set-Cookie: railway_sid=dGhpc2lzYXNlY3VyZXRva2VuYW5kaXRpc3Zlcnlsb25n; 
            HttpOnly; Secure; SameSite=Strict; Max-Age=86400; Path=/
Content-Type: application/json

{
  "status": "success",
  "message": "Login successful",
  "data": {
    "user": {
      "id": "123456",
      "fullName": "John Doe",
      "email": "user@example.com",
      "role": "User"
    },
    "csrfToken": "Y3NyZnRva2VuaGVyZXdoaWNoaXNhbHNvdmVyeWxvbmc"
  }
}
```

#### Protected Request
```http
PUT /session/profile HTTP/1.1
Host: railway-app.com
Cookie: railway_sid=dGhpc2lzYXNlY3VyZXRva2VuYW5kaXRpc3Zlcnlsb25n
X-CSRF-Token: Y3NyZnRva2VuaGVyZXdoaWNoaXNhbHNvdmVyeWxvbmc
Content-Type: application/json

{
  "fullName": "John Updated Doe"
}
```

---

## Frontend Integration

### SessionAuthContext Usage

**Setup (App.js):**
```javascript
import { SessionAuthProvider } from './context/SessionAuthContext';

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <SessionAuthProvider>  {/* ⭐ Wrap app */}
          <AppRoutes />
        </SessionAuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
```

**Usage in Components:**
```javascript
import { useSessionAuth } from '../context/SessionAuthContext';

function MyComponent() {
  const { 
    user,              // Current user object
    isAuthenticated,   // Boolean: logged in?
    isAdmin,           // Boolean: admin role?
    login,             // Login function
    logout,            // Logout function
    loading,           // Loading state
  } = useSessionAuth();

  if (loading) return <Spinner />;
  if (!isAuthenticated) return <Redirect to="/login" />;

  return (
    <div>
      <h1>Welcome, {user.fullName}!</h1>
      <button onClick={logout}>Log Out</button>
    </div>
  );
}
```

---

### SessionApi Client

**Making Requests:**
```javascript
import sessionApi from './services/sessionApi';

// GET request
const response = await sessionApi.get('/bookings');

// POST request (CSRF token added automatically)
const response = await sessionApi.post('/bookings', {
  trainId: '12345',
  passengers: [...]
});

// Check auth status
if (sessionApi.isAuthenticated()) {
  const user = sessionApi.getUser();
  console.log('Logged in as:', user.email);
}
```

**Automatic CSRF Handling:**
```javascript
// sessionApi.js internals
class SessionApiClient {
  async request(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    
    // Auto-add CSRF token for state-changing requests
    if (isStateChangingRequest(options.method)) {
      headers['X-CSRF-Token'] = getCsrfToken();  // ⭐ Automatic
    }
    
    return fetch(url, {
      ...options,
      headers,
      credentials: 'include',  // ⭐ Always include cookies
    });
  }
}
```

---

## Session Limits & Concurrency

### Max 3 Concurrent Sessions

**Scenario:**
```
User has 3 active sessions:
1. Desktop Chrome (Created: 10:00 AM)  ← Oldest
2. Laptop Firefox (Created: 11:00 AM)
3. Phone Safari  (Created: 12:00 PM)   ← Newest

User logs in from Tablet (4th device at 1:00 PM)
→ Desktop Chrome session revoked automatically
→ Tablet session created
```

**Database State:**
```sql
-- Before 4th login
Sessions:
  ROWID  Session_ID  User_ID  Created_At   Is_Active
  101    abc...      555      10:00:00     true       ← Will be revoked
  102    def...      555      11:00:00     true
  103    ghi...      555      12:00:00     true

-- After 4th login
Sessions:
  ROWID  Session_ID  User_ID  Created_At   Is_Active
  101    abc...      555      10:00:00     false      ← Revoked
  102    def...      555      11:00:00     true
  103    ghi...      555      12:00:00     true
  104    jkl...      555      13:00:00     true       ← New session
```

**User Experience:**
- Desktop browser: Next request gets 401 → "Session expired, please log in again"
- Other 3 sessions: Continue working normally

---

## Audit Logging

### What is Logged

Every security-relevant event is logged to `Session_Audit_Log`:

| Event | Severity | Logged When |
|-------|----------|-------------|
| SESSION_CREATED | INFO | User logs in/registers |
| SESSION_VALIDATED | INFO | Session checked (can be verbose) |
| SESSION_REVOKED | INFO | User logs out |
| SESSION_EXPIRED | INFO | Session times out |
| SESSION_LIMIT_ENFORCED | INFO | Oldest session auto-revoked |
| CSRF_VALIDATION_FAILED | WARNING | CSRF token mismatch |
| SESSION_INVALID | WARNING | Invalid session ID presented |
| PASSWORD_CHANGED | INFO | User changed password |
| SUSPICIOUS_ACTIVITY | CRITICAL | Multiple failed logins, etc. |

### Audit Log Schema

```python
Session_Audit_Log:
{
    "ROWID": "111222",
    "Event_Type": "SESSION_CREATED",
    "Session_ID": "abc...xyz",  # Last 8 chars for privacy
    "User_ID": "555",
    "User_Email": "user@example.com",
    "IP_Address": "192.168.1.100",
    "Event_Timestamp": "2026-03-31T12:00:00Z",
    "Details": '{"user_agent": "Chrome/120", "device": "Desktop"}',
    "Severity": "INFO"
}
```

### Querying Audit Logs

**Find all events for a user:**
```python
GET /session/admin/audit?user_id=555
```

**Find suspicious activity:**
```python
SELECT * FROM Session_Audit_Log 
WHERE Severity IN ('WARNING', 'CRITICAL') 
  AND Event_Timestamp > '2026-03-30T00:00:00Z'
ORDER BY Event_Timestamp DESC
```

---

## Session Management UI

### Features

**SessionManagement.jsx Component:**
- View all active sessions (devices)
- See device info (browser, OS, IP)
- Mark current session
- Revoke individual sessions
- Revoke all other sessions

**Screenshot Example:**
```
┌───────────────────────────────────────────────────────────────┐
│  Active Sessions                                  [Refresh]  │
│                                                               │
│  These are devices currently logged into your account.        │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 🖥️  Chrome on Windows              [Current]           │ │
│  │     IP: 192.168.1.100                                    │ │
│  │     Last active: Just now                                │ │
│  │     Signed in: 2 hours ago                               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 📱  Safari on iOS                         [Log Out]     │ │
│  │     IP: 192.168.1.101                                    │ │
│  │     Last active: 5 min ago                               │ │
│  │     Signed in: 1 day ago                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Security tip: If you see a session you don't recognize,      │
│  log it out immediately and change your password.             │
└───────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Backend (config.py)

```python
# Session configuration
SESSION_SECRET = os.getenv('SESSION_SECRET', 'dev-secret-change-in-production')
SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
SESSION_IDLE_TIMEOUT_HOURS = int(os.getenv('SESSION_IDLE_TIMEOUT_HOURS', '6'))
MAX_CONCURRENT_SESSIONS = int(os.getenv('MAX_CONCURRENT_SESSIONS', '3'))

# Cookie settings
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'railway_sid')
SESSION_COOKIE_HTTPONLY = True  # Always true for security
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true') == 'true'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')

# CSRF settings
CSRF_TOKEN_LENGTH = int(os.getenv('CSRF_TOKEN_LENGTH', '32'))
CSRF_HEADER_NAME = os.getenv('CSRF_HEADER_NAME', 'X-CSRF-Token')
```

### Environment Variables (.env)

```bash
# Required
SESSION_SECRET=your_64_char_random_secret_here

# Optional (defaults shown)
SESSION_TIMEOUT_HOURS=24
SESSION_IDLE_TIMEOUT_HOURS=6
MAX_CONCURRENT_SESSIONS=3
SESSION_COOKIE_NAME=railway_sid
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Strict
CSRF_TOKEN_LENGTH=32
CSRF_HEADER_NAME=X-CSRF-Token
```

---

## Comparison: JWT vs Session

| Feature | JWT (Old) | Session (New) |
|---------|-----------|---------------|
| **Storage** | localStorage (client) | Database (server) |
| **Cookie** | None | HttpOnly cookie |
| **XSS Vulnerability** | ❌ High | ✅ Immune |
| **CSRF Vulnerability** | ✅ Immune | ✅ Protected (CSRF token) |
| **Logout** | ❌ Fake (token still valid) | ✅ Real (session revoked) |
| **Token Revocation** | ❌ Impossible | ✅ Instant |
| **Concurrent Limits** | ❌ No control | ✅ Max 3 sessions |
| **Session Management** | ❌ None | ✅ View/revoke sessions |
| **Audit Trail** | ❌ Partial | ✅ Complete |
| **Scalability** | ✅ Stateless | ⚠️ Requires DB queries |

---

## Best Practices

### Development
1. Use `SESSION_COOKIE_SECURE=false` for local dev (HTTP)
2. Use `SESSION_COOKIE_SECURE=true` for production (HTTPS required)
3. Never commit `.env` file with real secrets

### Production
1. Generate strong `SESSION_SECRET` (64+ random characters)
2. Enable `SESSION_COOKIE_SECURE=true`
3. Use `SESSION_COOKIE_SAMESITE=Strict`
4. Set up session cleanup cron job (remove expired sessions)
5. Monitor `Session_Audit_Log` for suspicious activity

### Security Monitoring
```python
# Daily cron job
POST /session/admin/cleanup-expired

# Weekly review
SELECT Event_Type, COUNT(*) as count 
FROM Session_Audit_Log 
WHERE Event_Timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY Event_Type
ORDER BY count DESC;
```

---

## Troubleshooting

### Session Not Persisting

**Symptom:** User logs in but immediately logged out on refresh.

**Causes:**
1. **Cookie not being sent:** Check `credentials: 'include'` in fetch requests
2. **CORS misconfigured:** Backend must allow credentials from frontend origin
3. **HTTPS mismatch:** Secure cookie on HTTP won't work
4. **SameSite too strict:** Use `None` for cross-domain (requires Secure=true)

**Fix:**
```python
# Backend CORS config
CORS(app, 
     origins=['http://localhost:3001', 'https://your-domain.com'],
     supports_credentials=True,  # ⭐ Required
     allow_headers=['Content-Type', 'X-CSRF-Token'])
```

### CSRF Validation Failing

**Symptom:** POST/PUT requests fail with 403 "CSRF validation failed".

**Causes:**
1. CSRF token not stored in frontend after login
2. CSRF token not sent in header
3. CSRF token expired/wrong

**Fix:**
```javascript
// After login, store CSRF token
const response = await sessionApi.login({ email, password });
setCsrfToken(response.data.csrfToken);  // ⭐ Don't forget!

// Verify it's sent
console.log('CSRF token:', getCsrfToken());
```

### Session Expired Too Quickly

**Symptom:** User logged out after 1 hour of activity.

**Cause:** Idle timeout (6 hours) but absolute timeout (24 hours) triggered.

**Check:**
```python
# Backend logs
logger.info(f"Session {session_id} - Created: {created}, Now: {now}, Diff: {diff}")
```

---

## Summary

### How It All Works Together

1. **User logs in** → Backend creates session record, sends HttpOnly cookie
2. **Frontend stores** user info + CSRF token in memory
3. **Browser automatically** includes session cookie in all requests to domain
4. **Backend middleware** validates session on every protected route
5. **CSRF token** validated on state-changing requests (POST/PUT/DELETE)
6. **Session updated** with last accessed time (sliding timeout)
7. **User logs out** → Session revoked in DB, cookie cleared

### Key Security Benefits

✅ **HttpOnly cookies** → XSS-proof  
✅ **CSRF tokens** → CSRF-proof  
✅ **Server-side storage** → Instant revocation  
✅ **Concurrent limits** → Reduce attack surface  
✅ **Audit logging** → Detective controls  
✅ **Sliding timeout** → Balance security & UX  

---

*Generated: 2026-03-31*  
*Version: 1.0*  
*System: Smart Railway Ticketing System*
