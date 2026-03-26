# Create Test User in CloudScale

## Quick Start

### Option 1: Using Python Script (Recommended)
```bash
Double-click: create_user.bat
```

### Option 2: Using cURL
```bash
Double-click: create_user_curl.bat
```

### Option 3: Manual API Call
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

## Test User Details

```json
{
  "Full_Name": "Test User Verification",
  "Email": "testuser@railway.com",
  "Password": "TestPassword123!",
  "Phone_Number": "9876543210",
  "Address": "Test Address, Test City"
}
```

---

## What Happens

### On Success (201/200)
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "User_ID": "123456789",
    "Email": "testuser@railway.com",
    "Full_Name": "Test User Verification",
    "Role": "User",
    "Account_Status": "Active",
    "Created_At": "2026-03-22T16:50:00Z"
  }
}
```

### Expected Fields in CloudScale
- ✅ User_ID (auto-generated)
- ✅ Email: testuser@railway.com
- ✅ Full_Name: Test User Verification
- ✅ Password_Hash: (bcrypt encrypted, NOT plain text)
- ✅ Phone_Number: 9876543210
- ✅ Address: Test Address, Test City
- ✅ Role: User
- ✅ Account_Status: Active
- ✅ Created_At: (timestamp)
- ✅ Updated_At: (timestamp)

---

## Verify in CloudScale

1. Open CloudScale Creator Web Console
2. Navigate to: **Tables → Users**
3. Look for email: `testuser@railway.com`
4. Verify fields:
   - [ ] Email correct
   - [ ] Full_Name correct
   - [ ] Password_Hash is bcrypt (looks like: $2b$12$...)
   - [ ] Role is "User"
   - [ ] Account_Status is "Active"
   - [ ] All timestamps populated

---

## Testing Sign In

After user is created, test authentication:

```bash
curl -X POST http://localhost:3000/server/catalyst_backend/api/signin \
  -H "Content-Type: application/json" \
  -d '{
    "Email": "testuser@railway.com",
    "Password": "TestPassword123!"
  }'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "User_ID": "123456789",
      "Email": "testuser@railway.com",
      "Full_Name": "Test User Verification",
      "Role": "User"
    }
  }
}
```

---

## Troubleshooting

### Error: Connection refused
```
⚠️ Catalyst server not running
→ Run: catalyst serve
```

### Error: 400 Bad Request
```
⚠️ Check email format and password requirements
→ Email must be valid format
→ Password must be at least 6 characters
→ Password must contain alphanumeric characters
```

### Error: 409 Conflict
```
⚠️ Email already exists
→ Try different email address
→ Example: testuser2@railway.com
```

### User not appearing in CloudScale
```
⚠️ Check CloudScale connectivity
→ Verify TABLES configuration in code
→ Check API logs for errors
→ Try creating user again
```

---

## Scripts Available

| Script | Method | When to Use |
|--------|--------|-------------|
| `create_user.bat` | Python + requests | Most reliable |
| `create_user_curl.bat` | cURL command | If Python unavailable |
| `create_test_user.py` | Direct Python | For debugging |

---

## API Endpoint Details

**Endpoint:** `POST /api/register`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "Full_Name": "string (required)",
  "Email": "string (required, unique)",
  "Password": "string (required, min 6 chars)",
  "Phone_Number": "string (optional)",
  "Address": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": { /* user object */ }
}
```

---

## Next Steps

1. ✅ Run one of the user creation scripts
2. ✅ Check API response for success
3. ✅ Navigate to CloudScale and verify record
4. ✅ Test signin with created credentials
5. ✅ Test API operations with JWT token

---

## Quick Command Reference

```bash
# Create user
create_user.bat

# Or with curl directly
curl -X POST http://localhost:3000/server/catalyst_backend/api/register \
  -H "Content-Type: application/json" \
  -d '{"Full_Name":"Test","Email":"test@railway.com","Password":"Test123!"}'

# Verify in CloudScale
# → Open CloudScale Creator
# → Tables → Users
# → Search for email: testuser@railway.com
```

