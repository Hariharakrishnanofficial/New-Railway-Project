# 🔧 Email Troubleshooting Guide

**Email Configured:** krishnan.hari@zappyworks.com  
**Status:** Verified in Catalyst Console ✅  
**Issue:** Email still not sending ⚠️

---

## Quick Checks

### 1. Restart Server

Did you restart after configuring email?

```bash
# REQUIRED: Restart to load new email config
catalyst serve
```

### 2. Check Backend Logs

When you try to register, look for these logs:

**GOOD logs (email working):**
```
INFO: OTP created for user@example.com
INFO: OTP email sent to user@example.com
```

**BAD logs (email failing):**
```
ERROR: Failed to send OTP email: {...}
ERROR: OTP send failed for user@example.com
```

### 3. Check Email Format

The Catalyst Email API might need different format. Let me check...

---

## Possible Issues & Fixes

### Issue A: Wrong Email API Format

Catalyst might need `from_email` as **string** not **list**.

**Current code (line 238):**
```python
mail_obj = {
    'from_email': FROM_EMAIL,  # ← String
    'to_email': [email],        # ← Array
    ...
}
```

**Try this fix** if you see error about email format:

Edit `services/otp_service.py` line 237-243:
```python
mail_obj = {
    'from_email': FROM_EMAIL,
    'to_email': email,  # ← Change from [email] to email
    'subject': subject,
    'content': content,
    'html_mode': True
}
```

---

### Issue B: Email Service Not Enabled

**Check in Catalyst Console:**
1. Go to: Project Settings → Services
2. Find: **Email Service**
3. Ensure: Status = **ENABLED**

---

### Issue C: Using Wrong Email Format

Catalyst might expect different parameters:

**Option 1: Use from_email (current)**
```python
'from_email': 'krishnan.hari@zappyworks.com'
```

**Option 2: Use from_email_id**
```python
'from_email_id': '<email-id-from-console>'  # Like: 31207000000123456
```

To get email ID:
1. Catalyst Console → Integrations → Email
2. Click on your verified email
3. Look for "Email ID" field

---

## What to Check Now

### Step 1: Check Backend Logs

Try to register and share the **exact error** from logs:
```bash
catalyst logs --tail 50
```

Look for lines with:
- `ERROR`
- `Failed to send OTP`
- `email`

### Step 2: Test Email Sending Directly

Add this test endpoint to check if email works:

**File:** `main.py` (in debug section)

```python
@app.route('/debug/test-email', methods=['POST'])
def test_email():
    """Test email sending (DEVELOPMENT ONLY)."""
    try:
        import zcatalyst_sdk
        from services.otp_service import FROM_EMAIL
        
        app = zcatalyst_sdk.initialize()
        mail = app.email()
        
        result = mail.send_mail({
            'from_email': FROM_EMAIL,
            'to_email': 'your-email@example.com',  # ← Change this
            'subject': 'Test Email from Smart Railway',
            'content': 'If you receive this, email is working!',
            'html_mode': False
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Email sent',
            'result': str(result)
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'type': type(e).__name__
        }), 500
```

Then test:
```bash
curl -X POST http://localhost:3000/server/smart_railway_app_function/debug/test-email
```

---

## Common Email Errors & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_ID` | Email not verified | Verify email in console |
| `No such from_email` | Wrong email address | Update CATALYST_FROM_EMAIL |
| `Email service not enabled` | Service disabled | Enable in console |
| `Invalid email format` | Wrong API parameters | Try different format |
| `Quota exceeded` | Out of email credits | Check quota in console |

---

## Next Steps

**Please share:**
1. ✅ Did you restart server after configuring email?
2. ✅ What exact error shows in backend logs?
3. ✅ Is email service ENABLED in Catalyst Console?

Then I can provide specific fix!

---

**Troubleshooting Version:** 1.0  
**Email:** krishnan.hari@zappyworks.com  
**Status:** Configured, needs debugging
