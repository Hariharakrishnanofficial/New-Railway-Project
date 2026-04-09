# User and Employee Login Flow With Sample Values
Date: 2026-04-09

This document explains the session-based login flow with concrete sample values for both passengers and employees.

## Overview
The backend uses server-side sessions.

- The server stores the raw `Session_ID` in the database.
- The browser receives a signed cookie value.
- The frontend stores the CSRF token in memory.
- Protected requests send the cookie automatically and include `X-CSRF-Token` for state-changing operations.

## Common Sample Values

### Passenger sample
- Email: `rahul.sharma@example.com`
- Password: `Passenger@123`
- User ID in Users table: `501245`
- Raw Session_ID stored in DB: `847362918374628193`
- Signed cookie sent to browser: `847362918374628193.8f2a1c9d4e7b...`
- CSRF token: `zQ3rM8bN1pL5vX2kA7tY9uH4sD6fG0cJ`

### Employee sample
- Email: `meera.patel@railway.com`
- Password: `Employee@123`
- Employee ROWID in Employees table: `900118`
- Raw Session_ID stored in DB: `673829104556781245`
- Signed cookie sent to browser: `673829104556781245.1ac0f2e9b7c3...`
- CSRF token: `Qm8kX1sT4pV7nC2dL5rH9aF0zW6eJ3u`

## Passenger Login Flow

### 1) Login request
Request:

```http
POST /session/login
Content-Type: application/json
```

```json
{
  "email": "rahul.sharma@example.com",
  "password": "Passenger@123"
}
```

### 2) Backend processing
The backend does the following:

1. Looks up the user by email in the `Users` table.
2. Verifies the password hash.
3. Confirms account status is active.
4. Creates a new session record.
5. Stores the raw session ID in the `Sessions` table.
6. Signs the session ID before sending it to the browser.
7. Returns the CSRF token in the response body.

### 3) Response example
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "user": {
      "id": "501245",
      "fullName": "Rahul Sharma",
      "email": "rahul.sharma@example.com",
      "phoneNumber": "+91-9876543210",
      "role": "USER",
      "accountStatus": "Active",
      "type": "user"
    },
    "type": "user",
    "csrfToken": "zQ3rM8bN1pL5vX2kA7tY9uH4sD6fG0cJ"
  }
}
```

### 4) Cookie set by server
```http
Set-Cookie: railway_sid=847362918374628193.8f2a1c9d4e7b...; HttpOnly; Secure; SameSite=Strict; Path=/
```

### 5) What the browser stores
- `railway_sid` cookie: signed session value
- CSRF token: kept in frontend memory only
- User object: kept in React state or context

### 6) Protected request example
Request:

```http
PUT /session/profile
Cookie: railway_sid=847362918374628193.8f2a1c9d4e7b...
X-CSRF-Token: zQ3rM8bN1pL5vX2kA7tY9uH4sD6fG0cJ
Content-Type: application/json
```

```json
{
  "fullName": "Rahul Kumar Sharma",
  "phoneNumber": "+91-9998887776"
}
```

### 7) Internal backend behavior for protected request
The middleware:

1. Reads the cookie.
2. Unsings and normalizes it to the raw session ID.
3. Loads the session row from `Sessions`.
4. Stores the raw session ID in request context.
5. Validates the CSRF token against the raw session ID.
6. Allows the route handler to continue.

## Employee Login Flow

### 1) Login request
Request:

```http
POST /session/employee/login
Content-Type: application/json
```

```json
{
  "email": "meera.patel@railway.com",
  "password": "Employee@123"
}
```

### 2) Backend processing
The backend does the following:

1. Authenticates directly against the `Employees` table.
2. Maps the employee profile to a response object.
3. Creates a server-side session with `user_type = employee`.
4. Stores the raw session ID in the database.
5. Sends the signed cookie to the browser.
6. Returns the CSRF token.

### 3) Response example
```json
{
  "status": "success",
  "message": "Employee login successful",
  "data": {
    "employee": {
      "id": "900118",
      "employeeId": "EMP-10021",
      "fullName": "Meera Patel",
      "email": "meera.patel@railway.com",
      "role": "ADMIN",
      "department": "Operations",
      "designation": "Operations Manager",
      "phoneNumber": "+91-9988776655",
      "type": "employee"
    },
    "user": {
      "id": "900118",
      "employeeId": "EMP-10021",
      "fullName": "Meera Patel",
      "email": "meera.patel@railway.com",
      "role": "ADMIN",
      "department": "Operations",
      "designation": "Operations Manager",
      "phoneNumber": "+91-9988776655",
      "type": "employee"
    },
    "csrfToken": "Qm8kX1sT4pV7nC2dL5rH9aF0zW6eJ3u"
  }
}
```

### 4) Cookie set by server
```http
Set-Cookie: railway_sid=673829104556781245.1ac0f2e9b7c3...; HttpOnly; Secure; SameSite=Strict; Path=/
```

### 5) Employee protected request example
Request:

```http
POST /session/admin/sessions/revoke-all
Cookie: railway_sid=673829104556781245.1ac0f2e9b7c3...
X-CSRF-Token: Qm8kX1sT4pV7nC2dL5rH9aF0zW6eJ3u
Content-Type: application/json
```

```json
{}
```

### 6) Internal backend behavior for employee request
The middleware:

1. Reads the cookie.
2. Normalizes it to the raw session ID.
3. Confirms the session belongs to an employee.
4. Validates the CSRF token.
5. Uses the raw session ID for current-session comparison.
6. Lets the admin route proceed.

## Logout Flow

### Request
```http
POST /session/logout
Cookie: railway_sid=847362918374628193.8f2a1c9d4e7b...
```

### Behavior
1. Browser sends the signed cookie automatically.
2. Backend normalizes the cookie value to the raw session ID.
3. Backend revokes the matching session row in the database.
4. Backend clears the cookie.
5. Frontend clears in-memory CSRF and user state.

### Response
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```

## Why This Flow Is Safer Than Client-Side Tokens
- The browser cannot read the session cookie because it is `HttpOnly`.
- The session can be revoked immediately on the server.
- CSRF protection is enforced for state-changing requests.
- Session IDs are validated against the database on every protected request.

## Key Rules To Remember
- Use the signed cookie only as transport format.
- Use the raw session ID for database queries.
- Keep CSRF token in frontend memory, not localStorage.
- Use the same session cookie name across login, validation, and logout.

## Quick Summary
- Passenger login: `Users` table -> session row -> signed cookie -> CSRF token.
- Employee login: `Employees` table -> session row -> signed cookie -> CSRF token.
- Middleware normalizes the cookie and uses the raw session ID internally.
