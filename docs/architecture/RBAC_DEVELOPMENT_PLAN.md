# Role & Permission (RBAC) - Development Plan & Implementation Structure
Smart Railway Ticketing System  
**Date:** April 10, 2026

---

## 1. Overview

This document describes the Role-Based Access Control (RBAC) model for the Smart Railway Ticketing System, including concepts, development phases, and implementation structure for secure, flexible, and auditable access control.

---

## 2. Core Concepts

- **User Types:**
  - Passenger (User): Ticket buyers
  - Employee: Staff (Admin, Employee, Custom roles)
- **Roles:**
  - Admin: Full access
  - Employee: Limited access
  - Custom: E.g., Customer Service, Operations
- **Permissions:**
  - Format: `module.action` (e.g., `bookings.create`)
  - Stored as JSON in Employees table
  - Example:
    ```json
    {
      "modules": {
        "bookings": ["view", "create"],
        "trains": ["view"]
      },
      "admin_access": false
    }
    ```
- **Modules:** bookings, trains, stations, users, employees, reports, announcements, settings, audit_logs
- **Actions:** view, create, edit, delete, cancel, refund, export, invite, deactivate, manage_permissions
- **Restrictions:** Advanced conditions (e.g., refund limit) encoded in permissions JSON

---

## 3. Development Plan

### Phase 1: Core Infrastructure
- Create `core/permission_validator.py` for permission parsing, validation, and decorators
- Extend `employee_service.py` to fetch and validate permissions
- Store permissions as JSON in Employees table

### Phase 2: Route Migration
- Replace role-only decorators with `@require_permission(module, action)` in all sensitive routes
- Update all admin/employee CRUD, bookings, trains, stations, announcements, and audit log routes

### Phase 3: Permission Management & Audit
- Add admin endpoints to view, update, and validate permissions
- Log all permission changes to `Admin_Logs` for auditability
- Example endpoints:
  - `GET /admin/permissions/defaults`
  - `PUT /admin/employees/<id>/permissions`
  - `GET /admin/permissions/audit`

### Phase 4: Testing & Documentation
- Unit and integration tests for permission checks and bypass scenarios
- Document permission structure, decorator usage, and admin workflows

---

## 4. Implementation Structure

### 4.1 Permission Validator Module
- **File:** `core/permission_validator.py`
- **Responsibilities:**
  - Parse and validate permission JSON
  - Provide decorators: `@require_permission`, `@require_any_permission`, `@require_all_permissions`
  - Validate restrictions

### 4.2 Service Layer
- **File:** `services/employee_service.py`
- **Responsibilities:**
  - Fetch employee permissions from DB
  - Validate and create permission objects

### 4.3 Route Protection
- **Pattern:**
  ```python
  @require_permission('bookings', 'cancel')
  def cancel_booking(...):
      ...
  ```
- **Migration:** Replace all `@require_admin`/role checks with permission-based decorators

### 4.4 Permission Management Endpoints
- **File:** `routes/permission_management.py`
- **Endpoints:**
  - `GET /admin/permissions/defaults` - View default templates
  - `POST /admin/permissions/validate` - Validate permission JSON
  - `GET/PUT /admin/employees/<id>/permissions` - View/update employee permissions
  - `GET /admin/permissions/audit` - View audit log

### 4.5 Audit Logging
- **Table:** `Admin_Logs`
- **Events:** Log all permission changes and denials

### 4.6 Testing
- **Files:** `tests/test_permission_validator.py`, `tests/test_permission_decorators.py`, `tests/test_rbac_integration.py`
- **Coverage:** Permission checks, bypass attempts, audit log creation

---

## 5. Example Permission Object
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

## 6. Implementation Checklist
- [ ] Core permission validator module
- [ ] Route migration to permission-based decorators
- [ ] Admin endpoints for permission management
- [ ] Audit logging for all permission changes
- [ ] Comprehensive tests and documentation

---

## 7. Summary

RBAC in the Smart Railway Ticketing System enforces least privilege, supports custom roles, and enables secure, scalable operations. The phased plan ensures a robust, testable, and auditable implementation.
