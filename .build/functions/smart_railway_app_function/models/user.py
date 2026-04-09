"""
User Model

Entity schema for Users table.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from models.base_model import BaseModel


@dataclass
class User(BaseModel):
    """User entity model."""

    __tablename__ = 'Users'

    # Core fields
    User_Name: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    Password_Hash: Optional[str] = None

    # Profile fields
    First_Name: Optional[str] = None
    Last_Name: Optional[str] = None
    Date_Of_Birth: Optional[str] = None
    Gender: Optional[str] = None
    Address: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    Pincode: Optional[str] = None

    # Account fields
    Role: str = 'passenger'  # passenger, admin, operator
    Is_Active: bool = True
    Is_Verified: bool = False
    Last_Login: Optional[str] = None

    @classmethod
    def get_required_fields(cls) -> List[str]:
        return ['User_Name', 'Email', 'Phone', 'Password_Hash']

    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.First_Name and self.Last_Name:
            return f"{self.First_Name} {self.Last_Name}"
        return self.User_Name or ''

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.Role == 'admin'

    def is_operator(self) -> bool:
        """Check if user has operator role."""
        return self.Role in ['admin', 'operator']
