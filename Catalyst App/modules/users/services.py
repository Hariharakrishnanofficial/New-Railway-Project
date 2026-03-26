"""
User Services - Business Logic Layer
=====================================
Handles user registration, authentication, and session management.
Uses Argon2 for password hashing and JWT for session tokens.
"""

from __future__ import annotations
import os
import secrets
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict

import jwt

# Argon2 password hashing
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHashError
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    import hashlib

from modules.users.repository import user_repo
from modules.users.models import (
    UserCreate, UserLogin, UserUpdate, UserResponse, TokenResponse,
    PasswordChange, PasswordReset, PasswordResetConfirm,
    UserRole, UserStatus, TOKEN_EXPIRY, BOOKING_LIMITS, LOCKOUT_SETTINGS
)

logger = logging.getLogger(__name__)


# =============================================================================
# EXCEPTIONS
# =============================================================================

class AuthError(Exception):
    """Base authentication error."""
    pass


class InvalidCredentialsError(AuthError):
    """Invalid email or password."""
    pass


class UserNotFoundError(AuthError):
    """User not found."""
    pass


class UserExistsError(AuthError):
    """User already exists."""
    pass


class AccountLockedError(AuthError):
    """Account is locked due to too many failed attempts."""
    pass


class AccountInactiveError(AuthError):
    """Account is inactive or suspended."""
    pass


class TokenExpiredError(AuthError):
    """Token has expired."""
    pass


class InvalidTokenError(AuthError):
    """Token is invalid."""
    pass


class ValidationError(Exception):
    """Validation error."""
    pass


# =============================================================================
# PASSWORD HASHER (ARGON2)
# =============================================================================

