"""
Validation helpers for request data.
"""

import re


def validate_email(email):
    """Simple email validation"""
    if not email:
        return False
    pattern = r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'
    return re.match(pattern, email) is not None


def validate_required(data, fields):
    """Check for missing required fields"""
    if not data:
        return False, ["No data provided"]
    missing = [f for f in fields if f not in data or data[f] is None or data[f] == ""]
    return len(missing) == 0, missing


def extract_lookup_id(field):
    """Extract ID from a Zoho lookup field (dict or string)."""
    if isinstance(field, dict):
        return field.get("ID")
    return field  # assume it's already a string ID
