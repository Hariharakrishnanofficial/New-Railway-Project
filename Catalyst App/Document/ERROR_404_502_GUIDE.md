# 404 & 502 Error Diagnosis Guide

## Error Meanings

### 404 (Not Found)
**What it means:** Browser requested a resource that doesn't exist on the server
```
Browser → Server: "Get /path/to/resource"
Server → Browser: "I don't have that file" (404)
```

**Common causes:**
- Missing CSS/JS files from build
- Wrong API endpoint path
- Frontend trying to load images/assets that don't exist
- Route not registered on backend

### 502 (Bad Gateway)
**What it means:** Gateway/proxy (Catalyst) can't reach the actual backend server
```
Browser → Catalyst Gateway → Backend Flask
Catalyst can't connect to Flask → 502
```

**Common causes:**
- Flask backend service crashed or not running
- Port 3000 backend process died
- Flask code error/exception
- Connection refused

---

## Diagnosis Steps

### Step 1: Open Browser DevTools
**Windows: Press `F12`** → Go to **Network** tab

Then reload the page and look for:
- Red entries (failed requests)
- 404 errors → Check **URL column** - what file failed?
- 502 errors → Check which API endpoint failed?

**Screenshot what you see:**

```
Example 1 - 404 for CSS file:
GET /app/static/main.css  404  2.5s

Example 2 - 502 for API call:
GET /server/catalyst_backend/api/signin  502  3.2s
```

---

### Step 2: Check Which URLs Fail

| URL | Status | Type | Means |
|-----|--------|------|-------|
| `http://localhost:3000/app/` | 200 ✓ | HTML | Frontend loads OK |
| `http://localhost:3000/app/assets/main.js` | 404 ✗ | JS | Build missing files |
| `http://localhost:3000/server/catalyst_backend/` | 502 ✗ | API | Backend crashed |
| `http://localhost:3000/server/catalyst_backend/api/signin` | 502 ✗ | API | Flask not responding |

---

## Common Scenarios & Fixes

### Scenario 1: Only 404 for CSS/JS files
**Problem:** Frontend loads but styling/functionality broken

**Check:**
```bash
# Verify build files exist:
ls catalyst-frontend/build/assets/

# Should show files like:
# - main.js (or index.xxxxx.js)
# - style.css (or similar)
# - etc.
```

**Fix:**
```bash
# Rebuild frontend:
cd catalyst-frontend
npm run build
cd ..
catalyst serve
```

---

### Scenario 2: 502 on API calls (Backend)
**Problem:** Frontend loads but API calls fail

**Check 1: Is Flask running?**
```bash
# Look for Flask process:
tasklist | find /I "python"

# If no Python process, Flask crashed
```

**Check 2: Flask error in logs**
```bash
# Check Catalyst logs:
type catalyst-serve.log | findstr /I "error"

# Flask error messages appear here
```

**Check 3: Test Flask directly**
```bash
# Windows PowerShell:
Invoke-WebRequest http://localhost:3000/server/catalyst_backend/ -ErrorAction SilentlyContinue

# Should show: StatusCode 200 or error message
# If connection refused: Flask not running
```

---

## Fixed Error Examples

### Example 1: 404 on Stylesheet
```
Error: Failed to load resource: status 404 (Not Found)
Resource: GET /app/assets/style.abc123.css

Fix: Rebuild frontend → npm run build
```

### Example 2: 502 on Backend
```
Error: Failed to load resource: status 502 (Bad Gateway)
Resource: GET /server/catalyst_backend/api/signin

Fix: Check if Flask running:
1. ps aux | grep python
2. If not running: catalyst serve
3. If running but error: check logs
```

---

## Complete Diagnostic Checklist

### Frontend 404 Issues
- [ ] Run `npm run build` in catalyst-frontend/
- [ ] Verify `catalyst-frontend/build/assets/` has files
- [ ] Check `index.html` references correct asset paths
- [ ] Restart `catalyst serve`

### Backend 502 Issues
- [ ] Check if Flask is running: `tasklist | find /I "python"`
- [ ] Check catalyst logs for Python errors
- [ ] Verify `functions/catalyst_backend/` has code
- [ ] Check imports in main Flask app
- [ ] Verify database connection working
- [ ] Restart `catalyst serve`

### Both 404 & 502
- [ ] Clean: Delete `.build` folder
- [ ] Rebuild: `catalyst serve`
- [ ] Wait 60 seconds for full startup
- [ ] Check browser console (F12)

---

## What Each Status Means in Detail

### 404 Not Found
```
Status: 404
Reason: The resource path doesn't exist on server

HTTP Headers:
GET /path/to/missing/file HTTP/1.1
Host: localhost:3000

Response:
HTTP/1.1 404 Not Found
Content-Type: text/html
<html>404 Page Not Found</html>
```

**When you see 404:**
- File wasn't included in build
- Wrong path in code (typo)
- Asset moved/deleted
- CDN/external link broken

---

### 502 Bad Gateway
```
Status: 502
Reason: Gateway can't reach backend server

Flow:
Browser → Catalyst Gateway (port 3000)
         → Tries to connect to Flask backend
         → Flask not responding/crashed
         → Returns 502

HTTP Headers:
GET /server/catalyst_backend/api/signin HTTP/1.1
Host: localhost:3000

Response:
HTTP/1.1 502 Bad Gateway
Content-Type: text/html
<html>502 Bad Gateway - Backend Unreachable</html>
```

**When you see 502:**
- Backend server crashed
- Backend port not accessible
- Connection timeout
- Backend process killed

---

## Real Example Walkthrough

### You See Both Errors:
```
Failed to load resource: status 404 (Not Found) 
  GET /app/assets/main.js

Failed to load resource: status 502 (Bad Gateway)
  GET /server/catalyst_backend/api/signin
```

**What's happening:**
1. Browser loads `index.html` → OK (200)
2. Browser tries to load `main.js` → Fails (404 - build missing)
3. Browser tries API call to signin → Fails (502 - Flask not running)

**Fix:**
1. Clean and rebuild:
   ```bash
   rm .build -r
   rm catalyst-frontend/build -r
   catalyst serve
   wait 60 seconds...
   ```

2. Verify both work:
   - http://localhost:3000/app/ → Shows UI ✓
   - Open F12 Console → No red errors ✓
   - Try signin → Works ✓

---

## Quick Debug Script

Create `debug_errors.bat`:

```batch
@echo off
echo === CHECKING FOR ERRORS ===
echo.
echo [1] Checking if Flask is running:
tasklist | find /I "python"
echo.
echo [2] Checking if Node is running:
tasklist | find /I "node.exe"
echo.
echo [3] Testing Frontend (http://localhost:3000/app/):
curl -I http://localhost:3000/app/ 2>nul | findstr /R "200 404 502"
echo.
echo [4] Testing Backend (http://localhost:3000/server/catalyst_backend/):
curl -I http://localhost:3000/server/catalyst_backend/ 2>nul | findstr /R "200 404 502"
echo.
pause
```

---

## Next Steps

1. **Open Browser DevTools (F12)**
2. **Go to Network tab**
3. **Reload page (Ctrl+R)**
4. **Find the red entries** and note the URLs
5. **Share which URLs are failing** with their status codes
6. **Check the logs** in catalyst-serve.log

Then I can give you exact fix!

