"""
Base Controller

Abstract base class for all MVC controllers.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from flask import jsonify, request
from repositories.cloudscale_repository import CloudScaleRepository
from models.base_model import BaseModel


class BaseController:
    """
    Base controller class with common CRUD operations.

    All controllers inherit from this class and can override
    methods for custom business logic.
    """

    def __init__(self, table_name: str, model_class: type = None):
        """
        Initialize controller with repository.

        Args:
            table_name: CloudScale table name
            model_class: Model class for validation
        """
        self.table_name = table_name
        self.model_class = model_class
        self.repo = CloudScaleRepository(table_name)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_all(self, page: int = 1, limit: int = 20,
                filters: Dict = None) -> Tuple[List[Dict], Dict]:
        """
        Get all records with pagination.

        Returns:
            Tuple of (data list, pagination metadata)
        """
        try:
            offset = (page - 1) * limit
            data = self.repo.get_all(limit=limit, offset=offset)

            # Get total count for pagination
            total = self.repo.count(filters)
            total_pages = (total + limit - 1) // limit

            pagination = {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
            }

            return data, pagination

        except Exception as e:
            self.logger.error(f"Error in get_all: {e}")
            return [], {'page': 1, 'limit': limit, 'total': 0, 'total_pages': 0}

    def get_by_id(self, record_id: str) -> Optional[Dict]:
        """Get single record by ID."""
        try:
            return self.repo.get_by_id(record_id)
        except Exception as e:
            self.logger.error(f"Error in get_by_id: {e}")
            return None

    def create(self, data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Create new record.

        Returns:
            Tuple of (created record, error message)
        """
        try:
            # Validate using model if available
            if self.model_class:
                model = self.model_class.from_dict(data)
                error = model.validate()
                if error:
                    return None, error

            result = self.repo.create(data)
            return result, None

        except Exception as e:
            self.logger.error(f"Error in create: {e}")
            return None, str(e)

    def update(self, record_id: str, data: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Update existing record.

        Returns:
            Tuple of (updated record, error message)
        """
        try:
            # Check if record exists
            existing = self.repo.get_by_id(record_id)
            if not existing:
                return None, "Record not found"

            result = self.repo.update(record_id, data)
            return result, None

        except Exception as e:
            self.logger.error(f"Error in update: {e}")
            return None, str(e)

    def delete(self, record_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete record by ID.

        Returns:
            Tuple of (success boolean, error message)
        """
        try:
            # Check if record exists
            existing = self.repo.get_by_id(record_id)
            if not existing:
                return False, "Record not found"

            success = self.repo.delete(record_id)
            return success, None

        except Exception as e:
            self.logger.error(f"Error in delete: {e}")
            return False, str(e)

    def soft_delete(self, record_id: str) -> Tuple[bool, Optional[str]]:
        """Soft delete by setting Is_Active to False."""
        return self.update(record_id, {'Is_Active': False})

    # Response helpers
    def success_response(self, data: Any, message: str = "Success",
                        status_code: int = 200) -> Tuple[Dict, int]:
        """Create success response."""
        return {
            'success': True,
            'message': message,
            'data': data
        }, status_code

    def error_response(self, message: str, status_code: int = 400) -> Tuple[Dict, int]:
        """Create error response."""
        return {
            'success': False,
            'error': message
        }, status_code

    def paginated_response(self, data: List, pagination: Dict,
                          message: str = "Success") -> Tuple[Dict, int]:
        """Create paginated response."""
        return {
            'success': True,
            'message': message,
            'data': data,
            'pagination': pagination
        }, 200
