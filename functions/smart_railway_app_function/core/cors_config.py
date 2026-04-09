"""
CORS Configuration Module
Secure Cross-Origin Resource Sharing configuration.
"""

import os
import logging
from flask import request
from typing import List, Optional

logger = logging.getLogger(__name__)


class CORSConfig:
    """
    CORS configuration manager with strict origin validation.
    """
    
    def __init__(self, allowed_origins: Optional[List[str]] = None):
        """
        Initialize CORS configuration.
        
        Args:
            allowed_origins: List of allowed origins (must be explicit)
        """
        self.allowed_origins = allowed_origins or self._get_default_origins()
        
        # Validate no wildcards when using credentials
        if '*' in self.allowed_origins:
            logger.error("CORS: Wildcard (*) not allowed with credentials")
            raise ValueError("Cannot use wildcard origin with credentials")
        
        logger.info(f"CORS: Allowed origins: {self.allowed_origins}")
    
    def _get_default_origins(self) -> List[str]:
        """Get default allowed origins from environment."""
        env_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
        
        if not env_origins:
            # Default for development
            is_dev = os.getenv('APP_ENVIRONMENT') == 'development'
            if is_dev:
                return [
                    'http://localhost:3000',
                    'http://localhost:3001',
                    'http://127.0.0.1:3000',
                    'http://127.0.0.1:3001',
                ]
            else:
                # Production MUST specify origins
                logger.error("CORS: No allowed origins configured in production!")
                return []
        
        # Parse comma-separated list
        origins = [o.strip() for o in env_origins.split(',') if o.strip()]
        
        # Validate each origin
        validated = []
        for origin in origins:
            if origin == '*':
                logger.error("CORS: Wildcard not allowed")
                continue
            
            if not origin.startswith(('http://', 'https://')):
                logger.warning(f"CORS: Invalid origin {origin} (missing scheme)")
                continue
            
            validated.append(origin)
        
        return validated
    
    def is_allowed(self, origin: Optional[str]) -> bool:
        """
        Check if origin is allowed.
        
        Args:
            origin: Origin header value
        
        Returns:
            True if origin is in allowed list
        """
        if not origin:
            return False
        
        # Exact match required
        is_allowed = origin in self.allowed_origins
        
        if not is_allowed:
            logger.warning(f"CORS: Blocked origin: {origin}")
        
        return is_allowed
    
    def get_allowed_origin(self, request_origin: Optional[str]) -> Optional[str]:
        """
        Get allowed origin for response header.
        
        Args:
            request_origin: Origin from request header
        
        Returns:
            Origin to set in Access-Control-Allow-Origin, or None if not allowed
        """
        if self.is_allowed(request_origin):
            return request_origin
        return None


def create_cors_middleware(app, allowed_origins: Optional[List[str]] = None):
    """
    Create CORS middleware for Flask app.
    
    Args:
        app: Flask app instance
        allowed_origins: List of allowed origins (optional)
    """
    cors_config = CORSConfig(allowed_origins)
    
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to response."""
        origin = request.headers.get('Origin')
        
        # Get allowed origin (validated)
        allowed_origin = cors_config.get_allowed_origin(origin)
        
        if allowed_origin:
            # Set specific origin (never *)
            response.headers['Access-Control-Allow-Origin'] = allowed_origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Always set these (even if origin not allowed)
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.headers['Vary'] = 'Origin'  # Important for caching
        
        return response
    
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight OPTIONS requests."""
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return add_cors_headers(response)
    
    return cors_config
