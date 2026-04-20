# Role & Permission (RBAC) - Concepts, Development, and Phases
Smart Railway Ticketing System  
**Date:** April 9, 2026

---

## 1. Introduction

Role-Based Access Control (RBAC) is a security model that restricts system access based on a user's role and assigned permissions. In the Smart Railway Ticketing System, RBAC ensures that only authorized users can perform sensitive operations, supporting both security and operational flexibility.

---

## 2. Core Concepts

### 2.1 User Types
- **Passenger (User):** Ticket buyers, limited to booking and profile actions.
- **Employee:** Staff, including Admins and regular employees, with varying permissions.

### 2.2 Roles
- **Admin:** Full system access, can manage all modules and permissions.
- **Employee:** Limited access, actions depend on assigned permissions.
- **Custom Roles:** (e.g., Customer Service, Operations) with tailored permissions.

### 2.3 Permissions
- **Format:** `module.action` (e.g., `bookings.create`, `trains.delete`)
- **Stored as:** JSON in Employees table, e.g.
  ```json
  {
    "modules": {
      "bookings": ["view", "create", "cancel"],
      "trains": ["view"]
    },
    "admin_access": false
  }
  ```
- **Granularity:** Can specify actions and restrictions per module.

### 2.4 Modules & Actions
- **Modules:** bookings, trains, stations, users, employees, reports, announcements, settings, audit_logs
- **Actions:** view, create, edit, delete, cancel, refund, export, invite, deactivate, manage_permissions

### 2.5 Restrictions
- Advanced conditions (e.g., refund limit, export format) can be encoded in the permissions JSON.

---

## 3. Authentication vs Authorization
- **Authentication:** Verifies user identity (session, HMAC cookie, CSRF token)
- **Authorization:** Checks if user has permission for a specific action (via decorators and permission checks)

---

## 4. RBAC Development Phases

### Phase 1: Core Infrastructure
- Implement `core/permission_validator.py` for permission parsing, validation, and decorators.
- Extend `employee_service.py` to fetch and validate permissions.
- Store permissions as JSON in Employees table.

### Phase 2: Route Migration
- Replace role-only decorators with `@require_permission(module, action)` in all sensitive routes.
- Example:
  ```python
  @require_permission('bookings', 'cancel')
  def cancel_booking(...):
      ...
  ```
- Update all admin/employee CRUD, bookings, trains, stations, announcements, and audit log routes.

### Phase 3: Permission Management & Audit
- Add admin endpoints to view, update, and validate permissions.
- Log all permission changes to `Admin_Logs` for auditability.
- Example endpoints:
  - `GET /admin/permissions/defaults`
  - `PUT /admin/employees/<id>/permissions`
  - `GET /admin/permissions/audit`

### Phase 4: Testing & Documentation
- Unit and integration tests for permission checks and bypass scenarios.
- Document permission structure, decorator usage, and admin workflows.

---

## 5. Security Model & Best Practices
- **Defense in Depth:** Multiple layers (HTTPS, session, CSRF, RBAC, audit)
- **Least Privilege:** Grant only necessary permissions per role
- **Audit Trail:** All permission changes and denials are logged
- **Validation:** Permission JSON is schema-validated before saving
- **Admin Override:** Admins can bypass checks if `admin_access` is true

---

## 6. Example Permission Object
```json
{
  "modules": {
    "bookings": ["view", "create", "cancel"],
    "trains": ["view", "edit"]
  },
  "admin_access": false,
  "can_invite_employees": false,
  "version": 1
}
```

---

## 7. Decorator Usage Pattern
```python
@require_permission('trains', 'edit')
def edit_train(...):
    ...

@require_any_permission('reports.view', 'reports.export')
def get_reports(...):
    ...
```

---

## 8. Implementation Checklist
- [ ] Core permission validator module
- [ ] Route migration to permission-based decorators
- [ ] Admin endpoints for permission management
- [ ] Audit logging for all permission changes
- [ ] Comprehensive tests and documentation

---

## 9. Summary
RBAC in the Smart Railway Ticketing System provides secure, flexible, and auditable access control. By combining role and permission checks, the system enforces least privilege, supports custom roles, and enables safe scaling of operations.
