"""
HTTPS Enforcement Middleware
Redirects HTTP requests to HTTPS in production.
"""

import os
import logging
from flask import request, redirect

logger = logging.getLogger(__name__)


class HTTPSEnforcer:
    """
    Middleware to enforce HTTPS in production.
    
    Features:
    - Redirects HTTP to HTTPS (301 permanent redirect)
    - Checks X-Forwarded-Proto header for proxies
    - Respects environment configuration
    - Logs HTTP requests in production
    """
    
    def __init__(self, app=None):
        """
        Initialize HTTPS enforcer.
        
        Args:
            app: Flask app instance (optional)
        """
        self.enabled = os.getenv('APP_ENVIRONMENT') == 'production'
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Register HTTPS enforcer with Flask app."""
        if self.enabled:
            app.before_request(self.enforce_https)
            logger.info("HTTPS enforcement enabled (PRODUCTION MODE)")
        else:
            logger.info("HTTPS enforcement disabled (DEVELOPMENT MODE)")
    
    def enforce_https(self):
        """
        Enforce HTTPS for all requests in production.
        
        Redirects HTTP requests to HTTPS with 301 (permanent redirect).
        """
        if not self.enabled:
            return None
        
        # Check if request is already HTTPS
        is_secure = request.is_secure
        
        # Check X-Forwarded-Proto header (for proxies/load balancers)
        forwarded_proto = request.headers.get('X-Forwarded-Proto', '').lower()
        if forwarded_proto == 'https':
            is_secure = True
        
        if not is_secure:
            # Log insecure request attempt
            logger.warning(f"HTTP request blocked: {request.method} {request.path} from {request.remote_addr}")
            
            # Build HTTPS URL
            url = request.url.replace('http://', 'https://', 1)
            
            # 301 Permanent Redirect
            return redirect(url, code=301)
        
        return None


def create_https_enforcer(app):
    """
    Factory function to create HTTPS enforcer.
    
    Args:
        app: Flask app instance
    
    Returns:
        HTTPSEnforcer instance
    """
    return HTTPSEnforcer(app)
