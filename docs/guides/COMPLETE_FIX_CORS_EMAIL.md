# ✅ Complete Fix: CORS and Email Issues

**Date:** April 2, 2026  
**Status:** Ready to implement

---

## 📊 Issues Summary

### Issue 1: CORS Blocked ✅ ALREADY FIXED
```
CORS: Blocked origin: https://smart-railway-app-60066581545.development.catalystserverless.in
```

**Status:** ✅ **FIXED** - Deployed domain is already in `.env` line 53

### Issue 2: Email Configuration ⚠️ NEEDS FIX
```
Failed to send OTP email: {'code': 'INVALID_ID', 'message': 'No such from_email with the given id exists'}
```

**Status:** ⚠️ **NEEDS CATALYST CONSOLE CONFIGURATION**

---

## 🔧 Solution: Configure Email in Catalyst Console

### Step-by-Step Fix

#### 1. Go to Catalyst Console

Navigate to: https://catalyst.zoho.com/console

Select your project: **Smart Railway App** (Project ID: 31207000000078061)

#### 2. Navigate to Email Configuration

```
Console → Integrations → Email
```

#### 3. Configure Email Sender

Click **"Configure Email"** or **"Add Email"**

Fill in:
- **From Email:** Your verified email address
  - Example: `noreply@yourdomain.com`
  - Or use: `hariharakrishnan1117@gmail.com` (your email)
- **From Name:** `Smart Railway Ticketing`
- **Reply To:** (optional) support@yourdomain.com

#### 4. Verify Email

- Zoho will send a verification email
- Click the verification link
- Wait for status to change to: ✅ **Verified**

#### 5. Get the Email Configuration

After verification, note one of:

**Option A: Email Address (Current approach)**
```
Use the verified email address directly
```

**Option B: Email ID (Recommended)**
```
The Email ID will be shown in the console
Format: 31207000000XXXXXX
```

---

## 🔄 Quick Fix Options

### Option 1: Use Verified Email Address (Simplest)

**No code changes needed!** Just update `.env`:

```bash
# In .env, update line 37 or add:
CATALYST_FROM_EMAIL=hariharakrishnan1117@gmail.com
```

**Requirements:**
1. Email must be verified in Catalyst Console
2. Email must match exactly

**Restart server:**
```bash
catalyst serve
```

---

### Option 2: Use Email ID (Recommended for Production)

**Requires minor code change:**

#### Step 1: Get Email ID from Console

After configuring email, the console will show an Email ID like:
```
31207000000123456
```

#### Step 2: Add to .env

```bash
# Add this new variable
CATALYST_FROM_EMAIL_ID=31207000000123456
```

#### Step 3: Update otp_service.py

```python
# services/otp_service.py, line 36-38

# OLD:
FROM_EMAIL = os.getenv('CATALYST_FROM_EMAIL', 'noreply@smartrailway.com')

# NEW:
FROM_EMAIL_ID = os.getenv('CATALYST_FROM_EMAIL_ID')  # For email ID
FROM_EMAIL = os.getenv('CATALYST_FROM_EMAIL', 'noreply@smartrailway.com')  # Fallback
```

```python
# services/otp_service.py, line 237-243

# OLD:
mail_obj = {
    'from_email': FROM_EMAIL,
    'to_email': [email],
    'subject': subject,
    'content': content,
    'html_mode': True
}

# NEW:
mail_obj = {
    'to_email': [email],
    'subject': subject,
    'content': content,
    'html_mode': True
}

# Use email ID if available, otherwise use email address
if FROM_EMAIL_ID:
    mail_obj['from_email_id'] = FROM_EMAIL_ID
else:
    mail_obj['from_email'] = FROM_EMAIL
```

---

## ⚡ Recommended: Use Option 1 (Verified Email)

**For fastest fix, use Option 1:**

### 1. Verify Your Email in Catalyst Console

```
1. Go to: https://catalyst.zoho.com/console
2. Your Project → Integrations → Email
3. Add Email: hariharakrishnan1117@gmail.com
4. Verify from email you receive
5. Wait for ✅ Verified status
```

### 2. Update .env

```bash
# Make sure this line is set correctly:
CATALYST_FROM_EMAIL=hariharakrishnan1117@gmail.com
```

### 3. Restart Server

```bash
# Stop current server (Ctrl+C)
catalyst serve
```

### 4. Test Registration

```
1. Go to your deployed app
2. Try to register with a test email
3. Check logs for: "OTP email sent to..."
```

---

## 🔍 Troubleshooting

### Email Still Fails After Configuration

**Check 1: Email Service Enabled**
```
Console → Project Settings → Services
Ensure "Email Service" is ENABLED
```

**Check 2: Email Verified**
```
Console → Integrations → Email
Status should be: ✅ Verified (not ⏳ Pending)
```

**Check 3: Correct Email in .env**
```bash
# Must match exactly what's in console
CATALYST_FROM_EMAIL=exact-email@from-console.com
```

**Check 4: Email Quota**
```
Console → Integrations → Email → Usage
Check if you have quota remaining
```

### CORS Still Blocking

If CORS still blocks:

**Check 1: Server Restarted**
```bash
# Must restart after .env changes
catalyst serve
```

**Check 2: Correct Domain in Logs**
```
Look for log line:
CORS: Allowed origins: [...includes your domain...]
```

**Check 3: Protocol Matches**
```bash
# Frontend uses HTTPS, backend allows HTTPS
https://smart-railway-app-60066581545.development.catalystserverless.in
```

---

## 📝 Testing Checklist

After fix, verify:

### CORS Test
- [ ] Deployed frontend can call backend
- [ ] Logs show: `CORS: Allowed origin: https://...`
- [ ] No CORS errors in browser console

### Email Test  
- [ ] Registration sends OTP email
- [ ] Email arrives in inbox
- [ ] Logs show: `OTP email sent to: ...`
- [ ] No error: `INVALID_ID`

---

## 🎯 Current .env Status

Your `.env` currently has:

✅ **CORS:** Correctly configured (line 53)
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://smart-railway-app-60066581545.development.catalystserverless.in
```

⚠️ **EMAIL:** Needs verification in console
```bash
CATALYST_FROM_EMAIL=noreply@smartrailway.com  # ← Needs to be verified email
```

---

## 🚀 Action Plan

### Immediate (5 minutes)

1. **Open Catalyst Console**
2. **Configure & Verify Email** (use hariharakrishnan1117@gmail.com)
3. **Update .env if different email**
4. **Restart server**

### Test (2 minutes)

1. **Try registration from deployed app**
2. **Check logs for success**
3. **Verify email received**

### If Still Failing

1. **Check email service enabled in console**
2. **Verify email status is ✅ Verified**
3. **Check email quota**
4. **Contact Catalyst support if needed**

---

## 📧 Expected Log After Fix

```
INFO    CORS: Allowed origins: ['http://localhost:3000', ..., 'https://smart-railway-app-60066581545.development.catalystserverless.in']
INFO    OTP created for user@example.com (purpose: registration)
INFO    OTP email sent to user@example.com  ← This should appear
✅ No errors about INVALID_ID
```

---

## Summary

| Issue | Status | Fix Required |
|-------|--------|--------------|
| CORS Blocked | ✅ Fixed | None - already in .env |
| Email Not Sending | ⚠️ Pending | Configure & verify email in Catalyst Console |

**Total Time to Fix:** ~5-10 minutes (mostly waiting for email verification)

**Next Step:** Go to Catalyst Console and configure email service.

---

**Fix Guide Version:** 1.0  
**Date:** April 2, 2026  
**Tested:** Pending user action
