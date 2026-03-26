"""
User Models - CloudScale Table Schema & Data Classes
=====================================================
Defines the Users table structure and validation schemas.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# =============================================================================
# CLOUDSCALE TABLE SCHEMA: Users
# =============================================================================
"""
CREATE TABLE Users (
    ROWID           BIGINT PRIMARY KEY AUTO_INCREMENT,
    Email           VARCHAR(255) UNIQUE NOT NULL,
    Password_Hash   VARCHAR(255) NOT NULL,
    Full_Name       VARCHAR(255) NOT NULL,
    Phone           VARCHAR(20),
    Role            VARCHAR(20) DEFAULT 'user',
    Status          VARCHAR(30) DEFAULT 'active',

    -- Verification
    Is_Email_Verified    BOOLEAN DEFAULT false,
    Is_Phone_Verified    BOOLEAN DEFAULT false,
    Is_Aadhar_Verified   BOOLEAN DEFAULT false,
    Aadhar_Number        VARCHAR(20),

    -- Profile
    Date_Of_Birth   DATE,
    Gender          VARCHAR(10),
    Address         TEXT,
    City            VARCHAR(100),
    State           VARCHAR(100),
    Pincode         VARCHAR(10),

    -- Session & Security
    Session_Token       VARCHAR(500),
    Token_Expires_At    DATETIME,
    Refresh_Token       VARCHAR(500),
    Refresh_Expires_At  DATETIME,
    Last_Login_At       DATETIME,
    Last_Login_IP       VARCHAR(50),
    Failed_Login_Count  INT DEFAULT 0,
    Locked_Until        DATETIME,

    -- Password Reset
    Reset_Token         VARCHAR(255),
    Reset_Token_Expires DATETIME,

    -- Booking Limits
    Monthly_Booking_Count   INT DEFAULT 0,
    Booking_Count_Reset_At  DATE,

    -- Timestamps
    Created_At      DATETIME DEFAULT CURRENT_TIMESTAMP,
    Updated_At      DATETIME,

    -- Indexes
    INDEX idx_email (Email),
    INDEX idx_phone (Phone),
    INDEX idx_session_token (Session_Token),
    INDEX idx_status (Status)
);
"""

# Field definitions for CloudScale
USERS_TABLE_FIELDS = {
    'ROWID': {'type': 'bigint', 'primary_key': True, 'auto_increment': True},
    'Email': {'type': 'varchar', 'length': 255, 'unique': True, 'required': True},
    'Password_Hash': {'type': 'varchar', 'length': 255, 'required': True},
    'Full_Name': {'type': 'varchar', 'length': 255, 'required': True},
    'Phone': {'type': 'varchar', 'length': 20},
    'Role': {'type': 'varchar', 'length': 20, 'default': 'user'},
    'Status': {'type': 'varchar', 'length': 30, 'default': 'active'},

    # Verification fields
    'Is_Email_Verified': {'type': 'boolean', 'default': False},
    'Is_Phone_Verified': {'type': 'boolean', 'default': False},
    'Is_Aadhar_Verified': {'type': 'boolean', 'default': False},
    'Aadhar_Number': {'type': 'varchar', 'length': 20},

    # Profile fields
    'Date_Of_Birth': {'type': 'date'},
    'Gender': {'type': 'varchar', 'length': 10},
    'Address': {'type': 'text'},
    'City': {'type': 'varchar', 'length': 100},
    'State': {'type': 'varchar', 'length': 100},
    'Pincode': {'type': 'varchar', 'length': 10},

    # Session fields
    'Session_Token': {'type': 'varchar', 'length': 500},
    'Token_Expires_At': {'type': 'datetime'},
    'Refresh_Token': {'type': 'varchar', 'length': 500},
    'Refresh_Expires_At': {'type': 'datetime'},
    'Last_Login_At': {'type': 'datetime'},
    'Last_Login_IP': {'type': 'varchar', 'length': 50},
    'Failed_Login_Count': {'type': 'int', 'default': 0},
    'Locked_Until': {'type': 'datetime'},

    # Password reset fields
    'Reset_Token': {'type': 'varchar', 'length': 255},
    'Reset_Token_Expires': {'type': 'datetime'},

    # Booking limits
    'Monthly_Booking_Count': {'type': 'int', 'default': 0},
    'Booking_Count_Reset_At': {'type': 'date'},

    # Timestamps
    'Created_At': {'type': 'datetime', 'default': 'CURRENT_TIMESTAMP'},
    'Updated_At': {'type': 'datetime'},
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UserCreate:
    """Schema for creating a new user."""
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None

    def validate(self) -> list:
        """Validate user creation data. Returns list of errors."""
        errors = []

        # Email validation
        if not self.email:
            errors.append("Email is required")
        elif '@' not in self.email or '.' not in self.email:
            errors.append("Invalid email format")
        elif len(self.email) > 255:
            errors.append("Email too long (max 255 characters)")

        # Password validation
        if not self.password:
            errors.append("Password is required")
        elif len(self.password) < 8:
            errors.append("Password must be at least 8 characters")
        elif len(self.password) > 128:
            errors.append("Password too long (max 128 characters)")
        elif not any(c.isupper() for c in self.password):
            errors.append("Password must contain at least one uppercase letter")
        elif not any(c.islower() for c in self.password):
            errors.append("Password must contain at least one lowercase letter")
        elif not any(c.isdigit() for c in self.password):
            errors.append("Password must contain at least one digit")

        # Full name validation
        if not self.full_name:
            errors.append("Full name is required")
        elif len(self.full_name) < 2:
            errors.append("Full name must be at least 2 characters")
        elif len(self.full_name) > 255:
            errors.append("Full name too long (max 255 characters)")

        # Phone validation (optional but must be valid if provided)
        if self.phone:
            phone_digits = ''.join(filter(str.isdigit, self.phone))
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                errors.append("Phone number must be 10-15 digits")

        # Gender validation
        if self.gender and self.gender.lower() not in ['male', 'female', 'other']:
            errors.append("Gender must be 'Male', 'Female', or 'Other'")

        return errors


@dataclass
class UserLogin:
    """Schema for user login."""
    email: str
    password: str

    def validate(self) -> list:
        """Validate login data."""
        errors = []
        if not self.email:
            errors.append("Email is required")
        if not self.password:
            errors.append("Password is required")
        return errors


@dataclass
class UserUpdate:
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PasswordChange:
    """Schema for password change."""
    current_password: str
    new_password: str
    confirm_password: str

    def validate(self) -> list:
        """Validate password change data."""
        errors = []

        if not self.current_password:
            errors.append("Current password is required")

        if not self.new_password:
            errors.append("New password is required")
        elif len(self.new_password) < 8:
            errors.append("New password must be at least 8 characters")
        elif not any(c.isupper() for c in self.new_password):
            errors.append("New password must contain at least one uppercase letter")
        elif not any(c.islower() for c in self.new_password):
            errors.append("New password must contain at least one lowercase letter")
        elif not any(c.isdigit() for c in self.new_password):
            errors.append("New password must contain at least one digit")

        if self.new_password != self.confirm_password:
            errors.append("New password and confirm password do not match")

        if self.current_password == self.new_password:
            errors.append("New password must be different from current password")

        return errors


@dataclass
class PasswordReset:
    """Schema for password reset request."""
    email: str

    def validate(self) -> list:
        """Validate password reset data."""
        errors = []
        if not self.email:
            errors.append("Email is required")
        return errors


@dataclass
class PasswordResetConfirm:
    """Schema for confirming password reset."""
    token: str
    new_password: str
    confirm_password: str

    def validate(self) -> list:
        """Validate password reset confirmation."""
        errors = []

        if not self.token:
            errors.append("Reset token is required")

        if not self.new_password:
            errors.append("New password is required")
        elif len(self.new_password) < 8:
            errors.append("Password must be at least 8 characters")

        if self.new_password != self.confirm_password:
            errors.append("Passwords do not match")

        return errors


@dataclass
class UserResponse:
    """User data returned to client (excludes sensitive fields)."""
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str = "user"
    status: str = "active"
    is_email_verified: bool = False
    is_phone_verified: bool = False
    is_aadhar_verified: bool = False
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: dict) -> 'UserResponse':
        """Create UserResponse from database row."""
        return cls(
            id=row.get('ROWID'),
            email=row.get('Email', ''),
            full_name=row.get('Full_Name', ''),
            phone=row.get('Phone'),
            role=row.get('Role', 'user'),
            status=row.get('Status', 'active'),
            is_email_verified=row.get('Is_Email_Verified', False),
            is_phone_verified=row.get('Is_Phone_Verified', False),
            is_aadhar_verified=row.get('Is_Aadhar_Verified', False),
            date_of_birth=row.get('Date_Of_Birth'),
            gender=row.get('Gender'),
            city=row.get('City'),
            state=row.get('State'),
            last_login_at=row.get('Last_Login_At'),
            created_at=row.get('Created_At'),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TokenResponse:
    """Token response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # seconds
    refresh_expires_in: int = 604800  # 7 days in seconds
    user: Optional[UserResponse] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'refresh_expires_in': self.refresh_expires_in,
        }
        if self.user:
            result['user'] = self.user.to_dict()
        return result


# =============================================================================
# CONSTANTS
# =============================================================================

# Booking limits based on verification status
BOOKING_LIMITS = {
    'unverified': 6,      # Monthly limit for unverified users
    'verified': 12,       # Monthly limit for Aadhar verified users
}

# Token expiration times (in seconds)
TOKEN_EXPIRY = {
    'access_token': 3600,           # 1 hour
    'refresh_token': 604800,        # 7 days
    'reset_token': 3600,            # 1 hour
    'email_verification': 86400,    # 24 hours
}

# Account lockout settings
LOCKOUT_SETTINGS = {
    'max_failed_attempts': 5,
    'lockout_duration_minutes': 30,
}
