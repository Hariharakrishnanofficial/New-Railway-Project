# 🔐 SESSION ID SYSTEM - Complete Architecture & Real Examples

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     SMART RAILWAY TICKETING SYSTEM               │
│                                                                  │
│  Session-Based Authentication (Replaces JWT)                    │
│  ✅ Server-side sessions                                         │
│  ✅ HttpOnly cookies                                             │
│  ✅ CSRF protection                                              │
│  ✅ Concurrent session limiting                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Real-Time Example: User Registration & Session Creation

### Step 1: User Registers

**Frontend (React):**
```jsx
// User fills registration form
const formData = {
  fullName: "John Doe",
  email: "john@example.com",
  password: "SecurePass123",
  phoneNumber: "+1234567890"
};

// User clicks "Register"
const result = await initiateRegistration(formData);
// Backend sends OTP email
```

**Browser Console:**
```javascript
// Network tab shows POST request
POST /session/register/initiate
Headers: 
  Content-Type: application/json

Body:
{
  "fullName": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "phoneNumber": "+1234567890"
}
```

---

### Step 2: User Verifies OTP

**Frontend (React):**
```jsx
// User receives email and enters 6-digit code
const otp = "847291";

const result = await verifyRegistration(
  "john@example.com",
  otp
);
```

**Network Request:**
```
POST /session/register/verify
Body:
{
  "email": "john@example.com",
  "otp": "847291"
}
```

---

### Step 3: Backend Creates Session

**Backend (Python) - Inside `verify_registration()` route:**

```python
# Step 1: Verify OTP
otp_valid, message = verify_otp("john@example.com", "847291", "registration")
if not otp_valid:
    return error("Invalid OTP")

# Step 2: Hash password
hashed_password = hash_password("SecurePass123")

# Step 3: Create user in database
user_data = {
    'Full_Name': "John Doe",
    'Email': "john@example.com",
    'Password': hashed_password,
    'Role': 'User',
    'Account_Status': 'Active',
    'Email_Verified': 'true'
}
result = cloudscale_repo.create_record('Users', user_data)
user_id = result['data']['ROWID']  # e.g., "12345"

# Step 4: Create session
session_id, csrf_token = create_session(
    user_id=user_id,
    user_email="john@example.com",
    user_role='User',
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    device_fingerprint=None
)

# Step 5: Store session in database
session_data = {
    'User_ID': user_id,
    'Session_ID': session_id,      # 43-char secure token
    'CSRF_Token': csrf_token,      # 43-char secure token
    'Status': 'Active',
    'IP_Address': '192.168.1.100',
    'User_Agent': 'Mozilla/5.0...',
    'Created_At': datetime.utcnow(),
    'Last_Activity': datetime.utcnow(),
    'Expires_At': datetime.utcnow() + timedelta(hours=24)
}
cloudscale_repo.create_record('Sessions', session_data)
```

---

### Step 4: Browser Receives Session Cookie

**Backend Response:**

```http
HTTP/1.1 201 Created
Set-Cookie: railway_sid=SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=; 
            Path=/; 
            HttpOnly; 
            Secure; 
            SameSite=Strict; 
            Expires=Tue, 01-Apr-2026 04:28:48 GMT

{
  "status": "success",
  "message": "Registration successful",
  "data": {
    "user": {
      "id": "12345",
      "fullName": "John Doe",
      "email": "john@example.com",
      "role": "User",
      "emailVerified": true
    },
    "csrfToken": "g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg="
  }
}
```

**Browser Storage:**

```javascript
// Cookies (automatic, HttpOnly - not accessible to JavaScript)
Cookies:
  railway_sid: SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
  Domain: localhost
  Path: /
  HttpOnly: ✅ (JavaScript cannot access)
  Secure: ✅ (HTTPS only)
  SameSite: Strict ✅ (CSRF protection)

// LocalStorage (JavaScript controlled)
LocalStorage:
  currentUser: {"id":"12345","email":"john@example.com",...}
  csrfToken: "g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg="
```

---

## 📊 Database Tables: Real Data Examples

