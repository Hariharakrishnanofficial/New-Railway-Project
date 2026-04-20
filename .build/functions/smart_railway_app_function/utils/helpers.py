"""
Helper Functions

General utility functions for the application.
"""

import random
import string
from datetime import datetime
from typing import Optional
import math


def generate_pnr(prefix: str = 'SR') -> str:
    """
    Generate a unique PNR (Passenger Name Record).

    Args:
        prefix: PNR prefix (default: 'SR' for Smart Railway)

    Returns:
        10-character alphanumeric PNR
    """
    # Format: SR + 2 random letters + 6 random digits
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    digits = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{letters}{digits}"


def generate_booking_reference() -> str:
    """
    Generate a unique booking reference.

    Returns:
        Booking reference string (e.g., 'BK2024032700001')
    """
    date_part = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=5))
    return f"BK{date_part}{random_part}"


def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID for payments.

    Returns:
        Transaction ID string
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TXN{timestamp}{random_part}"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_fare(base_fare: float, distance_km: float, class_multiplier: float = 1.0) -> float:
    """
    Calculate ticket fare based on distance.

    Args:
        base_fare: Base fare amount
        distance_km: Journey distance in km
        class_multiplier: Class-based fare multiplier

    Returns:
        Calculated fare amount
    """
    # Simple fare calculation: base + (distance * rate * class_multiplier)
    distance_rate = 0.75  # Rs per km
    fare = base_fare + (distance_km * distance_rate * class_multiplier)
    return round(fare, 2)


def calculate_arrival_time(departure_time: str, duration_minutes: int) -> str:
    """
    Calculate arrival time from departure and duration.

    Args:
        departure_time: Departure time in HH:MM format
        duration_minutes: Journey duration in minutes

    Returns:
        Arrival time in HH:MM format
    """
    dep = datetime.strptime(departure_time, '%H:%M')
    hours = duration_minutes // 60
    minutes = duration_minutes % 60

    total_minutes = dep.hour * 60 + dep.minute + duration_minutes
    arr_hour = (total_minutes // 60) % 24
    arr_minute = total_minutes % 60

    return f"{arr_hour:02d}:{arr_minute:02d}"


def mask_email(email: str) -> str:
    """
    Mask email for privacy (show first 2 and domain).

    Args:
        email: Email address

    Returns:
        Masked email (e.g., 'ra***@gmail.com')
    """
    if '@' not in email:
        return email
    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[:2] + '***'
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for privacy.

    Args:
        phone: Phone number

    Returns:
        Masked phone (e.g., '98****1234')
    """
    cleaned = ''.join(c for c in phone if c.isdigit())
    if len(cleaned) < 6:
        return phone
    return f"{cleaned[:2]}****{cleaned[-4:]}"


def paginate_result(items: list, page: int = 1, per_page: int = 20) -> dict:
    """
    Paginate a list of items.

    Args:
        items: List of items
        page: Current page number (1-indexed)
        per_page: Items per page

    Returns:
        Dictionary with paginated data and metadata
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page

    return {
        'data': items[start:end],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }
    }
