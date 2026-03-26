# Users Module - Complete Reference

## Overview

This module handles all user-related functionality:
- User registration and authentication
- Argon2 password hashing
- JWT session tokens (access + refresh)
- Profile management
- Password reset flow
- Account lockout protection
- Admin user management

---

## Folder Structure

```
modules/users/
├── __init__.py          # Module exports
├── models.py            # CloudScale schema & data classes
├── repository.py        # Database operations (ZCQL)
├── services.py          # Business logic (Argon2, JWT)
├── routes.py            # API endpoints
└── README.md            # This file
```

---

## CloudScale Table: Users

### Schema Definition

```sql
CREATE TABLE Users (
    ROWID               BIGINT PRIMARY KEY AUTO_INCREMENT,

    -- Core Fields
    Email               VARCHAR(255) UNIQUE NOT NULL,
    Password_Hash       VARCHAR(255) NOT NULL,
    Full_Name           VARCHAR(255) NOT NULL,
    Phone               VARCHAR(20),
    Role                VARCHAR(20) DEFAULT 'user',
    Status              VARCHAR(30) DEFAULT 'active',

    -- Verification
    Is_Email_Verified   BOOLEAN DEFAULT false,
    Is_Phone_Verified   BOOLEAN DEFAULT false,
    Is_Aadhar_Verified  BOOLEAN DEFAULT false,
    Aadhar_Number       VARCHAR(20),

    -- Profile
    Date_Of_Birth       DATE,
    Gender              VARCHAR(10),
    Address             TEXT,
    City                VARCHAR(100),
    State               VARCHAR(100),
    Pincode             VARCHAR(10),

    -- Session & Security
    Session_Token       VARCHAR(500),
    Token_Expires_At    DATETIME,
    Refresh_Token       VARCHAR(500),
    Refresh_Expires_At  DATETIME,
    Last_Login_At       DATETIME,
    Last_Login_IP       VARCHAR(50),
    Failed_Login_Count  INT DEFAULT 0,
    Locked_Until        DATETIME,

    -- Password Reset
    Reset_Token         VARCHAR(255),
    Reset_Token_Expires DATETIME,

    -- Booking Limits
    Monthly_Booking_Count   INT DEFAULT 0,
    Booking_Count_Reset_At  DATE,

    -- Timestamps
    Created_At          DATETIME DEFAULT CURRENT_TIMESTAMP,
    Updated_At          DATETIME
);
```

### Field Description

| Field | Type | Description |
|-------|------|-------------|
| `ROWID` | BIGINT | Primary key (auto) |
| `Email` | VARCHAR(255) | Unique email (lowercase) |
| `Password_Hash` | VARCHAR(255) | Argon2id hash |
| `Full_Name` | VARCHAR(255) | User's full name |
| `Phone` | VARCHAR(20) | Phone number |
| `Role` | VARCHAR(20) | user / admin / super_admin |
| `Status` | VARCHAR(30) | active / inactive / suspended |
| `Session_Token` | VARCHAR(500) | Current JWT access token |
| `Refresh_Token` | VARCHAR(500) | Current JWT refresh token |
| `Failed_Login_Count` | INT | Failed login attempts |
| `Locked_Until` | DATETIME | Account lockout timestamp |

---

## User Flow Diagrams

### 1. Registration Flow

```
┌─────────┐      POST /api/auth/register       ┌─────────────┐
│  Client │ ──────────────────────────────────>│   Routes    │
└─────────┘   { email, password, full_name }   └──────┬──────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │  Services   │
                                               │─────────────│
                                               │ 1. Validate │
                                               │ 2. Check dup│
                                               │ 3. Hash pwd │◄── Argon2id
                                               │ 4. Create   │
                                               │ 5. Gen token│◄── JWT
                                               └──────┬──────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │ Repository  │
                                               │─────────────│
                                               │ INSERT INTO │
                                               │   Users     │
                                               └──────┬──────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │ CloudScale  │
                                               │   (Users)   │
                                               └─────────────┘

Response:
{
  "success": true,
  "user": { id, email, full_name, role, ... },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600
}
```

### 2. Login Flow

```
┌─────────┐        POST /api/auth/login        ┌─────────────┐
│  Client │ ──────────────────────────────────>│   Routes    │
└─────────┘      { email, password }           └──────┬──────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │  Services   │
                                               └──────┬──────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
            ┌───────────────┐               ┌───────────────┐               ┌───────────────┐
            │ Check Account │               │Verify Password│               │ Generate Token│
            │    Status     │               │   (Argon2)    │               │    (JWT)      │
            └───────────────┘               └───────────────┘               └───────────────┘
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
            ┌───────────────┐               ┌───────────────┐               ┌───────────────┐
            │ - Is Active?  │               │ Hash Match?   │               │ Access Token  │
            │ - Is Locked?  │               │ - Yes: OK     │               │ (1hr expiry)  │
            │ - Failed cnt? │               │ - No: +1 fail │               │               │
            └───────────────┘               └───────────────┘               │ Refresh Token │
                                                                            │ (7day expiry) │
                                                                            └───────────────┘

Account Lockout:
- 5 failed attempts → Lock for 30 minutes
- Stored in: Failed_Login_Count, Locked_Until
```

### 3. Token Refresh Flow

