"""
Enhanced Auth Routes with CRUD operations
- POST /api/auth/register - CREATE user
- POST /api/auth/signin - READ user + authenticate
- GET /api/auth/profile/:id - READ profile
- PUT /api/auth/profile/:id - UPDATE profile
- POST /api/auth/change-password - UPDATE password
- DELETE /api/auth/account - DELETE account
- POST /api/auth/deactivate - SOFT DELETE account
"""

import logging
from flask import Blueprint, request, jsonify
from services.auth_crud_service import auth_crud_service
from core.security import decode_token, rate_limit, require_auth
from core.exceptions import RailwayException

logger = logging.getLogger(__name__)
auth_crud_bp = Blueprint('auth_crud', __name__)


# ══════════════════════════════════════════════════════════════════════════
#  CREATE - REGISTRATION
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/register', methods=['POST'])
def register():
    """
    CREATE: Register new user account
    POST /api/auth/register
    """
    try:
        from flask import request, jsonify
        data = request.get_json(silent=True) or {}
        
        if not data:
            return jsonify({"success": False, "error": "Invalid request"}), 400
        
        result = auth_crud_service.create_user(data)
        
        return jsonify({
            "success": True,
            "status": "created",
            "data": result,
        }), 201
        
    except Exception as e:
        logger.exception(f"Register error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ══════════════════════════════════════════════════════════════════════════
#  READ - SIGNIN
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/signin', methods=['POST'])
@rate_limit(max_calls=10, window_seconds=900)
def signin():
    """
    READ + AUTH: SignIn with credentials
    POST /api/auth/signin
    Body: { email, password }
    Returns: access_token, refresh_token, user_data
    """
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or data.get("Email") or "").strip()
        password = (data.get("password") or data.get("Password") or "").strip()
        
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Invalid request: email and password required"
            }), 400
        
        result = auth_crud_service.signin(email, password)
        
        return jsonify({
            "success": True,
            "status": "authenticated",
            "data": result,
        }), 200
        
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f"SignIn error: {e}")
        error_msg = str(e)
        return jsonify({
            "success": False,
            "error": "SignIn failed",
            "details": error_msg
        }), 500


# ══════════════════════════════════════════════════════════════════════════
#  READ - GET PROFILE
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/profile/<user_id>', methods=['GET'])
@require_auth
def get_profile(user_id):
    """
    READ: Get user profile
    GET /api/auth/profile/:user_id
    """
    try:
        result = auth_crud_service.get_user_profile(user_id)
        
        return jsonify({
            "success": True,
            "status": "retrieved",
            "data": result,
        }), 200
        
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f"Get profile error: {e}")
        return jsonify({"success": False, "error": "Failed to retrieve profile"}), 500


# ══════════════════════════════════════════════════════════════════════════
#  UPDATE - PROFILE
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/profile/<user_id>', methods=['PUT'])
@require_auth
def update_profile(user_id):
    """
    UPDATE: Update user profile
    PUT /api/auth/profile/:user_id
    Body: { full_name?, phone_number?, address? }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        result = auth_crud_service.update_profile(user_id, data)
        
        return jsonify({
            "success": True,
            "status": "updated",
            "data": result,
        }), 200
        
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f"Update profile error: {e}")
        return jsonify({"success": False, "error": "Failed to update profile"}), 500


# ══════════════════════════════════════════════════════════════════════════
#  UPDATE - CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """
    UPDATE: Change user password
    POST /api/auth/change-password
    Body: { user_id, old_password, new_password }
    """
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        result = auth_crud_service.change_password(user_id, old_password, new_password)
        
        return jsonify({
            "success": True,
            "status": "updated",
            "data": result,
        }), 200
        
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f"Change password error: {e}")
        return jsonify({"success": False, "error": "Failed to change password"}), 500


# ══════════════════════════════════════════════════════════════════════════
#  DELETE - DELETE ACCOUNT (PERMANENT)
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/delete-account', methods=['POST'])
@require_auth
def delete_account():
    """
    DELETE: Permanently delete user account
    POST /api/auth/delete-account
    Body: { user_id, password }
    WARNING: This cannot be undone
    """
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        password = data.get("password")
        
        result = auth_crud_service.delete_account(user_id, password)
        
        return jsonify({
            "success": True,
            "status": "deleted",
            "data": result,
        }), 200
        
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f"Delete account error: {e}")
        return jsonify({"success": False, "error": "Failed to delete account"}), 500


# ══════════════════════════════════════════════════════════════════════════
#  DELETE - DEACTIVATE ACCOUNT (SOFT DELETE)
# ══════════════════════════════════════════════════════════════════════════

@auth_crud_bp.route('/api/auth/deactivate-account', methods=['POST'])
@require_auth
def deactivate_account():
    """
    SOFT DELETE: Deactivate user account (reversible)
    POST /api/auth/deactivate-account
    Body: { user_id, password }
    """
    try:
        data = request.get_json(silent=True) or {}
        user_id = data.get("user_id")
        password = data.get("password")
        
        result = auth_crud_service.deactivate_account(user_id, password)
        
        return jsonify({
            "success": True,
            "status": "deactivated",
            "data": result,
        }), 200
        
    except RailwayException as e:
        return jsonify(e.to_response()), e.status_code
    except Exception as e:
        logger.exception(f"Deactivate account error: {e}")
        return jsonify({"success": False, "error": "Failed to deactivate account"}), 500
