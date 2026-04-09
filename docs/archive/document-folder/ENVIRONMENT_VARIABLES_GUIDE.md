# 🔐 Complete Environment Variables Guide

## Quick Answer: Which Variables Need Generation?

| Variable | Generate? | How | Security Level |
|----------|-----------|-----|-----------------|
| `SECRET_KEY` | ✅ YES | Python: `secrets.token_hex(32)` | CRITICAL |
| `SESSION_SECRET` | ✅ YES | Python: `secrets.token_hex(64)` | CRITICAL |
| `JWT_SECRET_KEY` | ✅ YES | Python: `secrets.token_hex(64)` | CRITICAL |
| `CSRF_HEADER_NAME` | ❌ NO | Use default: `X-CSRF-Token` | LOW |
| `CATALYST_FROM_EMAIL` | ✅ YES | Set to verified email | MEDIUM |
| `ADMIN_SETUP_KEY` | ✅ YES | Create strong password | CRITICAL |

---

## 🔑 Secret Keys: Generate vs. Default

### Keys That MUST Be Generated

**`SECRET_KEY`**
- Purpose: Flask session encryption
- Must generate: YES
- Security: CRITICAL ⚠️

**`SESSION_SECRET`**
- Purpose: CSRF token signing
- Must generate: YES
- Security: CRITICAL ⚠️

**`JWT_SECRET_KEY`**
- Purpose: JWT token signing (deprecated, but still needed)
- Must generate: YES
- Security: CRITICAL ⚠️

### Keys/Values That Use Defaults (Can Override)

**`CSRF_HEADER_NAME`**
- Purpose: HTTP header name for CSRF validation
- Default: `X-CSRF-Token`
- Must generate: NO
- Can change: YES, but rarely needed

---

## 🛠️ How to Generate Secure Keys

### Method 1: Python (RECOMMENDED)

```bash
# Generate all keys at once
python3 << 'EOF'
import secrets

print("=" * 60)
print("🔐 SECURE KEY GENERATION")
print("=" * 60)

# SECRET_KEY (32 bytes = 64 hex chars)
secret_key = secrets.token_hex(32)
print(f"\nSECRET_KEY={secret_key}")

# SESSION_SECRET (64 bytes = 128 hex chars)
session_secret = secrets.token_hex(64)
print(f"\nSESSION_SECRET={session_secret}")

# JWT_SECRET_KEY (64 bytes = 128 hex chars)
jwt_secret = secrets.token_hex(64)
print(f"\nJWT_SECRET_KEY={jwt_secret}")

print("\n" + "=" * 60)
print("✅ Copy these values to your .env file")
print("=" * 60)
EOF
```

**Output:**
```
SECRET_KEY=a7f8e9d2c1b4f5g6h7i8j9k0l1m2n3o4
SESSION_SECRET=b9f8e7d6c5a4f3g2h1i0j9k8l7m6n5o4p3q2r1s0t9u8v7w6x5y4z3
JWT_SECRET_KEY=c1f0e9d8c7b6a5f4g3h2i1j0k9l8m7n6o5p4q3r2s1t0u9v8w7x6y5z4
```

### Method 2: OpenSSL (Linux/Mac)

```bash
# SECRET_KEY
openssl rand -hex 32

# SESSION_SECRET
openssl rand -hex 64

# JWT_SECRET_KEY
openssl rand -hex 64
```

### Method 3: Online Generator

⚠️ **NOT RECOMMENDED for production**

Only use for development/testing:
- https://www.random.org/bytes/ (extract hex)
- Or generate offline locally

---

## 📋 Complete Environment Variables Reference

### CRITICAL: Security Keys (Must Generate)

```env
# ══════════════════════════════════════════════════════════════════
# 🔐 CRITICAL SECURITY KEYS - GENERATE IMMEDIATELY
# ══════════════════════════════════════════════════════════════════

# Flask application secret key (64-hex chars minimum)
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<generate-with-script-above>

# Session authentication secret (128-hex chars minimum)
# Generate: python -c "import secrets; print(secrets.token_hex(64))"
SESSION_SECRET=<generate-with-script-above>

# JWT token signing secret (128-hex chars minimum)
# Generate: python -c "import secrets; print(secrets.token_hex(64))"
JWT_SECRET_KEY=<generate-with-script-above>

# Admin setup key - strong password (min 12 characters)
# Create your own: must be complex
ADMIN_SETUP_KEY=railadmin@2026
```

### Session Management

```env
# ══════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════

# Session cookie name (can customize)
SESSION_COOKIE_NAME=railway_sid

# Session timeout (hours) - when session expires
SESSION_TIMEOUT_HOURS=24

# Idle timeout (hours) - expires if inactive
SESSION_IDLE_TIMEOUT_HOURS=6

# Maximum concurrent sessions per user
MAX_CONCURRENT_SESSIONS=3

# Cookie security flags
SESSION_COOKIE_SECURE=true          # HTTPS only (false for localhost)
SESSION_COOKIE_SAMESITE=Strict      # CSRF protection

# CSRF token configuration
CSRF_TOKEN_LENGTH=32                # Bytes (not hex chars)
CSRF_HEADER_NAME=X-CSRF-Token       # HTTP header name
```

