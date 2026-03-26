"""
Date conversion helpers for CloudScale database.
"""

from datetime import datetime


def to_zoho_date_only(date_str):
    """Convert 'YYYY-MM-DD' or 'DD-MMM-YYYY HH:MM:SS' → 'DD-MMM-YYYY' for Zoho date fields."""
    if not date_str:
        return None
    MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
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


def format_zoho_date(date_str):
    """
    Convert date from 'DD-MMM-YYYY HH:MM:SS' to 'YYYY-MM-DD HH:MM:SS'
    Example: '12-Mar-2026 13:08:30' -> '2026-03-12 13:08:30'
    """
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%d-%b-%Y %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # if already in correct format, return as is
        return date_str


def to_zoho_datetime(dt_str):
    """Convert ISO datetime to Zoho format 'DD-MMM-YYYY HH:MM:SS'."""
    MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    if not dt_str:
        return datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    s = str(dt_str).strip()
    if len(s) >= 11 and s[2] == '-' and s[6] == '-':
        return s  # already Zoho format
    try:
        dt = datetime.strptime(s.replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d-%b-%Y %H:%M:%S")
    except Exception:
        pass
    return datetime.now().strftime("%d-%b-%Y %H:%M:%S")
