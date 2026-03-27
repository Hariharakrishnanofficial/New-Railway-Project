"""
Input Validators

Common validation functions for user input.
"""

import re
from datetime import datetime
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number (Indian format).

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Indian mobile: 10 digits starting with 6-9, optionally prefixed with +91 or 91
    pattern = r'^(\+91|91)?[6-9]\d{9}$'
    return bool(re.match(pattern, cleaned))


def validate_date(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """
    Validate date string format.

    Args:
        date_str: Date string to validate
        format_str: Expected format (default: YYYY-MM-DD)

    Returns:
        True if valid, False otherwise
    """
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def validate_time(time_str: str, format_str: str = '%H:%M') -> bool:
    """
    Validate time string format.

    Args:
        time_str: Time string to validate
        format_str: Expected format (default: HH:MM)

    Returns:
        True if valid, False otherwise
    """
    if not time_str:
        return False
    try:
        datetime.strptime(time_str, format_str)
        return True
    except ValueError:
        return False


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input to prevent SQL injection.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ''
    # Escape SQL special characters
    sanitized = value.replace("'", "''")
    sanitized = sanitized.replace('"', '')
    sanitized = sanitized.replace(';', '')
    sanitized = sanitized.replace('--', '')
    sanitized = sanitized.replace('/*', '')
    sanitized = sanitized.replace('*/', '')
    # Truncate to max length
    return sanitized[:max_length]


def validate_pnr(pnr: str) -> bool:
    """
    Validate PNR format (10 alphanumeric characters).

    Args:
        pnr: PNR to validate

    Returns:
        True if valid, False otherwise
    """
    if not pnr:
        return False
    pattern = r'^[A-Z0-9]{10}$'
    return bool(re.match(pattern, pnr.upper()))


def validate_train_number(train_number: str) -> bool:
    """
    Validate train number format.

    Args:
        train_number: Train number to validate

    Returns:
        True if valid, False otherwise
    """
    if not train_number:
        return False
    # Indian Railways train numbers: 5 digits
    pattern = r'^\d{5}$'
    return bool(re.match(pattern, train_number))


def validate_station_code(code: str) -> bool:
    """
    Validate station code format.

    Args:
        code: Station code to validate

    Returns:
        True if valid, False otherwise
    """
    if not code:
        return False
    # Station codes: 2-5 uppercase letters
    pattern = r'^[A-Z]{2,5}$'
    return bool(re.match(pattern, code.upper()))
