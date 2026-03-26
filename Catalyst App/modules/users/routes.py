"""
User Routes - API Endpoints
============================
Defines all HTTP endpoints for user authentication and management.
"""

from __future__ import annotations
import logging
from functools import wraps
from flask import Blueprint, jsonify, request, g

from modules.users.services import (
    user_service,
    ValidationError, AuthError, InvalidCredentialsError,
    UserNotFoundError, UserExistsError, AccountLockedError,
    AccountInactiveError, TokenExpiredError, InvalidTokenError
)
from modules.users.models import (
    UserCreate, UserLogin, UserUpdate,
    PasswordChange, PasswordReset, PasswordResetConfirm
)

logger = logging.getLogger(__name__)

# =============================================================================
# BLUEPRINT
# =============================================================================

users_bp = Blueprint('users', __name__, url_prefix='/api')


# =============================================================================
# AUTH DECORATORS
# =============================================================================

def require_auth(f):
    """
    Decorator to require valid JWT authentication.
    Sets g.current_user with user info from token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid Authorization header'
            }), 401

        token = auth_header.replace('Bearer ', '')

        try:
            user_info = user_service.validate_token(token)
            g.current_user = user_info
            return f(*args, **kwargs)

        except TokenExpiredError:
            return jsonify({
                'success': False,
                'error': 'Token has expired',
                'code': 'TOKEN_EXPIRED'
            }), 401

        except InvalidTokenError as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'code': 'INVALID_TOKEN'
            }), 401

        except Exception as e:
            logger.error(f"Auth error: {e}")
            return jsonify({
                'success': False,
                'error': 'Authentication failed'
            }), 401

    return decorated


def require_admin(f):
    """
    Decorator to require admin role.
    Must be used after @require_auth.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401

        role = g.current_user.get('role', 'user')
        if role not in ['admin', 'super_admin']:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403

        return f(*args, **kwargs)

    return decorated


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@users_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({'success': False, 'error': str(e)}), 400


@users_bp.errorhandler(InvalidCredentialsError)
def handle_invalid_credentials(e):
    return jsonify({'success': False, 'error': str(e)}), 401


@users_bp.errorhandler(UserNotFoundError)
def handle_user_not_found(e):
    return jsonify({'success': False, 'error': str(e)}), 404


@users_bp.errorhandler(UserExistsError)
def handle_user_exists(e):
    return jsonify({'success': False, 'error': str(e)}), 409


@users_bp.errorhandler(AccountLockedError)
def handle_account_locked(e):
    return jsonify({'success': False, 'error': str(e), 'code': 'ACCOUNT_LOCKED'}), 423


