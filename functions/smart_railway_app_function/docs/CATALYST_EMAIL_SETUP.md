# Zoho Catalyst Email Setup for OTP Verification

## 📋 Overview

OTP (One-Time Password) verification for registration requires sending emails through Zoho Catalyst Email Service. This guide explains how to set it up.

---

## 🔧 Step 1: Setup in Zoho Catalyst Console

### 1.1 Navigate to Email Service

```
Catalyst Console
  ├─ Your Project
  ├─ Email Service
  └─ Verified Senders ← Click here
```

### 1.2 Add & Verify Email Address

**Important:** Catalyst only allows sending from verified email addresses.

1. Click **+ Add Sender**
2. Enter email address you want to send from (e.g., `noreply@smartrailway.com`)
3. Catalyst sends verification email to that address
4. **Click verification link** in the email
5. Email is now verified ✅

> **⚠️ Note:** You can use:
> - `noreply@yourdomain.com` (requires domain ownership)
> - `support@yourdomain.com`
> - Or any email you have access to

---

## 🔑 Step 2: Environment Variables

### 2.1 Create .env File

In your backend directory:
```bash
functions/smart_railway_app_function/
```

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2.2 Configure Catalyst Email

Edit `.env` and set the verified sender email:

```env
# ══ OTP EMAIL VERIFICATION ════════════════════════════════════════
# The verified sender email from Zoho Catalyst Console
CATALYST_FROM_EMAIL=noreply@smartrailway.com

# OTP validity period (minutes)
OTP_EXPIRY_MINUTES=15

# Maximum verification attempts before OTP invalidated
OTP_MAX_ATTEMPTS=3

# Cooldown between resend requests (seconds)
OTP_RESEND_COOLDOWN_SECONDS=60

# App name displayed in email templates
APP_NAME=Smart Railway
```

### 2.3 Other Required Variables

Ensure these are also configured:

```env
# Session management
SESSION_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(64))">
SESSION_TIMEOUT_HOURS=24
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Strict

# Admin setup
ADMIN_SETUP_KEY=railadmin@2026
ADMIN_EMAIL=admin@admin.com
```

---

## 📧 Step 3: Email Templates

The OTP service automatically generates professional HTML emails for:

### Registration OTP Email
```
┌─────────────────────────────────┐
│      🚂 Smart Railway           │
│                                 │
│   Verify Your Email             │
│                                 │
│   ┌─────────────────────────┐   │
│   │   Your Code: 847291     │   │
│   └─────────────────────────┘   │
│                                 │
│   ⏱️  Expires in 15 minutes     │
│                                 │
│   If you didn't sign up,        │
│   ignore this email.            │
└─────────────────────────────────┘
```

Generated from `otp_service.py`:
- `_build_registration_email()`
- `_build_password_reset_email()`
- `_build_generic_otp_email()`

---

## 🧪 Step 4: Testing

### 4.1 Test Email Sending (Backend)

```bash
cd functions/smart_railway_app_function

# Test that email can be sent
python -c "
from services.otp_service import send_registration_otp
result = send_registration_otp('your-test-email@example.com')
print('Email sent:', result)
"
```

### 4.2 Test Registration Flow (Frontend)

1. Start the React app: `npm start`
2. Go to `http://localhost:3000/app`
3. Click **Register**
4. Fill registration form
5. Click **Register** button
6. You should see OTP verification screen
7. Check your email for the 6-digit code
8. Enter code and verify

### 4.3 Debug Output

If development mode (Catalyst SDK not available):
```
[DEV] OTP for user@example.com: 123456
```

Logs will show in backend console.

---

## 🔍 Environment Variable Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `CATALYST_FROM_EMAIL` | `noreply@smartrailway.com` | Verified sender email address |
| `OTP_EXPIRY_MINUTES` | `15` | How long OTP is valid (minutes) |
| `OTP_MAX_ATTEMPTS` | `3` | Max verification attempts before invalidation |
| `OTP_RESEND_COOLDOWN_SECONDS` | `60` | Minimum seconds between resend requests |
| `APP_NAME` | `Smart Railway` | App name in email templates |

---

## 🐛 Troubleshooting

### Problem: "Catalyst SDK not available"

**Cause:** SDK not installed in Python environment

**Solution:**
```bash
pip install zcatalyst-sdk
```

If SDK unavailable, OTP service logs to console (dev mode):
```
[DEV] OTP for user@example.com: 123456
```

### Problem: "Failed to send email"

**Cause 1:** Email not verified in Catalyst
- Check Catalyst Console → Email Service → Verified Senders
- Verify the email address you're using

**Cause 2:** Wrong CATALYST_FROM_EMAIL
- Verify the email in .env matches verified sender in Catalyst
- **Must match exactly**

**Cause 3:** Catalyst service down
- Check Zoho status: https://status.zoho.com
- Try resending after a few minutes

### Problem: OTP expires too quickly

**Solution:** Increase `OTP_EXPIRY_MINUTES` in .env:
```env
OTP_EXPIRY_MINUTES=30
```

### Problem: User can't resend OTP

**Issue:** Cooldown still active

**Cause:** Less than 60 seconds since last resend

**Solution:** Wait or decrease `OTP_RESEND_COOLDOWN_SECONDS`:
```env
OTP_RESEND_COOLDOWN_SECONDS=30
```

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `services/otp_service.py` | OTP generation, email sending, verification |
| `routes/otp_register.py` | Registration endpoints (initiate, verify, resend) |
| `context/SessionAuthContext.jsx` | Frontend auth context with OTP methods |
| `components/OTPVerification.jsx` | OTP input UI component |
| `.env.example` | Environment variable template |

---

## 🔒 Security Notes

✅ **Good practices implemented:**
- 6-digit cryptographically secure OTP (via `secrets` module)
- 15-minute expiration by default
- Max 3 verification attempts
- 60-second resend cooldown
- Constant-time OTP comparison (prevents timing attacks)
- HttpOnly session cookies (not accessible to JavaScript)
- CSRF protection on all state-changing requests

⚠️ **Remember:**
- Never commit `.env` to version control
- Don't hardcode email addresses or secrets
- Use HTTPS in production (`SESSION_COOKIE_SECURE=true`)
- Verify email addresses in Catalyst before using

---

## 📞 Support

If email sending fails:
1. Check `.env` configuration
2. Verify email in Zoho Catalyst Console
3. Check backend logs for error messages
4. Test with `send_registration_otp()` function

