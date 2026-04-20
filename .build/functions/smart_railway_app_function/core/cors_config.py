"""
CORS Configuration Module
Secure Cross-Origin Resource Sharing configuration.
"""

import os
import logging
from urllib.parse import urlparse

from flask import request
from typing import List, Optional

logger = logging.getLogger(__name__)

_CATALYST_DEV_ORIGIN_SUFFIX = ".development.catalystserverless.in"

def _normalize_origin(origin: str) -> str:
    """Normalize an Origin for strict comparisons (no path/query; no trailing slash)."""
    origin = (origin or "").strip()
    if origin.endswith('/'):
        origin = origin[:-1]

    try:
        parsed = urlparse(origin)
        if parsed.scheme and parsed.netloc:
            host = (parsed.hostname or "").lower()
            if not host:
                return origin
            netloc = host
            if parsed.port:
                netloc = f"{host}:{parsed.port}"
            return f"{parsed.scheme.lower()}://{netloc}"
    except Exception:
        return origin

    return origin


def _is_catalyst_dev_origin(origin: str) -> bool:
    """Allow Catalyst development serverless origins by host suffix."""
    try:
        parsed = urlparse((origin or "").strip())
        host = (parsed.hostname or "").lower()
        return bool(host) and host.endswith(_CATALYST_DEV_ORIGIN_SUFFIX)
    except Exception:
        return False


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
        raw_origins = allowed_origins or self._get_default_origins()
        self.allowed_origins = sorted({_normalize_origin(o) for o in raw_origins if o})
        
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
            
            validated.append(_normalize_origin(origin))
        
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
        
        norm_origin = _normalize_origin(origin)

        # Exact match required for cross-origin, but treat same-origin as allowed.
        if norm_origin in self.allowed_origins:
            return True

        # Catalyst dev deployments use dynamic subdomains; allow by suffix.
        if _is_catalyst_dev_origin(norm_origin):
            return True

        try:
            forwarded_proto = (request.headers.get('X-Forwarded-Proto') or '').split(',')[0].strip()
            forwarded_host = (request.headers.get('X-Forwarded-Host') or '').split(',')[0].strip()

            scheme = forwarded_proto or request.scheme
            host = forwarded_host or request.host

            same_origin = _normalize_origin(f"{scheme}://{host}")
            if norm_origin == same_origin:
                return True
        except Exception:
            pass

        logger.warning(f"CORS: Blocked origin: {origin}")
        return False
    
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
