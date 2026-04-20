"""
RBAC Routes - Role/Permission introspection.

Role-only RBAC: permissions are derived from code constants, not per-employee DB fields.
These endpoints are intended for admin UI display and troubleshooting.
"""

import logging
from flask import Blueprint, jsonify

from core.permission_validator import require_permission
from services.employee_service import DEFAULT_ADMIN_PERMISSIONS, DEFAULT_EMPLOYEE_PERMISSIONS

logger = logging.getLogger(__name__)
rbac_bp = Blueprint("rbac", __name__)


@rbac_bp.route("/admin/rbac/permissions", methods=["GET"])
@require_permission('audit_logs', 'view')
def get_role_permissions():
    """Return the fixed permission maps for each role."""
    return jsonify(
        {
            "status": "success",
            "data": {
                "model": "role_only",
                "roles": {
                    "ADMIN": DEFAULT_ADMIN_PERMISSIONS,
                    "EMPLOYEE": DEFAULT_EMPLOYEE_PERMISSIONS,
                    "USER": {
                        "modules": {},
                        "admin_access": False,
                        "can_invite_employees": False,
                    },
                },
            },
        }
    ), 200