### Sessions Table

```sql
-- Actual row in Sessions table
INSERT INTO Sessions VALUES (
  ROWID: 1001,
  User_ID: 12345,
  Session_ID: "SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=",
  CSRF_Token: "g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=",
  Status: "Active",
  IP_Address: "192.168.1.100",
  User_Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
  Device_Fingerprint: NULL,
  Created_At: "2026-03-31T16:28:48.265Z",
  Last_Activity: "2026-03-31T16:28:48.265Z",
  Expires_At: "2026-04-01T16:28:48.265Z",
  Max_Concurrent_Sessions: 3,
  Login_Count: 1
);
```

### Users Table

```sql
-- Corresponding user record
SELECT * FROM Users WHERE ROWID = 12345;

ROWID: 12345,
Full_Name: "John Doe",
Email: "john@example.com",
Password: "$2b$12$abcdef123456...",  -- bcrypt hash
Phone_Number: "+1234567890",
Role: "User",
Account_Status: "Active",
Email_Verified: "true",
Email_Verified_At: "2026-03-31T16:28:48.265Z",
Created_At: "2026-03-31T16:28:48.265Z",
Last_Login: "2026-03-31T16:28:48.265Z"
```

---

## 🔄 Subsequent Requests: Using the Session

### User Makes Authenticated Request

**Frontend (React):**
```jsx
// User clicks "Book a Ticket"
const response = await api.post('/bookings', {
  trainId: "TR001",
  seatCount: 2,
  price: 5000
});
```

**Browser Automatic Behavior:**

```http
POST /bookings HTTP/1.1
Host: api.smartrailway.com
Cookie: railway_sid=SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
X-CSRF-Token: g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
Content-Type: application/json

{
  "trainId": "TR001",
  "seatCount": 2,
  "price": 5000
}
```

**What Happens:**
1. Browser automatically includes `railway_sid` cookie (HttpOnly)
2. Frontend includes `X-CSRF-Token` header
3. Backend receives both

---

### Backend Session Validation

**Backend (Python) - Inside booking route:**

```python
from core.session_middleware import require_session

@app.route('/bookings', methods=['POST'])
@require_session  # Decorator validates session
def create_booking():
    """
    Decorator flow:
    1. Extract session_id from cookies
    2. Query Sessions table
    3. Validate session is active
    4. Validate CSRF token
    5. Check if expired
    6. Check idle timeout
    7. If valid: pass user to handler
    8. If invalid: return 401 Unauthorized
    """
    
    # At this point, session is validated
    # Current user info available from session
    user_id = session.get('user_id')          # "12345"
    user_email = session.get('user_email')    # "john@example.com"
    user_role = session.get('user_role')      # "User"
    
    # Create booking
    booking = {
        'User_ID': user_id,
        'Train_ID': request.json['trainId'],
        'Seat_Count': request.json['seatCount'],
        'Total_Price': request.json['price'],
        'Status': 'Confirmed'
    }
    
    result = cloudscale_repo.create_record('Bookings', booking)
    
    return jsonify({
        'status': 'success',
        'booking': result
    })
```

---

## 🔐 Session Validation Flow: Detailed

```
User Request
  │
  ├─ 1. Extract Session Cookie
  │    Cookie: railway_sid=SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
  │
  ├─ 2. Query Database
  │    SELECT * FROM Sessions
  │    WHERE Session_ID = 'SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg='
  │
  ├─ 3. Validate Status
  │    Status = 'Active' ✅
  │
  ├─ 4. Check Expiration
  │    Now: 2026-03-31 16:30:00
  │    Expires_At: 2026-04-01 16:28:48
  │    Status: Valid ✅
  │
  ├─ 5. Check Idle Timeout
  │    Last_Activity: 2026-03-31 16:28:48
  │    Idle_Timeout: 6 hours = 21600 seconds
  │    Elapsed: 120 seconds
  │    Status: Valid ✅
  │
  ├─ 6. Validate CSRF Token
  │    Header: X-CSRF-Token = g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
  │    DB: CSRF_Token = g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
  │    Status: Valid ✅
  │
  ├─ 7. Update Activity
  │    UPDATE Sessions
  │    SET Last_Activity = NOW()
  │    WHERE Session_ID = '...'
  │
  └─ ✅ Request Authorized
     Pass control to route handler
     User authenticated as: user_id=12345
```