```
┌─────────┐       POST /api/auth/refresh       ┌─────────────┐
│  Client │ ──────────────────────────────────>│   Routes    │
└─────────┘     { refresh_token }              └──────┬──────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │  Services   │
                                               │─────────────│
                                               │ 1. Verify   │
                                               │    refresh  │
                                               │    token    │
                                               │             │
                                               │ 2. Check DB │
                                               │    match    │
                                               │             │
                                               │ 3. Generate │
                                               │    new pair │
                                               └──────┬──────┘
                                                      │
                                                      ▼
Response:
{
  "success": true,
  "access_token": "new_eyJ...",   ◄── New tokens
  "refresh_token": "new_eyJ...",
  "expires_in": 3600
}
```

### 4. Password Reset Flow

```
Step 1: Request Reset
─────────────────────
Client → POST /api/auth/password/reset { email }
       → Generate reset_token (32 bytes, URL-safe)
       → Store in: Reset_Token, Reset_Token_Expires (1 hour)
       → Send email with reset link (TODO)
       → Response: "If email exists, you'll receive a link"


Step 2: Confirm Reset
─────────────────────
Client → POST /api/auth/password/reset/confirm
         { token, new_password, confirm_password }
       → Find user by Reset_Token (if not expired)
       → Hash new password with Argon2
       → Update Password_Hash
       → Clear Reset_Token
       → Response: "Password reset successful"
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login & get tokens |
| POST | `/api/auth/logout` | Yes | Logout & invalidate tokens |
| POST | `/api/auth/refresh` | No | Refresh access token |
| GET | `/api/auth/validate` | Yes | Validate token |

### Password

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/password/change` | Yes | Change password |
| POST | `/api/auth/password/reset` | No | Request reset email |
| POST | `/api/auth/password/reset/confirm` | No | Reset with token |

### Profile

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/users/me` | Yes | Get my profile |
| PUT | `/api/users/me` | Yes | Update my profile |

### Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/users` | Admin | List all users |
| GET | `/api/users/{id}` | Admin | Get user by ID |
| PUT | `/api/users/{id}/role` | Admin | Change user role |
| PUT | `/api/users/{id}/status` | Admin | Change user status |

---

## Password Hashing (Argon2)

### Why Argon2?
- Winner of Password Hashing Competition (2015)
- Resistant to GPU/ASIC attacks
- Memory-hard (prevents parallel attacks)
- Configurable parameters

### Configuration
```python
PasswordHasher(
    time_cost=3,       # Iterations
    memory_cost=65536, # 64 MB memory
    parallelism=4,     # 4 threads
    hash_len=32,       # 32 byte hash
    salt_len=16,       # 16 byte salt
)
```

### Hash Format
```
$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>
```

### Fallback (if argon2 unavailable)
```python
# SHA-256 with salt (not recommended)
sha256${salt}${hash}
```

---

## JWT Token Structure

### Access Token Payload
```json
{
  "sub": "123",           // User ID
  "email": "user@example.com",
  "role": "user",
  "type": "access",
  "iat": 1711353600,      // Issued at
  "exp": 1711357200       // Expires (1 hour)
}
```

### Refresh Token Payload
```json
{
  "sub": "123",           // User ID
  "type": "refresh",
  "jti": "unique_id",     // Token ID (for revocation)
  "iat": 1711353600,
  "exp": 1711958400       // Expires (7 days)
}
```

### Token Storage (CloudScale)
```
Session_Token      → Current access token
Token_Expires_At   → Access token expiry
Refresh_Token      → Current refresh token
Refresh_Expires_At → Refresh token expiry
```

---

## Security Features

### 1. Account Lockout
```python
LOCKOUT_SETTINGS = {
    'max_failed_attempts': 5,
    'lockout_duration_minutes': 30,
}
```

### 2. Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- Maximum 128 characters

### 3. Token Revocation
- Tokens stored in DB
- Logout clears tokens
- Password change invalidates all sessions

### 4. Rate Limiting
- Failed login tracking
- Auto-lock after 5 attempts
- IP logging for audit

---

## Usage Examples

### Register a User
```python
from modules.users import user_service, UserCreate

user_data = UserCreate(
    email="john@example.com",
    password="SecurePass123",
    full_name="John Doe",
    phone="9876543210"
)

result = user_service.register(user_data)
# Returns: { success, user, access_token, refresh_token }
```

### Login
```python
from modules.users import user_service, UserLogin

login_data = UserLogin(
    email="john@example.com",
    password="SecurePass123"
)

result = user_service.login(login_data, ip_address="192.168.1.1")
# Returns: { success, user, access_token, refresh_token }
```

### Validate Token
```python
from modules.users import user_service

user_info = user_service.validate_token(access_token)
# Returns: { valid, user_id, email, role }
```

### Use in Flask App
```python
# app.py
from flask import Flask
from modules.users import users_bp

app = Flask(__name__)
app.register_blueprint(users_bp)
```

### Protect Routes
```python
from modules.users import require_auth, require_admin

@app.route('/api/protected')
@require_auth
def protected_route():
    user_id = g.current_user['user_id']
    return {'message': f'Hello user {user_id}'}

@app.route('/api/admin-only')
@require_auth
@require_admin
def admin_route():
    return {'message': 'Admin access granted'}
```

---

## Dependencies

```txt
# requirements.txt
argon2-cffi>=21.3.0    # Argon2 password hashing
PyJWT>=2.8.0           # JWT tokens
zcatalyst-sdk>=0.0.2   # CloudScale database
```

---

## Configuration

```python
# Environment variables
JWT_SECRET_KEY=your-256-bit-secret-key-change-in-production
```

---

*Module Version: 1.0*
*Created: 2026-03-25*
