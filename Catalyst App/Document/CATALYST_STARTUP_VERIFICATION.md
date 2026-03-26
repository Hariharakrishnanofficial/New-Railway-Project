# ✅ CATALYST APP LOCAL TESTING - STARTUP & VERIFICATION GUIDE

## 🚀 QUICK START

### Step 1: Navigate to Catalyst App
```cmd
cd "f:\Railway Project Backend\Catalyst App"
```

### Step 2: Start Catalyst Serve
```cmd
catalyst serve
```

### Step 3: Wait for Startup (30-60 seconds)
Watch terminal for:
```
✓ Functions compiled
✓ Frontend ready
✓ Server started on port 3000
```

### Step 4: Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:9000/api

---

## 📊 CURRENT PROJECT STATUS

### Frontend Build ✅
- **Location**: `f:\Railway Project Backend\Catalyst App\catalyst-frontend\build`
- **Status**: Build folder exists
- **Files**: 
  - ✅ index.html (SPA entry)
  - ✅ 404.html (client routing fallback)
  - ✅ assets/ (minified JS/CSS)
  - ✅ favicon.ico
  - ✅ manifest.json
- **Ready**: YES - can be served immediately

### Backend Functions ✅
- **Location**: `f:\Railway Project Backend\Catalyst App\functions\catalyst_backend`
- **Framework**: Flask 2.3.2 + zcatalyst-sdk
- **Status**: Code present and configured
- **Requirements**: All in requirements.txt
- **Ready**: YES - can be started

### Catalyst Config ✅
- **File**: `f:\Railway Project Backend\Catalyst App\catalyst.json`
- **Frontend Source**: `catalyst-frontend/build`
- **Functions Target**: `catalyst_backend`
- **Status**: Properly configured

---

## 🏗️ ARCHITECTURE AT LOCALHOST

```
┌─────────────────────────────────────────────┐
│        CATALYST LOCAL ARCHITECTURE           │
└─────────────────────────────────────────────┘

BROWSER
  │
  └─→ http://localhost:3000
      │
      ├─→ Static Frontend (React SPA)
      │   └─ Files from catalyst-frontend/build/
      │
      └─→ API Calls
          │
          └─→ http://localhost:9000/api
              │
              ├─→ Backend Functions (Flask)
              │   └─ functions/catalyst_backend/
              │
              └─→ CloudScale Database (Local/In-Memory)
                  └─ Tables from catalyst-config.json
```

---

## 🔑 KEY ENDPOINTS

### Frontend
- **Main App**: http://localhost:3000
- **Admin Dashboard**: http://localhost:3000/dashboard
- **Login**: http://localhost:3000/login
- **Trains**: http://localhost:3000/trains
- **Stations**: http://localhost:3000/stations
- **Bookings**: http://localhost:3000/bookings
- **Search**: http://localhost:3000/search

### Backend API
- **Health Check**: http://localhost:9000/api/health
- **Login**: POST http://localhost:9000/api/auth/login
- **Trains**: http://localhost:9000/api/trains
- **Stations**: http://localhost:9000/api/stations
- **Bookings**: http://localhost:9000/api/bookings
- **Search**: http://localhost:9000/api/search/trains

---

## 📋 PRE-STARTUP VERIFICATION

### ✅ Check 1: Catalyst CLI Installed
```cmd
catalyst --version
```
**Expected Output**: `@zoho/catalyst-cli/X.X.X`

**If fails**: 
```cmd
npm install -g @zoho/catalyst-cli
catalyst login
```

### ✅ Check 2: Catalyst Configuration
```cmd
cd "f:\Railway Project Backend\Catalyst App"
type .catalystrc
```
**Expected Output**: JSON with project ID and env config

### ✅ Check 3: Frontend Build Exists
```cmd
dir catalyst-frontend\build\index.html
```
**Expected Output**: File found

**If missing**:
```cmd
cd catalyst-frontend
npm install
npm run build
cd ..
```

### ✅ Check 4: Backend Code Ready
```cmd
dir functions\catalyst_backend\app.py
dir functions\catalyst_backend\requirements.txt
```
**Expected Output**: Both files present

### ✅ Check 5: Node.js & Python Installed
```cmd
node --version
npm --version
python --version
```
**Expected Output**:
- Node.js: v16+ or v18+
- npm: 8+
- Python: 3.8+

