#!/usr/bin/env python3
"""
Update Postman Collection with Session and Employee Endpoints
"""

import json
from pathlib import Path

# File paths
original_file = Path("functions/smart_railway_app_function/docs/Smart_Railway_API.postman_collection.json")

# Load the collection
with open(original_file, 'r', encoding='utf-8') as f:
    collection = json.load(f)

print("Updating Postman collection...")
print(f"Collection: {collection['info']['name']}")

# Add new collection variables
new_variables = [
    {"key": "sessionId", "value": "", "type": "string"},
    {"key": "csrfToken", "value": "", "type": "string"},
    {"key": "employeeId", "value": "", "type": "string"},
    {"key": "invitationId", "value": "", "type": "string"},
    {"key": "invitationToken", "value": "", "type": "string"}
]

# Check if variables already exist
existing_var_keys = {var['key'] for var in collection.get('variable', [])}
for var in new_variables:
    if var['key'] not in existing_var_keys:
        collection['variable'].append(var)
        print(f"  + Added variable: {var['key']}")

# Update collection description
collection['info']['description'] = """Complete REST API collection for Smart Railway Ticketing System v2.0

Base URL: {{baseUrl}}
Authentication: Session-based (HttpOnly cookies) or Bearer Token (JWT)

## Setup Instructions:
1. Set `baseUrl` variable to your server URL
2. For passengers: Run 'Session Auth > Passenger Login'
3. For employees: Run 'Session Auth > Employee Login'
4. Session ID and CSRF token are auto-saved
5. All authenticated requests use session cookies automatically

## Session Variables:
- sessionId: Current session ID
- csrfToken: CSRF token for state-changing requests
- employeeId: Current employee ID (for employee sessions)
- invitationId: Last created invitation ID
- invitationToken: Invitation token for registration"""

print("  + Updated collection description")

# ============================================================================
# SESSION AUTH ENDPOINTS (Add new folder)
# ============================================================================

session_auth_folder = {
    "name": "01A. Session Auth",
    "item": [
        {
            "name": "Passenger Login",
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            "var jsonData = pm.response.json();",
                            "if (jsonData.status === 'success') {",
                            "    pm.collectionVariables.set('csrfToken', jsonData.data.csrf_token);",
                            "    pm.collectionVariables.set('userId', jsonData.data.user_id);",
                            "    pm.test('Login successful', function() {",
                            "        pm.expect(jsonData.status).to.eql('success');",
                            "    });",
                            "}"
                        ],
                        "type": "text/javascript"
                    }
                }
            ],
            "request": {
                "auth": {"type": "noauth"},
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": '{\n    "email": "passenger@example.com",\n    "password": "password123"\n}'
                },
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/session/login",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "session", "login"]
                },
                "description": "Login as passenger user. Sets HttpOnly session cookie automatically."
            },
            "response": []
        },
        {
            "name": "Employee Login",
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            "var jsonData = pm.response.json();",
                            "if (jsonData.status === 'success') {",
                            "    pm.collectionVariables.set('csrfToken', jsonData.data.csrf_token);",
                            "    pm.collectionVariables.set('employeeId', jsonData.data.employee_id);",
                            "    pm.test('Employee login successful', function() {",
                            "        pm.expect(jsonData.status).to.eql('success');",
                            "        pm.expect(jsonData.data.user_type).to.eql('employee');",
                            "    });",
                            "}"
                        ],
                        "type": "text/javascript"
                    }
                }
            ],
            "request": {
                "auth": {"type": "noauth"},
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": '{\n    "email": "admin@railway.com",\n    "password": "admin123"\n}'
                },
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/session/employee/login",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "session", "employee", "login"]
                },
                "description": "Login as employee/admin. Sets HttpOnly session cookie automatically."
            },
            "response": []
        },
        {
            "name": "Validate Session",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/session/validate",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "session", "validate"]
                },
                "description": "Validate current session and return user/employee data."
            },
            "response": []
        },
        {
            "name": "Logout",
            "request": {
                "method": "POST",
                "header": [{"key": "X-CSRF-Token", "value": "{{csrfToken}}"}],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/session/logout",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "session", "logout"]
                },
                "description": "Logout and destroy session. Clears session cookie."
            },
            "response": []
        }
    ],
    "description": "Session-based authentication endpoints using HttpOnly cookies."
}

# ============================================================================
# EMPLOYEE MANAGEMENT ENDPOINTS (Add new folder)
# ============================================================================

