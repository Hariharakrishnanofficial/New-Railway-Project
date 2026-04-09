"""
Base Model

Abstract base class for all entity models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class BaseModel:
    """
    Base model class with common fields and methods.

    All entity models inherit from this class.
    """
    ROWID: Optional[str] = None
    CREATORID: Optional[str] = None
    CREATEDTIME: Optional[str] = None
    MODIFIEDTIME: Optional[str] = None

    # Table name - override in child classes
    __tablename__: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {k: v for k, v in asdict(self).items()
                if not k.startswith('_') and v is not None}

    def to_json(self) -> Dict[str, Any]:
        """Convert model to JSON-safe dictionary."""
        data = self.to_dict()
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary."""
        # Filter only valid fields
        valid_fields = {k: v for k, v in data.items()
                       if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

    @classmethod
    def get_table_name(cls) -> str:
        """Get CloudScale table name."""
        return cls.__tablename__

    @classmethod
    def get_required_fields(cls) -> List[str]:
        """Get list of required fields (override in child)."""
        return []

    def validate(self) -> Optional[str]:
        """
        Validate model data.

        Returns:
            Error message if validation fails, None if valid
        """
        required = self.get_required_fields()
        data = self.to_dict()

        missing = [f for f in required if not data.get(f)]
        if missing:
            return f"Missing required fields: {', '.join(missing)}"
        return None
