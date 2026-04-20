# Role-Based Access Control (RBAC) Design for Smart Railway Ticketing System

## 1. Architecture Overview

- **Backend:** Modular Flask (Blueprints per module)
- **Frontend:** React (modular, route-based)
- **Database:** Zoho CloudScale (ZCQL)
- **Modules:** Auth, Trains, Tickets, Employees, etc.
- **RBAC Integration:** Centralized roles/permissions, enforced at API and UI layers, extensible for new modules/actions

---

## 2. RBAC Design

### Roles (examples)
- **Admin:** Full access (manage trains, users, employees, reports)
- **Manager:** Manage trains, view reports, manage bookings
- **Employee:** View assigned tasks, assist users
- **User:** Book tickets, view own bookings

### Permissions (examples)
- `train:create`, `train:update`, `train:delete`, `train:view`
- `ticket:book`, `ticket:cancel`, `ticket:view`
- `user:manage`, `employee:manage`, `report:view`
- Each permission: `<module>:<action>`

### Mapping
| Role    | Permissions (examples)                |
|---------|---------------------------------------|
| Admin   | All                                   |
| Manager | train:*, ticket:*, report:view        |
| User    | ticket:book, ticket:view, ticket:cancel |

---

## 3. Database Schema Changes

Add to `docs/architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md`:

### RBAC Tables

#### roles
- id (PK)
- name (string, unique)
- description (string)

#### permissions
- id (PK)
- name (string, unique, e.g., "train:create")
- description (string)

#### role_permissions
- id (PK)
- role_id (FK to roles)
- permission_id (FK to permissions)

#### user_roles
- id (PK)
- user_id (FK to users)
- role_id (FK to roles)

---

## 4. Step-by-Step Implementation Guide

### Backend (Flask)
1. **Define Models/Repositories:** Add models for `Role`, `Permission`, `RolePermission`, `UserRole`.
2. **Middleware/Decorator:** Create `@require_permission('train:create')` decorator to check permissions on protected routes.
3. **Role/Permission Assignment APIs:** Admin endpoints to assign roles to users, permissions to roles.
4. **Update Auth Logic:** On login/session creation, load user’s roles/permissions into session/context.

### Frontend (React)
1. **Store User Roles/Permissions:** On login, fetch and store user’s roles/permissions in app state.
2. **UI Access Control:** Show/hide UI elements based on permissions.
3. **Route Guards:** Protect routes using wrappers that check for required permissions.

---

## 5. Example Code Snippets

### Backend: Permission Decorator
```python
from functools import wraps
from flask import request, abort

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or not user.has_permission(permission):
                abort(403, "Forbidden")
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@train_bp.route('/create', methods=['POST'])
@require_permission('train:create')
def create_train():
    ...
```

### Frontend: Permission Gate
```jsx
export function PermissionGate({ permission, children }) {
  const { permissions } = useAuth();
  return permissions.includes(permission) ? children : null;
}

// Usage
<PermissionGate permission="train:create">
  <Button onClick={handleCreateTrain}>Create Train</Button>
</PermissionGate>
```

---

## 6. Best Practices
- Assign only necessary permissions (Principle of Least Privilege)
- Centralize permission management (avoid hardcoding)
- Log permission checks and access denials
- Enforce permissions on backend (never trust frontend alone)
- Design for extensibility (easy to add new roles/permissions)

---

## 7. Integration Notes
- Default all users to a basic role until roles are assigned
- Gradually add permission checks to modules
- Add admin UI for managing roles/permissions
- Ensure frontend/backend are always in sync for permissions

---

**End of RBAC Design Document**