---

## 🚀 STARTUP PROCEDURE

### Method 1: Using Batch Script (Easiest)
```cmd
cd "f:\Railway Project Backend\Catalyst App"
start.bat
```

**What it does**:
1. Kills any running Python processes
2. Clears .build directory
3. Runs `catalyst serve`

### Method 2: Direct Catalyst Command
```cmd
cd "f:\Railway Project Backend\Catalyst App"
catalyst serve
```

### Method 3: With Debug Logging
```cmd
cd "f:\Railway Project Backend\Catalyst App"
catalyst serve --debug
```

### Method 4: Custom Port
```cmd
catalyst serve --port 3001
```

---

## 📊 WHAT HAPPENS DURING STARTUP

### Timeline (30-60 seconds typical)

```
0s    → catalyst serve command starts
        ↓
5s    → Building frontend from build/ folder
        ↓
10s   → Starting backend Python environment
        ↓
15s   → Installing backend dependencies (if needed)
        ↓
20s   → Initializing CloudScale database connection
        ↓
25s   → Loading routes and blueprints
        ↓
30s   → Starting HTTP server on port 3000
        ↓
35s   → Backend functions ready on port 9000
        ↓
60s   → ✓ Server running
        → Ready to access at http://localhost:3000
```

### Expected Terminal Output

```
Starting Catalyst serve...

[INFO] Building application...
[INFO] Frontend: Loading from catalyst-frontend/build
[INFO] Backend: Initializing catalyst_backend
[INFO] Database: Connecting to CloudScale
[INFO] Auth: JWT configured
[INFO] CORS: Enabled for localhost

✓ Frontend server: http://localhost:3000
✓ Backend API: http://localhost:9000/api
✓ Status: Ready

Press Ctrl+C to stop server
```

---

## ✅ TESTING PHASE 1: FRONTEND

### Test 1.1: Can Load App
1. Open browser: http://localhost:3000
2. **Expected**: Login page or dashboard loads
3. **Check**: No 404 error, page renders

### Test 1.2: Check Network Tab
1. Press F12 → Network tab
2. Reload page (F5)
3. **Expected**: 
   - GET index.html → 200
   - GET assets/index-*.js → 200
   - GET assets/index-*.css → 200

### Test 1.3: Check Console
1. Press F12 → Console tab
2. **Expected**: No red errors
3. **Common to ignore**: 
   - "Missing favicon" (warning, not error)
   - "DevTools" messages (informational)

### Test 1.4: Navigation Works
1. Click "Trains" link
2. **Expected**: /trains page loads
3. Repeat for: Stations, Users, Bookings, Search

### Test 1.5: Responsive Design
1. Press F12 → Toggle device toolbar (Ctrl+Shift+M)
2. **Expected**: Layout adapts to mobile size
3. Try: Phone (375px) and tablet (768px) sizes

---

## ✅ TESTING PHASE 2: BACKEND API

### Test 2.1: Health Check
```cmd
curl http://localhost:9000/api/health
```

**Expected Response** (HTTP 200):
```json
{
  "status": "ok",
  "timestamp": "2026-03-22T16:00:00Z",
  "service": "Railway Ticketing API"
}
```

**If fails**:
- ❌ Connection refused → Backend not running
- ❌ 404 Not Found → Endpoint doesn't exist
- ❌ 500 Internal Error → Check logs

### Test 2.2: Test Login Endpoint
```cmd
curl -X POST http://localhost:9000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}"
```

**Expected Response** (HTTP 200):
```json
{
  "status": "success",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "role": "admin",
    "name": "Admin User"
  }
}
```

**Save the token for next tests** (copy value after "token":)

### Test 2.3: Get Stations List
```cmd
curl http://localhost:9000/api/stations ^
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Expected Response** (HTTP 200):
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "code": "DEL",
      "name": "Delhi",
      "city": "Delhi"
    },
    {
      "id": 2,
      "code": "BLR",
      "name": "Bangalore",
      "city": "Bangalore"
    }
  ],
  "count": 2
}
```

### Test 2.4: Get Trains List
```cmd
curl http://localhost:9000/api/trains ^
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

**Expected Response** (HTTP 200):
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Express 101",
      "train_number": "12345",
      "capacity": 500,
      "status": "active"
    }
  ],
  "count": 1
}
```

