# 🔧 Complete Environment Setup Guide for OTP Email Verification

## 📍 WHERE TO SETUP CATALYST_FROM_EMAIL

### Location 1: Zoho Catalyst Console (Browser)
```
https://catalyst.zoho.com/
  ├─ Your Project
  ├─ Infrastructure
  │  └─ Email
  │     └─ Verified Senders  ← Click here
  │        ├─ Add Sender
  │        └─ Verify Email
  └─ Use that email below ↓
```

### Location 2: .env File (Backend)
```
functions/smart_railway_app_function/.env
```

---

## 🚀 Step-by-Step Setup

### Phase 1: Zoho Catalyst Console Setup

#### 1.1 Login to Catalyst
```
1. Open: https://catalyst.zoho.com/
2. Login with your Zoho account
3. Select your Smart Railway project
```

#### 1.2 Navigate to Email Service
```
Left Sidebar:
  Infrastructure
    └─ Email
       └─ Verified Senders ← Click here
```

#### 1.3 Add a Sender Email
```
Button: "+ Add Sender"
  Input: noreply@smartrailway.com (or your domain)
  Click: "Add"
  
Catalyst sends verification email to that address
```

#### 1.4 Verify the Email
```
1. Check your email inbox (noreply@smartrailway.com)
2. Open Catalyst verification email
3. Click "Verify Email" link
4. Email is now verified in Catalyst ✅
```

#### 1.5 Copy the Verified Email
```
Example:
  noreply@smartrailway.com  ← Copy this
```

---

### Phase 2: Backend Environment Configuration

#### 2.1 Open .env File
```bash
File: functions/smart_railway_app_function/.env

Location on disk:
  F:\New Railway Project\functions\smart_railway_app_function\.env
```

#### 2.2 Set CATALYST_FROM_EMAIL
```env
# Copy the verified email from Catalyst Console
CATALYST_FROM_EMAIL=noreply@smartrailway.com
```

**⚠️ CRITICAL:** Must match exactly what you verified in Catalyst!

#### 2.3 Configure OTP Settings
```env
# How long the OTP code is valid (minutes)
OTP_EXPIRY_MINUTES=15

# How many times user can try wrong code
OTP_MAX_ATTEMPTS=3

# Minimum seconds between resend requests
OTP_RESEND_COOLDOWN_SECONDS=60

# Your app name in emails
APP_NAME=Smart Railway
```

#### 2.4 Configure Other Settings
```env
# Session management
SESSION_SECRET=<generate: python -c "import secrets; print(secrets.token_hex(64))">
SESSION_TIMEOUT_HOURS=24
SESSION_COOKIE_SECURE=true

# Admin setup
ADMIN_SETUP_KEY=railadmin@2026
ADMIN_EMAIL=admin@admin.com
```

---

### Phase 3: Verify Everything Works

#### 3.1 Test Email Sending
```bash
cd "F:\New Railway Project\functions\smart_railway_app_function"

python -c "
from services.otp_service import send_registration_otp
result = send_registration_otp('your-test-email@example.com')
print('Email sent:', result)
"
```

Expected output:
```
Email sent: {'success': True, 'message': 'Verification code sent to your email', 'expiresInMinutes': 15}
```

#### 3.2 Test Full Registration Flow
```bash
# Terminal 1: Start Backend
cd functions/smart_railway_app_function
python app.py

# Terminal 2: Start Frontend
cd railway-app
npm start
```

Then:
1. Open http://localhost:3000/app
2. Click **Register**
3. Fill registration form
4. Submit
5. Check email for OTP code
6. Enter code in browser
7. Account created! ✅

---

## 📋 Complete .env Configuration Template

```env
# ═══════════════════════════════════════════════════════════════
#  Smart Railway - Environment Configuration
#  🚨 DO NOT COMMIT THIS FILE TO GIT
# ═══════════════════════════════════════════════════════════════

# ══ OTP EMAIL VERIFICATION (MOST IMPORTANT) ════════════════════
CATALYST_FROM_EMAIL=noreply@smartrailway.com
OTP_EXPIRY_MINUTES=15
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60
APP_NAME=Smart Railway

# ══ SESSION MANAGEMENT ═════════════════════════════════════════
SESSION_SECRET=<64-character-random-string>
SESSION_TIMEOUT_HOURS=24
SESSION_IDLE_TIMEOUT_HOURS=6
MAX_CONCURRENT_SESSIONS=3
SESSION_COOKIE_NAME=railway_sid
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Strict
CSRF_TOKEN_LENGTH=32
CSRF_HEADER_NAME=X-CSRF-Token

# ══ ADMIN SETUP ════════════════════════════════════════════════
ADMIN_EMAIL=admin@admin.com
ADMIN_DOMAIN=admin.com
ADMIN_SETUP_KEY=railadmin@2026

# ══ FLASK / APP SETTINGS ═══════════════════════════════════════
APP_ENVIRONMENT=production
SECRET_KEY=<random-secret-key>
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com

# ══ JWT (DEPRECATED, BEING REPLACED) ═══════════════════════════
JWT_SECRET_KEY=<old-jwt-secret>
JWT_EXPIRY_MINUTES=60
JWT_REFRESH_DAYS=7

# ══ AI APIS ════════════════════════════════════════════════════
GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL=gemini-2.0-flash

# ══ RATE LIMITING ══════════════════════════════════════════════
RATE_LIMIT_AUTH=10
RATE_LIMIT_WINDOW=900

# ══ CACHE SETTINGS ═════════════════════════════════════════════
CACHE_TTL_TRAINS=3600
CACHE_TTL_STATIONS=86400
```

