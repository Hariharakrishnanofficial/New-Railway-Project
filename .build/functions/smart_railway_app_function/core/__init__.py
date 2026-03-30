"""
Core module - Security, exceptions, and utilities.
"""

from .security import (
    hash_password,
    verify_password,
    generate_access_token,
    generate_refresh_token,
    decode_token,
    require_auth,
    require_admin,
    get_current_user_id,
    get_current_user_email,
    get_current_user_role,
    rate_limit,
)

from .exceptions import (
    RailwayException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    TrainNotFoundError,
    BookingNotFoundError,
    UserNotFoundError,
    SeatUnavailableError,
    DatabaseError,
)

__all__ = [
    # Security
    'hash_password',
    'verify_password',
    'generate_access_token',
    'generate_refresh_token',
    'decode_token',
    'require_auth',
    'require_admin',
    'get_current_user_id',
    'get_current_user_email',
    'get_current_user_role',
    'rate_limit',
    # Exceptions
    'RailwayException',
    'AuthenticationError',
    'AuthorizationError',
    'ValidationError',
    'TrainNotFoundError',
    'BookingNotFoundError',
    'UserNotFoundError',
    'SeatUnavailableError',
    'DatabaseError',
]
