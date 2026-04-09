# 🔧 Fix: "Method Not Allowed" Error

**Error:** `{"message":"Method not allowed","status":"error"}`  
**Endpoint:** `/server/smart_railway_app_function/session/register/initiate`  
**Date:** April 2, 2026

---

## Root Cause

The endpoint **only accepts POST** requests, but something is sending **GET** (or OPTIONS without proper CORS headers).

---

## Quick Tests

### Test 1: Check if Endpoint Exists

```bash
curl -X GET https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function/session/register/test
```

**Expected:** 200 OK with test message  
**If 404:** Blueprint not registered

### Test 2: Check CORS Preflight

```bash
curl -X OPTIONS \
  -H "Origin: https://smart-railway-app-60066581545.development.catalystserverless.in" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function/session/register/initiate
```

**Expected:** 200 OK with CORS headers  
**If error:** CORS misconfigured

### Test 3: Try POST Request

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Origin: https://smart-railway-app-60066581545.development.catalystserverless.in" \
  -d '{"fullName":"Test User","email":"test@example.com","password":"Test123!","phoneNumber":"1234567890"}' \
  https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function/session/register/initiate
```

**Expected:** Success or email error (not "Method not allowed")

---

## Solution 1: Add OPTIONS Handler to Route

The route needs to explicitly handle OPTIONS for CORS preflight.

### Edit: `routes/otp_register.py`

```python
# Line 168 - Add OPTIONS to allowed methods
@otp_register_bp.route('/session/register/initiate', methods=['POST', 'OPTIONS'])
@rate_limit(max_calls=30, window_seconds=3600)
def initiate_registration():
    """
    Step 1: Validate registration data and send OTP email.
    """
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    # Rest of the existing code...
    data = _extract_payload()
    # ...
```

---

## Solution 2: Check Frontend is Using POST

### Verify Frontend Code

Check `railway-app/src/services/sessionApi.js` line 287:

```javascript
async initiateRegistration({ fullName, email, password, phoneNumber }) {
  const response = await this.request('/session/register/initiate', {
    method: 'POST',  // ← Must be POST
    body: JSON.stringify({ fullName, email, password, phoneNumber }),
  });
  return response;
}
```

**If it says `method: 'GET'`** → Change to `'POST'`

---

## Solution 3: Check Browser Network Tab

1. Open your deployed frontend
2. Open DevTools (F12)
3. Go to **Network** tab
4. Try to register
5. Look for the request to `/session/register/initiate`
6. Check:
   - **Method:** Should be `POST`
   - **Status:** Should NOT be 405
   - **Request Headers:** Should include `Origin`
   - **Response Headers:** Should include `Access-Control-Allow-Origin`

---

## Most Likely Fix

The CORS middleware handles OPTIONS globally, but the route might need explicit OPTIONS support. Apply **Solution 1**:

```python
# File: functions/smart_railway_app_function/routes/otp_register.py
# Line 168

# OLD:
@otp_register_bp.route('/session/register/initiate', methods=['POST'])

# NEW:
@otp_register_bp.route('/session/register/initiate', methods=['POST', 'OPTIONS'])
```

Then add OPTIONS handler at the start of the function:

```python
def initiate_registration():
    """Step 1: Validate registration data and send OTP email."""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    # Existing code continues...
    data = _extract_payload()
```

---

## Apply Same Fix to Other Routes

Also update:

1. `/session/register/verify` (line 269)
2. `/session/register/resend-otp` (line 421)

```python
@otp_register_bp.route('/session/register/verify', methods=['POST', 'OPTIONS'])
@otp_register_bp.route('/session/register/resend-otp', methods=['POST', 'OPTIONS'])
```

---

## Complete Fix Code

I'll create the fix now...
