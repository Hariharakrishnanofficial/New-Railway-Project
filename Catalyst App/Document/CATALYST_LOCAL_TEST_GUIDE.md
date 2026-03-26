# 🚀 Catalyst App - Local Testing & Startup Guide

## 📋 Pre-Startup Checklist

### Requirements
- [ ] Catalyst CLI installed (`catalyst --version`)
- [ ] Node.js/npm installed (for frontend)
- [ ] Python 3.8+ installed (for backend)
- [ ] Frontend build exists (`catalyst-frontend/build/`)
- [ ] Backend dependencies ready
- [ ] .env files configured

### Check Before Starting
```bash
# Check Catalyst CLI
catalyst --version

# Check Node.js
node --version
npm --version

# Check Python
python --version
```

---

## 🚀 Starting the Application

### Option 1: Using Windows Batch Script (Recommended)
```bash
cd "f:\Railway Project Backend\Catalyst App"
start.bat
```

### Option 2: Manual Catalyst Serve Command
```bash
cd "f:\Railway Project Backend\Catalyst App"
catalyst serve
```

### Option 3: With Custom Port
```bash
catalyst serve --port 3000
```

---

## 📊 Expected Output

### When Catalyst Starts Successfully

```
Starting Catalyst serve...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Catalyst Development Server Started
✓ Frontend:  http://localhost:3000
✓ Backend:   http://localhost:9000
✓ Health:    http://localhost:3000/api/health
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### What Gets Started
- 🟢 **Frontend** (React SPA): http://localhost:3000
- 🟢 **Backend** (Flask Functions): http://localhost:9000
- 🟢 **Database** (CloudScale local): In-memory/local

---

## ✅ Testing Checklist

### Step 1: Test Frontend (http://localhost:3000)

#### Visual Test
- [ ] Page loads without 404 error
- [ ] Sidebar visible on left
- [ ] Top bar with navigation visible
- [ ] Dashboard/Overview page displays
- [ ] No console errors (F12 → Console tab)

#### Navigation Test
- [ ] Click "Trains" → Page loads
- [ ] Click "Stations" → Page loads
- [ ] Click "Users" → Page loads
- [ ] Click "Bookings" → Page loads
- [ ] Click "Search" → Search form visible

#### Storage Test (F12 → Application → SessionStorage)
- [ ] After login: `rail_access_token` visible
- [ ] Token format: `eyJ0eXAiOiJKV1QiLCJhbGc...` (JWT)

---

### Step 2: Test Backend API (http://localhost:9000/api)

#### Health Check
```bash
curl http://localhost:9000/api/health
# Expected: {"status": "ok", "timestamp": "2026-03-22T..."}
```

#### Auth Endpoint
```bash
curl -X POST http://localhost:9000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
# Expected: {"status": "success", "token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "user": {...}}
```

#### Station List
```bash
curl http://localhost:9000/api/stations \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
# Expected: {"status": "success", "data": [...], "count": 5}
```

#### Train List
```bash
curl http://localhost:9000/api/trains \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
# Expected: {"status": "success", "data": [...], "count": 10}
```

#### Search Trains
```bash
curl "http://localhost:9000/api/search/trains?from=STA001&to=STA002&date=2026-03-25" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
# Expected: {"status": "success", "results": [...]}
```

---

### Step 3: Test Frontend-Backend Integration

#### 3.1: Test Login Flow
1. Go to http://localhost:3000
2. Login page should load
3. Enter test credentials:
   - Email: `admin@example.com`
   - Password: `admin123`
4. Click "Sign In"
5. Should redirect to Dashboard (if working)
6. Check Network tab (F12) for POST /api/auth/login request
7. Check response: Should have `token` and `user` data

#### 3.2: Test CRUD Operation (Create)
1. Navigate to **Trains** page
2. Click **"Add Train"** button
3. Fill form:
   - Train Name: "Express 101"
   - Train Number: "12345"
   - Capacity: 500
   - Status: "Active"
4. Click "Submit"
5. Check Network tab (F12) for POST /api/trains request
6. Expected response: `{"status": "success", "id": 1, "message": "Train created"}`
7. Table should refresh with new train

#### 3.3: Test CRUD Operation (Read)
1. On Trains page, observe table
2. Click any train row
3. Details should display
4. Check Network tab for GET /api/trains/:id request

#### 3.4: Test CRUD Operation (Update)
1. Click edit icon on a train row
2. Modify a field (e.g., change capacity)
3. Click "Save"
4. Check Network tab for PUT /api/trains/:id request
5. Table should update

#### 3.5: Test CRUD Operation (Delete)
1. Click delete icon on a train row
2. Confirm dialog appears
3. Click "Delete"
4. Check Network tab for DELETE /api/trains/:id request
5. Train should disappear from table

#### 3.6: Test Search
1. Go to **Search** page
2. Select:
   - From Station
   - To Station
   - Travel Date
   - Class (optional)
3. Click "Search"
4. Check Network: GET /api/search/trains
5. Results should display (or "No trains found")
6. Try booking (if results shown)

---

### Step 4: Check Browser Console

**F12 → Console Tab - Should be clear of errors:**

✅ No red errors
✅ No 404 errors
✅ No CORS errors
✅ No "undefined" warnings
✅ No "Cannot find module" messages

**Common Errors to Look For:**
```
❌ Access-Control-Allow-Origin error → CORS misconfigured
❌ 401 Unauthorized → JWT token issue
❌ 404 Not Found → Backend endpoint missing
❌ Failed to fetch → Backend not running
❌ Cannot set property → State management issue
```

---

### Step 5: Check Network Tab

**F12 → Network Tab - Monitor API calls:**

1. **Login Request**
   - URL: `http://localhost:9000/api/auth/login`
   - Method: `POST`
   - Status: `200` ✅
   - Response: Contains `token`