### OTP Email Configuration

```env
# ══════════════════════════════════════════════════════════════════
# OTP EMAIL VERIFICATION
# ══════════════════════════════════════════════════════════════════

# Verified sender email from Zoho Catalyst
CATALYST_FROM_EMAIL=noreply@smartrailway.com

# OTP settings
OTP_EXPIRY_MINUTES=15
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60
APP_NAME=Smart Railway
```

### Admin Configuration

```env
# ══════════════════════════════════════════════════════════════════
# ADMIN & AUTH
# ══════════════════════════════════════════════════════════════════

ADMIN_EMAIL=admin@admin.com
ADMIN_DOMAIN=admin.com
ADMIN_SETUP_KEY=railadmin@2026
```

### Flask Configuration

```env
# ══════════════════════════════════════════════════════════════════
# FLASK APPLICATION
# ══════════════════════════════════════════════════════════════════

APP_ENVIRONMENT=production          # or 'development'
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### JWT Configuration (DEPRECATED)

```env
# ══════════════════════════════════════════════════════════════════
# JWT (BEING REPLACED BY SESSION SYSTEM - Keep for migration)
# ══════════════════════════════════════════════════════════════════

JWT_EXPIRY_MINUTES=60
JWT_REFRESH_DAYS=7
```

### External Services

```env
# ══════════════════════════════════════════════════════════════════
# EXTERNAL APIS & SERVICES
# ══════════════════════════════════════════════════════════════════

GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL=gemini-2.0-flash
```

### Rate Limiting & Cache

```env
# ══════════════════════════════════════════════════════════════════
# RATE LIMITING & CACHE
# ══════════════════════════════════════════════════════════════════

RATE_LIMIT_AUTH=10                  # Failed attempts
RATE_LIMIT_WINDOW=900               # Time window (seconds)

CACHE_TTL_TRAINS=3600               # Cache duration (seconds)
CACHE_TTL_STATIONS=86400
```

---

## 📝 Step-by-Step Setup

### Step 1: Generate Security Keys

```bash
cd functions/smart_railway_app_function

python3 << 'EOF'
import secrets

# Generate keys
secret_key = secrets.token_hex(32)
session_secret = secrets.token_hex(64)
jwt_secret = secrets.token_hex(64)

print("SECRET_KEY=" + secret_key)
print("SESSION_SECRET=" + session_secret)
print("JWT_SECRET_KEY=" + jwt_secret)
EOF
```

### Step 2: Create .env File

```bash
# Copy template
cp .env.example .env

# Edit .env with your favorite editor
nano .env
# or
code .env
```

### Step 3: Paste Generated Keys

```env
# Paste the generated values:
SECRET_KEY=<paste-generated-value>
SESSION_SECRET=<paste-generated-value>
JWT_SECRET_KEY=<paste-generated-value>
ADMIN_SETUP_KEY=railadmin@2026
```

### Step 4: Configure Other Values

```env
# Email
CATALYST_FROM_EMAIL=noreply@smartrailway.com

# Session
SESSION_TIMEOUT_HOURS=24
MAX_CONCURRENT_SESSIONS=3

# Admin
ADMIN_EMAIL=admin@admin.com

# Environment
APP_ENVIRONMENT=production
```

### Step 5: Verify Configuration

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv('.env')

# Check critical keys are set
critical_keys = ['SECRET_KEY', 'SESSION_SECRET', 'JWT_SECRET_KEY']
for key in critical_keys:
    value = os.getenv(key)
    if value and len(value) > 20:
        print(f"✅ {key}: {value[:20]}... (length: {len(value)})")
    else:
        print(f"❌ {key}: NOT SET or too short")
EOF
```

---

## 🔒 Security Best Practices

### DO ✅

- ✅ Generate keys using `secrets` module (cryptographically secure)
- ✅ Use 64-hex character keys for critical functions
- ✅ Store .env file in `.gitignore` (never commit)
- ✅ Use HTTPS in production (SESSION_COOKIE_SECURE=true)
- ✅ Rotate keys periodically (every 3-6 months)
- ✅ Use different keys for dev/staging/production
- ✅ Keep .env file permissions restricted (chmod 600)

### DON'T ❌

- ❌ Hardcode secrets in source code
- ❌ Use weak/simple keys like "password123"
- ❌ Share .env file via email or chat
- ❌ Commit .env to version control
- ❌ Use same keys across environments
- ❌ Expose .env file in error messages
- ❌ Use HTTP in production (SESSION_COOKIE_SECURE=false)

---

## 🎯 Key Generation Script

Create `generate_secrets.py`:

```python
#!/usr/bin/env python3
"""
Generate secure environment variables for Smart Railway system.
Run this once and copy output to .env file.
"""

import secrets
import sys

def generate_hex_key(bytes_length: int) -> str:
    """Generate a cryptographically secure random hex key."""
    return secrets.token_hex(bytes_length)

def generate_strong_password(length: int = 16) -> str:
    """Generate a strong random password."""
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("\n" + "="*70)
    print("🔐 SMART RAILWAY - SECURE ENVIRONMENT GENERATOR")
    print("="*70 + "\n")
    
    # Generate keys
    secret_key = generate_hex_key(32)           # 64 hex chars
    session_secret = generate_hex_key(64)       # 128 hex chars
    jwt_secret = generate_hex_key(64)           # 128 hex chars
    admin_key = generate_strong_password(20)    # 20-char password
    
    # Display
    output = f"""
# ═══════════════════════════════════════════════════════════════════════════════
# 🔐 CRITICAL SECURITY KEYS - COPY TO .env FILE
# ═══════════════════════════════════════════════════════════════════════════════

# Flask secret key (for session encryption)
SECRET_KEY={secret_key}

# Session authentication secret (for CSRF token signing)
SESSION_SECRET={session_secret}

# JWT token secret (for token signing)
JWT_SECRET_KEY={jwt_secret}

# Admin setup key (for first-time admin registration)
ADMIN_SETUP_KEY={admin_key}

# ═══════════════════════════════════════════════════════════════════════════════
# ✅ Generated at: {__import__('datetime').datetime.now().isoformat()}
# ═══════════════════════════════════════════════════════════════════════════════
"""
    
    print(output)
    print("\n📋 INSTRUCTIONS:")
    print("1. Copy all values above")
    print("2. Open: functions/smart_railway_app_function/.env")
    print("3. Replace placeholder values with values above")
    print("4. Save file")
    print("5. Never share these keys!")
    print("\n")

if __name__ == '__main__':
    main()
```

**Usage:**
```bash
python generate_secrets.py
```

---

## 📊 Variable Dependency Map

```
.env (Environment Variables)
  │
  ├─ SECRET_KEY
  │  └─ Used by: Flask application
  │     Purpose: Session encryption
  │     Generated: YES (64 hex)
  │
  ├─ SESSION_SECRET
  │  └─ Used by: CSRF token signing
  │     Purpose: CSRF protection
  │     Generated: YES (128 hex)
  │
  ├─ JWT_SECRET_KEY
  │  └─ Used by: JWT token creation (deprecated)
  │     Purpose: Token signing
  │     Generated: YES (128 hex)
  │
  ├─ CSRF_HEADER_NAME
  │  └─ Used by: Request validation
  │     Default: X-CSRF-Token
  │     Generated: NO
  │
  ├─ SESSION_COOKIE_NAME
  │  └─ Used by: Browser cookies
  │     Default: railway_sid
  │     Generated: NO
  │
  ├─ CATALYST_FROM_EMAIL
  │  └─ Used by: Email service
  │     Purpose: OTP email sender
  │     Generated: YES (verified email)
  │
  └─ ADMIN_SETUP_KEY
     └─ Used by: Admin registration
        Purpose: First-time setup verification
        Generated: YES (strong password)
```

---

## ✅ Verification Checklist

Before starting the application:

```bash
# Check all critical keys are set
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv('.env')

critical = {
    'SECRET_KEY': 64,
    'SESSION_SECRET': 128,
    'JWT_SECRET_KEY': 128,
    'CATALYST_FROM_EMAIL': 5,
    'ADMIN_SETUP_KEY': 8,
}

print("🔍 Environment Variable Verification\n")

all_good = True
for key, min_len in critical.items():
    value = os.getenv(key)
    if value and len(str(value)) >= min_len:
        status = "✅"
    else:
        status = "❌"
        all_good = False
    
    print(f"{status} {key:25} {len(str(value)) if value else 0:3} chars")

if all_good:
    print("\n✅ All critical variables set correctly!")
else:
    print("\n❌ Some variables missing or too short")
    
EOF
```

---

## 🔄 Key Rotation Guide

For production, rotate keys periodically:

### Plan:
1. Generate new keys
2. Update staging environment
3. Test thoroughly
4. Update production
5. Update all dependent services

### Script:
```bash
# Generate new keys
python generate_secrets.py > new_keys.txt

# Backup old .env
cp .env .env.backup.$(date +%Y%m%d)

# Update with new keys
# (manually or with sed)
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=<new-value>/" .env

# Restart application
systemctl restart railway-app
```

---

## 📚 Related Documentation

- [`SESSION_ARCHITECTURE_GUIDE.md`](./SESSION_ARCHITECTURE_GUIDE.md) - How session IDs work
- [`QUICK_SETUP_OTP.md`](./QUICK_SETUP_OTP.md) - OTP configuration
- `functions/smart_railway_app_function/.env.example` - Template file
- `functions/smart_railway_app_function/.env` - Your configuration

---

## 🆘 Troubleshooting

### "KeyError: SECRET_KEY"
**Cause:** Variable not in .env
**Fix:** Add SECRET_KEY to .env file

### "Invalid secret key length"
**Cause:** Key too short
**Fix:** Regenerate with 64+ hex characters

### "CSRF token invalid"
**Cause:** SESSION_SECRET changed after session created
**Fix:** Clear all sessions or don't change key on live system

### "Email sending failed"
**Cause:** CATALYST_FROM_EMAIL not verified
**Fix:** Check email verified in Zoho Catalyst Console