employee_folder = {
    "name": "02A. Employees",
    "item": [
        {
            "name": "Send Invitation",
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            "var jsonData = pm.response.json();",
                            "if (jsonData.status === 'success') {",
                            "    pm.collectionVariables.set('invitationId', jsonData.data.invitation_id);",
                            "    pm.collectionVariables.set('invitationToken', jsonData.data.registration_link.split('invitation=')[1]);",
                            "    pm.test('Invitation sent', function() {",
                            "        pm.expect(jsonData.status).to.eql('success');",
                            "    });",
                            "}"
                        ],
                        "type": "text/javascript"
                    }
                }
            ],
            "request": {
                "method": "POST",
                "header": [
                    {"key": "Content-Type", "value": "application/json"},
                    {"key": "X-CSRF-Token", "value": "{{csrfToken}}"}
                ],
                "body": {
                    "mode": "raw",
                    "raw": '{\n    "email": "employee@example.com",\n    "role": "Employee",\n    "department": "Operations",\n    "designation": "Station Master"\n}'
                },
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/invite",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "invite"]
                },
                "description": "Send employee invitation email (Admin only)."
            },
            "response": []
        },
        {
            "name": "List Invitations",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/invitations?limit=50",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "invitations"],
                    "query": [
                        {"key": "limit", "value": "50"}
                    ]
                },
                "description": "List all employee invitations (Admin only)."
            },
            "response": []
        },
        {
            "name": "Refresh Invitation",
            "request": {
                "method": "POST",
                "header": [{"key": "X-CSRF-Token", "value": "{{csrfToken}}"}],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/invitations/{{invitationId}}/refresh",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "invitations", "{{invitationId}}", "refresh"]
                },
                "description": "Refresh invitation expiry (Admin only)."
            },
            "response": []
        },
        {
            "name": "Reinvite Employee",
            "request": {
                "method": "POST",
                "header": [{"key": "X-CSRF-Token", "value": "{{csrfToken}}"}],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/invitations/{{invitationId}}/reinvite",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "invitations", "{{invitationId}}", "reinvite"]
                },
                "description": "Resend invitation email (Admin only)."
            },
            "response": []
        },
        {
            "name": "Get All Employees",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees?limit=100",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees"],
                    "query": [
                        {"key": "limit", "value": "100"}
                    ]
                },
                "description": "List all employees (Admin only)."
            },
            "response": []
        },
        {
            "name": "Get Employee by ID",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/{{employeeId}}",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "{{employeeId}}"]
                },
                "description": "Get employee details (Admin only)."
            },
            "response": []
        },
        {
            "name": "Update Employee",
            "request": {
                "method": "PUT",
                "header": [
                    {"key": "Content-Type", "value": "application/json"},
                    {"key": "X-CSRF-Token", "value": "{{csrfToken}}"}
                ],
                "body": {
                    "mode": "raw",
                    "raw": '{\n    "full_name": "Updated Name",\n    "department": "New Department",\n    "designation": "New Position"\n}'
                },
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/{{employeeId}}",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "{{employeeId}}"]
                },
                "description": "Update employee details (Admin only)."
            },
            "response": []
        },
        {
            "name": "Deactivate Employee",
            "request": {
                "method": "POST",
                "header": [{"key": "X-CSRF-Token", "value": "{{csrfToken}}"}],
                "url": {
                    "raw": "{{baseUrl}}/server/smart_railway_app_function/admin/employees/{{employeeId}}/deactivate",
                    "host": ["{{baseUrl}}"],
                    "path": ["server", "smart_railway_app_function", "admin", "employees", "{{employeeId}}", "deactivate"]
                },
                "description": "Deactivate employee account (Admin only)."
            },
            "response": []
        }
    ],
    "description": "Employee management endpoints for admin users."
}

# Insert new folders after Authentication folder
collection['item'].insert(1, session_auth_folder)
collection['item'].insert(2, employee_folder)

print("  + Added folder: 01A. Session Auth (4 endpoints)")
print("  + Added folder: 02A. Employees (8 endpoints)")

# Save updated collection
with open(original_file, 'w', encoding='utf-8') as f:
    json.dump(collection, f, indent='\t', ensure_ascii=False)

print("\nCollection updated successfully!")
print(f"Total folders: {len(collection['item'])}")
print(f"Total variables: {len(collection['variable'])}")
print(f"\nBackup saved at: functions/smart_railway_app_function/docs/Smart_Railway_API.postman_collection.backup.json")
print(f"Updated file: {original_file}")
