"""
RBAC Routes - Role permission management.
"""

import logging
from flask import Blueprint, jsonify, request

from core.permission_validator import require_permission
from services.employee_service import (
    RBAC_ROLE_PERMISSIONS_SETTING_KEY,
    get_role_permissions_map,
    upsert_role_permissions_map,
)

logger = logging.getLogger(__name__)
rbac_bp = Blueprint("rbac", __name__)


@rbac_bp.route("/admin/rbac/permissions", methods=["GET"])
@require_permission('settings', 'view')
def get_role_permissions():
    """Return configured role permission maps (with defaults fallback)."""
    roles = get_role_permissions_map()
    return jsonify(
        {
            "status": "success",
            "data": {
                "model": "role_configurable",
                "setting_key": RBAC_ROLE_PERMISSIONS_SETTING_KEY,
                "roles": roles,
            },
        }
    ), 200


@rbac_bp.route("/admin/rbac/permissions", methods=["PUT"])
@require_permission('settings', 'edit')
def update_role_permissions():
    """Create/update the RBAC role permissions setting."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    result = upsert_role_permissions_map(payload)
    if not result.get('success'):
        logger.warning("Failed to update RBAC role permissions: %s", result.get('error'))
        return jsonify({
            "status": "error",
            "message": "Failed to update role permissions",
            "error": result.get('error', ''),
        }), 400

    return jsonify({
        "status": "success",
        "message": "Role permissions updated",
        "data": result.get('data', {}),
    }), 200
