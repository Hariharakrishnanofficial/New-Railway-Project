"""
Data Formatters

Common formatting functions for display output.
"""

from datetime import datetime
from typing import Optional


def format_currency(amount: float, currency: str = 'INR') -> str:
    """
    Format amount as currency string.

    Args:
        amount: Numeric amount
        currency: Currency code (default: INR)

    Returns:
        Formatted currency string
    """
    if currency == 'INR':
        return f"₹{amount:,.2f}"
    elif currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"


def format_date(date_obj, output_format: str = '%d %b %Y') -> str:
    """
    Format date object or string to display format.

    Args:
        date_obj: datetime object or date string
        output_format: Output format (default: '25 Mar 2024')

    Returns:
        Formatted date string
    """
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except ValueError:
            return date_obj
    return date_obj.strftime(output_format)


def format_datetime(dt_obj, output_format: str = '%d %b %Y %H:%M') -> str:
    """
    Format datetime object or string to display format.

    Args:
        dt_obj: datetime object or datetime string
        output_format: Output format (default: '25 Mar 2024 14:30')

    Returns:
        Formatted datetime string
    """
    if isinstance(dt_obj, str):
        try:
            dt_obj = datetime.fromisoformat(dt_obj.replace('Z', '+00:00'))
        except ValueError:
            return dt_obj
    return dt_obj.strftime(output_format)


def format_pnr(pnr: str) -> str:
    """
    Format PNR for display (add spacing).

    Args:
        pnr: Raw PNR string

    Returns:
        Formatted PNR (e.g., 'ABC 123 4567')
    """
    pnr = pnr.upper().replace(' ', '')
    if len(pnr) == 10:
        return f"{pnr[:3]} {pnr[3:6]} {pnr[6:]}"
    return pnr


def format_duration(minutes: int) -> str:
    """
    Format duration from minutes to human readable.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string (e.g., '5h 30m')
    """
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"


def format_distance(km: float) -> str:
    """
    Format distance in kilometers.

    Args:
        km: Distance in kilometers

    Returns:
        Formatted string (e.g., '1,234 km')
    """
    return f"{km:,.0f} km"


def format_seat_number(coach: str, seat: int) -> str:
    """
    Format seat number for display.

    Args:
        coach: Coach code
        seat: Seat number

    Returns:
        Formatted seat (e.g., 'S5-42')
    """
    return f"{coach}-{seat}"