---

## 🔄 Session Lifecycle: Complete Example

### Timeline

```
Time: 16:28:48
Event: User completes registration
  └─ Session created
    ├─ Session_ID: "abc123def456..."
    ├─ Status: "Active"
    ├─ Created_At: 16:28:48
    ├─ Last_Activity: 16:28:48
    ├─ Expires_At: 16:28:48 + 24h = next day 16:28:48
    └─ Idle_Timeout: 6 hours

Time: 16:30:00 (after 132 seconds)
Event: User books a ticket
  └─ Session validation
    ├─ Check: Status = "Active" ✅
    ├─ Check: Not expired (132s < 24h) ✅
    ├─ Check: Not idle (132s < 6h) ✅
    ├─ Update: Last_Activity = 16:30:00
    └─ ✅ Request authorized

Time: 17:00:00 (after 1800 seconds = 30 minutes)
Event: User views profile
  └─ Session still active
    └─ Last_Activity updated to 17:00:00

Time: 22:28:48 (after 6 hours exactly)
Event: User inactive for 6 hours, makes request
  └─ Session validation
    ├─ Check: Status = "Active" ✅
    ├─ Check: Not expired (6h < 24h) ✅
    ├─ Check: Idle timeout?
    │  ├─ Last_Activity: 17:00:00
    │  ├─ Now: 22:28:48
    │  ├─ Elapsed: 5h 28m 48s
    │  └─ Still valid (< 6h) ✅
    └─ Request authorized

Time: 22:32:00 (after 6 hours 3 minutes inactivity)
Event: User makes request after 6h+ inactivity
  └─ Session validation
    ├─ Check: Status = "Active" ✅
    ├─ Check: Not expired (6h 3m < 24h) ✅
    ├─ Check: Idle timeout?
    │  ├─ Last_Activity: 17:00:00
    │  ├─ Now: 22:32:00
    │  ├─ Elapsed: 5h 32m ← EXCEEDS 6 HOUR LIMIT
    │  └─ ❌ Session IDLE - revoked
    └─ ❌ UNAUTHORIZED
      └─ User must re-login

Time: 16:28:48 (next day, exactly 24 hours later)
Event: Session absolute timeout
  └─ Even if user is active
    ├─ Created_At: Yesterday 16:28:48
    ├─ Expires_At: Today 16:28:48
    ├─ ❌ EXPIRED
    └─ User must re-login (even if active!)
```

---

## 👥 Multiple Sessions: Concurrent Session Example

### User Logs In From Multiple Devices

```
Device 1 (Desktop)
├─ Login: 09:00
├─ Session_ID: sess_001
├─ Status: Active
└─ Last_Activity: 10:30

Device 2 (Mobile - New)
├─ Login: 10:15
├─ Session_ID: sess_002
├─ Status: Active
└─ Last_Activity: 10:15

Device 3 (Tablet - New)
├─ Login: 10:20
├─ Session_ID: sess_003
├─ Status: Active
└─ Last_Activity: 10:20

Device 4 (Laptop - Attempting login)
├─ Requesting: sess_004
├─ MAX_CONCURRENT_SESSIONS: 3
├─ Current Active Sessions: 3
└─ Result: ❌ REJECTED
   Action: Revoke oldest session (sess_001)
   ├─ sess_001.Status = "Revoked"
   ├─ Create new session (sess_004)
   └─ Desktop user is logged out!
```

### Database State

```sql
SELECT * FROM Sessions WHERE User_ID = 12345;

Session_ID  | Status    | Device      | Last_Activity | Expires_At
────────────┼───────────┼─────────────┼───────────────┼────────────
sess_001    | Revoked   | Desktop     | 10:30         | (expired)
sess_002    | Active    | Mobile      | 10:15         | 13:15
sess_003    | Active    | Tablet      | 10:20         | 13:20
sess_004    | Active    | Laptop      | 10:25         | 13:25
```

