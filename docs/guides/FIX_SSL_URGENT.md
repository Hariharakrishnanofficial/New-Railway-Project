# 🚨 URGENT: SSL Certificate Fix

**Error:** `Could not find a suitable TLS CA certificate bundle`  
**Solution:** Clean rebuild (2 minutes)

---

## Steps to Fix

### 1. Stop Catalyst Server

**In your terminal where Catalyst is running:**
```
Press Ctrl+C
```

Wait for it to fully stop.

---

### 2. Delete .build Directory

**Option A: Using File Explorer**
1. Navigate to: `F:\New Railway Project`
2. Delete the `.build` folder
3. **If "Access Denied"** - Close any terminals/editors that might have files open

**Option B: Using Command Prompt**
```cmd
cd "F:\New Railway Project"
rmdir /s /q .build
```

**Option C: Using PowerShell**
```powershell
cd "F:\New Railway Project"
Remove-Item -Recurse -Force .build
```

---

### 3. Restart Catalyst

```bash
catalyst serve
```

Catalyst will rebuild everything with correct certificate paths.

---

## Expected Result

**After restart, logs should show:**
```
✅ INFO: Execution started
✅ INFO: HTTPS enforcement disabled (DEVELOPMENT MODE)
✅ INFO: CORS: Allowed origins: [...]
```

**NOT see:**
```
❌ ERROR: Could not find a suitable TLS CA certificate bundle
```

---

## Quick Test

After server restarts:

1. **Try to register** a new user
2. **Check logs** - should show:
   ```
   INFO: OTP created for user@example.com
   INFO: OTP email sent to user@example.com
   ```
3. **Check email** - OTP should arrive

---

## If .build Won't Delete

**Still getting "Access Denied"?**

1. **Close ALL terminals** running Catalyst
2. **Close VS Code** (or any IDE with the project open)
3. **Restart your computer** (if desperate)
4. **Try deleting again**

Or just:
```cmd
# Force close any Python processes
taskkill /F /IM python.exe /T

# Then delete
rmdir /s /q ".build"

# Then restart
catalyst serve
```

---

## Why This Fixes It

The `.build` directory has **cached incorrect paths** to certifi.

**Deleting it forces Catalyst to:**
1. Rebuild from scratch
2. Copy dependencies with correct paths
3. Use system-installed certifi

---

## DO THIS NOW

```bash
# 1. Stop server
Ctrl+C

# 2. Delete .build
rmdir /s /q .build

# 3. Restart
catalyst serve
```

**Then try registration - email should work!** 🎯

---

**Fix Time:** 2 minutes  
**Status:** CRITICAL - blocks all functionality  
**Next:** Stop server → Delete .build → Restart
