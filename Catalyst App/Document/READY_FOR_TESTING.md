# ✅ READY FOR POSTMAN TESTING

## IMPORTANT: NO TOKEN NEEDED FOR REGISTRATION

✅ **Registration is a PUBLIC endpoint** - Anyone can register without token

Token is ONLY needed for:
- Getting profile
- Updating profile  
- Changing password
- Account settings

---

## 3 SAMPLE USERS YOU CAN CREATE

### User 1 - Regular User
```json
{
  "Full_Name": "John Doe",
  "Email": "john.doe@railway.com",
  "Password": "Password123!",
  "Phone_Number": "9876543210",
  "Address": "123 Main Street, Mumbai, India"
}
```

### User 2 - Regular User
```json
{
  "Full_Name": "Sarah Johnson",
  "Email": "sarah.johnson@railway.com",
  "Password": "Sarah456!",
  "Phone_Number": "9876543211",
  "Address": "456 Oak Avenue, Delhi, India"
}
```

### User 3 - Admin User (will get Admin role because email ends with @admin.com)
```json
{
  "Full_Name": "Admin User",
  "Email": "admin@admin.com",
  "Password": "AdminPass789!",
  "Phone_Number": "9876543212",
  "Address": "Admin Building, Head Office, India"
}
```

---

## POSTMAN SETUP (3 MINUTES)

### 1. Open Postman & Create New Request
- Click "+" or "New" button

### 2. Set Method to POST
- Dropdown shows "GET" by default
- Click and select "POST"

### 3. Paste URL
```
http://localhost:3000/server/catalyst_backend/api/auth/register
```

### 4. Add Header
- Tab: Headers
- Key: `Content-Type`
- Value: `application/json`

### 5. Add Body
- Tab: Body
- Select: "raw" radio button
- Dropdown: "JSON"
- Paste one of the sample users above

### 6. Click Send

---

## WHAT YOU'LL SEE

### Success (Status 201):
```json
{
  "success": true,
  "status": "created",
  "data": {
    "message": "User registered successfully",
    "user_id": "123456789",
    "email": "john.doe@railway.com",
    "role": "User"
  }
}
```

### Error (Status 409 - Email Exists):
```json
{
  "success": false,
  "error": "Registration failed",
  "details": "Email already registered"
}
```

### Error (Status 400 - Invalid):
```json
{
  "success": false,
  "error": "Invalid request: JSON body required",
  "details": "..."
}
```

---

## THEN TEST SIGNIN

**Same 3 users can sign in with their email and password**

**Endpoint:** `POST http://localhost:3000/server/catalyst_backend/api/auth/signin`

**Body:**
```json
{
  "Email": "john.doe@railway.com",
  "Password": "Password123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "User_ID": "123456789",
      "Email": "john.doe@railway.com",
      "Full_Name": "John Doe",
      "Role": "User"
    }
  }
}
```

---

## TOKEN USAGE

After signin, you get `access_token`. Use it for protected endpoints:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

Example - Get Profile (protected, needs token):
- **URL:** `http://localhost:3000/server/catalyst_backend/api/auth/profile`
- **Method:** GET
- **Header:** `Authorization: Bearer <access_token>`

---

## FILES TO READ

| File | Purpose |
|------|---------|
| `POSTMAN_STEP_BY_STEP.md` | Detailed step-by-step instructions (READ THIS FIRST) |
| `POSTMAN_QUICK_CARD.txt` | Quick reference card |
| `POSTMAN_GUIDE.md` | Complete testing guide |
| `FIX_UNABLE_TO_SERVE.md` | If you get errors |

---

## QUICK START

1. **Open:** POSTMAN_STEP_BY_STEP.md
2. **Follow:** Each step carefully
3. **Copy:** Sample user JSON
4. **Paste:** Into Postman Body
5. **Send:** Click Send button
6. **Verify:** Status 201, success true

---

## REMEMBER

✅ Registration = NO TOKEN NEEDED  
✅ Each email registers ONCE  
✅ Password minimum 6 characters  
✅ Email must have @ symbol  
✅ Phone and Address are OPTIONAL  
✅ After signin, use access_token for protected endpoints  

---

**You're ready! Start with POSTMAN_STEP_BY_STEP.md** 🚀

