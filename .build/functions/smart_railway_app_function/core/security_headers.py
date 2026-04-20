"""
Security Headers Middleware
Adds comprehensive security headers to all HTTP responses.
"""

import os
from flask import request


class SecurityHeaders:
    """
    Security headers configuration and middleware.
    
    Implements OWASP recommended security headers.
    """
    
    def __init__(self, app=None, config=None):
        """
        Initialize security headers middleware.
        
        Args:
            app: Flask app instance (optional)
            config: Custom headers configuration (optional)
        """
        self.config = config or {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Register security headers with Flask app."""
        app.after_request(self.add_security_headers)
    
    def add_security_headers(self, response):
        """
        Add security headers to response.
        
        Headers added:
        - X-Frame-Options: Prevent clickjacking
        - X-Content-Type-Options: Prevent MIME sniffing
        - X-XSS-Protection: Enable XSS filter (legacy)
        - Referrer-Policy: Control referrer information
        - Permissions-Policy: Control browser features
        - Strict-Transport-Security: Enforce HTTPS (if secure)
        - Content-Security-Policy: Prevent XSS and injection attacks
        """
        
        # X-Frame-Options: Prevent clickjacking
        if 'X-Frame-Options' not in response.headers:
            response.headers['X-Frame-Options'] = self.config.get(
                'x_frame_options', 'DENY'
            )
        
        # X-Content-Type-Options: Prevent MIME sniffing
        if 'X-Content-Type-Options' not in response.headers:
            response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection: Enable browser XSS filter (legacy, but still useful)
        if 'X-XSS-Protection' not in response.headers:
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy: Control referrer information
        if 'Referrer-Policy' not in response.headers:
            response.headers['Referrer-Policy'] = self.config.get(
                'referrer_policy', 'strict-origin-when-cross-origin'
            )
        
        # Permissions-Policy: Control browser features (replaces Feature-Policy)
        if 'Permissions-Policy' not in response.headers:
            permissions = self.config.get('permissions_policy', 
                'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
            )
            response.headers['Permissions-Policy'] = permissions
        
        # Strict-Transport-Security: Enforce HTTPS
        is_secure = request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https'
        is_production = os.getenv('APP_ENVIRONMENT') == 'production'
        
        if is_secure and is_production and 'Strict-Transport-Security' not in response.headers:
            hsts = self.config.get('hsts', 'max-age=31536000; includeSubDomains')
            response.headers['Strict-Transport-Security'] = hsts
        
        # Content-Security-Policy: Prevent XSS and injection attacks
        if 'Content-Security-Policy' not in response.headers:
            csp = self._build_csp()
            response.headers['Content-Security-Policy'] = csp
        
        return response
    
    def _build_csp(self) -> str:
        """
        Build Content Security Policy header.
        
        CSP prevents XSS by controlling which resources can be loaded.
        """
        if 'content_security_policy' in self.config:
            return self.config['content_security_policy']
        
        # Default CSP - ADJUST FOR YOUR APPLICATION
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' data: https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        return "; ".join(csp_directives)


def create_security_headers(app, config=None):
    """
    Factory function to create and attach security headers middleware.
    
    Args:
        app: Flask app instance
        config: Optional custom configuration
    """
    return SecurityHeaders(app, config)
