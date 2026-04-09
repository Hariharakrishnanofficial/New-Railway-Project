# 📍 Routing Architecture - Production Standard

**Version:** 2.1  
**Updated:** April 3, 2026  
**Status:** Production Ready

---

## Overview

This app uses **BrowserRouter** with `basename="/app"` for clean URLs without hash fragments.

---

## URL Structure

### Production URLs

```
Base URL: https://smart-railway-app-60066581545.development.catalystserverless.in

Frontend (Clean URLs - no hash):
  /app/                    → Redirects to login if not authenticated
  /app/login              → Login page
  /app/register           → Registration page
  /app/forgot-password    → Password reset
  /app/search             → Train search
  /app/book               → Booking page
  /app/my-bookings        → User's bookings
  /app/pnr-status         → PNR lookup
  /app/cancel-ticket      → Cancel booking
  /app/profile            → User profile

Admin:
  /app/admin              → Admin dashboard
  /app/admin/users        → User management
  /app/admin/trains       → Train management
  /app/admin/stations     → Station management
  /app/admin/bookings     → Booking management
  /app/admin/routes       → Route management
  /app/admin/fares        → Fare management
  /app/admin/inventory    → Inventory
  /app/admin/logs         → Admin logs
  /app/admin/settings     → Settings

Backend API:
  /server/smart_railway_app_function/health
  /server/smart_railway_app_function/session/login
  /server/smart_railway_app_function/session/logout
  /server/smart_railway_app_function/session/validate
  /server/smart_railway_app_function/session/register/initiate
  /server/smart_railway_app_function/session/register/verify
```

---

## Route Types

### 1. Public Routes (`PublicRoute`)

**Behavior:** Only accessible when NOT logged in. Redirects to home if already authenticated.

**Routes:**
- `/login` - Login page
- `/register` - Registration page  
- `/forgot-password` - Password reset
- `/admin-setup` - Initial admin setup

```javascript
<PublicRoute>
  <AuthPage />
</PublicRoute>
```

### 2. Protected Routes (`ProtectedRoute`)

**Behavior:** Requires authentication. Redirects to login if not authenticated, saving the original URL for redirect after login.

**Routes:**
- `/` - Home/Dashboard
- `/search` - Train search
- `/book` - Booking
- `/my-bookings` - User's bookings
- `/pnr-status` - PNR lookup
- `/cancel-ticket` - Cancel booking
- `/profile` - User profile

```javascript
<ProtectedRoute>
  <PassengerLayout />
</ProtectedRoute>
```

### 3. Admin Routes (`AdminRoute`)

**Behavior:** Requires authentication + admin role. Redirects to login if not authenticated, or home if not admin.

**Routes:**
- `/admin` - Admin dashboard
- `/admin/users` - User management
- `/admin/trains` - Train management
- `/admin/stations` - Station management
- `/admin/bookings` - Booking management
- `/admin/train-routes` - Route management
- `/admin/fares` - Fare management
- `/admin/inventory` - Inventory
- `/admin/announcements` - Announcements
- `/admin/logs` - Admin logs
- `/admin/settings` - Settings

```javascript
<AdminRoute>
  <AdminLayout />
</AdminRoute>
```

---

## Routing Features

### ✅ Implemented (Production Standard)

1. **BrowserRouter with basename** - Clean URLs, no hash fragments
2. **Route guards** - Public, Protected, Admin routes
3. **Login redirect** - Saves original URL, redirects after login
4. **Loading states** - Shows spinner while checking auth
5. **404 page** - Proper not found page
6. **Nested routes** - Layouts with child routes
7. **Admin protection** - Role-based access control

### Redirect After Login

When a user tries to access a protected page:
1. They're redirected to `/login`
2. The original URL is saved in `location.state.from`
3. After successful login, they're redirected back

```javascript
// In ProtectedRoute
if (!isAuthenticated) {
  return <Navigate to="/login" state={{ from: location }} replace />;
}

// In PublicRoute (after login)
const from = location.state?.from?.pathname || '/';
return <Navigate to={from} replace />;
```

---

## Configuration

### package.json

```json
{
  "homepage": "/app",
  ...
}
```

The `homepage` field tells React where the app is hosted. This ensures:
- Assets load from `/app/static/...`
- Links work correctly in production

### BrowserRouter with basename

**We use BrowserRouter with `basename="/app"` for:**
1. Clean URLs without hash fragments (`/app/login` instead of `/app/#/login`)
2. Better SEO potential
3. Standard URL structure

**URLs look like:**
```
https://domain.com/app/login
https://domain.com/app/search
https://domain.com/app/admin/users
```