### Test 2.5: Create New Train
```cmd
curl -X POST http://localhost:9000/api/trains ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer <YOUR_TOKEN>" ^
  -d "{\"name\":\"Test Train\",\"train_number\":\"99999\",\"capacity\":600,\"status\":\"active\"}"
```

**Expected Response** (HTTP 201 or 200):
```json
{
  "status": "success",
  "message": "Train created successfully",
  "id": 2,
  "data": { ... }
}
```

---

## ✅ TESTING PHASE 3: INTEGRATION (Frontend ↔ Backend)

### Test 3.1: Login Flow
1. Go to http://localhost:3000
2. Enter email: `admin@example.com`
3. Enter password: `admin123`
4. Click "Sign In"
5. **Expected**: 
   - POST /api/auth/login request succeeds
   - Token stored in sessionStorage
   - Redirects to dashboard
   - Dashboard loads with data

**Verify**:
- F12 → Application → SessionStorage
- Check `rail_access_token` exists
- Check Network tab for POST auth/login

### Test 3.2: View Trains Page
1. After login, go to http://localhost:3000/trains
2. **Expected**:
   - GET /api/trains request
   - Table loads with train data
   - Shows train names, numbers, capacity

**Verify**:
- F12 → Network → Find /api/trains
- Check response has "data" array
- Table renders correctly

### Test 3.3: Create New Train (CRUD Create)
1. On Trains page, click "Add Train" or "+" button
2. Fill form:
   - Name: "Test Express"
   - Number: "99999"
   - Capacity: "750"
   - Status: "Active"
3. Click "Submit"
4. **Expected**:
   - POST /api/trains request sent
   - Response: HTTP 201 or 200
   - Table refreshes with new train
   - Success toast shows

**Verify**:
- F12 → Network → Find POST /api/trains
- Response has status: "success"
- New train appears in table

### Test 3.4: Update Train (CRUD Update)
1. In Trains table, click "Edit" on any train
2. Change a field (e.g., capacity to 800)
3. Click "Save"
4. **Expected**:
   - PUT /api/trains/:id request
   - Response: HTTP 200
   - Table updates immediately
   - Success toast shows

### Test 3.5: Delete Train (CRUD Delete)
1. In Trains table, click "Delete" on a train
2. Confirm deletion dialog
3. **Expected**:
   - DELETE /api/trains/:id request
   - Response: HTTP 200
   - Train disappears from table
   - Success toast shows

### Test 3.6: Search Trains
1. Go to http://localhost:3000/search
2. Select:
   - From Station: (any)
   - To Station: (any different)
   - Date: (future date)
3. Click "Search"
4. **Expected**:
   - GET /api/search/trains request
   - Results show (or "no trains found")
   - Can click a train to book

---

## 🔍 DEBUGGING COMMON ISSUES

### ❌ Issue: Frontend shows blank page
**Cause**: index.html not loading

**Debug**:
```cmd
# Check file exists
dir "f:\Railway Project Backend\Catalyst App\catalyst-frontend\build\index.html"

# Check size (should be > 5KB)
# If < 5KB, rebuild frontend
cd catalyst-frontend
npm run build
cd ..
catalyst serve
```

### ❌ Issue: API returns 401 Unauthorized
**Cause**: JWT token missing or invalid

**Debug**:
1. Check JWT_SECRET_KEY in functions/catalyst_backend/config.py
2. Check token in sessionStorage (F12 → Application)
3. Try login again to get fresh token
4. Check Authorization header format: "Bearer <token>"

### ❌ Issue: API returns 404 Not Found
**Cause**: Endpoint doesn't exist

**Debug**:
1. Check route file exists: `functions/catalyst_backend/routes/`
2. Check blueprint registered in app.py
3. Check URL spelling matches
4. Try with token: add `-H "Authorization: Bearer <token>"`

### ❌ Issue: "Port 3000 already in use"
**Cause**: Another process on port 3000

**Debug**:
```cmd
# Find process on port 3000
netstat -ano | findstr :3000

# Kill process (replace XXXX with PID)
taskkill /PID XXXX /F

# Or use different port
catalyst serve --port 3001
```

