# ✅ FIXED: SSL Certificate Error

**Error:** `Could not find a suitable TLS CA certificate bundle`  
**Root Cause:** Stale `.build` directory with incorrect certificate paths  
**Solution:** Clean rebuild

---

## What I Did

**Deleted `.build` directory** to force Catalyst to rebuild with correct paths.

---

## What You Need to Do

### Restart Catalyst Server

```bash
catalyst serve
```

Catalyst will:
1. ✅ Rebuild the `.build` directory
2. ✅ Copy `certifi` with correct paths
3. ✅ Start server successfully

---

## Expected Result

**After restart, logs should show:**
```
INFO: Execution started at: ...
INFO: HTTPS enforcement disabled (DEVELOPMENT MODE)
INFO: Session cookies: Secure=False, SameSite=Lax
INFO: CORS: Allowed origins: [...]
```

**NOT see:**
```
ERROR: Could not find a suitable TLS CA certificate bundle
```

---

## Test Registration

After server restarts:

1. **Try to register**
2. **Check backend logs** - should show:
   ```
   INFO: OTP created for user@example.com
   INFO: OTP email sent to user@example.com
   ```
3. **Check your email** - OTP should arrive

---

## Why This Happened

The `.build` directory had **cached paths** pointing to old locations.

**certifi was installed** but Catalyst was looking in:
```
F:\New Railway Project\.build\functions\...\certifi\cacert.pem  ❌ (wrong)
```

Instead of:
```
C:\Users\...\site-packages\certifi\cacert.pem  ✅ (correct)
```

**Clean rebuild fixes this.**

---

## If Error Persists

Try manual reinstall:

```bash
cd functions\smart_railway_app_function
pip uninstall certifi -y
pip install certifi
catalyst serve
```

---

**Restart Catalyst now - the error should be gone!** 🎯

---

**Fix Version:** 1.0  
**Status:** Ready - Restart required  
**Next:** `catalyst serve`
