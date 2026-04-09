# 🔧 Quick Fix: Rate Limit & 401 Errors

**Date:** April 3, 2026  
**Errors:** 429 TOO MANY REQUESTS, 401 UNAUTHORIZED

---

## Issue 1: Rate Limit Hit (429)

### What Happened
You tried to register too many times and hit the rate limit:
- **Limit:** 30 attempts per hour
- **Current:** Limit exceeded

### Quick Fix Options

#### Option A: Wait (Easiest)
Wait 1 hour for the rate limit to reset automatically.

#### Option B: Increase Rate Limit (For Development)

1. **Edit `.env`** - Add or update:
   ```bash
   # Increase rate limits for development
   RATE_LIMIT_AUTH=1000
   RATE_LIMIT_WINDOW=3600
   ```

2. **Restart server:**
   ```bash
   catalyst serve
   ```

#### Option C: Clear Rate Limit Storage (Immediate)

**Add this temporary endpoint** to clear rate limits:

`functions/smart_railway_app_function/main.py` (in the debug section):

```python
# Around line 180, in the if APP_ENVIRONMENT == 'development' block:

@app.route('/debug/clear-rate-limits', methods=['POST'])
def clear_rate_limits():
    """Clear all rate limit counters (DEVELOPMENT ONLY)."""
    from core.security import _rate_store, _rate_lock
    
    with _rate_lock:
        _rate_store.clear()
    
    return jsonify({
        'status': 'success',
        'message': 'Rate limits cleared'
    }), 200
```

Then call it:
```bash
curl -X POST http://localhost:3000/server/smart_railway_app_function/debug/clear-rate-limits
```

---

## Issue 2: 401 UNAUTHORIZED Errors

### What Happened
The frontend is calling `/session/validate` when you're NOT logged in yet.

### Root Cause
The frontend's `AuthContext` or session validation runs on every page load, including the registration page.

### Solution: Ignore 401 on Public Pages

The frontend should handle this gracefully. Check if your `AuthContext` does this:

**File:** `railway-app/src/contexts/AuthContext.jsx` (or similar)

```javascript
useEffect(() => {
  // Only validate session on protected pages
  const publicPaths = ['/login', '/register', '/'];
  const currentPath = window.location.pathname;
  
  // Skip validation on public pages
  if (publicPaths.includes(currentPath)) {
    return;
  }
  
  // Otherwise validate session
  validateSession();
}, []);
```

**OR** handle the 401 silently:

```javascript
async function validateSession() {
  try {
    const response = await sessionApi.validateSession();
    setUser(response.data.user);
  } catch (error) {
    // Silently handle 401 on public pages
    if (error.status === 401) {
      setUser(null);
      // Don't show error to user
      return;
    }
    // Show other errors
    console.error('Session validation failed:', error);
  }
}
```

---

## Recommended Fix (Do This Now)

### 1. Increase Rate Limit for Development

**Edit `.env`:**
```bash
# Add these lines (or update existing)
RATE_LIMIT_AUTH=1000
RATE_LIMIT_WINDOW=3600
```

### 2. Restart Server
```bash
# Stop current server (Ctrl+C)
catalyst serve
```

### 3. Test Registration Again
Try registering - the 429 error should be gone.

---

## Long-Term Fixes

### For Production

1. **Keep strict rate limits** (current: 30 per hour is good)
2. **Show user-friendly message** for 429 errors
3. **Add visual feedback** (countdown timer, "Please wait X seconds")

### For Frontend

1. **Don't validate session on public pages**
2. **Handle 401 gracefully** (silently clear user state)
3. **Add loading states** to prevent multiple submissions

---

## Current Rate Limits

| Endpoint | Limit | Window | File |
|----------|-------|--------|------|
| `/session/register/initiate` | 30 | 1 hour | otp_register.py:169 |
| `/session/register/verify` | 30 | 1 hour | otp_register.py:274 |
| `/session/register/resend-otp` | 10 | 1 hour | otp_register.py:430 |

---

## Quick Test Commands

### Check if rate limit is the issue:
```bash
# Should show current rate limit state
curl http://localhost:3000/server/smart_railway_app_function/session/register/initiate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"fullName":"Test","email":"test@test.com","password":"Test123!","phoneNumber":"123"}'
```

**Expected:**
- 429 = Still rate limited
- 400 = Rate limit cleared (now showing validation errors, which is progress!)

---

## Summary

| Error | Cause | Fix |
|-------|-------|-----|
| **429 TOO MANY REQUESTS** | Hit rate limit (30/hr) | Increase in .env or wait 1 hour |
| **401 UNAUTHORIZED** | Frontend validating session on public page | Handle 401 gracefully in frontend |

---

## Next Steps

1. ✅ Update `.env` with higher rate limits
2. ✅ Restart server
3. ✅ Try registration again
4. ⚠️ Still need to configure email in Catalyst Console

---

**After these fixes, you should be able to register** (though email won't send until you configure it in Catalyst Console as explained earlier).

**Fix Version:** 1.0  
**Status:** Ready to apply
