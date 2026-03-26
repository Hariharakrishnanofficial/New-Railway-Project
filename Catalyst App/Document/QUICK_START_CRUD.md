# CATALYST APP - QUICK START GUIDE (CRUD AUTH)

## 🚀 What's New

Complete CRUD authentication system with Registration and Sign In functionality.

### Backend
- **7 new endpoints** for user registration, sign in, profile management, password changes, and account deletion
- **Rate limiting** to prevent brute force attacks
- **JWT token generation** for secure authentication
- **Password encryption** with bcrypt

### Frontend
- **AuthPage** - Beautiful tabbed interface for Registration and Sign In
- **ProfilePage** - Enhanced profile management with 3 tabs (Profile, Password, Settings)
- **authApi** - Complete API service layer
- **Modern styling** - Responsive design with gradients and smooth animations

---

## 📋 File Checklist

```
✅ Backend
  □ functions/catalyst_backend/routes/auth_crud.py (NEW)
  □ functions/catalyst_backend/services/auth_crud_service.py (EXISTING, used by routes)
  □ functions/catalyst_backend/routes/__init__.py (UPDATED - added blueprint)

✅ Frontend
  □ catalyst-frontend/src/services/authApi.js (NEW)
  □ catalyst-frontend/src/pages/AuthPage.jsx (NEW)
  □ catalyst-frontend/src/pages/ProfilePage_NEW.jsx (NEW alternative)
  □ catalyst-frontend/src/styles/AuthPage.css (NEW)
  □ catalyst-frontend/src/styles/ProfilePage.css (NEW)
  □ catalyst-frontend/src/App.jsx (UPDATED - routing)
```

---

## 🧪 Testing Locally

### Step 1: Start Catalyst Server

```bash
cd "f:\Railway Project Backend\Catalyst App"
catalyst serve
```

You should see:
```
✓ catalyst_backend: http://localhost:3000/server/catalyst_backend/
```

### Step 2: Access Frontend

Open browser to: **http://localhost:5173**

(If not available, check Catalyst CLI output for the correct port)

### Step 3: Test Registration

1. You should see the **AuthPage** with Sign In and Register tabs
2. Click **Register** tab
3. Fill the form:
   ```
   Full Name: Test User
   Email: testuser@example.com
   Password: TestPass123!
   Confirm Password: TestPass123!
   Phone: +1 555-1234
   Address: 123 Main St
   ```
4. Click **"Create Account"**
5. Expect success message and redirect to Sign In tab

### Step 4: Test Sign In

1. In the Sign In tab, enter:
   ```
   Email: testuser@example.com
   Password: TestPass123!
   ```
2. Click **"Sign In"**
3. Expect redirect to dashboard

### Step 5: Test Profile Management

1. After signing in, look for user menu/profile link
2. Click to open **ProfilePage**
3. Test the three tabs:

   **Tab 1 - Profile Info:**
   - Update Full Name, Phone, Address
   - Click "Save Changes"
   - Verify success message

   **Tab 2 - Change Password:**
   - Current Password: `TestPass123!`
   - New Password: `NewPass456!`
   - Confirm: `NewPass456!`
   - Click "Update Password"
   - Verify success message

   **Tab 3 - Account Settings:**
   - View account information
   - Click "Deactivate" to temporarily disable account
   - Enter password when prompted
   - Account should redirect to signin page

### Step 6: Test Account Recovery

1. Try to sign in with old credentials (should work after deactivation)
2. Account should be reactivated on successful signin

---

## 🔌 API Endpoints

### Public (No Auth Required)

**Register:**
```
POST /api/auth/register
Content-Type: application/json

{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "phone_number": "+1 555-1234",
  "address": "123 Main St"
}
```

