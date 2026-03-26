# 🚀 CATALYST APP - QUICK COMMAND REFERENCE

## 📋 ONE-LINE STARTUP

```cmd
cd "f:\Railway Project Backend\Catalyst App" && catalyst serve
```

Access at: **http://localhost:3000**

---

## 🎯 STARTUP COMMANDS

### Windows Batch (Easiest)
```cmd
cd "f:\Railway Project Backend\Catalyst App"
start.bat
```

### Direct Catalyst CLI
```cmd
cd "f:\Railway Project Backend\Catalyst App"
catalyst serve
```

### With Custom Port
```cmd
catalyst serve --port 3001
```

### With Debug Logging
```cmd
catalyst serve --debug
```

### Stop Server
```
Press: Ctrl + C (in terminal)
```

---

## 🧪 QUICK TESTS (Copy-Paste Ready)

### Test 1: Health Check
```cmd
curl http://localhost:9000/api/health
```

**Expected**: HTTP 200 with status "ok"

### Test 2: Login
```cmd
curl -X POST http://localhost:9000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}"
```

**Expected**: HTTP 200 with JWT token

### Test 3: Get Trains (replace TOKEN with token from Test 2)
```cmd
curl http://localhost:9000/api/trains ^
  -H "Authorization: Bearer TOKEN"
```

**Expected**: HTTP 200 with trains array

### Test 4: Get Stations
```cmd
curl http://localhost:9000/api/stations ^
  -H "Authorization: Bearer TOKEN"
```

**Expected**: HTTP 200 with stations array

### Test 5: Search Trains
```cmd
curl "http://localhost:9000/api/search/trains?from=STA001&to=STA002&date=2026-03-25" ^
  -H "Authorization: Bearer TOKEN"
```

**Expected**: HTTP 200 with search results

---

## 🏗️ BUILD COMMANDS

### Build Frontend
```cmd
cd catalyst-frontend
npm install
npm run build
cd ..
```

### Rebuild Everything
```cmd
# Clean
rd /s /q catalyst-frontend\build
rd /s /q .build

# Rebuild frontend
cd catalyst-frontend
npm run build
cd ..

# Start catalyst
catalyst serve
```

---

## 🔧 TROUBLESHOOTING COMMANDS

### Check Catalyst CLI
```cmd
catalyst --version
```

### Check Node.js
```cmd
node --version
npm --version
```

### Check Python
```cmd
python --version
pip list | findstr zcatalyst
```

### Kill Process on Port 3000
```cmd
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Kill Process on Port 9000
```cmd
netstat -ano | findstr :9000
taskkill /PID <PID> /F
```

### View Catalyst Logs
```cmd
type catalyst-live.log
```

### View Last 20 Lines of Log
```cmd
powershell -Command "Get-Content catalyst-live.log -Tail 20"
```

---

## 📍 IMPORTANT PATHS

| Item | Path |
|------|------|
| Catalyst Root | `f:\Railway Project Backend\Catalyst App` |
| Frontend | `f:\Railway Project Backend\Catalyst App\catalyst-frontend` |
| Backend | `f:\Railway Project Backend\Catalyst App\functions\catalyst_backend` |
| Frontend Build | `f:\Railway Project Backend\Catalyst App\catalyst-frontend\build` |
| Catalyst Config | `f:\Railway Project Backend\Catalyst App\catalyst.json` |
| Backend Entry | `f:\Railway Project Backend\Catalyst App\functions\catalyst_backend\app.py` |

---

## 🌐 ACCESS POINTS

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React SPA (UI) |
| Login | http://localhost:3000/login | Authentication page |
| Dashboard | http://localhost:3000/dashboard | Admin dashboard |
| API Health | http://localhost:9000/api/health | Backend health check |
| API Base | http://localhost:9000/api | All API endpoints |

---

## 📊 TEST CREDENTIALS

**Default Admin User**:
- Email: `admin@example.com`
- Password: `admin123`
- Role: `admin`

---

## 🔐 BROWSER DEVELOPER TOOLS (F12)

### Check Console
```
F12 → Console tab
Look for: Red errors, CORS errors, 404 messages
```

### Check Network Requests
```
F12 → Network tab
Reload page (F5)
Check: Status codes (should be 200-201), response times (< 1 sec)
```

### Check SessionStorage
```
F12 → Application → SessionStorage
Look for: rail_access_token (JWT token)
```

### Check Local Storage
```
F12 → Application → Local Storage
Look for: Any app configuration data
```

---

## 📋 PRE-STARTUP CHECKLIST

```cmd
REM Check requirements
node --version
npm --version
python --version
catalyst --version

