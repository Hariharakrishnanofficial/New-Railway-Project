"""
Date conversion helpers for CloudScale database.
Handles conversion between ISO format (YYYY-MM-DD) and Zoho format (DD-MMM-YYYY).
"""

from datetime import datetime, timedelta
from typing import Optional

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def to_zoho_date_only(date_str: Optional[str]) -> Optional[str]:
    """
    Convert 'YYYY-MM-DD' or 'DD-MMM-YYYY HH:MM:SS' → 'DD-MMM-YYYY' for Zoho date fields.
    
    Examples:
        '2026-03-30' → '30-Mar-2026'
        '30-Mar-2026 14:30:00' → '30-Mar-2026'
    """
    if not date_str:
        return None
    
    s = str(date_str).strip()
    
    # Already "DD-MMM-YYYY ..." format
    if len(s) >= 11 and s[2] == '-' and s[6] == '-':
        return s.split(' ')[0]
    
    # "YYYY-MM-DD" format
    if len(s) >= 10 and s[4] == '-' and s[7] == '-':
        try:
            yyyy, mm, dd = s[:10].split('-')
            return f"{dd.zfill(2)}-{MONTHS[int(mm)-1]}-{yyyy}"
        except Exception:
            pass
    
    return s


def to_zoho_datetime(dt_str: Optional[str]) -> str:
    """
    Convert ISO datetime to Zoho format 'DD-MMM-YYYY HH:MM:SS'.
    
    Examples:
        '2026-03-30T14:30:00' → '30-Mar-2026 14:30:00'
        '2026-03-30 14:30:00' → '30-Mar-2026 14:30:00'
    """
    if not dt_str:
        return datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    
    s = str(dt_str).strip()
    
    # Already Zoho format
    if len(s) >= 11 and s[2] == '-' and s[6] == '-':
        return s
    
    try:
        dt = datetime.strptime(s.replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d-%b-%Y %H:%M:%S")
    except Exception:
        pass
    
    return datetime.now().strftime("%d-%b-%Y %H:%M:%S")


def format_zoho_date(date_str: Optional[str]) -> Optional[str]:
    """
    Convert date from 'DD-MMM-YYYY HH:MM:SS' to 'YYYY-MM-DD HH:MM:SS'.
    
    Example:
        '12-Mar-2026 13:08:30' → '2026-03-12 13:08:30'
    """
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%d-%b-%Y %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return date_str


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in various formats to datetime object.
    
    Supported formats:
        - YYYY-MM-DD
        - DD-MMM-YYYY
        - YYYY-MM-DD HH:MM:SS
        - DD-MMM-YYYY HH:MM:SS
    """
    if not date_str:
        return None
    
    s = str(date_str).strip()
    
    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d-%b-%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(s[:len(fmt)+5], fmt)
        except Exception:
            continue
    
    return None


def get_zoho_date_criteria(date_str: str) -> str:
    """
    Convert a date string to Zoho criteria format (DD-MMM-YYYY).
    This is used in ZCQL WHERE clauses.
    """
    dt = parse_date(date_str)
    if dt:
        return dt.strftime('%d-%b-%Y')
    return to_zoho_date_only(date_str) or date_str


def is_within_booking_window(journey_date: str, advance_days: int = 120) -> bool:
    """
    Check if journey date is within the allowed booking window.
    
    Args:
        journey_date: Journey date in any supported format
        advance_days: Maximum days in advance booking is allowed
    
    Returns:
        True if date is valid for booking
    """
    dt = parse_date(journey_date)
    if not dt:
        return False
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    max_date = today + timedelta(days=advance_days)
    
    # Journey must be today or later, and within advance window
    return today <= dt <= max_date


def hours_until(target_datetime: str) -> float:
    """
    Calculate hours until a target datetime.
    
    Args:
        target_datetime: Target datetime in any supported format
    
    Returns:
        Hours until target (negative if target is in the past)
    """
    dt = parse_date(target_datetime)
    if not dt:
        return 0.0
    
    now = datetime.now()
    delta = dt - now
    return delta.total_seconds() / 3600
