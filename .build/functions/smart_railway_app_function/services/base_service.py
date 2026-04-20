"""
Base Service Class

Provides common functionality for all service classes.
"""

import logging
from typing import Any, Dict, List, Optional
from repositories.cloudscale_repository import CloudScaleRepository

logger = logging.getLogger(__name__)


class BaseService:
    """Base class for all services with common functionality."""

    def __init__(self, table_name: str):
        """
        Initialize the base service.

        Args:
            table_name: The CloudScale table this service operates on
        """
        self.table_name = table_name
        self.repo = CloudScaleRepository(table_name)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a record by its ID."""
        try:
            return self.repo.get_by_id(record_id)
        except Exception as e:
            self.logger.error(f"Error getting {self.table_name} by ID {record_id}: {e}")
            return None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all records with pagination."""
        try:
            return self.repo.get_all(limit=limit, offset=offset)
        except Exception as e:
            self.logger.error(f"Error getting all {self.table_name}: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new record."""
        try:
            return self.repo.create(data)
        except Exception as e:
            self.logger.error(f"Error creating {self.table_name}: {e}")
            return None

    def update(self, record_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing record."""
        try:
            return self.repo.update(record_id, data)
        except Exception as e:
            self.logger.error(f"Error updating {self.table_name} {record_id}: {e}")
            return None

    def delete(self, record_id: str) -> bool:
        """Delete a record by ID."""
        try:
            return self.repo.delete(record_id)
        except Exception as e:
            self.logger.error(f"Error deleting {self.table_name} {record_id}: {e}")
            return False

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> Optional[str]:
        """
        Validate that all required fields are present.

        Returns:
            Error message if validation fails, None if valid
        """
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return f"Missing required fields: {', '.join(missing)}"
        return None