2. **Trains List Request**
   - URL: `http://localhost:9000/api/trains`
   - Method: `GET`
   - Status: `200` ✅
   - Response: Array of trains

3. **Create Train Request**
   - URL: `http://localhost:9000/api/trains`
   - Method: `POST`
   - Status: `201` ✅ (or 200)
   - Response: Created train object

4. **Check Timing**
   - Fast requests: < 500ms ✅
   - Slow requests: > 2000ms ⚠️ (might need optimization)

---

## 🐛 Troubleshooting

### Issue 1: "Catalyst command not found"
```
ERROR: 'catalyst' is not recognized as an internal or external command

SOLUTION:
1. Install Catalyst CLI globally
2. npm install -g @zoho/catalyst-cli
3. catalyst login
4. catalyst serve
```

### Issue 2: Port Already in Use
```
ERROR: Port 3000 is already in use

SOLUTION:
Option A: Kill process on port 3000
Option B: Use different port
  catalyst serve --port 3001

Windows Kill:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Issue 3: Frontend Shows Blank Page
```
CAUSE: Build folder missing or index.html not served

SOLUTION:
1. Build frontend: cd catalyst-frontend && npm run build
2. Verify build/ folder exists
3. Restart catalyst serve
4. Check Network tab for index.html request
```

### Issue 4: Backend Not Starting
```
ERROR: Backend functions not running

SOLUTION:
1. Check Python version: python --version (need 3.8+)
2. Check dependencies: pip list | grep zcatalyst
3. Check .env file exists
4. Check app.py is in functions/catalyst_backend/
5. Review catalyst-live.log for errors
```

### Issue 5: Login Fails (401 Unauthorized)
```
CAUSE: JWT token issue or wrong credentials

SOLUTION:
1. Check backend log for auth errors
2. Verify JWT_SECRET_KEY in config.py
3. Check credentials: admin@example.com / admin123
4. Try creating new test user
5. Check token format in sessionStorage
```

### Issue 6: API Calls Return 404
```
CAUSE: Endpoint not found in backend

