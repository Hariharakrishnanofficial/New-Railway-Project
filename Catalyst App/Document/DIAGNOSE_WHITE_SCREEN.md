# White Screen Diagnosis & Fix Guide

## Problem Analysis

Your URLs are returning white screens:
- `http://localhost:3000/app/` → white screen (frontend)
- `http://localhost:3000/server/catalyst_backend/` → likely 404 or empty

### Root Cause
**Build folder is locked/busy during clean:**
```
Error: EBUSY: resource busy or locked, rmdir '.build\functions\catalyst_backend'
```

This happens when:
1. Node process is still running from previous serve
2. Files are locked by file explorer or IDE
3. `.build` folder has stale/incomplete artifacts

---

## Quick Fix (Recommended)

### Step 1: Stop All Node Processes
```bash
# Windows - use Task Manager or:
taskkill /F /PID <PID>  # Replace <PID> with node process ID

# Check active processes:
tasklist /FI "IMAGENAME eq node.exe"
```

### Step 2: Clean Build Artifacts
```bash
cd "F:\Railway Project Backend\Catalyst App"
rmdir /s /q .build
rmdir /s /q catalyst-frontend\build
rmdir /s /q functions\catalyst_backend\.build
```

### Step 3: Rebuild and Start
```bash
catalyst serve
```

---

## Why White Screen Happens

| URL | Should Show | If White | Reason |
|-----|-------------|----------|--------|
| `http://localhost:3000/app/` | React dashboard UI | Blank/white | Build files incomplete or corrupted |
| `http://localhost:3000/server/catalyst_backend/` | API response (JSON) | Blank | No route handler or server error |

---

## What Each URL Does

### Frontend (`/app/`)
- Served from: `catalyst-frontend/build/index.html`
- Loads React components
- Should display dashboard with navbar, sidebar, user menu

### Backend API (`/server/catalyst_backend/`)
- Entry point for all backend routes
- No data at root (needs specific endpoints like `/api/register`, `/api/signin`)
- Test with: `http://localhost:3000/server/catalyst_backend/health` (if health check exists)

---

## Troubleshooting Steps

### 1. Verify Build Exists
```powershell
Test-Path "catalyst-frontend/build/index.html"  # Should be True
Test-Path ".build/functions"  # Should be True after serve starts
```

### 2. Check for File Locks
```bash
# Windows - check what processes have files open:
handle.exe | grep "catalyst_backend"  # Download handle.exe from MS Sysinternals
```

### 3. Clean Cache Files
```bash
# Remove Node cache
node_modules/.cache
.catalyst cache files
.env files (check if corrupted)
```

### 4. Verify catalyst.json Configuration
```json
{
  "functions": {
    "targets": ["catalyst_backend"],
    "ignore": [],
    "source": "functions"
  },
  "client": {
    "source": "catalyst-frontend"
  }
}
```
✓ This looks correct

### 5. Check Frontend Build
```bash
# Verify index.html exists and has content
cat catalyst-frontend/build/index.html | head -20
```

---

## Complete Clean Restart Checklist

- [ ] Stop any running Node processes
- [ ] Close IDE/editor (may have file locks)
- [ ] Close File Explorer windows to catalyst folders
- [ ] Delete `.build` folder completely
- [ ] Delete `catalyst-frontend/build` folder
- [ ] Run `catalyst serve`
- [ ] Wait 30-60 seconds for build and start
- [ ] Navigate to `http://localhost:3000/app/`
- [ ] Should see React dashboard (not white screen)

---

## Expected Output When Running `catalyst serve`

```
(node:XXXX) [DEP0040] DeprecationWarning: The `punycode` module is deprecated...

✓ Client built successfully
✓ Functions built successfully

>>>>>>>>>>>>> Advanced I/O <<<<<<<<<<<
i catalyst_backend: http://localhost:3000/server/catalyst_backend/
✓ Server running...
```

---

## If White Screen Persists

1. **Check browser console** (F12 → Console tab)
   - Look for JavaScript errors
   - Check network requests to `/app/`

2. **Check Catalyst logs**
   ```bash
   # Current log file:
   catalyst-serve.log
   # Delete old logs and restart for fresh output
   ```

3. **Verify Flask backend is running**
   ```bash
   # Test directly:
   curl http://localhost:3000/server/catalyst_backend/
   ```

4. **Check for port conflicts**
   ```bash
   netstat -ano | findstr :3000
   ```

5. **Enable verbose mode**
   ```bash
   catalyst serve --verbose
   ```

---

## Next Steps

1. **Apply Quick Fix above**
2. **Test both URLs:**
   - Frontend: `http://localhost:3000/app/` → Should show UI
   - Backend: `http://localhost:3000/server/catalyst_backend/` → Should show server info or 404 (not blank)
3. **If still white, share:**
   - Browser console errors
   - Full `catalyst serve` output
   - Current `catalyst-serve.log` content

