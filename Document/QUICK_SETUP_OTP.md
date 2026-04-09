# ⚡ QUICK SETUP CHECKLIST - OTP Email Verification

## What You Need to Do (3 Simple Steps)

### Step 1: Setup Verified Email in Zoho Catalyst ✉️
```
Catalyst Console 
  → Your Project
  → Email Service
  → Verified Senders
  → Add Sender
  → Enter: noreply@smartrailway.com (or your domain)
  → Click verification link in email
  → Done! Email is verified ✅
```

### Step 2: Configure Environment Variables 🔑
```bash
# Already created: functions/smart_railway_app_function/.env

# Edit this file and set:
CATALYST_FROM_EMAIL=noreply@smartrailway.com  # Match verified email
OTP_EXPIRY_MINUTES=15
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60
APP_NAME=Smart Railway
```

### Step 3: Verify Setup ✅
```bash
# Test that backend can send emails
cd functions/smart_railway_app_function

python -c "
from services.otp_service import send_registration_otp
result = send_registration_otp('your-email@example.com')
print('Result:', result)
"
```

Expected output:
```
Result: {'success': True, 'message': '...', 'expiresInMinutes': 15}
```

---

## Where Are The Files?

| File | Purpose | Location |
|------|---------|----------|
| Configuration | Environment variables | `functions/smart_railway_app_function/.env` |
| Template | Variable reference | `functions/smart_railway_app_function/.env.example` |
| OTP Service | Email sending logic | `functions/smart_railway_app_function/services/otp_service.py` |
| Routes | API endpoints | `functions/smart_railway_app_function/routes/otp_register.py` |
| Setup Guide | Full instructions | `functions/smart_railway_app_function/docs/CATALYST_EMAIL_SETUP.md` |

---

## CATALYST_FROM_EMAIL Explained

### What is it?
The email address that OTP emails will come FROM.

### Where to get it?
1. Login to Zoho Catalyst Console
2. Go to **Email Service** → **Verified Senders**
3. Click **Add Sender**
4. Enter any email you own (e.g., `noreply@example.com`)
5. Verify the email (click link in verification email)
6. Copy that email address

### Where to put it?
File: `functions/smart_railway_app_function/.env`

```env
CATALYST_FROM_EMAIL=noreply@smartrailway.com
```

### ⚠️ IMPORTANT
- **Must match** a verified sender email in Catalyst
- If it doesn't match, emails will fail silently
- Can verify multiple emails and use any of them
- Double-check spelling!

---

## How Email Verification Works

```
User registers
    ↓
Backend validates form
    ↓
Generates OTP: 847291
    ↓
Stores in database
    ↓
Sends via Zoho Catalyst Email (from CATALYST_FROM_EMAIL)
    ↓
Beautiful HTML email reaches user
    ↓
User enters 6-digit code
    ↓
Backend verifies code
    ↓
Account created ✅
```

---

## OTP Email Template

Users will receive:
```
┌────────────────────────────────────┐
│         🚂 Smart Railway           │
│                                    │
│   Verify Your Email                │
│                                    │
│   Welcome to Smart Railway!        │
│   Use the code below to complete   │
│   your registration.               │
│                                    │
│ ┌──────────────────────────────┐   │
│ │   Your Verification Code:    │   │
│ │          847291              │   │
│ └──────────────────────────────┘   │
│                                    │
│   ⏱️  This code expires in        │
│      15 minutes                    │
│                                    │
│   If you didn't request this,      │
│   you can safely ignore it.        │
│                                    │
│   © 2026 Smart Railway             │
└────────────────────────────────────┘
```

---

## Environment Variables Summary

```bash
# CRITICAL - Must set before using OTP
CATALYST_FROM_EMAIL=noreply@smartrailway.com

# Optional - Customize behavior
OTP_EXPIRY_MINUTES=15              # How long OTP is valid
OTP_MAX_ATTEMPTS=3                 # Failed attempts before lockout
OTP_RESEND_COOLDOWN_SECONDS=60     # Wait between resends
APP_NAME=Smart Railway             # Company name in emails
```

---

## Testing the Full Flow

### Backend Test
```bash
python -c "
from services.otp_service import send_registration_otp
result = send_registration_otp('test@example.com')
print(result)
"
```

### Frontend Test
1. `npm start` in `railway-app/`
2. Go to http://localhost:3000/app
3. Click **Register**
4. Fill in form
5. Submit → OTP screen appears
6. Check email for code
7. Enter code → Account created!

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Emails not sent | Check `CATALYST_FROM_EMAIL` is verified in Catalyst |
| "No verified senders" | Add & verify email in Catalyst Console |
| OTP expired | Increase `OTP_EXPIRY_MINUTES` in .env |
| Can't resend | Wait for `OTP_RESEND_COOLDOWN_SECONDS` |
| Catalyst SDK error | Run `pip install zcatalyst-sdk` |

---

## Security Checklist

- ✅ OTP uses cryptographically secure random (secrets module)
- ✅ 6-digit code with 15-minute expiry
- ✅ Max 3 attempts before lockout
- ✅ Constant-time comparison (no timing attacks)
- ✅ Password hashed only after OTP verified
- ✅ HttpOnly cookies (not accessible to JavaScript)
- ✅ CSRF tokens on all state-changing requests
- ✅ Rate limiting on OTP endpoints