**Note:** BrowserRouter requires server-side configuration to serve `index.html` for all routes under `/app/`. Zoho Catalyst handles this automatically for web client apps.

---

## Route Hierarchy

```
BrowserRouter (basename="/app")
└── ToastProvider
    └── AuthProvider
        └── Routes
            ├── /login (PublicRoute → AuthPage)
            ├── /register (PublicRoute → AuthPage)
            ├── /forgot-password (PublicRoute → ForgotPasswordPage)
            ├── /admin-setup (PublicRoute → AuthPage)
            │
            ├── / (ProtectedRoute → PassengerLayout)
            │   ├── index → HomePage
            │   ├── search → SearchPage
            │   ├── book → BookingPage
            │   ├── my-bookings → MyBookingsPage
            │   ├── pnr-status → PnrStatusPage
            │   ├── cancel-ticket → CancelTicketPage
            │   └── profile → ProfilePage
            │
            ├── /admin (AdminRoute → AdminLayout)
            │   ├── index → DashboardPage
            │   ├── users → UsersPage
            │   ├── admin-users → AdminUsersPage
            │   ├── trains → TrainsPage
            │   ├── stations → StationsPage
            │   ├── bookings → AdminBookingsPage
            │   ├── train-routes → TrainRoutesPage
            │   ├── fares → FaresPage
            │   ├── inventory → InventoryPage
            │   ├── announcements → AnnouncementsPage
            │   ├── logs → AdminLogsPage
            │   └── settings → SettingsPage
            │
            └── * (NotFoundPage)
```

---

## Navigation

### Programmatic Navigation

```javascript
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();
  
  const handleClick = () => {
    navigate('/search');          // Navigate to search
    navigate('/admin/users');     // Navigate to admin users
    navigate(-1);                 // Go back
    navigate('/', { replace: true }); // Replace history
  };
}
```

### Link Component

```javascript
import { Link } from 'react-router-dom';

<Link to="/search">Search Trains</Link>
<Link to="/admin/users">Manage Users</Link>
```

### Standard Links (HTML)

```html
<!-- These work because BrowserRouter handles /app/ routes -->
<a href="/app/login">Login</a>
<a href="/app/search">Search</a>
```

---

## Best Practices

### 1. Always Use Route Guards

```javascript
// ✅ Good - Uses route guard
<ProtectedRoute>
  <MyPage />
</ProtectedRoute>

// ❌ Bad - No protection
<Route path="/secret" element={<SecretPage />} />
```

### 2. Handle Loading States

```javascript
// ✅ Good - Shows loading while checking auth
if (loading) return <LoadingSpinner />;
```

### 3. Use Nested Routes for Layouts

```javascript
// ✅ Good - Layout wraps children
<Route path="/" element={<Layout />}>
  <Route index element={<Home />} />
  <Route path="about" element={<About />} />
</Route>
```

### 4. Provide 404 Handler

```javascript
// ✅ Good - Catches unknown routes
<Route path="*" element={<NotFoundPage />} />
```

---

## Testing Routes

### Manual Testing Checklist

- [ ] `/app/` - Redirects to login if not authenticated
- [ ] `/app/login` - Shows login page
- [ ] `/app/register` - Shows registration page
- [ ] Login → Redirects to home
- [ ] Login from protected page → Redirects back to that page
- [ ] `/app/admin` - Redirects to login for non-admin
- [ ] `/app/admin` - Shows dashboard for admin
- [ ] Unknown route → Shows 404 page
- [ ] Browser back/forward works
- [ ] Refresh on any page works

---

## Troubleshooting

### "Page not found" on refresh

**Cause:** Server not configured to serve index.html for all routes  
**Fix:** Zoho Catalyst handles this automatically. If using another host, configure catch-all routing.

### Login redirect loop

**Cause:** Auth check returning wrong value  
**Fix:** Check `isAuthenticated` and `loading` state

### Admin route accessible to non-admin

**Cause:** Missing AdminRoute wrapper or role check  
**Fix:** Wrap with `<AdminRoute>`

### Assets not loading

**Cause:** Missing `homepage` in package.json  
**Fix:** Add `"homepage": "/app"` to package.json

---

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| BrowserRouter | ✅ | Clean URLs with basename="/app" |
| Public routes | ✅ | Login, register, forgot-password |
| Protected routes | ✅ | Passenger pages |
| Admin routes | ✅ | Admin pages with role check |
| Login redirect | ✅ | Returns to original page |
| 404 page | ✅ | Proper not found handler |
| Loading states | ✅ | Shows spinner during auth check |
| Nested layouts | ✅ | PassengerLayout, AdminLayout |

**Status:** Production Ready ✅

---

**Documentation Version:** 2.1  
**Last Updated:** April 3, 2026
