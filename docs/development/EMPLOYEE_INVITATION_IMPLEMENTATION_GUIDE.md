# Employee Invitation and Login Implementation Guide

> Last Updated: April 8, 2026  
> Status: Active implementation guide

## Purpose
This guide explains how the employee invitation flow works end to end, how user and employee login are handled, and how to operate and troubleshoot the feature in daily development.

## What Is Implemented

### Invitation and Registration
- Admin can send employee invitations from the admin UI.
- Invitation email includes a tokenized registration link.
- Employee can register through invitation token.
- Invitation is marked used after successful registration.

### Login Separation
- User and employee login are handled with separate backend endpoints.
- Frontend supports login mode selection.
- Session and CSRF behavior are consistent for both login types.

## Key Files and Responsibilities

### Backend
- routes and handlers:
  - functions/smart_railway_app_function/routes/employee_invitation_routes.py
  - functions/smart_railway_app_function/routes/session_auth.py
- business logic:
  - functions/smart_railway_app_function/services/employee_invitation_service.py
  - functions/smart_railway_app_function/services/employee_service.py
- data access:
  - functions/smart_railway_app_function/repositories/cloudscale_repository.py

### Frontend
- invitation management UI:
  - railway-app/src/pages/admin/EmployeeInvitation.jsx
- invitation registration UI:
  - railway-app/src/pages/auth/RegisterPage.jsx
- login UI:
  - railway-app/src/pages/auth/LoginPage.jsx
  - railway-app/src/pages/auth/AuthPage.jsx
- routing:
  - railway-app/src/App.js
- API client and auth context:
  - railway-app/src/services/sessionApi.js
  - railway-app/src/context/SessionAuthContext.jsx

## End-to-End Flow

## 1) Admin Sends Invitation
1. Admin opens Employee Invitations page.
2. Admin enters email (department and designation are optional).
3. Frontend calls POST /admin/employees/invite.
4. Backend validates role and email uniqueness against Employees and Users.
5. Backend creates invitation token and invitation record.
6. Backend sends invitation email.

Result:
- Invitation row is created.
- Invitation appears in invitation list.
- Recipient gets registration link.

## 2) Employee Registers Using Invitation
1. Employee clicks emailed link with invitation query parameter.
2. Frontend route resolves employee registration page.
3. Frontend submits employee registration payload with invitation token.
4. Backend verifies token, expiry, and usage status.
5. Backend creates user and employee records.
6. Backend marks invitation as used.

Result:
- Employee account is created.
- Invitation status changes to used.

## 3) User and Employee Login
1. Login UI lets the user choose login mode (user or employee).
2. Frontend sends credentials with selected login type.
3. Backend endpoint differs by mode:
   - user login endpoint
   - employee login endpoint
4. On success, session cookie and CSRF token are established.

Result:
- Passenger users proceed to passenger routes.
- Staff users (employee or admin) proceed to admin routes.

## Routing Details You Must Keep
- Employee invitation links expect employee registration route to exist.
- Frontend router includes employee registration path and maps it to RegisterPage.
- If this route is removed or renamed, invitation links will fail.

## API Summary

### Admin Invitation APIs
- POST /admin/employees/invite
- GET /admin/employees/invitations
- POST /admin/employees/invitations/{id}/refresh
- POST /admin/employees/invitations/{id}/reinvite

### Employee Registration API
- POST /employee/register

### Authentication APIs
- POST /session/login
- POST /session/employee/login

## Validation Rules and Current Behavior

### Invitation Form
- Required:
  - email
- Optional:
  - department
  - designation
- Role defaults to Employee unless changed to Admin.

### Backend Invitation Safety
- Duplicate check in Employees table.
- Duplicate check in Users table.
- Existing active invitation check.
- Secure random invitation token generation.
- Invitation expiry window from environment configuration.

### Registration Safety
- Token must be valid, unused, and not expired.
- Password length validated.
- Duplicate account prevention.
- Invitation marked used only after account creation succeeds.

## Operational Handling Guide

## Daily Admin Operation
1. Open Employee Invitations.
2. Enter email and choose role.
3. Optionally set department and designation.
4. Send invitation.
5. Monitor status cards and invitation list.
6. Use Refresh or Reinvite for expired or stale invites.

## Handling Failed Sends
- If invitation record is created but email send fails:
  - invitation may still exist in database
  - retry via Reinvite action
  - verify email service configuration

## Handling Expired Links
- Use Refresh to extend expiry and resend.
- Use Reinvite to generate a new token and resend.

## Handling Duplicate Email Errors
- Check if the email already exists as:
  - passenger in Users
  - employee in Employees
- Use a different email or clean up stale test data as needed.

## Troubleshooting Checklist

### Invite Button Fails
- Verify current user session has admin privileges.
- Confirm API path /admin/employees/invite is reachable.
- Check backend logs for validation errors.

### Email Not Received
- Confirm invitation created in invitation list.
- Verify mail service credentials and sender configuration.
- Use Reinvite and check backend logs for email provider response.

### Invitation Link Opens 404 or Wrong Screen
- Confirm router includes employee registration route.
- Confirm link format matches frontend route expectations.

### Employee Cannot Login
- Confirm registration completed successfully.
- Confirm employee login endpoint is used.
- Confirm account status is active.

## Recommended Test Sequence
1. Send invitation with only email.
2. Open invitation list and verify pending status.
3. Register via invitation link.
4. Verify invitation becomes used.
5. Login as employee from login page in employee mode.
6. Login as user from login page in user mode.

## Change Management Notes
- Keep invitation link format and router path aligned.
- Keep session auth and login mode handling consistent across:
  - LoginPage
  - AuthPage
  - SessionAuthContext
  - sessionApi
- If you modify response payload fields, update both frontend parsing and backend responses together.

## File Update Log for This Guide
- Added this implementation guide document.
- Reflects current behavior where invitation form accepts email-only input.
- Reflects current routing and login mode handling.