REM Check files exist
dir "f:\Railway Project Backend\Catalyst App\catalyst-frontend\build\index.html"
dir "f:\Railway Project Backend\Catalyst App\functions\catalyst_backend\app.py"
dir "f:\Railway Project Backend\Catalyst App\catalyst.json"

REM Navigate to app
cd "f:\Railway Project Backend\Catalyst App"

REM Start
catalyst serve
```

---

## ✅ VERIFICATION CHECKLIST

After startup, verify:

```cmd
REM Test Frontend
curl http://localhost:3000

REM Test Backend Health
curl http://localhost:9000/api/health

REM Test Auth
curl -X POST http://localhost:9000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@example.com\",\"password\":\"admin123\"}"
```

---

## 🐛 COMMON ERRORS & FIXES

### Error: Catalyst command not found
```cmd
npm install -g @zoho/catalyst-cli
catalyst login
```

### Error: Port 3000 already in use
```cmd
catalyst serve --port 3001
```

### Error: Frontend shows blank page
```cmd
cd catalyst-frontend && npm run build && cd .. && catalyst serve
```

### Error: CORS error in browser
```
Check app.py has:
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
Restart backend
```

### Error: 401 Unauthorized
```
Check token in sessionStorage (F12)
Try login again
Check JWT_SECRET_KEY matches
```

---

## 📝 TESTING WORKFLOW

```cmd
REM Step 1: Start server
cd "f:\Railway Project Backend\Catalyst App"
catalyst serve

REM Step 2: In browser, open
http://localhost:3000

REM Step 3: Test login
Email: admin@example.com
Password: admin123

REM Step 4: In another terminal, test API
curl http://localhost:9000/api/health
curl http://localhost:9000/api/trains -H "Authorization: Bearer <token>"

REM Step 5: Test CRUD on UI
Create/Read/Update/Delete trains via web interface

REM Step 6: Check results
F12 → Console (no errors)
F12 → Network (all 200s)
F12 → Application (token exists)
```

---

## 🎯 SUCCESS INDICATORS

✅ Frontend loads (http://localhost:3000)  
✅ Backend responds (http://localhost:9000/api/health = 200)  
✅ Login works (POST /api/auth/login = 200)  
✅ Can view data (GET /api/trains = 200)  
✅ Can create (POST /api/trains = 201/200)  
✅ Can update (PUT /api/trains/:id = 200)  
✅ Can delete (DELETE /api/trains/:id = 200)  
✅ No console errors (F12)  
✅ No CORS errors  

---

## 📊 LOGS & MONITORING

### Watch Live Log
```cmd
REM Windows PowerShell
Get-Content catalyst-live.log -Wait
```

### Check Last Errors
```cmd
findstr /i "error" catalyst-live.log
```

### Search Logs
```cmd
findstr "keyword" catalyst-live.log
```

---

## 🔄 RESTART PROCEDURE

```cmd
REM Stop current server
Ctrl + C (in terminal running catalyst serve)

REM Wait 5 seconds for cleanup

REM Start again
catalyst serve
```

---

## 📞 QUICK HELP

| Need | Command | File |
|------|---------|------|
| Full test guide | Read | CATALYST_LOCAL_TEST_GUIDE.md |
| Startup steps | Read | CATALYST_STARTUP_VERIFICATION.md |
| API reference | Read | CLAUDE_CATALYST_SKILLSET.md |
| Database schema | Read | CLOUDSCALE_DATABASE_SCHEMA.md |
| Troubleshooting | Read | CATALYST_LOCAL_TEST_GUIDE.md (Troubleshooting) |

---

## 📍 All in One

**Complete startup from scratch**:

```cmd
REM Navigate
cd "f:\Railway Project Backend\Catalyst App"

REM Check prerequisites
node --version
npm --version
python --version

REM If frontend needs rebuild
cd catalyst-frontend && npm run build && cd ..

REM Start catalyst
catalyst serve

REM In another terminal, test
curl http://localhost:3000
curl http://localhost:9000/api/health
```

**Then open browser**: http://localhost:3000

**Login with**: admin@example.com / admin123

---

**Ready to go!** 🚀