@users_bp.errorhandler(AccountInactiveError)
def handle_account_inactive(e):
    return jsonify({'success': False, 'error': str(e), 'code': 'ACCOUNT_INACTIVE'}), 403


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@users_bp.route('/auth/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Register a new user account.

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "full_name": "John Doe",
            "phone": "9876543210",        (optional)
            "date_of_birth": "1990-01-15", (optional)
            "gender": "Male"               (optional)
        }

    Response:
        {
            "success": true,
            "message": "Registration successful",
            "user": { ... },
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 3600
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        user_create = UserCreate(
            email=data.get('email', ''),
            password=data.get('password', ''),
            full_name=data.get('full_name', ''),
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
        )

        result = user_service.register(user_create)
        return jsonify(result), 201

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except UserExistsError as e:
        return jsonify({'success': False, 'error': str(e)}), 409
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@users_bp.route('/auth/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authenticate user and return tokens.

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }

    Response:
        {
            "success": true,
            "message": "Login successful",
            "user": { ... },
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 3600
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        user_login = UserLogin(
            email=data.get('email', ''),
            password=data.get('password', ''),
        )

        # Get client IP
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

        result = user_service.login(user_login, ip_address=ip_address)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except InvalidCredentialsError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except AccountLockedError as e:
        return jsonify({'success': False, 'error': str(e), 'code': 'ACCOUNT_LOCKED'}), 423
    except AccountInactiveError as e:
        return jsonify({'success': False, 'error': str(e), 'code': 'ACCOUNT_INACTIVE'}), 403
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Login failed'}), 500


@users_bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    POST /api/auth/logout
    Logout user and invalidate session tokens.

    Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    try:
        user_id = g.current_user.get('user_id')
        result = user_service.logout(user_id)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


@users_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """
    POST /api/auth/refresh
    Refresh access token using refresh token.

    Request Body:
        {
            "refresh_token": "eyJ..."
        }

    Response:
        {
            "success": true,
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 3600
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('refresh_token'):
            return jsonify({'success': False, 'error': 'Refresh token required'}), 400

        result = user_service.refresh_tokens(data['refresh_token'])
        return jsonify(result), 200

    except TokenExpiredError:
        return jsonify({
            'success': False,
            'error': 'Refresh token has expired. Please login again.',
            'code': 'REFRESH_TOKEN_EXPIRED'
        }), 401
    except InvalidTokenError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INVALID_REFRESH_TOKEN'
        }), 401
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Token refresh failed'}), 500


@users_bp.route('/auth/validate', methods=['GET'])
@require_auth
def validate_token():
    """
    GET /api/auth/validate
    Validate access token and return user info.

    Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "valid": true,
            "user_id": 123,
            "email": "user@example.com",
            "role": "user"
        }
    """
    return jsonify(g.current_user), 200


# =============================================================================
# PASSWORD ENDPOINTS
# =============================================================================

@users_bp.route('/auth/password/change', methods=['POST'])
@require_auth
def change_password():
    """
    POST /api/auth/password/change
    Change password for authenticated user.

    Headers:
        Authorization: Bearer <access_token>

    Request Body:
        {
            "current_password": "OldPass123",
            "new_password": "NewSecurePass456",
            "confirm_password": "NewSecurePass456"
        }

    Response:
        {
            "success": true,
            "message": "Password changed successfully. Please login again."
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        password_change = PasswordChange(
            current_password=data.get('current_password', ''),
            new_password=data.get('new_password', ''),
            confirm_password=data.get('confirm_password', ''),
        )

        user_id = g.current_user.get('user_id')
        result = user_service.change_password(user_id, password_change)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except InvalidCredentialsError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Password change failed'}), 500


@users_bp.route('/auth/password/reset', methods=['POST'])
def request_password_reset():
    """
    POST /api/auth/password/reset
    Request password reset email.

    Request Body:
        {
            "email": "user@example.com"
        }

    Response:
        {
            "success": true,
            "message": "If this email is registered, you will receive a password reset link."
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        password_reset = PasswordReset(email=data.get('email', ''))

        result = user_service.request_password_reset(password_reset)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Password reset request error: {e}", exc_info=True)
        # Always return success for security
        return jsonify({
            'success': True,
            'message': 'If this email is registered, you will receive a password reset link.'
        }), 200


@users_bp.route('/auth/password/reset/confirm', methods=['POST'])
def confirm_password_reset():
    """
    POST /api/auth/password/reset/confirm
    Reset password using reset token.

    Request Body:
        {
            "token": "reset_token_here",
            "new_password": "NewSecurePass456",
            "confirm_password": "NewSecurePass456"
        }

    Response:
        {
            "success": true,
            "message": "Password reset successful. Please login with your new password."
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        reset_confirm = PasswordResetConfirm(
            token=data.get('token', ''),
            new_password=data.get('new_password', ''),
            confirm_password=data.get('confirm_password', ''),
        )

        result = user_service.confirm_password_reset(reset_confirm)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except InvalidTokenError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Password reset confirm error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Password reset failed'}), 500


# =============================================================================
# PROFILE ENDPOINTS
# =============================================================================

@users_bp.route('/users/me', methods=['GET'])
@require_auth
def get_my_profile():
    """
    GET /api/users/me
    Get current user's profile.

    Headers:
        Authorization: Bearer <access_token>

    Response:
        {
            "success": true,
            "user": { ... },
            "booking_info": {
                "monthly_bookings": 3,
                "monthly_limit": 6,
                "can_book": true
            }
        }
    """
    try:
        user_id = g.current_user.get('user_id')
        result = user_service.get_profile(user_id)
        return jsonify(result), 200

    except UserNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Get profile error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500


@users_bp.route('/users/me', methods=['PUT'])
@require_auth
def update_my_profile():
    """
    PUT /api/users/me
    Update current user's profile.

    Headers:
        Authorization: Bearer <access_token>

    Request Body:
        {
            "full_name": "John Doe",
            "phone": "9876543210",
            "date_of_birth": "1990-01-15",
            "gender": "Male",
            "address": "123 Main St",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600001"
        }

    Response:
        {
            "success": true,
            "message": "Profile updated successfully",
            "user": { ... }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        user_update = UserUpdate(
            full_name=data.get('full_name'),
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
        )

        user_id = g.current_user.get('user_id')
        result = user_service.update_profile(user_id, user_update)
        return jsonify(result), 200

    except UserNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Update profile error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@users_bp.route('/users', methods=['GET'])
@require_auth
@require_admin
def get_all_users():
    """
    GET /api/users
    Get all users (admin only).

    Headers:
        Authorization: Bearer <admin_access_token>

    Query Parameters:
        limit: int (default: 100)
        offset: int (default: 0)

    Response:
        {
            "success": true,
            "data": [ ... ],
            "total": 500,
            "limit": 100,
            "offset": 0
        }
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        result = user_service.get_all_users(limit=limit, offset=offset)
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Get all users error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get users'}), 500


@users_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user_by_id(user_id: int):
    """
    GET /api/users/{user_id}
    Get user by ID (admin only).

    Headers:
        Authorization: Bearer <admin_access_token>

    Response:
        {
            "success": true,
            "user": { ... },
            "booking_info": { ... }
        }
    """
    try:
        result = user_service.get_profile(user_id)
        return jsonify(result), 200

    except UserNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to get user'}), 500


@users_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@require_auth
@require_admin
def update_user_role(user_id: int):
    """
    PUT /api/users/{user_id}/role
    Update user role (admin only).

    Headers:
        Authorization: Bearer <admin_access_token>

    Request Body:
        {
            "role": "admin"
        }

    Response:
        {
            "success": true,
            "message": "User role updated to admin"
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('role'):
            return jsonify({'success': False, 'error': 'Role is required'}), 400

        admin_id = g.current_user.get('user_id')
        result = user_service.update_user_role(user_id, data['role'], admin_id)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except UserNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Update role error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to update role'}), 500


@users_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@require_auth
@require_admin
def update_user_status(user_id: int):
    """
    PUT /api/users/{user_id}/status
    Update user status (admin only).

    Headers:
        Authorization: Bearer <admin_access_token>

    Request Body:
        {
            "status": "active"
        }

    Response:
        {
            "success": true,
            "message": "User status updated to active"
        }
    """
    try:
        data = request.get_json()
        if not data or not data.get('status'):
            return jsonify({'success': False, 'error': 'Status is required'}), 400

        admin_id = g.current_user.get('user_id')
        result = user_service.update_user_status(user_id, data['status'], admin_id)
        return jsonify(result), 200

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except UserNotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Update status error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Failed to update status'}), 500