class PasswordService:
    """
    Password hashing service using Argon2id.

    Argon2 is the winner of the Password Hashing Competition and is
    recommended for password hashing. Argon2id is the hybrid version
    that provides protection against both side-channel and GPU attacks.

    Parameters:
        - time_cost: Number of iterations (default: 3)
        - memory_cost: Memory usage in KB (default: 65536 = 64MB)
        - parallelism: Number of parallel threads (default: 4)
        - hash_len: Length of the hash in bytes (default: 32)
        - salt_len: Length of the salt in bytes (default: 16)
    """

    def __init__(self):
        if ARGON2_AVAILABLE:
            self.hasher = PasswordHasher(
                time_cost=3,           # Number of iterations
                memory_cost=65536,     # 64 MB
                parallelism=4,         # 4 threads
                hash_len=32,           # 32 bytes hash
                salt_len=16,           # 16 bytes salt
            )
            logger.info("Using Argon2id for password hashing")
        else:
            self.hasher = None
            logger.warning("Argon2 not available, using SHA-256 fallback")

    def hash_password(self, password: str) -> str:
        """
        Hash a password using Argon2id.

        Args:
            password: Plain text password

        Returns:
            Argon2id hash string
        """
        if self.hasher:
            return self.hasher.hash(password)
        else:
            # Fallback to SHA-256 with salt (not recommended for production)
            salt = secrets.token_hex(16)
            hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
            return f"sha256${salt}${hash_value}"

    def verify_password(self, password: str, hash_str: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hash_str: Stored hash to verify against

        Returns:
            True if password matches, False otherwise
        """
        try:
            if self.hasher and hash_str.startswith('$argon2'):
                self.hasher.verify(hash_str, password)
                return True
            elif hash_str.startswith('sha256$'):
                # Fallback verification
                parts = hash_str.split('$')
                if len(parts) == 3:
                    salt = parts[1]
                    stored_hash = parts[2]
                    computed_hash = hashlib.sha256((salt + password).encode()).hexdigest()
                    return secrets.compare_digest(computed_hash, stored_hash)
            return False
        except (VerifyMismatchError, InvalidHashError):
            return False
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def needs_rehash(self, hash_str: str) -> bool:
        """
        Check if a password hash needs to be rehashed.

        This can happen when Argon2 parameters are updated.
        """
        if self.hasher and hash_str.startswith('$argon2'):
            return self.hasher.check_needs_rehash(hash_str)
        # SHA-256 hashes should be upgraded to Argon2
        return hash_str.startswith('sha256$')


# Global password service
password_service = PasswordService()


# =============================================================================
# TOKEN SERVICE (JWT)
# =============================================================================

class TokenService:
    """
    JWT Token service for session management.

    Generates and validates:
    - Access tokens (short-lived, for API access)
    - Refresh tokens (long-lived, for getting new access tokens)
    """

    def __init__(self):
        self.secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.access_token_expiry = TOKEN_EXPIRY['access_token']
        self.refresh_token_expiry = TOKEN_EXPIRY['refresh_token']

    def generate_access_token(self, user_id: int, email: str, role: str) -> Tuple[str, datetime]:
        """
        Generate a JWT access token.

        Args:
            user_id: User's ROWID
            email: User's email
            role: User's role

        Returns:
            Tuple of (token_string, expiry_datetime)
        """
        expires_at = datetime.utcnow() + timedelta(seconds=self.access_token_expiry)

        payload = {
            'sub': str(user_id),
            'email': email,
            'role': role,
            'type': 'access',
            'iat': datetime.utcnow(),
            'exp': expires_at,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expires_at

    def generate_refresh_token(self, user_id: int) -> Tuple[str, datetime]:
        """
        Generate a JWT refresh token.

        Args:
            user_id: User's ROWID

        Returns:
            Tuple of (token_string, expiry_datetime)
        """
        expires_at = datetime.utcnow() + timedelta(seconds=self.refresh_token_expiry)

        payload = {
            'sub': str(user_id),
            'type': 'refresh',
            'jti': secrets.token_urlsafe(32),  # Unique token ID
            'iat': datetime.utcnow(),
            'exp': expires_at,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expires_at

    def generate_token_pair(self, user_id: int, email: str, role: str) -> Dict:
        """
        Generate both access and refresh tokens.

        Returns:
            Dictionary with tokens and expiry information
        """
        access_token, access_expires = self.generate_access_token(user_id, email, role)
        refresh_token, refresh_expires = self.generate_refresh_token(user_id)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_expires_at': access_expires,
            'refresh_expires_at': refresh_expires,
            'token_type': 'Bearer',
            'expires_in': self.access_token_expiry,
            'refresh_expires_in': self.refresh_token_expiry,
        }

    def verify_token(self, token: str, token_type: str = 'access') -> Dict:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            token_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            if payload.get('type') != token_type:
                raise InvalidTokenError(f"Expected {token_type} token")

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")

    def generate_reset_token(self) -> Tuple[str, datetime]:
        """
        Generate a password reset token.

        Returns:
            Tuple of (token_string, expiry_datetime)
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=TOKEN_EXPIRY['reset_token'])
        return token, expires_at


# Global token service
token_service = TokenService()


# =============================================================================
# USER SERVICE
# =============================================================================