---

## 🔒 Security: CSRF Protection Example

### Attack Scenario

```
Attacker's Website: malicious.com
  └─ Contains hidden form:
     <form action="https://smartrailway.com/bookings" method="POST">
       <input name="amount" value="100000">
       <input name="account" value="attacker_account">
       <!-- Auto-submits -->
     </form>

Victim (logged into smartrailway.com) visits malicious.com
  └─ Browser sends booking request
  └─ Browser automatically includes railway_sid cookie
  └─ But X-CSRF-Token header NOT in form
  └─ Backend validation:
     ├─ Received CSRF from header: MISSING
     ├─ Database CSRF: has value
     ├─ Comparison: MISSING ≠ value
     └─ ❌ Request REJECTED
```

### Safe Request (Legitimate User)

```
Smart Railway booking page
  └─ Has CSRF token in hidden field
  └─ User clicks "Book Ticket"
  └─ React sends:
     {
       Cookie: railway_sid=...
       Header X-CSRF-Token: g2wBbQAAAAdkAAhyZWFkX2luZm8...
       Body: {...booking data...}
     }
  └─ Backend validation:
     ├─ Session valid ✅
     ├─ CSRF token matches ✅
     ├─ IP address matches ✅
     └─ ✅ Request AUTHORIZED
```

---

## 📱 Real Request/Response Examples

### 1. Login Request

```http
POST /session/login HTTP/1.1
Host: api.smartrailway.com
Content-Type: application/json
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)

{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Set-Cookie: railway_sid=SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=; 
            Path=/; HttpOnly; Secure; SameSite=Strict
Content-Type: application/json

{
  "status": "success",
  "data": {
    "user": {
      "id": "12345",
      "email": "john@example.com",
      "fullName": "John Doe",
      "role": "User"
    },
    "csrfToken": "g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg="
  }
}
```

---

### 2. Authenticated Request (Book Ticket)

```http
POST /bookings HTTP/1.1
Host: api.smartrailway.com
Content-Type: application/json
Cookie: railway_sid=SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
X-CSRF-Token: g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=

{
  "trainId": "TR001",
  "seatCount": 2,
  "totalPrice": 5000
}
```

**Response:**
```http
HTTP/1.1 201 Created
Set-Cookie: railway_sid=SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=; 
            Path=/; HttpOnly; Secure; SameSite=Strict
Content-Type: application/json

{
  "status": "success",
  "data": {
    "bookingId": "BK12345",
    "status": "Confirmed",
    "trainId": "TR001",
    "seats": [12, 13],
    "totalPrice": 5000
  }
}
```

---

### 3. Unauthorized Request (Invalid Session)

```http
GET /profile HTTP/1.1
Host: api.smartrailway.com
Cookie: railway_sid=invalid_or_expired_token
```

**Response:**
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "status": "error",
  "message": "Session expired. Please login again.",
  "code": "SESSION_INVALID"
}
```

---

### 4. CSRF Attack Prevention

```http
POST /bookings HTTP/1.1
Host: api.smartrailway.com
Content-Type: application/json
Cookie: railway_sid=valid_session_id
-- NOTE: X-CSRF-Token header MISSING (like from form submission)

