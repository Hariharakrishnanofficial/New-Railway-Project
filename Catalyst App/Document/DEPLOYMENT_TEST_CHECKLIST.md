# 🧪 Railway Ticketing System - Deployment Test Checklist

**Date**: 2026-03-19
**Environment**: Catalyst Development

---

## 🔗 URLs

| Service | URL |
|---------|-----|
| **Frontend (Catalyst Client)** | `https://railway-ticketing-system-60066581545.development.catalyst-cs.in/` |
| **Backend (AppSail)** | `https://railway-project-backend-50039510865.development.catalystappsail.in/api/` |

---

## 📋 Pre-Deployment Commands

```bash
# Navigate to Catalyst App folder
cd "f:/Railway Project Backend/Catalyst App"

# Login (if needed)
catalyst login

# Deploy client only
catalyst deploy --only client

# Or deploy everything (functions + client)
catalyst deploy
```

---

## ✅ Test Cases

### 1. Backend Health Check
```bash
curl https://railway-project-backend-50039510865.development.catalystappsail.in/api/health
```
**Expected**: `{"status": "healthy", ...}`
**Result**: [ ] PASS / [ ] FAIL

---

### 2. Frontend Loads
- Open: Frontend URL in browser
- **Expected**: React app loads (RailAdmin title visible)
- **Result**: [ ] PASS / [ ] FAIL

---

### 3. CORS Verification (Browser Console)
```javascript
fetch('https://railway-project-backend-50039510865.development.catalystappsail.in/api/health')
  .then(r => r.json())
  .then(d => console.log('✅ CORS OK:', d))
  .catch(e => console.error('❌ CORS Error:', e))
```
**Expected**: No CORS errors, health data logged
**Result**: [ ] PASS / [ ] FAIL

---

### 4. Authentication Tests

#### 4.1 Login Page Renders
- Navigate to: `/login` or login route
- **Expected**: Login form visible
- **Result**: [ ] PASS / [ ] FAIL

#### 4.2 User Login
- Enter: Valid test credentials
- Click: Login
- **Expected**:
  - Token stored in sessionStorage
  - Redirects to dashboard
- **Result**: [ ] PASS / [ ] FAIL

#### 4.3 Verify Token Storage
```javascript
// Browser console after login:
sessionStorage.getItem('rail_access_token')
```
**Expected**: JWT token string (not null)
**Result**: [ ] PASS / [ ] FAIL

#### 4.4 Logout
- Click: Logout button
- **Expected**: Token cleared, redirects to login
- **Result**: [ ] PASS / [ ] FAIL

---

### 5. Core Features Tests

#### 5.1 Train Search
- Navigate to: Search page
- Enter: Source, destination, date
- Click: Search
- **Expected**: Train results displayed
- **Result**: [ ] PASS / [ ] FAIL

#### 5.2 View Train Details
- Click: Any train in results
- **Expected**: Train details, schedule, fares displayed
- **Result**: [ ] PASS / [ ] FAIL

#### 5.3 Create Booking (if logged in)
- Fill: Booking form with passengers
- Submit: Booking
- **Expected**: PNR generated, booking confirmed
- **Result**: [ ] PASS / [ ] FAIL

#### 5.4 PNR Lookup
- Enter: Valid PNR
- Submit
- **Expected**: Booking details displayed
- **Result**: [ ] PASS / [ ] FAIL

---

### 6. Admin Features Tests (Admin Login Required)

#### 6.1 Admin Dashboard
- Login as: Admin user
- Navigate to: Admin dashboard
- **Expected**: Overview stats visible
- **Result**: [ ] PASS / [ ] FAIL

#### 6.2 User Management
- Navigate to: Users page
- **Expected**: User list displayed
- **Result**: [ ] PASS / [ ] FAIL

#### 6.3 Train Management
- Navigate to: Trains page
- Test: View, Add, Edit train
- **Expected**: All CRUD operations work
- **Result**: [ ] PASS / [ ] FAIL

#### 6.4 Reports
- Navigate to: Reports page
- **Expected**: Analytics/revenue data displayed
- **Result**: [ ] PASS / [ ] FAIL

---

### 7. AI Features Tests

#### 7.1 AI Chat Widget
- Open: AI chat widget (bottom right)
- Type: "Find trains from Chennai to Bangalore"
- **Expected**: AI responds with search results
- **Result**: [ ] PASS / [ ] FAIL

#### 7.2 MCP Query
- Navigate to: MCP/AI test page (if available)
- **Expected**: Schema discovery works
- **Result**: [ ] PASS / [ ] FAIL

---

### 8. Error Handling Tests

#### 8.1 Invalid Route (404)
- Navigate to: `/invalid-page-xyz`
- **Expected**: Custom 404 page displayed
- **Result**: [ ] PASS / [ ] FAIL

#### 8.2 Unauthorized Access (401)
- Clear sessionStorage
- Try: Access protected route
- **Expected**: Redirects to login
- **Result**: [ ] PASS / [ ] FAIL

#### 8.3 Admin-Only Page (403)
- Login as: Regular user
- Try: Access admin page directly
- **Expected**: Access denied or redirect
- **Result**: [ ] PASS / [ ] FAIL

---

### 9. Performance Tests

#### 9.1 Page Load Time
- Measure: Initial page load (DevTools)
- **Expected**: < 3 seconds
- **Actual**: _____ seconds
- **Result**: [ ] PASS / [ ] FAIL

#### 9.2 API Response Time
- Measure: /api/health response (Network tab)
- **Expected**: < 1 second
- **Actual**: _____ ms
- **Result**: [ ] PASS / [ ] FAIL

---

## 📊 Test Summary

| Category | Pass | Fail | Total |
|----------|------|------|-------|
| Backend Health | | | 1 |
| Frontend | | | 1 |
| CORS | | | 1 |
| Authentication | | | 4 |
| Core Features | | | 4 |
| Admin Features | | | 4 |
| AI Features | | | 2 |
| Error Handling | | | 3 |
| Performance | | | 2 |
| **TOTAL** | | | **22** |

---

## 🔧 Troubleshooting

### If CORS Error:
1. Check backend config: `Backend/appsail-python/app.py`
2. Verify `CORS_ALLOWED_ORIGINS` includes frontend domain
3. Redeploy backend if changed

### If Login Fails (401):
1. Check: sessionStorage for token
2. Verify: Backend JWT_SECRET_KEY matches
3. Check: Network tab for actual response

### If Frontend Blank:
1. Check: Browser console for errors
2. Verify: dist files deployed correctly
3. Clear browser cache

### If API Not Reachable:
1. Verify: Backend is running (check AppSail status)
2. Check: Network tab for actual URL being called
3. Verify: .env.production has correct URL

---

## ✅ Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| QA | | | |
| Lead | | | |

---

**Status**: [ ] READY FOR PRODUCTION / [ ] NEEDS FIXES

**Notes**:
_________________________________
_________________________________
_________________________________