---

## 🔍 Verification Checklist

Before testing, verify:

- [ ] Email verified in Zoho Catalyst Console (Verified Senders)
- [ ] `.env` file exists at `functions/smart_railway_app_function/.env`
- [ ] `CATALYST_FROM_EMAIL` in `.env` matches verified email in Catalyst
- [ ] `SESSION_SECRET` is at least 64 characters
- [ ] All other required variables are set
- [ ] `.env` is in `.gitignore` (not committed)

---

## 🐛 Troubleshooting

### ❌ Problem: "Email sending failed"

**Solution 1: Check email is verified**
```
Catalyst Console
  → Email Service
  → Verified Senders
  → Verify that your email is listed here ✅
```

**Solution 2: Check .env configuration**
```env
# Must match verified email EXACTLY
CATALYST_FROM_EMAIL=noreply@smartrailway.com
```

**Solution 3: Check Python SDK installed**
```bash
pip list | grep zcatalyst
# Should show: zcatalyst-sdk

# If not installed:
pip install zcatalyst-sdk
```

### ❌ Problem: "Catalyst SDK not available"

**Solution:**
```bash
# Install the SDK
pip install zcatalyst-sdk

# Verify
python -c "import zcatalyst_sdk; print('OK')"
```

If unavailable, service falls back to logging (dev mode):
```
[DEV] OTP for user@example.com: 123456
```

### ❌ Problem: OTP expires too quickly

**Solution:** Increase expiry time
```env
# In .env file:
OTP_EXPIRY_MINUTES=30
```

### ❌ Problem: "Can't resend OTP - too soon"

**Expected behavior** - by design!

**Solution:** Wait 60 seconds (or adjust):
```env
# Minimum seconds between resends
OTP_RESEND_COOLDOWN_SECONDS=30
```

---

## 📁 File Structure

```
F:\New Railway Project\
├─ functions/smart_railway_app_function/
│  ├─ .env                          ← ADD YOUR CONFIG HERE
│  ├─ .env.example                  ← Template reference
│  ├─ app.py                        ← Flask app
│  ├─ config.py                     ← Python config
│  ├─ services/
│  │  └─ otp_service.py             ← OTP generation & email
│  ├─ routes/
│  │  └─ otp_register.py            ← Registration endpoints
│  └─ docs/
│     └─ CATALYST_EMAIL_SETUP.md    ← Full email setup guide
│
├─ railway-app/
│  ├─ src/
│  │  ├─ context/
│  │  │  └─ SessionAuthContext.jsx  ← Auth context
│  │  ├─ components/
│  │  │  └─ OTPVerification.jsx     ← OTP UI
│  │  └─ pages/auth/
│  │     └─ AuthPage.jsx            ← Registration page
│  └─ package.json
│
├─ QUICK_SETUP_OTP.md               ← Quick setup checklist
└─ ENVIRONMENT_SETUP_GUIDE.md       ← This file
```

---

## 🔐 Security Reminders

✅ **Good practices:**
- Use a separate email for noreply (e.g., `noreply@yourdomain.com`)
- Never use personal email as FROM address
- Keep SESSION_SECRET secure (generate random)
- Don't share .env file
- Add .env to .gitignore

❌ **Don't do:**
- Don't hardcode secrets in code
- Don't use same email for multiple apps
- Don't commit .env to version control
- Don't share ADMIN_SETUP_KEY

---

## 📞 Quick Reference

| What | Where |
|------|-------|
| Verify email | Zoho Catalyst Console → Email Service → Verified Senders |
| Set CATALYST_FROM_EMAIL | `functions/smart_railway_app_function/.env` |
| OTP service code | `functions/smart_railway_app_function/services/otp_service.py` |
| Registration routes | `functions/smart_railway_app_function/routes/otp_register.py` |
| Frontend auth context | `railway-app/src/context/SessionAuthContext.jsx` |
| Full email guide | `functions/smart_railway_app_function/docs/CATALYST_EMAIL_SETUP.md` |