{
  "trainId": "TR001",
  "seatCount": 100
}
```

**Response:**
```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "status": "error",
  "message": "CSRF token validation failed",
  "code": "CSRF_INVALID"
}
```

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  AuthPage.jsx    │         │  SessionAuthCtx  │         │
│  │  - Register      │────────▶│  - login()       │         │
│  │  - Login         │         │  - logout()      │         │
│  │  - Logout        │         │  - verify()      │         │
│  └──────────────────┘         └──────────────────┘         │
│           │                            │                    │
│           └────────────────┬───────────┘                    │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │  sessionApi.js  │                      │
│                    │  - POST /login  │                      │
│                    │  - POST /logout │                      │
│                    └────────┬────────┘                      │
└─────────────────────────────┼────────────────────────────────┘
                              │
                    HTTPS/TLS │
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                  Backend (Flask/Python)                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Request Processing Pipeline               │   │
│  │                                                     │   │
│  │  1. Extract session_id from Cookie                 │   │
│  │  2. Load session from Sessions table               │   │
│  │  3. Validate:                                      │   │
│  │     ├─ Status = "Active"                           │   │
│  │     ├─ Not expired (absolute timeout)              │   │
│  │     ├─ Not idle (inactivity timeout)               │   │
│  │     ├─ CSRF token matches (POST/PUT/DELETE)        │   │
│  │     └─ IP address matches (optional)               │   │
│  │  4. Update Last_Activity in database               │   │
│  │  5. Execute route handler                          │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐   │
│  │ login route  │    │ logout route │   │ register     │   │
│  │ - Create     │    │ - Set        │   │ - Create     │   │
│  │   user       │    │   Status=    │   │   user       │   │
│  │ - Create     │    │   'Revoked'  │   │ - Create     │   │
│  │   session    │    │ - Clear      │   │   session    │   │
│  │ - Set cookie │    │   cookie     │   │ - Set cookie │   │
│  └──────────────┘    └──────────────┘   └──────────────┘   │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
                    SQL/ZCQL │
                           │
┌──────────────────────────▼───────────────────────────────────┐
│            Zoho Catalyst CloudScale Database                │
│                                                              │
│  ┌────────────────┐    ┌───────────────┐                   │
│  │   Users        │    │   Sessions    │                   │
│  ├────────────────┤    ├───────────────┤                   │
│  │ ROWID (PK)     │    │ ROWID (PK)    │                   │
│  │ Email          │    │ User_ID (FK)  │                   │
│  │ Password_Hash  │    │ Session_ID    │                   │
│  │ Full_Name      │    │ CSRF_Token    │                   │
│  │ Role           │    │ Status        │                   │
│  │ Account_Status │    │ IP_Address    │                   │
│  │ Created_At     │    │ Last_Activity │                   │
│  │ Last_Login     │    │ Expires_At    │                   │
│  └────────────────┘    └───────────────┘                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Session ID Token Structure

**Generated:** Using `secrets.token_urlsafe(32)`

**Format:**
```
SFMyNTY.g2wBbQAAAAdkAAhyZWFkX2luZm8HYQBkAAd1c2VyX2lkYgAABXg=
├────┬──────────────────────────────────────────────────────────┤
│    │                                                          │
Prefix                        Base64-encoded content
(SFMyNTY)                     ├─ user_id
                              ├─ email
                              ├─ role
                              ├─ created_at
                              └─ (+ HMAC signature)
```

**Properties:**
- 43 characters long
- URL-safe (no special characters)
- Cryptographically random
- Includes HMAC signature (cannot be forged)
- Expires after 24 hours (configurable)

---

## 🎯 Summary: Session ID Flow

```
User Registration/Login
    ↓
System generates 43-char Session_ID (cryptographically secure)
    ↓
Session stored in database with:
  - User ID
  - Session ID
  - CSRF Token
  - Status (Active)
  - IP Address
  - User Agent
  - Timestamps (created, last_activity, expires)
    ↓
Session ID sent to browser as HttpOnly cookie
    ↓
CSRF Token sent to frontend (in localStorage)
    ↓
User makes authenticated request:
  - Browser automatically includes Session_ID cookie
  - Frontend manually includes CSRF_Token header
    ↓
Backend validates:
  - Session exists in DB ✓
  - Status is Active ✓
  - Not expired (absolute timeout) ✓
  - Not idle (inactivity timeout) ✓
  - CSRF token matches ✓
  - IP/User-Agent matches (optional) ✓
    ↓
If ALL validations pass:
  - Execute request
  - Update Last_Activity timestamp
  - Send response
    ↓
User makes another request:
  - Same validation process repeats
    ↓
User logs out:
  - Mark session Status = "Revoked"
  - Clear browser cookie
  - Clear frontend session data
```

This is the **session-based authentication system** that **replaces JWT tokens**!
