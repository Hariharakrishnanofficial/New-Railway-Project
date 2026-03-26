# POSTMAN TESTING - STEP BY STEP

## ❌ NO TOKEN NEEDED FOR REGISTRATION

Registration endpoint is **PUBLIC** - any user can register without authentication.

Token is only needed for:
- Getting profile
- Updating profile
- Changing password
- Account settings

---

## STEP 1: Open Postman

1. Open Postman app
2. Create new request (Click "+" tab or "New" button)

---

## STEP 2: Set Request Method

1. Click on method dropdown (currently shows "GET")
2. Select: **POST**

---

## STEP 3: Enter URL

1. Paste this URL:
```
http://localhost:3000/server/catalyst_backend/api/auth/register
```

---

## STEP 4: Add Headers

1. Click on **Headers** tab
2. Click in **Key** column, type: `Content-Type`
3. Click in **Value** column, type: `application/json`
4. Press Enter

✅ Should look like:
```
Content-Type | application/json
```

---

## STEP 5: Add Request Body

1. Click on **Body** tab
2. Select **raw** radio button (at bottom)
3. From dropdown (right side), select **JSON**
4. Copy and paste this sample record:

```json
{
  "Full_Name": "John Doe",
  "Email": "john.doe@railway.com",
  "Password": "Password123!",
  "Phone_Number": "9876543210",
  "Address": "123 Main Street, City, Country"
}
```

✅ Your screen should show:
- Body tab selected
- Raw button selected
- JSON format selected
- JSON code pasted in text area

---

## STEP 6: Send Request

1. Click **Send** button (top right)
2. Wait for response (should appear at bottom)

---

## EXPECTED RESPONSE (Success - 201)

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

✅ **Status should show: 201 Created** (top right corner)

---

## EXPECTED RESPONSE (Error)

```json
{
  "success": false,
  "error": "Registration failed",
  "details": "Email already registered"
}
```

or

```json
{
  "success": false,
  "error": "Invalid request: JSON body required",
  "details": "..."
}
```

---

## SAMPLE RECORDS TO TEST

### Test User 1:
```json
{
  "Full_Name": "Alice Smith",
  "Email": "alice.smith@railway.com",
  "Password": "SecurePass123!",
  "Phone_Number": "9876543211",
  "Address": "456 Oak Avenue, Mumbai, India"
}
```

### Test User 2:
```json
{
  "Full_Name": "Bob Johnson",
  "Email": "bob.johnson@railway.com",
  "Password": "MyPassword456!",
  "Phone_Number": "9876543212",
  "Address": "789 Pine Road, Delhi, India"
}
```

### Test User 3 (Admin - email ends with @admin.com):
```json
{
  "Full_Name": "Admin User",
  "Email": "admin@admin.com",
  "Password": "AdminPass789!",
  "Phone_Number": "9876543213",
  "Address": "Admin Building, City, Country"
}
```

---

## FIELD REQUIREMENTS

| Field | Required | Min Length | Notes |
|-------|----------|-----------|-------|
| Full_Name | ✅ Yes | - | Any text |
| Email | ✅ Yes | - | Must have @, must be unique |
| Password | ✅ Yes | 6 chars | Min 6 characters |
| Phone_Number | ❌ Optional | - | Any format |
| Address | ❌ Optional | - | Any text |

---

## TESTING CHECKLIST

- [ ] Postman is open
- [ ] Method is POST
- [ ] URL pasted correctly
- [ ] Headers tab has `Content-Type: application/json`
- [ ] Body tab selected
- [ ] Raw button selected
- [ ] JSON format selected
- [ ] Sample record pasted
- [ ] Send button clicked
- [ ] Response shows status 201
- [ ] Response contains "success": true

---

## NEXT: AFTER SUCCESSFUL REGISTRATION

### To Sign In with Created User:

**URL:** `http://localhost:3000/server/catalyst_backend/api/auth/signin`

**Method:** POST

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "Email": "john.doe@railway.com",
  "Password": "Password123!"
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
      "Email": "john.doe@railway.com",
      "Full_Name": "John Doe",
      "Role": "User"
    }
  }
}
```

✅ **Now you have access_token for protected endpoints**

---

## USING ACCESS TOKEN FOR PROTECTED ENDPOINTS

### Example: Get Profile

**URL:** `http://localhost:3000/server/catalyst_backend/api/auth/profile`

**Method:** GET

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <YOUR_ACCESS_TOKEN>
```

Example:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## TROUBLESHOOTING

### Issue: Status 400 - "Invalid request: JSON body required"
**Fix:** Check that Body is set to "raw" and "JSON" format

### Issue: Status 409 - "Email already registered"
**Fix:** Use a different email address (each email can only register once)

### Issue: Status 500 - "Registration failed"
**Fix:** 
- Check all required fields are filled
- Verify JSON syntax is correct
- Check backend logs

### Issue: Can't connect
**Fix:** Make sure `catalyst serve` is running

---

## QUICK CHECKLIST FOR EACH TEST

```
1. URL: http://localhost:3000/server/catalyst_backend/api/auth/register
2. Method: POST
3. Headers: Content-Type: application/json
4. Body: raw JSON with all required fields
5. Click Send
6. Check Status Code (201 = success)
7. Check "success": true in response
```

---

## FINAL SUMMARY

✅ **NO TOKEN NEEDED** for registration  
✅ **Registration is PUBLIC** endpoint  
✅ **Token only needed** after signin  
✅ **Use sample records** provided above  
✅ **Each email** can only register once  
✅ **Password minimum** 6 characters  

**Ready to test?** Start from STEP 1 above! 🚀

