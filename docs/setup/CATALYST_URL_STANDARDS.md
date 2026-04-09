# 📌 Zoho Catalyst URL Standards

**Your Current URL:** `https://smart-railway-app-60066581545.development.catalystserverless.in/app/./`  
**Issue:** `/app/./` contains redundant `./`

---

## ✅ Correct URL Formats

### Web Client (Frontend)
```
https://smart-railway-app-60066581545.development.catalystserverless.in/app/
```

Or for specific pages:
```
https://smart-railway-app-60066581545.development.catalystserverless.in/app/#/login
https://smart-railway-app-60066581545.development.catalystserverless.in/app/#/register
https://smart-railway-app-60066581545.development.catalystserverless.in/app/#/home
```

### Backend API (Functions)
```
https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function/
```

API endpoints:
```
/server/smart_railway_app_function/health
/server/smart_railway_app_function/session/login
/server/smart_railway_app_function/session/register/initiate
/server/smart_railway_app_function/session/validate
```

---

## Zoho Catalyst URL Structure

```
https://{project-name}-{project-id}.{environment}.catalystserverless.in/{path}
```

| Part | Value | Description |
|------|-------|-------------|
| Project Name | `smart-railway-app` | Your project name |
| Project ID | `60066581545` | Unique project identifier |
| Environment | `development` | `development` or `production` |
| Path | `/app/` or `/server/` | Client or server path |

---

## Environment URLs

### Development
```
https://smart-railway-app-60066581545.development.catalystserverless.in/
```

### Production (after deploying)
```
https://smart-railway-app-60066581545.catalystserverless.in/
```

Note: Production URL **doesn't have** `.development` in it.

---

## Path Meanings

| Path | Purpose | Example |
|------|---------|---------|
| `/app/` | Web client (React frontend) | `/app/#/login` |
| `/server/{function-name}/` | Backend function APIs | `/server/smart_railway_app_function/health` |

---

## ⚠️ What's Wrong with Your URL

```
/app/./  ❌ Wrong
/app/    ✅ Correct
```

The `./` is a "current directory" reference that's redundant in URLs.

**How it might have happened:**
- Incorrect link in your code
- Browser/router adding it automatically
- Build configuration issue

---

## Check Your React Router

If you're using React Router with Hash routing:

**Correct format:**
```javascript
// index.js or App.js
import { HashRouter } from 'react-router-dom';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </HashRouter>
  );
}
```

**Resulting URLs:**
```
/app/#/          → Home
/app/#/login     → Login
/app/#/register  → Register
```

---

## Check Your Base URL Configuration

### In `index.html` or build config:

```html
<!-- Correct -->
<base href="/app/" />

<!-- NOT this -->
<base href="/app/./" />
```

### In `package.json`:

```json
{
  "homepage": "/app"
}
```

Or in `.env`:
```
PUBLIC_URL=/app
```

---

## Correct CORS Origins

In your backend `.env`:
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://smart-railway-app-60066581545.development.catalystserverless.in
```

**Don't include `/app/` in CORS origin** - just the domain.

---

## Summary

| What | Correct URL |
|------|-------------|
| **Frontend** | `https://smart-railway-app-60066581545.development.catalystserverless.in/app/` |
| **Frontend (Login)** | `https://smart-railway-app-60066581545.development.catalystserverless.in/app/#/login` |
| **Backend API** | `https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function/` |

---

## If You Want Clean URLs (No Hash)

Using `BrowserRouter` instead of `HashRouter`:

```javascript
import { BrowserRouter } from 'react-router-dom';
```

URLs become:
```
/app/login
/app/register
```

**But:** This requires server-side configuration to redirect all `/app/*` to `index.html` (Catalyst might not support this easily).

**Recommendation:** Stick with `HashRouter` for Catalyst deployments.

---

**Your corrected URL should be:**
```
https://smart-railway-app-60066581545.development.catalystserverless.in/app/
```

---

**Standard:** ✅ Yes, this is the correct Zoho Catalyst URL format  
**Issue:** Just remove the `./` from your URL
