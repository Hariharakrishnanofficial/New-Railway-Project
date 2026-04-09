# 🔧 Quick Fix: CORS and Email Configuration

**Date:** April 2, 2026  
**Issues:** CORS blocked, Email sending failed

---

## Issue 1: CORS Blocked ❌

### Error
```
CORS: Blocked origin: https://smart-railway-app-60066581545.development.catalystserverless.in
```

### Root Cause
Your deployed frontend URL is not in the CORS allowed origins list.

### ✅ Fixed
Added deployed domain to `.env`:
```bash
CORS_ALLOWED_ORIGINS=...,https://smart-railway-app-60066581545.development.catalystserverless.in
```

### Verify Fix
1. Restart server: `catalyst serve`
2. Check logs for: `CORS: Allowed origins: [... includes your domain ...]`

---

## Issue 2: Email Configuration Missing ❌

### Error
```
Failed to send OTP email: {
  'code': 'INVALID_ID', 
  'message': 'No such from_email with the given id exists', 
  'status_code': 404
}
```

### Root Cause
The email sender is not configured in Zoho Catalyst Console.

### ✅ How to Fix

#### Step 1: Configure Email Sender in Catalyst Console

1. **Go to Catalyst Console**
   - Navigate to: https://catalyst.zoho.com/console
   - Select your project: "Smart Railway App"

2. **Configure Email**
   - Go to: **Integrations → Email**
   - Click: **Add Email**
   - Configure:
     - **From Email:** Your verified email (e.g., noreply@yourdomain.com)
     - **From Name:** Smart Railway Ticketing
     - **Verify** the email address

3. **Get Email ID**
   - After creating, note the **Email ID** (looks like: 31207000000XXXXX)
   - Or use the email address directly

#### Step 2: Update Environment Variable

**Option A: Use Email ID (Recommended)**

Add to `.env`:
```bash
CATALYST_FROM_EMAIL_ID=31207000000XXXXX  # Your email ID from console
```

Update `services/email_service.py` to use:
```python
from_email = os.getenv('CATALYST_FROM_EMAIL_ID')
```

**Option B: Use Email Address**

The code currently uses email address. Make sure it matches exactly what's in Catalyst Console:
```bash
CATALYST_FROM_EMAIL=your-verified-email@domain.com
```

#### Step 3: Verify Email is Verified

In Catalyst Console:
- Email status should be: ✅ **Verified**
- If not verified, check your email for verification link

---

## Quick Fix Steps

### 1. Add Deployed Domain to CORS

```bash
# Already done - added to .env
CORS_ALLOWED_ORIGINS=...,https://smart-railway-app-60066581545.development.catalystserverless.in
```

### 2. Configure Email in Catalyst Console

```bash
# Go to Catalyst Console
1. Integrations → Email
2. Add Email → Configure sender
3. Verify email address
4. Copy Email ID
```

### 3. Update .env with Email ID

```bash
# Add this line to .env
CATALYST_FROM_EMAIL_ID=<your-email-id-from-console>
```

### 4. Restart Server

```bash
catalyst serve
```

---

## Alternative: Use Email Service Debugging

If email still doesn't work, check:

### Check 1: Email Service Enabled

```python
# In Catalyst Console
Project Settings → Services → Email Service
Status should be: ENABLED
```

### Check 2: Email Quota

```python
# In Catalyst Console
Integrations → Email → Usage
Check if quota is available
```

### Check 3: Test Email Manually

```python
# Test from Python console
from zcatalyst import mail
app = zcatalyst.init()
email = app.mail()
email.send_mail({
    'from_email': 'your-verified-email@domain.com',
    'to_email': 'test@example.com',
    'subject': 'Test',
    'body': 'Testing email service'
})
```

---

## Updated Code (If Needed)

If you need to update the email service to use Email ID instead of email address:

### services/email_service.py

```python
# Around line 15-25
def send_otp_email(email: str, otp: str, purpose: str = 'verification') -> bool:
    try:
        app = zcatalyst.init()
        mail = app.mail()
        
        # Use Email ID instead of email address
        from_email_id = os.getenv('CATALYST_FROM_EMAIL_ID')
        if not from_email_id:
            logger.error("CATALYST_FROM_EMAIL_ID not configured")
            return False
        
        # Send email using ID
        response = mail.send_mail({
            'from_email_id': from_email_id,  # Use ID instead of address
            'to_email': email,
            'subject': subject,
            'html_body': html_content
        })
```

---

## Environment Variables Checklist

After configuration, your `.env` should have:

```bash
# ✅ CORS - Includes deployed domain
CORS_ALLOWED_ORIGINS=http://localhost:3000,...,https://smart-railway-app-60066581545.development.catalystserverless.in

# ✅ Email - One of these:
CATALYST_FROM_EMAIL_ID=31207000000XXXXX          # Option A (recommended)
# OR
CATALYST_FROM_EMAIL=verified-email@domain.com    # Option B (current)

# ✅ Session
SESSION_SECRET=<your-64-char-secret>

# ✅ App
APP_ENVIRONMENT=development
```

---

## Verification

### Test CORS Fix

```bash
# From deployed frontend, try to register
# Check logs should show:
✅ CORS: Allowed origin: https://smart-railway-app-60066581545...
```

### Test Email Fix

```bash
# Try registration
# Check logs should show:
✅ OTP email sent to: user@example.com
✅ Email sent successfully
```

---

## Current Status

- ✅ CORS: **FIXED** - Added deployed domain
- ⚠️ Email: **NEEDS CONFIGURATION** - Configure in Catalyst Console

---

## Next Steps

1. **Configure email in Catalyst Console** (5 min)
2. **Add Email ID to .env** (1 min)
3. **Restart server** (1 min)
4. **Test registration** (2 min)

**Total time:** ~10 minutes

---

**Quick Fix Version:** 1.0  
**Date:** April 2, 2026  
**Status:** CORS Fixed ✅, Email Pending ⚠️
