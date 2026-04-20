"""
Permission Validator - Smart Railway Ticketing System

Provides helpers for employee RBAC permission checks.

Exports:
  - require_permission(module, action): Flask route decorator
  - validate_permissions(permissions): Basic permissions schema validation
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, List

from flask import jsonify

from core.session_middleware import (
    get_current_user_id,
    get_current_user_role,
    require_session_employee,
)
from services.employee_service import get_permissions_for_role


def validate_permissions(permissions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate (and lightly normalize) an employee permissions payload.

    Expected shape:
      {
        "modules": { "<module>": ["view", "edit", ...], ... },
        "admin_access": bool,
        "can_invite_employees": bool
      }
    """
    if permissions is None:
        raise ValueError("permissions is required")
    if not isinstance(permissions, dict):
        raise ValueError("permissions must be an object")

    modules = permissions.get("modules") or {}
    if not isinstance(modules, dict):
        raise ValueError("permissions.modules must be an object")

    normalized_modules: Dict[str, List[str]] = {}
    for module_name, actions in modules.items():
        if not isinstance(module_name, str) or not module_name.strip():
            raise ValueError("permissions.modules keys must be non-empty strings")
        if not isinstance(actions, list) or not all(isinstance(a, str) for a in actions):
            raise ValueError(f"permissions.modules['{module_name}'] must be a list of strings")
        normalized_modules[module_name] = [a.strip() for a in actions if a and a.strip()]

    admin_access = bool(permissions.get("admin_access", False))
    can_invite_employees = bool(permissions.get("can_invite_employees", False))

    return {
        "modules": normalized_modules,
        "admin_access": admin_access,
        "can_invite_employees": can_invite_employees,
    }


def require_permission(module: str, action: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator: requires a valid employee session + RBAC permission for (module, action).
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def permission_checked(*args: Any, **kwargs: Any) -> Any:
            # Session middleware should have populated request context.
            employee_row_id = get_current_user_id()
            if not employee_row_id:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "code": "AUTH_REQUIRED",
                            "message": "Authentication required",
                        }
                    ),
                    401,
                )

            # Evaluate permissions using the configured role map (with defaults fallback).
            role = (get_current_user_role() or "").strip()
            role_permissions = get_permissions_for_role(role)
            if role_permissions.get("admin_access"):
                return f(*args, **kwargs)

            allowed_actions = (role_permissions.get("modules") or {}).get(module, [])
            if action in allowed_actions:
                return f(*args, **kwargs)

            return (
                jsonify(
                    {
                        "status": "error",
                        "code": "FORBIDDEN",
                        "message": "You do not have permission to perform this action",
                    }
                ),
                403,
            )

        # Ensure an employee session exists before checking permissions.
        return require_session_employee(permission_checked)

    return decorator


__all__ = ["require_permission", "validate_permissions"]
