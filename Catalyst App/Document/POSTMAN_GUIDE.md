# Postman Collection - User Creation API

## How to Test in Postman

### Request 1: Register User

```
Method: POST
URL: http://localhost:3000/server/catalyst_backend/api/auth/register

Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "Full_Name": "Test User Verification",
  "Email": "testuser@railway.com",
  "Password": "TestPassword123!",
  "Phone_Number": "9876543210",
  "Address": "Test Address, Test City"
}
```

**Expected Response (201):**
```json
{
  "success": true,
  "status": "created",
  "data": {
    "message": "User registered successfully",
    "user_id": "123456789",
    "email": "testuser@railway.com",
    "role": "User"
  }
}
```

---

### Request 2: Sign In

```
Method: POST
URL: http://localhost:3000/server/catalyst_backend/api/auth/signin

Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "Email": "testuser@railway.com",
  "Password": "TestPassword123!"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "status": "authenticated",
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

### Request 3: Get Profile (Protected)

```
Method: GET
URL: http://localhost:3000/server/catalyst_backend/api/auth/profile

Headers:
  Authorization: Bearer <access_token_from_signin>

Example:
  Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "User_ID": "123456789",
    "Email": "testuser@railway.com",
    "Full_Name": "Test User Verification",
    "Phone_Number": "9876543210",
    "Address": "Test Address, Test City",
    "Role": "User",
    "Account_Status": "Active"
  }
}
```

---

## Troubleshooting in Postman

### Issue: Connection refused
- **Solution:** Make sure `catalyst serve` is running
- Check: `http://localhost:3000/server/catalyst_backend/` should be accessible

### Issue: 400 Bad Request
- **Solution:** Check JSON syntax in body
- Make sure: `Content-Type: application/json` header is set
- Select: Body → raw → JSON format

### Issue: 409 Conflict
- **Solution:** Email already registered
- Try: Different email address

### Issue: 500 Internal Server Error
- **Solution:** Check backend logs
- Error details now shown in response (look for `details` field)

### Issue: Still getting "unable to serve the request"
- Check detailed error message in response
- Restart catalyst: `catalyst serve`
- Wait 60 seconds for full startup
- Try test again

---

## Quick Checklist

- [ ] Catalyst server running (`catalyst serve`)
- [ ] API is responding (`/api/health` returns 200)
- [ ] Postman using POST method
- [ ] URL correct: `http://localhost:3000/server/catalyst_backend/api/auth/register`
- [ ] Headers include `Content-Type: application/json`
- [ ] Body is raw JSON format
- [ ] JSON is valid (no syntax errors)
- [ ] Required fields filled: Full_Name, Email, Password
- [ ] Email format is valid (has @)
- [ ] Password is at least 6 characters

---

## After Creating User

1. Open CloudScale: https://creator.zoho.com/
2. Go to: Tables → Users
3. Search for: testuser@railway.com
4. Verify: All fields populated correctly
5. Check: Password field is hashed (starts with $2b$12$)

