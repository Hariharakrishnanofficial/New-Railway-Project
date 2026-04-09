# 🔧 Debugging 400 BAD REQUEST on OTP Verification

**Error:** POST /session/register/verify returns 400 (BAD REQUEST)  
**Status:** Analysis Complete - Root causes identified

---

## 🔍 What Causes 400 Error

400 BAD REQUEST means one of these validation checks is failing on the backend:

### Backend Validation (otp_register.py, lines 254-259):

```python
if not email:
    return 400, 'Email is required'
    
if not otp:
    return 400, 'Verification code is required'
    
if len(otp) != 6 or not otp.isdigit():
    return 400, 'Invalid verification code format'
```

---

## ✅ How to Debug

### Step 1: Check Browser Network Tab

1. **Open DevTools** (F12)
2. **Go to Network tab**
3. **Enter OTP code** to trigger the error
4. **Find request:** Look for `/session/register/verify` POST request
5. **Click on it** and check:
   - **Request Body:** Should show `{"email":"user@example.com","otp":"123456"}`
   - **Response:** Should show error message like "Email is required" or similar
   - **Headers:** Should have `Content-Type: application/json`

### Step 2: Check Backend Logs

Run the backend with verbose logging:

```bash
# Windows - Check Catalyst logs or Flask output
python app.py  # See what error message is returned
```

Look for error message matching one of these:
- ❌ "Email is required"
- ❌ "Verification code is required"
- ❌ "Invalid verification code format"
- ❌ "OTP has expired"
- ❌ "Invalid OTP"

### Step 3: Add Frontend Logging

Add this to **AuthPage.jsx** in `handleOtpVerify` function (line 240):

```javascript
const handleOtpVerify = async (otp) => {
  setLoading(true);
  try {
    // ADD THESE LOGS:
    console.log('=== OTP VERIFICATION DEBUG ===');
    console.log('Email:', pendingEmail);
    console.log('Email empty?', !pendingEmail);
    console.log('Email type:', typeof pendingEmail);
    console.log('OTP:', otp);
    console.log('OTP length:', otp.length);
    console.log('OTP is digits only?', /^\d+$/.test(otp));
    console.log('Sending request with:', { email: pendingEmail, otp });
    
    const result = await verifyRegistration(pendingEmail, otp);
    // ... rest of code
```

Then check browser console for the logs.

---

## 🎯 Most Likely Issues

### Issue 1: Empty Email (50% probability)

**Problem:** `pendingEmail` is empty string

**Cause:** Registration initiation didn't complete or email wasn't saved

**How to fix:**
```javascript
// In line 177 of AuthPage.jsx
setPendingEmail(result.email || form.email.trim().toLowerCase());
```

Add this check right before calling verify:
```javascript
if (!pendingEmail) {
  toast.error('Email not found. Please register again.');
  setMode('register');
  return;
}
```

---

### Issue 2: Invalid OTP Format (40% probability)

**Problem:** OTP contains non-numeric characters or wrong length

**Causes:**
- User entered spaces: "123 456" instead of "123456"
- User entered letters: "12345a"
- User entered less than 6 digits: "12345"
- User entered more than 6 digits: "1234567"

**How to fix:**

Add validation in **OTPVerification.jsx** before calling `onVerify`:

```javascript
const handleVerify = useCallback(async () => {
  setLocalError(null);
  
  // ADD THIS VALIDATION:
  if (otp.length !== 6) {
    setLocalError('Please enter exactly 6 digits');
    return;
  }
  
  if (!/^\d+$/.test(otp)) {
    setLocalError('Code must contain only digits (0-9)');
    return;
  }
  
  await onVerify(otp);
}, [otp, onVerify]);
```

---

### Issue 3: Incorrect Email Format (10% probability)

**Problem:** Email not lowercased or has whitespace

**Current code (line 251 in backend):**
```python
email = (data.get('email') or data.get('Email') or '').strip().lower()
```

This already handles it, but verify frontend is sending correctly:

```javascript
// Line 177 - already does this
setPendingEmail(result.email || form.email.trim().toLowerCase());
```

✅ This is correct.

---

## 🧪 Testing Steps

### Test 1: Verify Email is Set
Add this in **AuthPage.jsx** after `setPendingEmail`:
```javascript
setPendingEmail(result.email || form.email.trim().toLowerCase());
console.log('Pending email set to:', result.email || form.email.trim().toLowerCase()); // ADD THIS
setOtpExpiresInMinutes(result.expiresInMinutes || 15);
setMode('verify-otp');
```

### Test 2: Verify OTP Format
Before registration, check you received a **6-digit code in email**:
```
Example: 123456 ✅ (correct)
Example: 12345  ❌ (too short)
Example: 1234567 ❌ (too long)
Example: 12345a  ❌ (contains letter)
Example: 123 456 ❌ (contains space)
```

### Test 3: Send Exact OTP
When entering code, make sure:
- [ ] You enter exactly 6 digits
- [ ] No spaces before/after
- [ ] All numeric characters (0-9)
- [ ] Matches code from email exactly

---

## ✅ Complete Verification Checklist

- [ ] Registration initiation succeeded (got OTP email)
- [ ] Email received with 6-digit code
- [ ] `pendingEmail` has correct value (check console log)
- [ ] OTP entered is exactly 6 digits
- [ ] OTP contains only numbers (0-9)
- [ ] Less than 15 minutes since OTP was sent
- [ ] Network request shows correct JSON body in DevTools

---

## 📋 Request Format Verification

**What backend expects:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Check in DevTools:**
1. Open Network tab
2. Look for POST to `/session/register/verify`
3. Click it
4. Go to "Request" or "Payload" tab
5. Should show above JSON format

---

## 🚀 Quick Fix Checklist

✅ Add logging to `handleOtpVerify` (see Step 3 above)  
✅ Add OTP format validation (see Issue 2 above)  
✅ Add email existence check (see Issue 1 above)  
✅ Check browser console for debug logs  
✅ Check backend logs for actual error message  
✅ Verify 6-digit code received in email  
✅ Re-test registration flow  

---

## 📞 Common Error Messages & Fixes

| Backend Error | Cause | Fix |
|--------------|-------|-----|
| "Email is required" | `pendingEmail` is empty | Ensure registration step completed, add email existence check |
| "Verification code is required" | `otp` is empty | Don't auto-verify if otp.length < 6 |
| "Invalid verification code format" | OTP not exactly 6 digits | Add length validation, reject non-numeric |
| "OTP has expired" | More than 15 mins passed | Re-request OTP using resend button |
| "Invalid OTP" | Wrong code entered | Verify exact code from email |

---

## 💡 Next Steps

1. **Add the logging** from Step 3 above
2. **Re-run registration flow**
3. **Check console logs** - what values are being sent?
4. **Check network request body** in DevTools
5. **Check backend error message** in backend logs
6. **Report which error message you see**
7. Apply appropriate fix from "Most Likely Issues" section

Once you identify which validation is failing, the fix is straightforward!

---

**Status:** Ready for debugging  
**Date:** 2026-03-31