class UserService:
    """
    Main service for user management operations.
    """

    def __init__(self):
        self.repo = user_repo
        self.password_service = password_service
        self.token_service = token_service

    # -------------------------------------------------------------------------
    # REGISTRATION
    # -------------------------------------------------------------------------

    def register(self, data: UserCreate) -> Dict:
        """
        Register a new user.

        Args:
            data: UserCreate schema with user details

        Returns:
            Dictionary with user info and tokens

        Raises:
            ValidationError: If validation fails
            UserExistsError: If email already registered
        """
        # Validate input
        errors = data.validate()
        if errors:
            raise ValidationError(", ".join(errors))

        # Normalize email
        email = data.email.lower().strip()

        # Check if user exists
        if self.repo.email_exists(email):
            raise UserExistsError(f"Email {email} is already registered")

        # Check phone uniqueness (if provided)
        if data.phone and self.repo.phone_exists(data.phone):
            raise UserExistsError(f"Phone number is already registered")

        # Hash password
        password_hash = self.password_service.hash_password(data.password)

        # Prepare user data
        user_data = {
            'Email': email,
            'Password_Hash': password_hash,
            'Full_Name': data.full_name.strip(),
            'Phone': data.phone,
            'Role': UserRole.USER.value,
            'Status': UserStatus.ACTIVE.value,
            'Is_Email_Verified': False,
            'Is_Phone_Verified': False,
            'Is_Aadhar_Verified': False,
            'Date_Of_Birth': data.date_of_birth,
            'Gender': data.gender.capitalize() if data.gender else None,
            'Monthly_Booking_Count': 0,
            'Failed_Login_Count': 0,
        }

        # Create user
        created_user = self.repo.create(user_data)
        user_id = created_user.get('ROWID')

        # Generate tokens
        tokens = self.token_service.generate_token_pair(
            user_id=user_id,
            email=email,
            role=UserRole.USER.value
        )

        # Update user with session tokens
        self.repo.update_session_token(
            user_id=user_id,
            session_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_expires_at=tokens['access_expires_at'],
            refresh_expires_at=tokens['refresh_expires_at'],
        )

        # Build response
        user_response = UserResponse(
            id=user_id,
            email=email,
            full_name=data.full_name,
            phone=data.phone,
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
            is_email_verified=False,
            is_aadhar_verified=False,
        )

        logger.info(f"User registered: {email}")

        return {
            'success': True,
            'message': 'Registration successful',
            'user': user_response.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': 'Bearer',
            'expires_in': tokens['expires_in'],
        }

    # -------------------------------------------------------------------------
    # LOGIN
    # -------------------------------------------------------------------------

    def login(self, data: UserLogin, ip_address: str = None) -> Dict:
        """
        Authenticate user and return tokens.

        Args:
            data: UserLogin schema
            ip_address: Client IP address

        Returns:
            Dictionary with user info and tokens

        Raises:
            ValidationError: If validation fails
            InvalidCredentialsError: If credentials are wrong
            AccountLockedError: If account is locked
            AccountInactiveError: If account is not active
        """
        # Validate input
        errors = data.validate()
        if errors:
            raise ValidationError(", ".join(errors))

        email = data.email.lower().strip()

        # Get user
        user = self.repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        user_id = user.get('ROWID')

        # Check account status
        status = user.get('Status', 'active')
        if status == UserStatus.INACTIVE.value:
            raise AccountInactiveError("Account is inactive")
        if status == UserStatus.SUSPENDED.value:
            raise AccountInactiveError("Account is suspended")

        # Check if account is locked
        locked_until = user.get('Locked_Until')
        if locked_until:
            lock_time = datetime.strptime(locked_until, '%Y-%m-%d %H:%M:%S')
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds // 60
                raise AccountLockedError(
                    f"Account is locked. Try again in {remaining} minutes"
                )
            else:
                # Lock expired, reset
                self.repo.reset_failed_login(user_id)

        # Verify password
        stored_hash = user.get('Password_Hash', '')
        if not self.password_service.verify_password(data.password, stored_hash):
            # Increment failed login count
            failed_count = int(user.get('Failed_Login_Count', 0) or 0)
            self.repo.increment_failed_login(user_id, failed_count)

            remaining_attempts = LOCKOUT_SETTINGS['max_failed_attempts'] - (failed_count + 1)
            if remaining_attempts > 0:
                raise InvalidCredentialsError(
                    f"Invalid email or password. {remaining_attempts} attempts remaining"
                )
            else:
                raise AccountLockedError(
                    f"Account locked for {LOCKOUT_SETTINGS['lockout_duration_minutes']} minutes"
                )

        # Check if password needs rehash
        if self.password_service.needs_rehash(stored_hash):
            new_hash = self.password_service.hash_password(data.password)
            self.repo.update_password(user_id, new_hash)
            logger.info(f"Password rehashed for user {user_id}")

        # Generate tokens
        tokens = self.token_service.generate_token_pair(
            user_id=user_id,
            email=email,
            role=user.get('Role', 'user')
        )

        # Update session
        self.repo.update_session_token(
            user_id=user_id,
            session_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_expires_at=tokens['access_expires_at'],
            refresh_expires_at=tokens['refresh_expires_at'],
            ip_address=ip_address,
        )

        # Build response
        user_response = UserResponse.from_db_row(user)

        logger.info(f"User logged in: {email}")

        return {
            'success': True,
            'message': 'Login successful',
            'user': user_response.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': 'Bearer',
            'expires_in': tokens['expires_in'],
        }

    # -------------------------------------------------------------------------
    # LOGOUT
    # -------------------------------------------------------------------------

    def logout(self, user_id: int) -> Dict:
        """
        Logout user by clearing session tokens.

        Args:
            user_id: User's ROWID

        Returns:
            Success message
        """
        self.repo.clear_session_token(user_id)
        logger.info(f"User {user_id} logged out")

        return {
            'success': True,
            'message': 'Logged out successfully'
        }

    # -------------------------------------------------------------------------
    # TOKEN REFRESH
    # -------------------------------------------------------------------------

    def refresh_tokens(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token pair

        Raises:
            InvalidTokenError: If refresh token is invalid
            TokenExpiredError: If refresh token has expired
        """
        # Verify refresh token
        payload = self.token_service.verify_token(refresh_token, token_type='refresh')
        user_id = int(payload.get('sub'))

        # Get user and verify refresh token matches
        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        stored_refresh = user.get('Refresh_Token')
        if stored_refresh != refresh_token:
            raise InvalidTokenError("Refresh token does not match")

        # Generate new tokens
        tokens = self.token_service.generate_token_pair(
            user_id=user_id,
            email=user.get('Email'),
            role=user.get('Role', 'user')
        )

        # Update session
        self.repo.update_session_token(
            user_id=user_id,
            session_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_expires_at=tokens['access_expires_at'],
            refresh_expires_at=tokens['refresh_expires_at'],
        )

        logger.info(f"Tokens refreshed for user {user_id}")

        return {
            'success': True,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'token_type': 'Bearer',
            'expires_in': tokens['expires_in'],
        }

    # -------------------------------------------------------------------------
    # PASSWORD MANAGEMENT
    # -------------------------------------------------------------------------

    def change_password(self, user_id: int, data: PasswordChange) -> Dict:
        """
        Change user's password.

        Args:
            user_id: User's ROWID
            data: PasswordChange schema

        Returns:
            Success message

        Raises:
            ValidationError: If validation fails
            InvalidCredentialsError: If current password is wrong
        """
        # Validate input
        errors = data.validate()
        if errors:
            raise ValidationError(", ".join(errors))

        # Get user
        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        # Verify current password
        if not self.password_service.verify_password(
            data.current_password,
            user.get('Password_Hash', '')
        ):
            raise InvalidCredentialsError("Current password is incorrect")

        # Hash and update new password
        new_hash = self.password_service.hash_password(data.new_password)
        self.repo.update_password(user_id, new_hash)

        # Clear all sessions (force re-login)
        self.repo.clear_session_token(user_id)

        logger.info(f"Password changed for user {user_id}")

        return {
            'success': True,
            'message': 'Password changed successfully. Please login again.'
        }

    def request_password_reset(self, data: PasswordReset) -> Dict:
        """
        Request password reset email.

        Args:
            data: PasswordReset schema with email

        Returns:
            Success message (always returns success for security)
        """
        errors = data.validate()
        if errors:
            raise ValidationError(", ".join(errors))

        email = data.email.lower().strip()
        user = self.repo.get_by_email(email)

        if user:
            # Generate reset token
            reset_token, expires_at = self.token_service.generate_reset_token()

            # Store reset token
            self.repo.set_reset_token(
                user_id=user.get('ROWID'),
                token=reset_token,
                expires_at=expires_at
            )

            # TODO: Send email with reset link
            # email_service.send_password_reset(email, reset_token)

            logger.info(f"Password reset requested for {email}")

        # Always return success (don't reveal if email exists)
        return {
            'success': True,
            'message': 'If this email is registered, you will receive a password reset link.'
        }

    def confirm_password_reset(self, data: PasswordResetConfirm) -> Dict:
        """
        Reset password using reset token.

        Args:
            data: PasswordResetConfirm schema

        Returns:
            Success message

        Raises:
            InvalidTokenError: If reset token is invalid or expired
        """
        errors = data.validate()
        if errors:
            raise ValidationError(", ".join(errors))

        # Find user by reset token
        user = self.repo.get_by_reset_token(data.token)
        if not user:
            raise InvalidTokenError("Invalid or expired reset token")

        # Hash and update new password
        new_hash = self.password_service.hash_password(data.new_password)
        self.repo.update_password(user.get('ROWID'), new_hash)

        logger.info(f"Password reset completed for user {user.get('ROWID')}")

        return {
            'success': True,
            'message': 'Password reset successful. Please login with your new password.'
        }

    # -------------------------------------------------------------------------
    # USER PROFILE
    # -------------------------------------------------------------------------

    def get_profile(self, user_id: int) -> Dict:
        """Get user profile."""
        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        user_response = UserResponse.from_db_row(user)

        # Add booking limit info
        can_book, current_count, max_limit = self.repo.can_book(user_id)

        return {
            'success': True,
            'user': user_response.to_dict(),
            'booking_info': {
                'monthly_bookings': current_count,
                'monthly_limit': max_limit,
                'can_book': can_book,
            }
        }

    def update_profile(self, user_id: int, data: UserUpdate) -> Dict:
        """Update user profile."""
        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        update_data = {}

        if data.full_name:
            update_data['Full_Name'] = data.full_name.strip()
        if data.phone:
            update_data['Phone'] = data.phone
        if data.date_of_birth:
            update_data['Date_Of_Birth'] = data.date_of_birth
        if data.gender:
            update_data['Gender'] = data.gender.capitalize()
        if data.address:
            update_data['Address'] = data.address
        if data.city:
            update_data['City'] = data.city
        if data.state:
            update_data['State'] = data.state
        if data.pincode:
            update_data['Pincode'] = data.pincode

        if update_data:
            self.repo.update(user_id, update_data)

        # Get updated user
        updated_user = self.repo.get_by_id(user_id)
        user_response = UserResponse.from_db_row(updated_user)

        return {
            'success': True,
            'message': 'Profile updated successfully',
            'user': user_response.to_dict()
        }

    # -------------------------------------------------------------------------
    # TOKEN VALIDATION
    # -------------------------------------------------------------------------

    def validate_token(self, token: str) -> Dict:
        """
        Validate access token and return user info.

        Args:
            token: JWT access token

        Returns:
            User info from token

        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
        """
        payload = self.token_service.verify_token(token, token_type='access')

        user_id = int(payload.get('sub'))
        user = self.repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundError("User not found")

        # Verify token matches stored session token
        stored_token = user.get('Session_Token')
        if stored_token != token:
            raise InvalidTokenError("Token has been revoked")

        return {
            'valid': True,
            'user_id': user_id,
            'email': payload.get('email'),
            'role': payload.get('role'),
        }

    # -------------------------------------------------------------------------
    # ADMIN OPERATIONS
    # -------------------------------------------------------------------------

    def get_all_users(self, limit: int = 100, offset: int = 0) -> Dict:
        """Get all users (admin only)."""
        users = self.repo.get_all(limit=limit, offset=offset)
        total = self.repo.count()

        return {
            'success': True,
            'data': [UserResponse.from_db_row(u).to_dict() for u in users],
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    def update_user_role(self, user_id: int, role: str, admin_id: int) -> Dict:
        """Update user role (admin only)."""
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise ValidationError(f"Invalid role. Must be one of: {valid_roles}")

        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        self.repo.update_role(user_id, role)

        logger.info(f"User {user_id} role changed to {role} by admin {admin_id}")

        return {
            'success': True,
            'message': f'User role updated to {role}'
        }

    def update_user_status(self, user_id: int, status: str, admin_id: int) -> Dict:
        """Update user status (admin only)."""
        valid_statuses = [s.value for s in UserStatus]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")

        user = self.repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")

        self.repo.update_status(user_id, status)

        logger.info(f"User {user_id} status changed to {status} by admin {admin_id}")

        return {
            'success': True,
            'message': f'User status updated to {status}'
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

user_service = UserService()
