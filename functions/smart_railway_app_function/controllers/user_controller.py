"""
User Controller

Business logic for user operations.
"""

from typing import Dict, Optional, Tuple
from controllers.base_controller import BaseController
from models.user import User
from core.security import hash_password, verify_password
from config import TABLES


class UserController(BaseController):
    """Controller for user-related operations."""

    def __init__(self):
        super().__init__(TABLES.get('users', 'Users'), User)

    def create_user(self, data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Create new user with password hashing.

        Args:
            data: User data including password

        Returns:
            Tuple of (created user, error message)
        """
        # Hash password before storing
        if 'Password' in data:
            data['Password_Hash'] = hash_password(data.pop('Password'))

        # Check for duplicate email
        existing = self.repo.find_one({'Email': data.get('Email')})
        if existing:
            return None, "Email already registered"

        # Check for duplicate phone
        existing = self.repo.find_one({'Phone': data.get('Phone')})
        if existing:
            return None, "Phone number already registered"

        return self.create(data)

    def authenticate(self, email: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Authenticate user by email and password.

        Returns:
            Tuple of (user data, error message)
        """
        user = self.repo.find_one({'Email': email})
        if not user:
            return None, "Invalid email or password"

        if not user.get('Is_Active', True):
            return None, "Account is deactivated"

        if not verify_password(password, user.get('Password_Hash', '')):
            return None, "Invalid email or password"

        # Remove sensitive data
        user.pop('Password_Hash', None)
        return user, None

    def change_password(self, user_id: str, old_password: str,
                       new_password: str) -> Tuple[bool, Optional[str]]:
        """Change user password."""
        user = self.get_by_id(user_id)
        if not user:
            return False, "User not found"

        if not verify_password(old_password, user.get('Password_Hash', '')):
            return False, "Current password is incorrect"

        new_hash = hash_password(new_password)
        result, error = self.update(user_id, {'Password_Hash': new_hash})
        return result is not None, error

    def get_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        return self.repo.find_one({'Email': email})

    def get_by_phone(self, phone: str) -> Optional[Dict]:
        """Get user by phone number."""
        return self.repo.find_one({'Phone': phone})

    def deactivate_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Deactivate user account."""
        return self.soft_delete(user_id)

    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        from datetime import datetime
        self.update(user_id, {'Last_Login': datetime.now().isoformat()})
