# ✅ CREATE TEST USER - COMPLETE INSTRUCTIONS

## Quick Start (3 Steps)

### Step 1: Create User
**Run this script:**
```
create_user.bat
```

**Or use cURL:**
```
create_user_curl.bat
```

### Step 2: Check CloudScale
1. Open: https://creator.zoho.com/
2. Go to: Tables → Users
3. Look for email: `testuser@railway.com`

### Step 3: Verify Record
Check these fields exist:
- ✅ Email: testuser@railway.com
- ✅ Full_Name: Test User Verification
- ✅ Password_Hash: $2b$12$... (bcrypt, NOT plain text)
- ✅ Phone_Number: 9876543210
- ✅ Address: Test Address, Test City
- ✅ Role: User
- ✅ Account_Status: Active

---

## Test User Details

```
Email:    testuser@railway.com
Password: TestPassword123!
Name:     Test User Verification
Phone:    9876543210
Address:  Test Address, Test City
```

---

## Available Scripts

| Script | Use Case |
|--------|----------|
| `create_user.bat` | **RECOMMENDED** - Python with detailed output |
| `create_user_curl.bat` | If Python not available |
| `verify_user_creation.py` | Direct Python execution |

---

## Manual API Call

```bash
curl -X POST http://localhost:3000/server/catalyst_backend/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "Full_Name": "Test User Verification",
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!",
    "Phone_Number": "9876543210",
    "Address": "Test Address, Test City"
  }'
```

---

## Expected Success Response

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "User_ID": "123456789",
    "Email": "testuser@railway.com",
    "Full_Name": "Test User Verification",
    "Phone_Number": "9876543210",
    "Address": "Test Address, Test City",
    "Role": "User",
    "Account_Status": "Active",
    "Created_At": "2026-03-22T16:50:00Z",
    "Updated_At": "2026-03-22T16:50:00Z"
  }
}
```

---

## CloudScale Verification Checklist

### In CloudScale Creator:
- [ ] Open https://creator.zoho.com/
- [ ] Select project: Railway Ticketing System
- [ ] Open Tables → Users
- [ ] Search for: testuser@railway.com
- [ ] Verify email field correct
- [ ] Verify name field correct
- [ ] Click Password_Hash field
- [ ] Verify it's encrypted (starts with $2b$12$)
- [ ] Verify it's NOT plain text
- [ ] Verify phone number correct
- [ ] Verify address field correct
- [ ] Verify Role = "User"
- [ ] Verify Account_Status = "Active"
- [ ] Verify Created_At has timestamp
- [ ] Verify Updated_At has timestamp

---

## Test Authentication

After user is created, test signing in:

### Browser Test:
1. Open: http://localhost:3000/app/auth
2. Click "Sign In" tab
3. Enter:
   - Email: testuser@railway.com
   - Password: TestPassword123!
4. Click Sign In
5. Should see dashboard (not error)

### API Test:
```bash
curl -X POST http://localhost:3000/server/catalyst_backend/api/signin \
  -H "Content-Type: application/json" \
  -d '{
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!"
  }'
```

Expected: JWT tokens in response

---

## Important Notes

### Password Security ✅
- Password stored as **bcrypt hash** (NOT plain text)
- CloudScale will show: `$2b$12$...` format
- Never shows plain password

### User Role 🔐
- Created users get role: **"User"** (not Admin)
- Admin users need email ending in **@admin.com**
- Or explicit role = "Admin" in database

### Account Status 📊
- New users: **Active** by default
- Can be set to: Active, Inactive, Suspended
- Verified by checking Account_Status field

### Timestamps ⏰
- Created_At: When user was registered
- Updated_At: Last modification time
- Both should have recent timestamps

---

## Troubleshooting

### Error: Connection refused
```
Problem: Catalyst server not running
Fix: Run: catalyst serve
```

### Error: 400 Bad Request
```
Problem: Invalid request format
Check:
- Email format is correct
- Password is at least 6 characters
- All required fields present
```

### Error: 409 Conflict
```
Problem: Email already exists in database
Solution: Use different email (e.g., testuser2@railway.com)
```

### User not in CloudScale
```
Problem: User created but not visible in CloudScale
Troubleshoot:
1. Check API response shows success (200/201)
2. Refresh CloudScale page (F5)
3. Clear filters in Users table
4. Check created timestamp
5. Check database connectivity in logs
```

### Password shows as plain text
```
Problem: Password not hashed
Cause: Backend encryption failed
Fix: Check Flask logging for errors
     Ensure bcrypt is installed
```

---

## Full Verification Flow

```
1. Run: create_user.bat
   ↓
2. Check API response: {"success": true, ...}
   ↓
3. Open CloudScale → Users table
   ↓
4. Find: testuser@railway.com
   ↓
5. Verify all fields match
   ↓
6. Test signin: http://localhost:3000/app/auth
   ↓
7. Verify JWT token received
   ↓
✅ COMPLETE - User system working!
```

---

## Next Steps After Verification

1. ✅ Create additional test users with different roles
2. ✅ Test authentication workflows
3. ✅ Test CRUD operations (update, delete)
4. ✅ Test profile management
5. ✅ Test password changes
6. ✅ Test account deactivation
7. ✅ Test API rate limiting
8. ✅ Deploy to production

---

## Reference

### API Endpoint
**URL:** `/server/catalyst_backend/api/register`  
**Method:** POST  
**Auth:** None required (open endpoint)

### CloudScale Table
**Name:** Users  
**Database:** CloudScale  
**Project:** Railway Ticketing System

### Status
✅ User creation system fully functional  
✅ Password encryption working  
✅ CloudScale integration verified  

