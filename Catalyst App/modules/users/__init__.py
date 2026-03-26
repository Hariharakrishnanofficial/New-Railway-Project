"""
Users Module
============
Complete user management module with authentication, session handling, and profiles.

Components:
    - models: Data schemas and CloudScale table definitions
    - repository: Database operations (CRUD)
    - services: Business logic (auth, tokens, passwords)
    - routes: API endpoints

Usage:
    from modules.users import users_bp, user_service

    # Register blueprint in app.py
    app.register_blueprint(users_bp)

    # Use service directly
    result = user_service.register(user_data)
"""

from modules.users.routes import users_bp, require_auth, require_admin
from modules.users.services import (
    user_service,
    password_service,
    token_service,
    UserService,
    PasswordService,
    TokenService,
    # Exceptions
    AuthError,
    ValidationError,
    InvalidCredentialsError,
    UserNotFoundError,
    UserExistsError,
    AccountLockedError,
    AccountInactiveError,
    TokenExpiredError,
    InvalidTokenError,
)
from modules.users.repository import user_repo, UserRepository
from modules.users.models import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    UserRole,
    UserStatus,
    TOKEN_EXPIRY,
    BOOKING_LIMITS,
    LOCKOUT_SETTINGS,
)

__all__ = [
    # Blueprint
    'users_bp',

    # Decorators
    'require_auth',
    'require_admin',

    # Services
    'user_service',
    'password_service',
    'token_service',
    'UserService',
    'PasswordService',
    'TokenService',

    # Repository
    'user_repo',
    'UserRepository',

    # Models/Schemas
    'UserCreate',
    'UserLogin',
    'UserUpdate',
    'UserResponse',
    'TokenResponse',
    'PasswordChange',
    'PasswordReset',
    'PasswordResetConfirm',
    'UserRole',
    'UserStatus',

    # Constants
    'TOKEN_EXPIRY',
    'BOOKING_LIMITS',
    'LOCKOUT_SETTINGS',

    # Exceptions
    'AuthError',
    'ValidationError',
    'InvalidCredentialsError',
    'UserNotFoundError',
    'UserExistsError',
    'AccountLockedError',
    'AccountInactiveError',
    'TokenExpiredError',
    'InvalidTokenError',
]