**Sign In:**
```
POST /api/auth/signin
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

### Protected (JWT Auth Required)

**Get Profile:**
```
GET /api/auth/profile/:user_id
Authorization: Bearer <access_token>
```

**Update Profile:**
```
PUT /api/auth/profile/:user_id
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Jane Doe",
  "phone_number": "+1 555-5678",
  "address": "456 Oak Ave"
}
```

**Change Password:**
```
POST /api/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "USER_ID",
  "old_password": "SecurePass123",
  "new_password": "NewSecurePass456"
}
```

**Deactivate Account:**
```
POST /api/auth/deactivate-account
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "USER_ID",
  "password": "SecurePass123"
}
```

**Delete Account (Permanent):**
```
POST /api/auth/delete-account
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "USER_ID",
  "password": "SecurePass123"
}
```

---

## 📊 Response Examples

### Success (Registration)
```json
{
  "success": true,
  "status": "created",
  "data": {
    "id": "12345",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "User",
    "account_status": "Active",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Success (Sign In)
```json
{
  "success": true,
  "status": "authenticated",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "12345",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "User"
    }
  }
}
```

### Error
```json
{
  "success": false,
  "error": "Email already exists"
}
```

---

## 🔒 Security Features

- ✅ **Password Hashing** - bcrypt with salt rounds
- ✅ **JWT Tokens** - Secure token-based authentication
- ✅ **Rate Limiting** - Prevents brute force attacks
- ✅ **Password Validation** - Minimum 6 characters required
- ✅ **Email Uniqueness** - Duplicate email checking
- ✅ **CORS Support** - Configured for frontend access
- ✅ **Token Expiry** - Automatic token refresh mechanism

---

## 🐛 Common Issues & Fixes

### Issue: "client-package.json file was not found"
**Solution:** Already fixed in catalyst.json. File should point to `catalyst-frontend` not `catalyst-frontend/build`

### Issue: CORS error accessing API
**Solution:** Ensure CORS headers are set in Flask app (already configured in app.py)

### Issue: "Endpoint not found" when accessing /api/auth/register
**Solution:** Ensure auth_crud blueprint is registered in routes/__init__.py (already done)

### Issue: Tokens not persisting after page reload
**Solution:** Check sessionStorage/localStorage in browser DevTools. Tokens should be saved by authApi.js

### Issue: Password change fails with "wrong password"
**Solution:** Password hashing must match. Verify bcrypt version consistency between backend and frontend

---

## 📁 Project Structure

```
Catalyst App
├── catalyst-frontend/
│   └── src/
│       ├── pages/
│       │   ├── AuthPage.jsx ← NEW (Registration + Sign In)
│       │   └── ProfilePage_NEW.jsx ← NEW (Enhanced profile)
│       ├── services/
│       │   └── authApi.js ← NEW (API calls)
│       ├── styles/
│       │   ├── AuthPage.css ← NEW
│       │   └── ProfilePage.css ← NEW
│       └── App.jsx ← UPDATED (Routing)
│
└── functions/
    └── catalyst_backend/
        ├── routes/
        │   ├── auth_crud.py ← NEW (Endpoints)
        │   └── __init__.py ← UPDATED
        └── services/
            └── auth_crud_service.py (Already exists)
```

---

## 🎯 Next Steps

1. **Verify all files are created** - Run `validate_crud.bat` or `validate_crud.sh`

2. **Start local testing:**
   ```bash
   cd "f:\Railway Project Backend\Catalyst App"
   catalyst serve
   ```

3. **Test complete flow:**
   - Register new account
   - Sign in
   - Update profile
   - Change password
   - Deactivate/Reactivate account

4. **Integrate with existing UI:**
   - Update navigation menu to link to Profile page
   - Add logout button
   - Enhance dashboard home page

5. **Deploy to Catalyst:**
   - Push changes to repository
   - Deploy via Catalyst CLI or web console

---

## 📚 Documentation Files

- `AUTH_CRUD_IMPLEMENTATION_COMPLETE.md` - Comprehensive implementation guide
- `validate_crud.bat` / `validate_crud.sh` - Validation scripts
- `CLAUDE_CATALYST_SKILLSET.md` - Full-stack technical reference
- `catalyst-frontend/claude.md` - Frontend-specific guide

---

## ✨ Features Summary

### Registration (CREATE)
- Accepts: Full Name, Email, Password, Phone (optional), Address (optional)
- Validates: Email uniqueness, password strength (6+ chars)
- Returns: User ID, email, role, account status
- Error: Duplicate email, weak password, missing fields

### Sign In (READ)
- Accepts: Email, Password
- Returns: JWT access token, refresh token, user object
- Error: Invalid credentials, user not found

### Profile (READ)
- Returns: Full user profile with all details
- Protected: JWT authentication required

### Update Profile (UPDATE)
- Allows: Full Name, Phone, Address
- Returns: Updated user object
- Protected: JWT authentication required

### Change Password (UPDATE)
- Requires: Old password verification + new password
- Validates: Password strength, old password match
- Protected: JWT authentication required

### Deactivate Account (SOFT DELETE)
- Reversible: Can sign in again to reactivate
- Requires: Password confirmation
- Status: Sets Account_Status to "Inactive"
- Protected: JWT authentication required

### Delete Account (HARD DELETE)
- Permanent: Cannot be recovered
- Requires: Password confirmation
- Protected: JWT authentication required

---

## 🎓 Learning Resources

- Backend: `functions/catalyst_backend/services/auth_crud_service.py`
- Frontend: `catalyst-frontend/src/services/authApi.js`
- Styling: `catalyst-frontend/src/styles/AuthPage.css`
- Routing: `catalyst-frontend/src/App.jsx`

---

**Status:** ✅ **READY FOR TESTING**

All CRUD operations are implemented and integrated. No configuration changes needed. Start catalyst serve and test!