### ❌ Issue: CORS error in browser
**Cause**: Backend CORS not configured for localhost

**Debug**:
1. Check app.py has CORS enabled
2. Check CORS_ALLOWED_ORIGINS includes localhost:3000
3. Restart backend
4. Clear browser cache (Ctrl+Shift+Delete)

### ❌ Issue: Network requests very slow (> 3 seconds)
**Cause**: Possible performance issue

**Debug**:
1. Check backend logs for slow queries
2. Add indexes to CloudScale tables
3. Check for N+1 query problems
4. Monitor CPU/Memory usage

---

## 📊 EXPECTED RESULTS

### ✅ Success Criteria

All of these should pass:

```
✅ Frontend loads at http://localhost:3000
✅ Backend API responds at http://localhost:9000/api/health
✅ Login succeeds with admin credentials
✅ Dashboard displays after login
✅ Can navigate to all pages (Trains, Stations, Users, Bookings)
✅ Can view list of trains (GET /api/trains)
✅ Can create new train (POST /api/trains)
✅ Can update existing train (PUT /api/trains/:id)
✅ Can delete train (DELETE /api/trains/:id)
✅ Can search trains with filters
✅ No console errors (F12 → Console)
✅ No CORS errors
✅ All network requests < 1 second
✅ 404.html exists and SPA routing works
✅ Token stored in sessionStorage
```

### 🟡 Partial Success (Some features working)
- Some pages load but not all
- Some API endpoints work but not all
- Login works but search doesn't
- Performance acceptable but not optimal

### 🔴 Failed (Not working)
- Frontend won't load
- Backend won't start
- Login fails completely
- Multiple API endpoints 404
- Database not accessible

---

## 📝 TEST EXECUTION CHECKLIST

Run through this and mark each:

```
STARTUP
 [ ] Catalyst CLI available
 [ ] Frontend build exists
 [ ] Backend code present
 [ ] Node.js v16+ installed
 [ ] Python 3.8+ installed
 [ ] "catalyst serve" command starts

FRONTEND (5 minutes)
 [ ] http://localhost:3000 loads
 [ ] No 404 error
 [ ] Login page visible
 [ ] Navigation works
 [ ] Console has no red errors

BACKEND (5 minutes)
 [ ] Health check: http://localhost:9000/api/health (200)
 [ ] Login endpoint works (200)
 [ ] Trains endpoint works (200)
 [ ] Stations endpoint works (200)
 [ ] Search endpoint works (200)

INTEGRATION (10 minutes)
 [ ] Can login successfully
 [ ] Dashboard loads after login
 [ ] Can view trains list
 [ ] Can create new train
 [ ] Can update train
 [ ] Can delete train
 [ ] Can search trains

QUALITY
 [ ] No console errors
 [ ] No CORS errors
 [ ] No 401/403 auth errors
 [ ] Responses < 1 second
 [ ] Pages load < 2 seconds

FINAL STATUS
 [ ] Everything working? → ✅ PASS
 [ ] Some issues? → 🟡 PARTIAL
 [ ] Major failures? → 🔴 FAIL
```

---

## 🚀 NEXT STEPS

### If Everything Works ✅
1. ✅ Commit changes to git
2. ✅ Note build passed locally
3. ✅ Ready for Catalyst deployment
4. ✅ Can proceed to production testing

### If Some Issues Found 🟡
1. Review troubleshooting section
2. Check logs: `catalyst-live.log`
3. Fix specific issues
4. Re-run tests
5. Document findings

### If Major Issues 🔴
1. Check startup errors in terminal
2. Review backend logs (catalyst-live.log)
3. Check frontend console (F12)
4. Verify all prerequisites installed
5. Run pre-startup verification checks

---

## 📞 REFERENCE DOCUMENTS

- **Full Test Guide**: CATALYST_LOCAL_TEST_GUIDE.md
- **Architecture**: CLAUDE_CATALYST_SKILLSET.md
- **Deployment**: PRODUCTION_CUTOVER_GUIDE.md
- **Database**: CLOUDSCALE_DATABASE_SCHEMA.md
- **API Reference**: CLAUDE_CATALYST_SKILLSET.md (Section 11)

---

**Ready to test! Follow steps above and verify each section.** 🚀
