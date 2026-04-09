"""
Cookie Signing Module - HMAC-based cookie integrity verification
Implements secure cookie signing to prevent tampering.
"""

import hmac
import hashlib
import logging
from typing import Optional

from config import SESSION_SECRET

logger = logging.getLogger(__name__)


class CookieSigner:
    """
    HMAC-based cookie signer for session integrity.
    
    Uses HMAC-SHA256 to sign cookie values, preventing tampering.
    Format: {value}.{signature}
    """
    
    def __init__(self, secret: str):
        """
        Initialize cookie signer with secret key.
        
        Args:
            secret: Secret key for HMAC signing (should be SESSION_SECRET)
        """
        if not secret or len(secret) < 32:
            raise ValueError("Cookie signing requires secret key >= 32 characters")
        
        self.secret = secret.encode('utf-8')
        self.algorithm = hashlib.sha256
    
    def sign(self, value: str) -> str:
        """
        Sign a cookie value with HMAC.
        
        Args:
            value: Plain cookie value (e.g., session ID)
        
        Returns:
            Signed value in format: {value}.{signature}
        
        Example:
            >>> signer = CookieSigner("my-secret")
            >>> signer.sign("12345")
            "12345.a1b2c3d4e5f6..."
        """
        if not value:
            raise ValueError("Cannot sign empty value")
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret,
            value.encode('utf-8'),
            self.algorithm
        ).hexdigest()
        
        # Return value.signature format
        return f"{value}.{signature}"
    
    def unsign(self, signed_value: str) -> Optional[str]:
        """
        Verify and extract original value from signed cookie.
        
        Args:
            signed_value: Signed value in format {value}.{signature}
        
        Returns:
            Original value if signature valid, None if invalid/tampered
        
        Example:
            >>> signer = CookieSigner("my-secret")
            >>> signer.unsign("12345.a1b2c3d4e5f6...")
            "12345"
            >>> signer.unsign("12345.invalid")
            None
        """
        if not signed_value or '.' not in signed_value:
            logger.warning("Invalid signed cookie format (missing separator)")
            return None
        
        # Split value and signature
        parts = signed_value.rsplit('.', 1)
        if len(parts) != 2:
            logger.warning("Invalid signed cookie format (wrong parts count)")
            return None
        
        value, provided_signature = parts
        
        # Generate expected signature
        expected_signature = hmac.new(
            self.secret,
            value.encode('utf-8'),
            self.algorithm
        ).hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(expected_signature, provided_signature):
            logger.warning(f"Cookie signature mismatch - possible tampering detected")
            return None
        
        return value
    
    def verify(self, signed_value: str) -> bool:
        """
        Verify if signed value is valid without extracting value.
        
        Args:
            signed_value: Signed cookie value
        
        Returns:
            True if signature valid, False otherwise
        """
        return self.unsign(signed_value) is not None


# Global signer instance (initialized with SESSION_SECRET)
_signer: Optional[CookieSigner] = None


def get_signer() -> CookieSigner:
    """Get global cookie signer instance."""
    global _signer
    if _signer is None:
        _signer = CookieSigner(SESSION_SECRET)
    return _signer


def sign_cookie(value: str) -> str:
    """
    Sign a cookie value (convenience function).
    
    Args:
        value: Plain cookie value
    
    Returns:
        Signed value
    """
    return get_signer().sign(value)


def unsign_cookie(signed_value: str) -> Optional[str]:
    """
    Unsign and verify a cookie value (convenience function).
    
    Args:
        signed_value: Signed cookie value
    
    Returns:
        Original value if valid, None if invalid
    """
    return get_signer().unsign(signed_value)


def verify_cookie(signed_value: str) -> bool:
    """
    Verify cookie signature without extracting value (convenience function).
    
    Args:
        signed_value: Signed cookie value
    
    Returns:
        True if valid, False otherwise
    """
    return get_signer().verify(signed_value)