SOLUTION:
1. Verify route exists in functions/catalyst_backend/routes/
2. Check route is registered in app.py
3. Check path spelling matches
4. Restart backend
5. Check Network tab for exact URL
```

### Issue 7: CORS Error
```
ERROR: Access-Control-Allow-Origin header missing

SOLUTION:
1. Check app.py has CORS configured
2. Verify localhost:3000 is in CORS_ALLOWED_ORIGINS
3. Restart backend
4. Clear browser cache (Ctrl+Shift+Delete)
5. Try in incognito mode
```

### Issue 8: Database Connection Failed
```
ERROR: CloudScale connection error

SOLUTION:
1. Run database_setup.py: python database_setup.py
2. Check catalyst-config.json is valid
3. Verify tables were created
4. Check .env DATABASE_URL is correct
5. Check catalyst.json is configured properly
```

---

## 📝 Test Results Template

Use this to document your testing:

```markdown
## Test Execution – [Date & Time]

### Environment
- Frontend URL: http://localhost:3000
- Backend URL: http://localhost:9000
- Catalyst CLI Version: [version]
- Node.js Version: [version]
- Python Version: [version]

### Frontend Tests
- [ ] Page loads without 404
- [ ] Navigation works
- [ ] Login successful
- [ ] Dashboard displays
- [ ] Console has no errors

### Backend Tests
- [ ] Health check passes
- [ ] Auth endpoint working
- [ ] Trains API responds
- [ ] Stations API responds
- [ ] Search API responds

### Integration Tests
- [ ] Login → Dashboard ✅/❌
- [ ] Create Train ✅/❌
- [ ] Read Trains ✅/❌
- [ ] Update Train ✅/❌
- [ ] Delete Train ✅/❌
- [ ] Search Trains ✅/❌

### Issues Found
1. [Issue description]
2. [Issue description]

### Status
🟢 **PASS** / 🟡 **PARTIAL** / 🔴 **FAIL**
```

---

## 🔄 Quick Start Commands

```bash
# Navigate to Catalyst App
cd "f:\Railway Project Backend\Catalyst App"

# Option 1: Use batch script
start.bat

# Option 2: Manual catalyst serve
catalyst serve

# Option 3: On custom port
catalyst serve --port 3001

# Option 4: Build frontend first, then serve
cd catalyst-frontend && npm run build && cd .. && catalyst serve

# Option 5: Stop running catalyst
Ctrl+C (in terminal)
```

---

## 📊 Expected Performance

### Page Load Times
- **Frontend Initial**: 1-3 seconds (first load)
- **Frontend Subsequent**: 200-500ms
- **API Endpoints**: < 500ms each
- **Total Dashboard Load**: 2-5 seconds

### Database Queries
- **Get all records**: < 100ms
- **Get single record**: < 50ms
- **Create record**: < 200ms
- **Update record**: < 200ms
- **Delete record**: < 200ms

---

## 🎯 Success Criteria

### Green Light ✅ (All Working)
- [ ] Frontend loads at http://localhost:3000
- [ ] Backend API responds at http://localhost:9000/api/health
- [ ] Login works successfully
- [ ] All CRUD operations work
- [ ] Search functionality works
- [ ] No console errors
- [ ] No CORS errors
- [ ] Network requests < 1 second
- [ ] Database queries work
- [ ] Integration flow complete

### Yellow Light 🟡 (Partial Working)
- Some pages load but not all
- Some API endpoints work but not all
- Login works but CRUD doesn't
- Performance is slow (> 2 seconds)

### Red Light 🔴 (Not Working)
- Frontend won't load
- Backend won't start
- Login fails
- Critical API endpoints return errors
- Database not accessible

---

## 📞 Getting Help

If tests fail:
1. Check the **Troubleshooting** section above
2. Review **catalyst-live.log** for backend errors
3. Check browser console (F12) for frontend errors
4. Check Network tab (F12) for API response details
5. Review this guide's common issues

---

**Ready to test!** 🚀
