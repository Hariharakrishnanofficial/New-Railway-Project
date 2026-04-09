"""
Unit tests for cookie signing module.
"""

import pytest
from core.cookie_signer import CookieSigner, sign_cookie, unsign_cookie


def test_sign_and_unsign():
    """Test basic sign/unsign flow."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    # Sign a value
    signed = signer.sign("12345678901234567890")
    assert '.' in signed
    assert signed.startswith("12345678901234567890.")
    
    # Unsign should return original value
    unsigned = signer.unsign(signed)
    assert unsigned == "12345678901234567890"


def test_tampered_signature_rejected():
    """Test that tampered signatures are rejected."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    signed = signer.sign("12345678901234567890")
    
    # Tamper with signature
    tampered = signed[:-5] + "xxxxx"
    
    # Should return None
    result = signer.unsign(tampered)
    assert result is None


def test_tampered_value_rejected():
    """Test that tampered values are rejected."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    signed = signer.sign("12345678901234567890")
    parts = signed.split('.')
    
    # Tamper with value
    tampered = "99999999999999999999." + parts[1]
    
    # Should return None (signature won't match)
    result = signer.unsign(tampered)
    assert result is None


def test_invalid_format_rejected():
    """Test that invalid formats are rejected."""
    signer = CookieSigner("test-secret-key-minimum-32-chars-long")
    
    # No separator
    assert signer.unsign("12345678901234567890") is None
    
    # Empty value
    assert signer.unsign("") is None
    
    # Only separator
    assert signer.unsign(".") is None


def test_different_secrets_incompatible():
    """Test that different secrets produce different signatures."""
    signer1 = CookieSigner("secret-key-one-minimum-32-chars-long!")
    signer2 = CookieSigner("secret-key-two-minimum-32-chars-long!")
    
    signed1 = signer1.sign("12345678901234567890")
    
    # Signer2 should not be able to unsign signer1's cookies
    result = signer2.unsign(signed1)
    assert result is None


def test_convenience_functions():
    """Test convenience wrapper functions."""
    # These use the global signer with SESSION_SECRET
    value = "test-session-id-12345678"
    
    # Sign
    signed = sign_cookie(value)
    assert '.' in signed
    
    # Unsign
    unsigned = unsign_cookie(signed)
    assert unsigned == value
    
    # Tampered should fail
    tampered = signed[:-5] + "xxxxx"
    assert unsign_cookie(tampered) is None
